#!/usr/bin/env python3
"""
职位语义搜索模块
使用向量嵌入实现自然语言搜索职位功能
"""

import sqlite3
import json
import os
import pickle
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv
from typing import List, Dict, Tuple, Optional

# 加载环境变量
env_path = os.path.join(os.path.dirname(__file__), 'config.env')
if os.path.exists(env_path):
    load_dotenv(env_path, override=True)

# 配置
DB_PATH = '/Users/lillianliao/notion_rag/personal-ai-headhunter/data/headhunter_dev.db'
VECTOR_CACHE_PATH = '/Users/lillianliao/notion_rag/personal-ai-headhunter/data/job_vectors.pkl'
CANDIDATE_VECTOR_CACHE_PATH = '/Users/lillianliao/notion_rag/personal-ai-headhunter/data/candidate_vectors.pkl'
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'text-embedding-v3')

# 初始化 OpenAI 客户端 (兼容阿里云)
client = OpenAI(
    api_key=os.getenv('OPENAI_API_KEY') or os.getenv('DASHSCOPE_API_KEY'),
    base_url=os.getenv('OPENAI_BASE_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
)

# =============================================================================
# 同义词映射功能
# =============================================================================
SYNONYMS_FILE = os.path.join(os.path.dirname(__file__), 'config', 'synonyms.yaml')
_synonym_cache = {}
_synonym_mtime = 0

def load_synonyms() -> Dict[str, str]:
    """加载同义词配置，返回 {别名: 标准形式} 映射"""
    global _synonym_cache, _synonym_mtime
    
    # 检查文件是否更新
    try:
        current_mtime = os.path.getmtime(SYNONYMS_FILE)
        if current_mtime == _synonym_mtime and _synonym_cache:
            return _synonym_cache
        _synonym_mtime = current_mtime
    except:
        if _synonym_cache:
            return _synonym_cache
        return {}
    
    synonym_map = {}
    
    try:
        import yaml
        with open(SYNONYMS_FILE, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # 处理所有分类
        for category in ['specialties', 'tech_skills', 'tech_domains']:
            for group in config.get(category, []):
                canonical = group['canonical'].lower().strip()
                synonym_map[canonical] = canonical  # 标准形式映射到自己
                for alias in group.get('aliases', []):
                    synonym_map[alias.lower().strip()] = canonical
                    
        _synonym_cache = synonym_map
        print(f"✅ 加载同义词配置: {len(synonym_map)} 条映射")
    except FileNotFoundError:
        print(f"⚠️ 同义词配置文件不存在: {SYNONYMS_FILE}，使用直接匹配")
    except Exception as e:
        print(f"❌ 加载同义词配置失败: {e}，使用直接匹配")
    
    return synonym_map

def normalize_tag(tag: str) -> str:
    """将标签标准化为规范形式（考虑同义词）"""
    synonym_map = load_synonyms()
    tag_lower = tag.lower().strip()
    return synonym_map.get(tag_lower, tag_lower)

def find_overlapping_tags(set1: set, set2: set) -> set:
    """找出两个标签集合的交集（考虑同义词）"""
    if not set1 or not set2:
        return set()
    
    # 将两个集合的标签都标准化
    normalized1 = {normalize_tag(t): t for t in set1}
    normalized2 = {normalize_tag(t): t for t in set2}
    
    # 找出标准形式的交集
    common_keys = set(normalized1.keys()) & set(normalized2.keys())
    
    # 返回原始标签（使用set1的形式）
    return {normalized1[k] for k in common_keys}



def get_embedding(text: str) -> List[float]:
    """获取文本的向量嵌入"""
    # 截断过长文本（阿里云限制 8192 tokens）
    text = text[:8000] if len(text) > 8000 else text
    
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text,
        dimensions=1024  # 使用 1024 维度以平衡性能和精度
    )
    return response.data[0].embedding


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """计算余弦相似度"""
    a = np.array(vec1)
    b = np.array(vec2)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def build_job_index(force_rebuild: bool = False) -> Dict:
    """
    构建职位向量索引
    返回: {job_id: {"embedding": [...], "title": "...", "company": "..."}}
    """
    # 检查缓存
    if not force_rebuild and os.path.exists(VECTOR_CACHE_PATH):
        with open(VECTOR_CACHE_PATH, 'rb') as f:
            cache = pickle.load(f)
            print(f"📦 从缓存加载 {len(cache)} 条职位向量")
            return cache
    
    print("🔄 开始构建职位向量索引...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 获取所有活跃职位
    cursor.execute("""
        SELECT id, title, company, raw_jd_text, structured_tags, location, required_experience_years, job_code
        FROM jobs 
        WHERE is_active = 1 AND raw_jd_text IS NOT NULL AND LENGTH(raw_jd_text) > 50
    """)
    jobs = cursor.fetchall()
    conn.close()
    
    print(f"📄 发现 {len(jobs)} 条有效职位")
    
    index = {}
    for i, (jid, title, company, jd_text, tags_str, location, exp_years, job_code) in enumerate(jobs):
        # 构建用于 embedding 的文本（职位名 + 公司 + JD 摘要）
        embed_text = f"职位: {title}\n公司: {company}\n\n{jd_text[:2000]}"
        
        try:
            embedding = get_embedding(embed_text)
            index[jid] = {
                "embedding": embedding,
                "title": title,
                "company": company,
                "location": location,
                "tags": json.loads(tags_str) if tags_str else {},
                "exp_years": exp_years,  # 存储经验年限
                "job_code": job_code or ""  # 存储职位编号
            }
            
            if (i + 1) % 20 == 0:
                print(f"  进度: {i + 1}/{len(jobs)}")
                
        except Exception as e:
            print(f"  ⚠️ 职位 {jid} embedding 失败: {e}")
    
    # 保存缓存
    with open(VECTOR_CACHE_PATH, 'wb') as f:
        pickle.dump(index, f)
    
    print(f"✅ 索引构建完成，共 {len(index)} 条职位")
    return index


def search_jobs(
    query: str, 
    top_k: int = 20,
    min_score: float = 0.3,
    tag_boost: bool = True
) -> List[Dict]:
    """
    语义搜索职位（关键词优先 + 向量语义补充）
    
    Args:
        query: 用户自然语言查询
        top_k: 返回结果数量
        min_score: 最低相似度阈值
        tag_boost: 是否使用标签加权
    
    Returns:
        匹配的职位列表，包含相似度分数
    """
    import jieba
    
    # 加载索引
    if not os.path.exists(VECTOR_CACHE_PATH):
        print("⚠️ 向量索引不存在，正在构建...")
        build_job_index()
    
    with open(VECTOR_CACHE_PATH, 'rb') as f:
        index = pickle.load(f)
    
    # 获取查询向量
    query_embedding = get_embedding(query)
    query_lower = query.lower()
    
    # ★★★ 使用jieba分词提取关键词 ★★★
    # 添加 AI/技术领域的专业术语到 jieba 词典
    custom_words = [
        "数字人", "大模型", "大语言模型", "多模态", "语音合成", "语音识别",
        "自动驾驶", "智能驾驶", "无人驾驶", "机器学习", "深度学习", "强化学习",
        "自然语言处理", "计算机视觉", "知识图谱", "推荐系统", "搜索引擎",
        "文生图", "图生图", "文生视频", "文本生成", "图像生成", "视频生成",
        "对话系统", "智能客服", "虚拟助手", "语音助手", "智能体",
        "预训练", "微调", "推理加速", "模型压缩", "量化部署",
        "分布式训练", "联邦学习", "知识蒸馏", "神经网络", "卷积神经网络",
        "循环神经网络", "注意力机制", "变换器", "生成对抗网络",
        "解决方案", "技术方案", "产品经理", "算法工程师", "算法专家",
    ]
    for w in custom_words:
        jieba.add_word(w)
    
    stop_words = {"找", "的", "岗位", "职位", "工作", "人才", "有", "在", "做", "过", 
                  "相关", "方向", "领域", "一个", "想", "需要", "寻找", "要", "求"}
    query_keywords = []
    for word in jieba.cut(query_lower):
        word = word.strip()
        if word not in stop_words and len(word) >= 2:
            query_keywords.append(word)
    
    # ★★★ 经验年限智能识别 ★★★
    import re
    exp_filter = None  # 用户要求的经验年限上限
    exp_match = re.search(r'(\d+)\s*年', query)
    if exp_match:
        exp_filter = int(exp_match.group(1))
    
    # 计算相似度
    results = []
    for jid, data in index.items():
        similarity = cosine_similarity(query_embedding, data["embedding"])
        title_lower = data["title"].lower()
        
        # 标签加权（可选）
        final_score = similarity
        match_reasons = []
        
        # ★★★ 经验年限过滤 ★★★
        job_exp = data.get("exp_years")
        exp_matched = False
        if exp_filter is not None and job_exp is not None:
            try:
                job_exp = int(job_exp)
                if job_exp <= exp_filter:
                    final_score += 0.25  # 符合经验要求大幅加分
                    match_reasons.append(f"📅 经验要求: {job_exp}年")
                    exp_matched = True
                elif job_exp <= exp_filter + 2:
                    # 稍微超出（如要求1年，实际需3年）轻微降分
                    final_score -= 0.15
                else:
                    final_score -= 0.40  # 大幅超出（如要求1年，实际需5年以上）重度降分
            except (ValueError, TypeError):
                pass  # 无法解析的跳过
        
        # ★★★ 核心优化：标题关键词匹配加分（专业术语权重更高）★★★
        # 通用词（如"技术"、"专家"）权重低，专业术语（如"AIGC"、"NLP"）权重高
        generic_keywords = {"技术", "专家", "工程师", "开发", "高级", "资深", "算法"}
        
        title_keyword_hits = 0
        for kw in query_keywords:
            if kw in title_lower:
                title_keyword_hits += 1
                if kw in generic_keywords:
                    final_score += 0.10  # 通用词 +10%
                else:
                    final_score += 0.20  # 专业术语 +20%（如AIGC、NLP、推荐等）
                match_reasons.insert(0, f"🎯 标题含: {kw}")
        
        # 多关键词组合加分（如"AIGC"+"技术"都命中）
        if title_keyword_hits >= 2:
            final_score += 0.15  # 额外奖励（提高组合匹配权重）
        
        # ★★★ 智能岗位类型识别 ★★★
        # 如果用户搜索"技术岗位"/"算法"，则优先技术岗，降低产品/销售岗
        tech_job_keywords = {"技术", "算法", "工程师", "开发", "研发", "研究员"}
        product_job_keywords = {"产品", "运营", "销售", "商务"}
        
        user_wants_tech = any(kw in query_lower for kw in tech_job_keywords)
        user_wants_product = any(kw in query_lower for kw in product_job_keywords)
        
        # 判断职位是技术岗还是产品岗
        title_is_tech = any(kw in title_lower for kw in ["算法", "工程师", "开发", "研发", "研究员", "架构师"])
        title_is_product = any(kw in title_lower for kw in ["产品", "运营", "销售", "商务", "拓展"])
        
        if user_wants_tech and not user_wants_product:
            if title_is_tech:
                final_score += 0.15  # 技术岗加分
                match_reasons.append("🔧 技术岗")
            elif title_is_product:
                final_score -= 0.20  # 产品岗大幅降分
        
        if user_wants_product and not user_wants_tech:
            if title_is_product:
                final_score += 0.15
                match_reasons.append("📦 产品岗")
            elif title_is_tech:
                final_score -= 0.10
        
        if tag_boost and data.get("tags"):
            tags = data["tags"]
            
            # 技术方向匹配
            for domain in tags.get("tech_domain", []):
                if domain.lower() in query_lower or any(kw in query_lower for kw in domain.lower().split("/")):
                    final_score += 0.05
                    match_reasons.append(f"技术方向: {domain}")
            
            # 细分专长匹配
            for spec in tags.get("specialty", []):
                if spec.lower() in query_lower:
                    final_score += 0.03
                    match_reasons.append(f"专长: {spec}")
            
            # 岗位类型匹配
            role = tags.get("role_type", "")
            if role and role.lower() in query_lower:
                final_score += 0.05
                match_reasons.append(f"岗位: {role}")
        
        # 设置分数上限100分
        final_score = min(final_score, 1.0)
        
        if final_score >= min_score:
            results.append({
                "id": jid,
                "title": data["title"],
                "company": data["company"],
                "location": data.get("location", ""),
                "similarity": round(similarity * 100, 1),
                "score": round(final_score * 100, 1),
                "match_reasons": match_reasons[:3],  # 最多显示3个原因
                "tags": data.get("tags", {})
            })
    
    # 按分数排序
    results.sort(key=lambda x: x["score"], reverse=True)
    
    return results[:top_k]


def get_index_stats() -> Dict:
    """获取索引统计信息"""
    if not os.path.exists(VECTOR_CACHE_PATH):
        return {"status": "not_built", "count": 0}
    
    with open(VECTOR_CACHE_PATH, 'rb') as f:
        index = pickle.load(f)
    
    return {
        "status": "ready",
        "count": len(index),
        "cache_path": VECTOR_CACHE_PATH
    }


def match_candidate_to_jobs(
    candidate_id: int,
    top_k: int = 20,
    min_score: float = 0.35
) -> List[Dict]:
    """
    为候选人匹配职位（向量语义匹配）
    
    Args:
        candidate_id: 候选人ID
        top_k: 返回结果数量
        min_score: 最低相似度阈值
    
    Returns:
        匹配的职位列表，包含相似度分数
    """
    # 加载职位向量索引
    if not os.path.exists(VECTOR_CACHE_PATH):
        print("⚠️ 职位向量索引不存在，请先运行 build_job_index()")
        return []
    
    with open(VECTOR_CACHE_PATH, 'rb') as f:
        job_index = pickle.load(f)
    
    # 获取候选人信息
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name, current_company, current_title, raw_resume_text, structured_tags
        FROM candidates WHERE id = ?
    """, (candidate_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return []
    
    name, company, title, resume_text, tags_str = row
    
    # 构建候选人 embedding 文本
    candidate_text = f"候选人: {name}\n当前职位: {title}\n当前公司: {company}\n\n简历摘要:\n{resume_text[:3000] if resume_text else ''}"
    
    # 获取候选人向量
    try:
        candidate_embedding = get_embedding(candidate_text)
    except Exception as e:
        print(f"获取候选人embedding失败: {e}")
        return []
    
    # 解析候选人标签用于加权（兼容字符串和字典类型）
    cand_tags = {}
    if tags_str:
        try:
            if isinstance(tags_str, str):
                parsed = json.loads(tags_str)
                if isinstance(parsed, dict):
                    cand_tags = parsed
            elif isinstance(tags_str, dict):
                cand_tags = tags_str
        except:
            cand_tags = {}  # 确保失败时也是空字典
    
    # 确保cand_tags是字典
    if not isinstance(cand_tags, dict):
        cand_tags = {}
    
    cand_domains = set(cand_tags.get("tech_domain", []))
    cand_role = cand_tags.get("role_type", "")
    cand_seniority = cand_tags.get("seniority", "")
    
    # 提取候选人的细分专长（清理格式）
    # 提取候选人的标签（兼容新旧格式）
    # 新格式: core_specialty + tech_skills
    # 旧格式: specialty
    cand_core_specialties = set()
    cand_tech_skills = set()
    
    # 清理函数：去除前缀和括号内容
    import re
    def clean_tag(s):
        # 去除"应用方向: "等前缀
        s = s.split(": ")[-1] if ": " in s else s
        # 去除括号内容，如 "语音合成 (TTS)" -> "语音合成"
        s = re.sub(r'\s*[\(（][^)）]*[\)）]', '', s)
        return s.lower().strip()
    
    # 新格式
    for s in cand_tags.get("core_specialty", []):
        cand_core_specialties.add(clean_tag(s))
    for s in cand_tags.get("tech_skills", []):
        cand_tech_skills.add(clean_tag(s))
    
    # 兼容旧格式（如果没有新格式字段）
    if not cand_core_specialties:
        generic_skills = {
            "sft微调", "sft", "预训练", "rlhf", "rlhf/对齐", 
            "推理加速", "模型压缩", "量化", "蒸馏", "模型压缩/量化",
            "rag/知识库", "rag", "知识库", "分布式训练",
            "算子优化", "框架开发"
        }
        for s in cand_tags.get("specialty", []):
            clean = clean_tag(s)
            if clean in generic_skills:
                cand_tech_skills.add(clean)
            else:
                cand_core_specialties.add(clean)
    
    # 与所有职位计算相似度
    results = []
    for jid, job_data in job_index.items():
        # 向量相似度
        similarity = cosine_similarity(candidate_embedding, job_data["embedding"])
        
        # 标签加权
        job_tags = job_data.get("tags", {})
        job_domains = set(job_tags.get("tech_domain", []))
        job_role = job_tags.get("role_type", "")
        
        # 提取职位标签（兼容新旧格式）
        job_core_specialties = set()
        job_tech_skills = set()
        
        for s in job_tags.get("core_specialty", []):
            job_core_specialties.add(clean_tag(s))
        for s in job_tags.get("tech_skills", []):
            job_tech_skills.add(clean_tag(s))
        
        # 兼容旧格式
        if not job_core_specialties:
            generic_skills = {
                "sft微调", "sft", "预训练", "rlhf", "rlhf/对齐", 
                "推理加速", "模型压缩", "量化", "蒸馏", "模型压缩/量化",
                "rag/知识库", "rag", "知识库", "分布式训练",
                "算子优化", "框架开发"
            }
            for s in job_tags.get("specialty", []):
                clean = clean_tag(s)
                if clean in generic_skills:
                    job_tech_skills.add(clean)
                else:
                    job_core_specialties.add(clean)
        
        bonus = 0
        penalty = 0
        match_reasons = []
        
        # ★★★ 核心专长匹配（高权重 +20%）【支持同义词】★★★
        core_overlap = find_overlapping_tags(cand_core_specialties, job_core_specialties)
        if core_overlap:
            bonus += len(core_overlap) * 0.20  # 核心专长每个 +20%
            match_reasons.insert(0, f"🎯 核心专长: {', '.join(list(core_overlap)[:2])}")
        
        # ★★★ 技术技能匹配（低权重 +2%）【支持同义词】★★★
        skill_overlap = find_overlapping_tags(cand_tech_skills, job_tech_skills)
        if skill_overlap:
            bonus += len(skill_overlap) * 0.02  # 技术技能每个只 +2%
            # 只有在没有核心匹配时才显示技能匹配
            if not core_overlap:
                match_reasons.append(f"技能: {', '.join(list(skill_overlap)[:2])}")
        
        # ★★★ 新增：标题关键词精确匹配（最高权重）★★★
        job_title_lower = job_data["title"].lower()
        for spec in cand_core_specialties:
            if spec in job_title_lower:
                bonus += 0.12  # 标题包含候选人专长，大幅加分
                match_reasons.insert(0, f"🎯 标题匹配: {spec}")
                break  # 只加一次
        
        # ★★★ TTS vs ASR 冲突检测 ★★★
        tts_keywords = {"语音合成", "tts", "text-to-speech"}
        asr_keywords = {"语音识别", "asr", "speech recognition", "speech-to-text"}
        
        cand_is_tts = bool(cand_core_specialties & tts_keywords)
        cand_is_asr = bool(cand_core_specialties & asr_keywords)
        job_is_tts = bool(job_core_specialties & tts_keywords) or "合成" in job_data["title"]
        job_is_asr = bool(job_core_specialties & asr_keywords) or "识别" in job_data["title"]
        
        # TTS候选人 vs ASR职位 → 降分
        if cand_is_tts and job_is_asr and not job_is_tts:
            penalty += 0.15
            match_reasons.append("⚠️ TTS vs ASR方向不符")
        # ASR候选人 vs TTS职位 → 降分
        if cand_is_asr and job_is_tts and not job_is_asr:
            penalty += 0.15
            match_reasons.append("⚠️ ASR vs TTS方向不符")
        
        # ★★★ CV vs NLP 冲突检测 ★★★
        cv_keywords = {"cv", "计算机视觉", "图像", "视频", "视觉", "3d", "三维"}
        nlp_keywords = {"nlp", "自然语言", "文本", "对话", "问答"}
        
        cand_is_cv = bool(cand_domains & {"CV"}) or bool(cand_core_specialties & cv_keywords)
        cand_is_nlp = bool(cand_domains & {"NLP"}) or bool(cand_core_specialties & nlp_keywords)
        job_is_cv = bool(job_domains & {"CV"}) or any(kw in job_data["title"].lower() for kw in ["视觉", "图像", "视频", "cv", "3d"])
        job_is_nlp = bool(job_domains & {"NLP"}) or any(kw in job_data["title"].lower() for kw in ["nlp", "文本", "对话"])
        
        # 纯CV候选人 vs 纯NLP职位（反之亦然）
        if cand_is_cv and not cand_is_nlp and job_is_nlp and not job_is_cv:
            penalty += 0.10
            match_reasons.append("⚠️ CV vs NLP方向差异")
        if cand_is_nlp and not cand_is_cv and job_is_cv and not job_is_nlp:
            penalty += 0.10
            match_reasons.append("⚠️ NLP vs CV方向差异")
        
        # ★★★ 推荐 vs 搜索 冲突检测（轻微差异）★★★
        rec_keywords = {"推荐系统", "推荐算法", "推荐", "个性化推荐", "ctr", "cvr"}
        search_keywords = {"搜索", "检索", "search", "ranking", "信息检索"}
        
        cand_is_rec = bool(cand_core_specialties & rec_keywords)
        cand_is_search = bool(cand_core_specialties & search_keywords)
        job_is_rec = bool(job_core_specialties & rec_keywords) or "推荐" in job_data["title"]
        job_is_search = bool(job_core_specialties & search_keywords) or "搜索" in job_data["title"]
        
        # 纯推荐 vs 纯搜索（轻微惩罚，因为有一定相关性）
        if cand_is_rec and not cand_is_search and job_is_search and not job_is_rec:
            penalty += 0.05
            match_reasons.append("⚠️ 推荐 vs 搜索方向差异")
        if cand_is_search and not cand_is_rec and job_is_rec and not job_is_search:
            penalty += 0.05
            match_reasons.append("⚠️ 搜索 vs 推荐方向差异")
        
        # ★★★ 职级匹配优化（加大惩罚力度）★★★
        job_seniority = job_tags.get("seniority", "")
        risk_flags = []  # 风险标签列表
        
        if cand_seniority and job_seniority:
            # 职级层次定义
            seniority_levels = {
                "初级": 1, "初级(0-3年)": 1,
                "中级": 2, "中级(3-5年)": 2,
                "高级": 3, "高级(5-8年)": 3,
                "专家": 4, "专家(8年+)": 4,
                "管理层": 5
            }
            cand_level = seniority_levels.get(cand_seniority, 0)
            job_level = seniority_levels.get(job_seniority, 0)
            
            if cand_level > 0 and job_level > 0:
                level_gap = cand_level - job_level
                
                # 候选人级别过高（overqualified）- 加大惩罚
                if level_gap >= 3:
                    penalty += 0.18  # -18%（严重资历过高）
                    risk_flags.append("资历严重过高(+3级)")
                    match_reasons.append("⚠️ 候选人资历严重过高")
                elif level_gap >= 2:
                    penalty += 0.12  # -12%（资历过高）
                    risk_flags.append("资历过高(+2级)")
                    match_reasons.append("⚠️ 候选人资历过高")
                elif level_gap == 1:
                    penalty += 0.05  # -5%（资历略过高）
                    risk_flags.append("资历略过高(+1级)")
                
                # 候选人级别过低（underqualified）- 大幅加大惩罚
                elif level_gap <= -3:
                    penalty += 0.30  # -30%（严重资历不足，几乎不可能）
                    risk_flags.append("资历严重不足(-3级)")
                    match_reasons.append("⚠️ 候选人资历严重不足")
                elif level_gap <= -2:
                    penalty += 0.20  # -20%（资历明显不足）
                    risk_flags.append("资历不足(-2级)")
                    match_reasons.append("⚠️ 候选人资历不足")
                elif level_gap == -1:
                    penalty += 0.08  # -8%（轻微资历不足）
                    risk_flags.append("资历略不足(-1级)")
                
                # 完美匹配
                elif level_gap == 0:
                    bonus += 0.03
                    match_reasons.append(f"🎯 职级匹配: {cand_seniority}")
        
        # 收集其他风险标签
        for reason in match_reasons:
            if "⚠️" in reason and "方向" in reason:
                risk_flags.append("方向偏移")
        
        # 技术方向匹配加分
        domain_overlap = cand_domains & job_domains
        if domain_overlap:
            bonus += len(domain_overlap) * 0.03
            match_reasons.append(f"技术方向: {', '.join(list(domain_overlap)[:2])}")
        
        # ★★★ 分池排序（Pool-based Matching）★★★
        # Pool A: 技术（算法IC/专家）
        # Pool B: 管理（Tech Lead/算法负责人）
        # Pool C: 产品（产品经理/运营）
        # Pool D: 销售（销售/解决方案架构师）
        
        ROLE_POOLS = {
            "技术": ["算法工程师", "算法专家", "算法研究员", "高级算法工程师"],
            "管理": ["技术管理"],
            "产品": ["产品经理", "AI产品专家", "AI产品经理", "运营"],
            "工程": ["工程开发", "运维/SRE", "数据工程师"],
            "销售": ["销售专家", "AI销售专家", "解决方案架构师", "行业解决方案架构师"]
        }
        
        def get_role_pool(role):
            for pool, roles in ROLE_POOLS.items():
                if role in roles:
                    return pool
            return None
        
        cand_pool = get_role_pool(cand_role)
        job_pool = get_role_pool(job_role)
        
        # 同池匹配加分
        if cand_role and job_role and cand_role == job_role:
            bonus += 0.05
            match_reasons.append(f"岗位匹配: {job_role}")
        elif cand_pool and job_pool:
            if cand_pool == job_pool:
                # 同池不同岗位
                bonus += 0.02
            elif cand_pool == "管理" and job_pool == "技术":
                # 管理 → 技术IC：降级可接受，小幅惩罚
                penalty += 0.03
                risk_flags.append("管理→IC降级")
            elif cand_pool == "技术" and job_pool == "管理":
                # 技术IC → 管理：升级机会，加分
                bonus += 0.02
            else:
                # ★★★ 跨池惩罚（核心规则）★★★
                CROSS_POOL_PENALTY = {
                    ("技术", "产品"): (0.15, "技术→产品"),
                    ("技术", "销售"): (0.18, "技术→销售"),
                    ("管理", "产品"): (0.12, "管理→产品"),
                    ("管理", "销售"): (0.15, "管理→销售"),
                    ("产品", "技术"): (0.15, "产品→技术"),
                    ("产品", "销售"): (0.08, "产品→销售"),
                    ("销售", "技术"): (0.18, "销售→技术"),
                    ("销售", "产品"): (0.10, "销售→产品"),
                    ("工程", "产品"): (0.12, "工程→产品"),
                    ("工程", "销售"): (0.15, "工程→销售"),
                }
                
                key = (cand_pool, job_pool)
                if key in CROSS_POOL_PENALTY:
                    pen, label = CROSS_POOL_PENALTY[key]
                    penalty += pen
                    risk_flags.append(f"跨池({label})")
                else:
                    # 其他跨池默认惩罚
                    penalty += 0.10
                    risk_flags.append(f"跨池({cand_pool}→{job_pool})")
        
        final_score = similarity + bonus - penalty
        final_score = min(final_score, 1.0)  # 分数上限100分
        
        # ★★★ 分级风险触发分数上限 ★★★
        # 严重风险（资历偏差+2级以上、跨池）→ 最高85分
        SEVERE_RISK_KEYWORDS = ["资历过高(+2级)", "资历严重过高", "资历不足(-2级)", "资历严重不足", "跨池"]
        has_severe_risk = any(
            any(keyword in flag for keyword in SEVERE_RISK_KEYWORDS) 
            for flag in risk_flags
        )
        
        # 一般风险（资历略偏差+1级、方向偏移等）→ 最高92分
        GENERAL_RISK_KEYWORDS = ["资历", "方向偏移", "管理→IC"]
        has_general_risk = any(
            any(keyword in flag for keyword in GENERAL_RISK_KEYWORDS) 
            for flag in risk_flags
        )
        
        if has_severe_risk:
            final_score = min(final_score, 0.85)  # 严重风险，最高85分
        elif has_general_risk:
            final_score = min(final_score, 0.92)  # 一般风险，最高92分
        
        final_score_pct = round(final_score * 100, 1)
        
        # 匹配分层
        has_any_risk = has_severe_risk or has_general_risk
        if final_score_pct >= 90 and not has_any_risk:
            match_tier = "强匹配"
        elif final_score_pct >= 75:
            match_tier = "可转型"
        else:
            match_tier = "泛化拓展"
        
        if final_score >= min_score:
            results.append({
                "job_id": jid,  # 保持兼容
                "id": jid,
                "job_code": job_data.get("job_code", ""),  # 添加职位编号
                "title": job_data["title"],
                "company": job_data["company"],
                "location": job_data.get("location", ""),
                "similarity": round(similarity * 100, 1),
                "score": final_score_pct,
                "match_tier": match_tier,      # 新增：匹配分层
                "risk_flags": risk_flags,       # 新增：风险标签
                "match_reasons": match_reasons[:3],
                "tags": job_tags
            })
    
    # 按分数排序
    results.sort(key=lambda x: x["score"], reverse=True)
    
    return results[:top_k]


# =============================================================================
# 候选人语义搜索
# =============================================================================

def build_candidate_index(force_rebuild: bool = False) -> Dict:
    """
    构建候选人向量索引
    返回: {candidate_id: {"embedding": [...], "name": "...", "company": "...", ...}}
    """
    # 检查缓存
    if not force_rebuild and os.path.exists(CANDIDATE_VECTOR_CACHE_PATH):
        with open(CANDIDATE_VECTOR_CACHE_PATH, 'rb') as f:
            cache = pickle.load(f)
            print(f"📦 从缓存加载 {len(cache)} 条候选人向量")
            return cache
    
    print("🔄 开始构建候选人向量索引...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 获取所有有简历内容的候选人
    cursor.execute("""
        SELECT id, name, current_company, current_title, raw_resume_text, 
               structured_tags, work_experiences
        FROM candidates 
        WHERE raw_resume_text IS NOT NULL AND LENGTH(raw_resume_text) > 50
    """)
    candidates = cursor.fetchall()
    conn.close()
    
    print(f"📄 发现 {len(candidates)} 条有效候选人")
    
    index = {}
    for i, (cid, name, company, title, resume_text, tags_str, work_exp) in enumerate(candidates):
        # 构建用于 embedding 的文本
        embed_parts = [f"候选人: {name or '未知'}"]
        if company:
            embed_parts.append(f"当前公司: {company}")
        if title:
            embed_parts.append(f"当前职位: {title}")
        
        # 解析标签
        tags = {}
        if tags_str:
            try:
                tags = json.loads(tags_str) if isinstance(tags_str, str) else tags_str
            except:
                pass
        
        # 添加技术方向和专长
        if tags.get("tech_domain"):
            embed_parts.append(f"技术方向: {', '.join(tags['tech_domain'])}")
        if tags.get("core_specialty"):
            embed_parts.append(f"核心专长: {', '.join(tags['core_specialty'])}")
        if tags.get("specialty"):
            embed_parts.append(f"专长: {', '.join(tags['specialty'])}")
        
        # 添加简历摘要
        embed_parts.append(f"\n简历摘要:\n{resume_text[:2500]}")
        
        embed_text = "\n".join(embed_parts)
        
        try:
            embedding = get_embedding(embed_text)
            index[cid] = {
                "embedding": embedding,
                "name": name,
                "company": company,
                "title": title,
                "tags": tags
            }
            
            if (i + 1) % 20 == 0:
                print(f"  进度: {i + 1}/{len(candidates)}")
                
        except Exception as e:
            print(f"  ⚠️ 候选人 {cid} embedding 失败: {e}")
    
    # 保存缓存
    with open(CANDIDATE_VECTOR_CACHE_PATH, 'wb') as f:
        pickle.dump(index, f)
    
    print(f"✅ 候选人索引构建完成，共 {len(index)} 条")
    return index


def search_candidates(
    query: str, 
    top_k: int = 20,
    min_score: float = 0.3,
    tag_boost: bool = True
) -> List[Dict]:
    """
    语义搜索候选人
    
    Args:
        query: 用户自然语言查询，如"找有广告行业AIGC经验的人才"
        top_k: 返回结果数量
        min_score: 最低相似度阈值
        tag_boost: 是否使用标签加权
    
    Returns:
        匹配的候选人列表，包含相似度分数
    """
    # 加载索引
    if not os.path.exists(CANDIDATE_VECTOR_CACHE_PATH):
        print("⚠️ 候选人向量索引不存在，正在构建...")
        build_candidate_index()
    
    with open(CANDIDATE_VECTOR_CACHE_PATH, 'rb') as f:
        index = pickle.load(f)
    
    # 获取查询向量
    query_embedding = get_embedding(query)
    query_lower = query.lower()
    
    # 计算相似度
    results = []
    for cid, data in index.items():
        similarity = cosine_similarity(query_embedding, data["embedding"])
        
        # 标签加权（可选）
        final_score = similarity
        match_reasons = []
        
        if tag_boost and data.get("tags"):
            tags = data["tags"]
            
            # 技术方向匹配
            for domain in tags.get("tech_domain", []):
                domain_lower = domain.lower()
                if domain_lower in query_lower or any(kw in query_lower for kw in domain_lower.split("/")):
                    final_score += 0.05
                    match_reasons.append(f"技术方向: {domain}")
            
            # 核心专长匹配（高权重）
            for spec in tags.get("core_specialty", []):
                if spec.lower() in query_lower:
                    final_score += 0.10
                    match_reasons.append(f"🎯 专长: {spec}")
            
            # 旧版专长匹配
            for spec in tags.get("specialty", []):
                if spec.lower() in query_lower:
                    final_score += 0.05
                    match_reasons.append(f"专长: {spec}")
            
            # 岗位类型匹配
            role = tags.get("role_type", "")
            if role and role.lower() in query_lower:
                final_score += 0.05
                match_reasons.append(f"岗位: {role}")
            
            # 级别匹配
            seniority = tags.get("seniority", "")
            if seniority:
                if ("专家" in query_lower or "senior" in query_lower) and "专家" in seniority:
                    final_score += 0.03
                    match_reasons.append(f"级别: {seniority}")
                elif ("高级" in query_lower) and "高级" in seniority:
                    final_score += 0.03
                    match_reasons.append(f"级别: {seniority}")
        
        # 公司名匹配
        if data.get("company") and data["company"].lower() in query_lower:
            final_score += 0.08
            match_reasons.append(f"🏢 公司: {data['company']}")
        
        # 常见公司/行业关键词匹配
        company_industry_map = {
            "字节": ["广告", "推荐", "抖音", "头条"],
            "阿里": ["电商", "淘宝", "天猫"],
            "腾讯": ["社交", "游戏", "微信"],
            "百度": ["搜索", "自动驾驶"],
            "美团": ["外卖", "本地生活"],
            "快手": ["短视频", "直播"],
        }
        if data.get("company"):
            for company_key, industries in company_industry_map.items():
                if company_key in data["company"]:
                    for ind in industries:
                        if ind in query_lower:
                            final_score += 0.05
                            match_reasons.append(f"行业: {ind}")
                            break
        
        if final_score >= min_score:
            results.append({
                "id": cid,
                "name": data["name"],
                "company": data.get("company", ""),
                "title": data.get("title", ""),
                "similarity": round(similarity * 100, 1),
                "score": round(final_score * 100, 1),
                "match_reasons": match_reasons[:3],
                "tags": data.get("tags", {})
            })
    
    # 按分数排序
    results.sort(key=lambda x: x["score"], reverse=True)
    
    return results[:top_k]


def get_candidate_index_stats() -> Dict:
    """获取候选人索引统计信息"""
    if not os.path.exists(CANDIDATE_VECTOR_CACHE_PATH):
        return {"status": "not_built", "count": 0}
    
    with open(CANDIDATE_VECTOR_CACHE_PATH, 'rb') as f:
        index = pickle.load(f)
    
    return {
        "status": "ready",
        "count": len(index),
        "cache_path": CANDIDATE_VECTOR_CACHE_PATH
    }


# CLI 入口
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("用法:")
        print("  python job_search.py build [--force]       # 构建职位索引")
        print("  python job_search.py build-cand [--force]  # 构建候选人索引")
        print("  python job_search.py search '查询词'        # 搜索职位")
        print("  python job_search.py search-cand '查询词'   # 搜索候选人")
        print("  python job_search.py stats                 # 查看索引状态")
        sys.exit(0)
    
    command = sys.argv[1]
    
    if command == "build":
        force = "--force" in sys.argv
        build_job_index(force_rebuild=force)
    
    elif command == "build-cand":
        force = "--force" in sys.argv
        build_candidate_index(force_rebuild=force)
    
    elif command == "search":
        if len(sys.argv) < 3:
            print("请提供搜索词")
            sys.exit(1)
        query = sys.argv[2]
        results = search_jobs(query)
        print(f"\n🔍 搜索职位: {query}")
        print(f"✅ 找到 {len(results)} 个匹配职位\n")
        for i, r in enumerate(results[:10], 1):
            print(f"{i}. [{r['score']}分] {r['title']} @ {r['company']}")
            if r["match_reasons"]:
                print(f"   匹配原因: {', '.join(r['match_reasons'])}")
    
    elif command == "search-cand":
        if len(sys.argv) < 3:
            print("请提供搜索词")
            sys.exit(1)
        query = sys.argv[2]
        results = search_candidates(query)
        print(f"\n🔍 搜索人才: {query}")
        print(f"✅ 找到 {len(results)} 个匹配候选人\n")
        for i, r in enumerate(results[:10], 1):
            print(f"{i}. [{r['score']}分] {r['name']} @ {r['company']} - {r['title']}")
            if r["match_reasons"]:
                print(f"   匹配原因: {', '.join(r['match_reasons'])}")
    
    elif command == "stats":
        job_stats = get_index_stats()
        cand_stats = get_candidate_index_stats()
        print(f"职位索引: {job_stats['status']} ({job_stats['count']} 条)")
        print(f"候选人索引: {cand_stats['status']} ({cand_stats['count']} 条)")
