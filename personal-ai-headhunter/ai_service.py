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
# 阿里云 Qwen 的 Embedding 模型通常为 text-embedding-v1
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-v1")

# 初始化客户端
client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)

# 初始化 ChromaDB
chroma_client = chromadb.PersistentClient(path="personal-ai-headhunter/data/chroma_db")

# Collections
candidates_collection = chroma_client.get_or_create_collection(name="candidates")
jobs_collection = chroma_client.get_or_create_collection(name="jobs")

from database import SessionLocal, SystemPrompt

class AIService:
    
    @staticmethod
    def _clean_json_string(text):
        """Clean markdown formatting from JSON string"""
        if not text: return ""
        text = text.strip()
        
        # 1. Try to find the first '{' and last '}'
        start_idx = text.find('{')
        end_idx = text.rfind('}')
        
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            text = text[start_idx : end_idx + 1]
            return text
            
        # 2. Fallback: Remove markdown code blocks if no braces found (unlikely for valid JSON)
        if "```" in text:
            import re
            match = re.search(r"```(?:json)?(.*?)```", text, re.DOTALL)
            if match:
                text = match.group(1).strip()
        
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
             你是一个专业的招聘专家。请分析以下简历文本，并提取关键信息。
             请严格返回 JSON 格式，不要包含 Markdown 代码块标记。
             
             需要提取的字段说明：
             - summary: 【核心评价】请生成一份 200-300 字的深度分析，包含：1) 核心竞争力与亮点；2) 职业发展路径总结；3) 潜在风险或短板。请使用 Markdown 格式进行分点描述。
             - skills: 技能列表 (数组)
             - name: 姓名
             - email: 邮箱
             - phone: 电话
             - age: 年龄 (数字，估算)
             - expect_location: 期望工作地点
             - education_level: 最高学历
             - current_company: 当前或最近一家公司
             - current_title: 当前或最近职位
             - experience_years: 工作年限 (数字)
             - education_details: 教育经历列表，每项包含: {"school": "学校名", "degree": "学位", "major": "专业", "year": "年份范围"}
             - work_experiences: 工作经历列表，每项包含: {"company": "公司名", "title": "职位", "time": "起止时间", "description": "主要工作内容，请提取关键项目和成果"}
             - project_experiences: 项目经历列表，每项包含: {"name": "项目名", "role": "角色", "time": "时间", "description": "项目描述与职责"}
             """
        
        # Prepare User Content
        if user_prompt_template:
            user_content = user_prompt_template.replace("{raw_text}", text[:4000])
        else:
            user_content = text[:4000]

        try:
            # Ensure JSON instruction is explicit for models that require it in messages
            # Force append JSON instruction to system prompt to satisfy API requirement
            if "json" not in system_prompt.lower():
                system_prompt += "\n请务必返回合法的 JSON 格式。"
            
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content
            content = AIService._clean_json_string(content)
            return json.loads(content)
        except Exception as e:
            print(f"LLM Error: {e}")
            # 返回默认空结构以防程序崩溃
            return {
                "name": "Parse Error",
                "skills": [],
                "summary": f"AI 解析失败: {str(e)}"
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

