import os
import json
import chromadb
from openai import OpenAI
from dotenv import load_dotenv
import uuid

# 加载环境变量
# 优先加载 config.env，规避 gitignore/cursorignore 问题
env_path = os.path.join(os.path.dirname(__file__), 'config.env')
if os.path.exists(env_path):
    load_dotenv(env_path, override=True)
else:
    # 备选: 尝试加载 .env.local 或 .env
    local_env = os.path.join(os.path.dirname(__file__), '.env.local')
    if os.path.exists(local_env):
        load_dotenv(local_env, override=True)
    else:
        load_dotenv()

# 配置
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-3.5-turbo")
# Qwen-VL 多模态视觉模型（用于OCR）
VL_MODEL_NAME = os.getenv("VL_MODEL_NAME", "qwen-vl-max-latest")
# 阿里云 Qwen 的 Embedding 模型通常为 text-embedding-v1
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-v1")

# 初始化客户端
client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)

# 初始化 ChromaDB
# 初始化 ChromaDB
base_dir = os.path.dirname(os.path.abspath(__file__))
chroma_db_path = os.path.join(base_dir, "data", "chroma_db")
chroma_client = chromadb.PersistentClient(path=chroma_db_path)

# Collections
candidates_collection = chroma_client.get_or_create_collection(name="candidates")
jobs_collection = chroma_client.get_or_create_collection(name="jobs")

from database import SessionLocal, SystemPrompt

class AIService:
    
    @staticmethod
    def _clean_json_string(text):
        """Clean markdown formatting from JSON string and fix common issues"""
        import re
        if not text: return ""
        text = text.strip()
        
        # 1. Remove markdown code blocks first
        if "```" in text:
            match = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
            if match:
                text = match.group(1).strip()
        
        # 2. Try to find the first '{' and last '}'
        start_idx = text.find('{')
        end_idx = text.rfind('}')
        
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            text = text[start_idx : end_idx + 1]
        
        # 3. Fix common JSON issues
        # Remove trailing commas before } or ]
        text = re.sub(r',\s*([\}\]])', r'\1', text)
        
        # Fix incomplete strings at the end (common with truncated responses)
        # If there's an unclosed string, try to close it
        if text.count('"') % 2 != 0:
            # Find the last unclosed quote and close the structure
            text = text.rstrip()
            if not text.endswith('}'):
                # Try to close gracefully
                text = text + '"}'
        
        return text

    @staticmethod
    def get_active_prompt(prompt_type, prompt_role='system'):
        session = SessionLocal()
        try:
            prompt = session.query(SystemPrompt).filter_by(prompt_type=prompt_type, prompt_role=prompt_role, is_active=True).order_by(SystemPrompt.created_at.desc()).first()
            if prompt:
                return prompt.content
            return "" 
        finally:
            session.close()

    @staticmethod
    def get_embedding(text):
        """获取文本的 Embedding 向量"""
        if not text:
            return []
        try:
            # 截断文本以符合 Embedding 模型限制
            # qwen-max 只是 Chat 模型，Embedding 依然受限于 text-embedding-v1 的输入长度 (2048 tokens)
            # 但为了尽可能多地保留信息，我们稍微放宽一点，如果 API 支持自动截断最好，否则手动截断
            # 这里改为 2000 字符，尽量利用窗口
            safe_text = text[:2000]
            
            response = client.embeddings.create(
                input=safe_text,
                model=EMBEDDING_MODEL
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Embedding Error: {e}")
            return []

    @staticmethod
    def parse_resume(text, user_prompt_template=None):
        """
        使用 LLM 分析简历文本，提取结构化数据。
        返回 JSON 格式。
        """
        system_prompt = AIService.get_active_prompt('candidate', 'system')
        if not system_prompt:
             # Fallback if DB is empty
             system_prompt = """
你是一个专业的招聘专家。请仔细分析以下简历文本。

🚨 核心要求：【禁止精简或概括】工作内容，必须【逐条完整提取】每一条工作经历的原始描述。
请严格返回 JSON 格式，不要包含 Markdown 代码块标记。

需要提取的字段说明：

**基础信息：**
- name: 姓名
- email: 邮箱
- phone: 电话
- age: 年龄 (数字，如无法确定则为null)
- expect_location: 期望工作地点（如无则取当前所在城市）
- education_level: 最高学历（本科/硕士/博士等）
- current_company: 当前或最近一家公司
- current_title: 当前或最近职位
- experience_years: 工作年限 (数字)

**教育经历 (education_details)：**
列表，每项包含:
{
    "school": "学校名",
    "degree": "学位",
    "major": "专业",
    "year": "年份范围",
    "courses": "主修课程（如有）"
}

**工作经历 (work_experiences)：**
列表，每项包含:
{
    "company": "公司名",
    "title": "职位",
    "time": "起止时间",
    "details": ["工作内容1完整原文", "工作内容2完整原文", ...]
}

🚨🚨🚨 极其重要 - 必须遵守：
1. details数组必须包含该职位下的【每一条】工作内容的【完整原文】
2. 【禁止】精简、概括、合并工作内容，必须保留原始表述
3. 每个bullet point（●、•、-、数字编号）都是一条独立的工作内容
4. 如果原文有5条工作内容，details数组就必须有5个元素
5. 不要使用description字段，所有内容放到details数组中

**项目经历 (project_experiences)：**
如果简历中有明确的"项目经历"部分，提取为列表，每项包含:
{
    "name": "项目名",
    "role": "角色",
    "time": "时间",
    "description": "项目描述与成果"
}
如果工作内容中包含具体项目（如"XX项目"、"XX系统"），也可提取为项目经历。

**奖项/成果 (awards_achievements)：**
列表，每项包含:
{
    "type": "类型（荣誉/竞赛/论文/专利）",
    "title": "名称",
    "time": "时间",
    "description": "描述"
}

**技能 (skills)：**
技能列表 (数组)，提取所有提到的技能、工具、语言等

**个人总结 (summary)：**
请生成一份 200-300 字的深度分析，包含：
1) 核心竞争力与亮点
2) 职业发展路径总结
3) 潜在风险或短板
请使用 Markdown 格式进行分点描述。

**备注 (notes)：**
其他无法归类的信息，如个人总结原文、自我评价、兴趣爱好等
"""
        
        # Prepare User Content - 增加截断长度以保留更多内容
        if user_prompt_template:
            user_content = user_prompt_template.replace("{raw_text}", text[:8000])
        else:
            user_content = text[:8000]

        try:
            # Ensure JSON instruction is explicit for models that require it in messages
            # Force append JSON instruction to system prompt to satisfy API requirement
            if "json" not in system_prompt.lower():
                system_prompt += "\n请务必返回合法的 JSON 格式。"
            
            print(f"🚀 开始调用LLM解析简历，文本长度: {len(user_content)} 字符")
            
            # 重试逻辑
            max_retries = 3
            content = None
            for attempt in range(max_retries):
                try:
                    response = client.chat.completions.create(
                        model=MODEL_NAME,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_content}
                        ],
                        temperature=0.1,
                        max_tokens=8000,  # 增加token上限确保完整输出
                        response_format={"type": "json_object"},
                        timeout=180  # 3分钟超时
                    )
                    content = response.choices[0].message.content
                    break  # 成功则跳出重试
                except Exception as retry_error:
                    print(f"⚠️ 尝试 {attempt+1}/{max_retries} 失败: {type(retry_error).__name__}")
                    if attempt < max_retries - 1:
                        import time
                        time.sleep(5)  # 等待5秒后重试
                    else:
                        raise retry_error  # 最后一次失败则抛出
            print(f"✅ LLM返回成功，长度: {len(content) if content else 0} 字符")
            print(f"📝 parse_resume原始返回（前1000字符）: {content[:1000] if content else 'None'}")
            content = AIService._clean_json_string(content)
            result = json.loads(content)
            print(f"✅ JSON解析成功，候选人: {result.get('name', 'N/A')}")
            return result
        except json.JSONDecodeError as e:
            print(f"❌ JSON解析失败: {e}")
            print(f"❌ 原始内容: {content[:2000] if content else 'None'}")
            return {
                "name": "Parse Error",
                "skills": [],
                "summary": f"JSON解析失败: {str(e)}"
            }
        except Exception as e:
            print(f"❌ LLM Error: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            # 返回默认空结构以防程序崩溃
            return {
                "name": "Parse Error",
                "skills": [],
                "summary": f"AI 解析失败: {type(e).__name__}: {str(e)}"
            }

    @staticmethod
    def parse_job(text, user_prompt_template=None):
        """
        使用 LLM 分析 JD 文本，提取结构化数据。
        """
        system_prompt = AIService.get_active_prompt('job', 'system')
        if not system_prompt:
             system_prompt = "你是一个专业的招聘专家。请分析以下职位描述 (JD)，并提取关键信息。请严格返回 JSON 格式。"

        # Prepare User Content
        if user_prompt_template:
            user_content = user_prompt_template.replace("{raw_text}", text[:4000])
        else:
            user_content = text[:4000]

        try:
            # Ensure JSON instruction is explicit for models that require it in messages
            messages = [
                {"role": "system", "content": system_prompt + "\nIMPORTANT: Output must be valid JSON. Do not use markdown code blocks."},
                {"role": "user", "content": user_content}
            ]
            
            # Add 'json' to the messages if it's missing to satisfy the API requirement
            if 'json' not in system_prompt.lower():
                 messages[0]['content'] += " Please respond in JSON format."

            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content
            content = AIService._clean_json_string(content)
            return json.loads(content)
        except Exception as e:
            print(f"LLM Error: {e}")
            return {
                "title": "Parse Error", 
                "analysis": {}
            }

    @staticmethod
    def ocr_job_image(image_base64):
        """
        使用 Qwen-VL 多模态模型识别 JD 图片并提取结构化信息。
        
        Args:
            image_base64: Base64 编码的图片数据
            
        Returns:
            dict: {
                "title": "职位名称",
                "company": "公司名称",
                "jd_text": "完整JD文本",
                "location": "工作地点",
                "experience_years": 经验年限
            }
        """
        system_prompt = """你是一个专业的招聘信息识别专家。请仔细识别图片中的**所有文字内容**，特别注意图片顶部的元信息。

请提取以下信息并返回 JSON 格式：
{
    "title": "职位名称（如：AI产品经理、算法工程师等）",
    "company": "公司名称（如：字节跳动、阿里巴巴等，可从团队介绍中推断）",
    "location": "工作地点（重点看图片顶部标签，如：北京、上海等）",
    "experience_years": 经验年限要求（数字，如：3表示3年以上）,
    "jd_text": "完整的职位描述文本，包括职位描述和职位要求，保持原文格式"
}

★★★ 重要提示 ★★★
1. **location（地点）通常在图片最上方**，格式如"北京 | 正式 | 产品经理"，请仔细查看图片顶部
2. 如果顶部有类似"北京"、"上海"、"深圳"等城市名，请提取到location字段
3. 公司名称如果图片中没有明确写，可以从"团队介绍"中的公司名推断
4. jd_text 请尽可能完整地提取所有文字内容
5. experience_years 请提取数字，如"3年及以上"提取为3"""

        try:
            response = client.chat.completions.create(
                model=VL_MODEL_NAME,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_base64}"
                                }
                            },
                            {
                                "type": "text",
                                "text": "请识别这张JD图片中的所有文字内容，并提取结构化信息。"
                            }
                        ]
                    }
                ],
                temperature=0.1,
                max_tokens=4096
            )
            content = response.choices[0].message.content
            content = AIService._clean_json_string(content)
            result = json.loads(content)
            print(f"✅ OCR识别成功: {result.get('title', 'N/A')}")
            return result
        except Exception as e:
            print(f"OCR Error: {e}")
            return {
                "title": "",
                "company": "",
                "jd_text": f"图片识别失败: {str(e)}",
                "location": "",
                "experience_years": None
            }

    @staticmethod
    def ocr_resume_image(image_base64):
        """
        使用 Qwen-VL 多模态模型识别简历图片并提取结构化信息。
        
        Args:
            image_base64: Base64 编码的图片数据
            
        Returns:
            dict: 与 parse_resume 返回格式一致的结构化简历数据
        """
        system_prompt = """你是一个专业的简历识别专家。请仔细识别图片中的**所有文字内容**，提取候选人的完整信息。

请提取以下信息并返回 JSON 格式：
{
    "name": "姓名",
    "email": "邮箱",
    "phone": "电话号码",
    "age": 年龄（数字，如无法确定则为null）,
    "expect_location": "期望工作地点",
    "education_level": "最高学历（如：博士/硕士/本科/大专）",
    "current_company": "当前或最近一家公司（如在校学生则为学校名）",
    "current_title": "当前或最近职位（如在校学生则为学生/研究生）",
    "experience_years": 工作年限（数字，在校生可为0）,
    "skills": ["技能1", "技能2", "技能3"],
    "education_details": [
        {"school": "学校名", "degree": "学位", "major": "专业", "year": "年份范围", "description": "相关课程或研究方向"}
    ],
    "work_experiences": [
        {"company": "公司名", "title": "职位", "time": "起止时间", "description": "主要工作内容"}
    ],
    "project_experiences": [
        {"name": "项目名", "role": "角色", "time": "时间", "description": "项目描述"}
    ],
    "awards_achievements": [
        {"type": "类型（奖项/荣誉/科研成果/竞赛/论文）", "title": "名称", "time": "时间", "description": "详细描述"}
    ],
    "summary": "候选人核心竞争力总结（100-200字）",
    "notes": "其他无法归类的信息（如学生工作、社团活动、自我评价等）",
    "raw_text": "图片中识别到的完整原文"
}

★★★ 重要提示 ★★★
1. 请尽可能完整地识别图片中的所有文字
2. 工作经历请按时间倒序排列（最近的在前）
3. 技能请提取所有出现的技术关键词
4. 如果是多页简历图片，请提取所有页面的内容
5. 联系方式（电话、邮箱）通常在简历顶部或底部

★★★ 特别说明 - awards_achievements字段 ★★★
请将以下内容提取到 awards_achievements 数组中：
- 所获荣誉（如：奖学金、三好学生、优秀毕业生等）
- 竞赛获奖（如：ACM、数学建模、Kaggle比赛等）
- 科研成果（如：发表论文、专利等）
- 学术成就（如：顶会论文 AAAI/NeurIPS/CVPR/ICML 等）

★★★ 特别说明 - notes字段 ★★★
无法归入上述任何类别的内容请放入 notes 字段，如：
- 学生工作（学生会、社团职务等）
- 自我评价
- 兴趣爱好
- 其他补充信息"""

        try:
            print(f"🖼️ 开始OCR识别简历图片，base64长度: {len(image_base64)} 字符")
            
            response = client.chat.completions.create(
                model=VL_MODEL_NAME,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                }
                            },
                            {
                                "type": "text",
                                "text": "请识别这张简历图片中的所有文字内容，并提取结构化信息。"
                            }
                        ]
                    }
                ],
                temperature=0.1,
                max_tokens=8000,  # 增加token上限以处理长简历
                timeout=180  # 3分钟超时（图片处理更慢）
            )
            content = response.choices[0].message.content
            print(f"✅ OCR返回成功，长度: {len(content) if content else 0} 字符")
            print(f"📝 OCR原始返回内容（前500字符）: {content[:500] if content else 'None'}")
            
            if not content or not content.strip():
                print("❌ OCR返回内容为空")
                return {
                    "name": "OCR识别失败",
                    "skills": [],
                    "summary": "模型返回内容为空，请重试",
                    "raw_text": ""
                }
            
            content = AIService._clean_json_string(content)
            result = json.loads(content)
            print(f"✅ 简历OCR识别成功: {result.get('name', 'N/A')}")
            return result
        except json.JSONDecodeError as e:
            print(f"Resume OCR JSON Error: {e}")
            print(f"Content that failed to parse: {content[:1000] if content else 'None'}")
            return {
                "name": "OCR识别失败",
                "skills": [],
                "summary": f"JSON解析失败: {str(e)}",
                "raw_text": content if content else ""
            }
        except Exception as e:
            print(f"Resume OCR Error: {e}")
            return {
                "name": "OCR识别失败",
                "skills": [],
                "summary": f"图片识别失败: {str(e)}",
                "raw_text": ""
            }

    @staticmethod
    def add_candidate_to_vector_db(candidate_id, text, metadata):
        """将候选人存入向量库"""
        vector_id = f"cand_{candidate_id}"
        embedding = AIService.get_embedding(text)
        if embedding:
            # 确保存储的 metadata 值都是字符串或数字，不能是列表
            clean_metadata = {}
            for k, v in metadata.items():
                if isinstance(v, list):
                    clean_metadata[k] = ", ".join(str(x) for x in v)
                elif v is None:
                    clean_metadata[k] = ""
                else:
                    clean_metadata[k] = v
            
            candidates_collection.upsert(
                ids=[vector_id],
                embeddings=[embedding],
                documents=[text[:1000]], # 存储部分原文用于预览
                metadatas=[clean_metadata]
            )
            return vector_id
        return None

    @staticmethod
    def add_job_to_vector_db(job_id, text, metadata):
        """将职位存入向量库"""
        vector_id = f"job_{job_id}"
        embedding = AIService.get_embedding(text)
        if embedding:
            clean_metadata = {}
            for k, v in metadata.items():
                if isinstance(v, list):
                    clean_metadata[k] = ", ".join(str(x) for x in v)
                elif isinstance(v, dict): # 处理嵌套字典，如 analysis
                    clean_metadata[k] = json.dumps(v, ensure_ascii=False)
                elif v is None:
                    clean_metadata[k] = ""
                else:
                    clean_metadata[k] = v

            jobs_collection.upsert(
                ids=[vector_id],
                embeddings=[embedding],
                documents=[text[:1000]],
                metadatas=[clean_metadata]
            )
            return vector_id
        return None

    @staticmethod
    def search_candidates(query_text, n_results=5):
        """搜索候选人 (混合检索)"""
        embedding = AIService.get_embedding(query_text)
        if not embedding:
            return []
            
        # 1. 向量搜索 (语义相似度)
        results = candidates_collection.query(
            query_embeddings=[embedding],
            n_results=n_results * 2 # 先多召回一些
        )
        
        # 2. 关键词重排序 (简单的 Re-ranking)
        # 这一步在 Python 层做，ChromaDB 的 where 只能做硬过滤
        # 我们把 query 拆成关键词，检查它们是否出现在 document 或 metadata 中
        
        # 如果没有结果直接返回
        if not results or not results['ids'] or not results['ids'][0]:
            return results

        # 简单的关键词匹配分数计算
        keywords = [k.lower() for k in query_text.split() if len(k) > 1]
        
        final_indices = []
        
        # 提取结果并打分
        scored_results = []
        for i, doc_id in enumerate(results['ids'][0]):
            doc_text = results['documents'][0][i].lower()
            metadata = results['metadatas'][0][i]
            meta_text = " ".join([str(v).lower() for v in metadata.values()])
            
            full_text = doc_text + " " + meta_text
            
            # 关键词命中分
            keyword_score = 0
            for k in keywords:
                if k in full_text:
                    keyword_score += 1
            
            # 向量距离 (越小越好，转为分数)
            vector_distance = results['distances'][0][i]
            vector_score = 1 / (1 + vector_distance) # 归一化到 0-1 左右
            
            # 混合分数：语义 70% + 关键词 30%
            # 对于职位匹配，关键词（如 "算法"、"Java"）往往是决定性的，可以适当调高权重
            final_score = 0.6 * vector_score + 0.4 * (keyword_score * 0.1) 
            
            scored_results.append({
                "index": i,
                "score": final_score,
                "id": doc_id
            })
            
        # 按分数降序排序
        scored_results.sort(key=lambda x: x["score"], reverse=True)
        
        # 截取前 n_results
        top_indices = [x["index"] for x in scored_results[:n_results]]
        
        # 重构返回结果结构
        new_results = {
            'ids': [[results['ids'][0][i] for i in top_indices]],
            'distances': [[results['distances'][0][i] for i in top_indices]], # 保持原始距离供参考
            'documents': [[results['documents'][0][i] for i in top_indices]],
            'metadatas': [[results['metadatas'][0][i] for i in top_indices]]
        }
        
        return new_results

    @staticmethod
    def assess_match(job_data, candidate_data):
        """
        使用 LLM 进行深度匹配评估 (模拟 Expert Analysis Session)
        """
        # 构造 Prompt，模拟 "bailian-recruitment-analyst"
        # 注入用户要求的参数: analysis_depth: expert, analysis_mode: deep
        system_prompt = """
        You are an expert recruitment analyst AI named "bailian-recruitment-analyst".
        
        Configuration:
        - analysis_depth: expert
        - analysis_mode: deep
        
        Your task is to deeply evaluate the match between a Job Position and a Candidate.
        Please provide a comprehensive analysis, not just a score.
        
        Output JSON format:
        {
            "match_score": 0-100,
            "reason": "One sentence summary",
            "pros": ["point 1", "point 2"],
            "cons": ["point 1", "point 2"],
            "suggestions": "Interview suggestions"
        }
        """
        
        user_content = f"""
        Job Context:
        {json.dumps(job_data, ensure_ascii=False)}
        
        Candidate Context:
        {json.dumps(candidate_data, ensure_ascii=False)}
        
        Query: 评估这位候选人和这个岗位的匹配度，请使用专家深度模式分析。
        """
        
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            print(f"Assessment Error: {e}")
            return {
                "match_score": 0,
                "reason": f"Analysis failed: {str(e)}",
                "pros": [],
                "cons": []
            }

