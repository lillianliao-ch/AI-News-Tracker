#!/usr/bin/env python3
"""
候选人-职位匹配引擎
基于结构化标签的多维度匹配
"""

import json
from typing import List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class MatchResult:
    """匹配结果"""
    candidate_id: int
    candidate_name: str
    total_score: float
    dimension_scores: Dict[str, float]
    match_details: Dict[str, any]
    recommendations: List[str]
    risks: List[str]


class MatchingEngine:
    """匹配引擎"""
    
    # 维度权重配置
    WEIGHTS = {
        "tech_domain": 0.30,      # 技术方向
        "role_type": 0.15,        # 岗位类型
        "role_orientation": 0.15, # 角色定位
        "tech_stack": 0.15,       # 技术栈
        "industry_exp": 0.10,     # 行业背景
        "seniority": 0.10,        # 职级层次
        "education": 0.05         # 教育背景
    }
    
    # 技术方向相似度矩阵（部分相关的方向）
    TECH_SIMILARITY = {
        ("大模型/LLM", "Agent/智能体"): 0.7,
        ("大模型/LLM", "NLP"): 0.8,
        ("Agent/智能体", "NLP"): 0.6,
        ("多模态", "CV"): 0.6,
        ("多模态", "语音"): 0.6,
        ("推荐系统", "搜索"): 0.7,
        ("AI Infra", "具身智能"): 0.4,
    }
    
    # 职级层次顺序
    SENIORITY_ORDER = ["初级(0-3年)", "中级(3-5年)", "高级(5-8年)", "专家(8年+)", "管理层"]
    
    def __init__(self, db_session):
        self.db = db_session
    
    def match_job_to_candidates(self, job_id: int, top_k: int = 20) -> List[MatchResult]:
        """为职位匹配候选人"""
        from database import Job, Candidate
        
        job = self.db.query(Job).filter(Job.id == job_id).first()
        if not job or not job.structured_tags:
            return []
        
        job_tags = json.loads(job.structured_tags) if isinstance(job.structured_tags, str) else job.structured_tags
        
        # 获取所有有标签的候选人
        candidates = self.db.query(Candidate).filter(
            Candidate.structured_tags != None
        ).all()
        
        results = []
        for cand in candidates:
            if not cand.structured_tags:
                continue
            cand_tags = json.loads(cand.structured_tags) if isinstance(cand.structured_tags, str) else cand.structured_tags
            
            result = self._calculate_match(job_tags, cand_tags, cand)
            results.append(result)
        
        # 按总分排序
        results.sort(key=lambda x: x.total_score, reverse=True)
        return results[:top_k]
    
    def _calculate_match(self, job_tags: dict, cand_tags: dict, candidate) -> MatchResult:
        """计算匹配分数"""
        scores = {}
        details = {}
        recommendations = []
        risks = []
        
        # 1. 技术方向匹配
        scores["tech_domain"], details["tech_domain"] = self._match_list_with_similarity(
            job_tags.get("tech_domain", []),
            cand_tags.get("tech_domain", []),
            self.TECH_SIMILARITY
        )
        
        # 2. 岗位类型匹配
        scores["role_type"] = 1.0 if job_tags.get("role_type") == cand_tags.get("role_type") else 0.3
        details["role_type"] = {"job": job_tags.get("role_type"), "candidate": cand_tags.get("role_type")}
        
        # 3. 角色定位匹配
        scores["role_orientation"], details["role_orientation"] = self._match_list(
            job_tags.get("role_orientation", []),
            cand_tags.get("role_orientation", [])
        )
        
        # 4. 技术栈匹配
        job_required = job_tags.get("tech_stack", []) or job_tags.get("required_stack", [])
        scores["tech_stack"], details["tech_stack"] = self._match_list(
            job_required,
            cand_tags.get("tech_stack", [])
        )
        
        # 5. 行业背景匹配
        scores["industry_exp"], details["industry_exp"] = self._match_list(
            job_tags.get("preferred_industry", []),
            cand_tags.get("industry_exp", [])
        )
        
        # 6. 职级匹配
        scores["seniority"], seniority_gap = self._match_seniority(
            job_tags.get("seniority", ""),
            cand_tags.get("seniority", "")
        )
        details["seniority"] = {"job": job_tags.get("seniority"), "candidate": cand_tags.get("seniority"), "gap": seniority_gap}
        
        if seniority_gap < 0:
            risks.append(f"候选人资历偏低 ({seniority_gap} 级)")
        elif seniority_gap > 1:
            risks.append(f"候选人可能资历过高 (+{seniority_gap} 级)")
        
        # 7. 教育背景匹配
        scores["education"] = self._match_education(
            job_tags.get("education_requirement", {}),
            cand_tags.get("education", {})
        )
        
        # 计算加权总分
        total_score = sum(scores[k] * self.WEIGHTS[k] for k in self.WEIGHTS)
        
        # 生成推荐理由
        if scores["tech_domain"] >= 0.8:
            recommendations.append("技术方向高度匹配")
        if scores["tech_stack"] >= 0.7:
            recommendations.append("技术栈契合度高")
        if scores["industry_exp"] >= 0.8:
            recommendations.append("有相关行业经验")
        
        return MatchResult(
            candidate_id=candidate.id,
            candidate_name=candidate.name,
            total_score=round(total_score * 100, 1),
            dimension_scores={k: round(v * 100, 1) for k, v in scores.items()},
            match_details=details,
            recommendations=recommendations,
            risks=risks
        )
    
    def _match_list(self, required: List[str], candidate: List[str]) -> Tuple[float, dict]:
        """列表匹配（Jaccard相似度）"""
        if not required:
            return 1.0, {"matched": [], "missing": []}
        if not candidate:
            return 0.0, {"matched": [], "missing": required}
        
        required_set = set(required)
        candidate_set = set(candidate)
        
        matched = required_set & candidate_set
        missing = required_set - candidate_set
        
        score = len(matched) / len(required_set) if required_set else 1.0
        
        return score, {"matched": list(matched), "missing": list(missing)}
    
    def _match_list_with_similarity(self, required: List[str], candidate: List[str], similarity_map: dict) -> Tuple[float, dict]:
        """带相似度的列表匹配"""
        if not required:
            return 1.0, {"matched": [], "similar": [], "missing": []}
        if not candidate:
            return 0.0, {"matched": [], "similar": [], "missing": required}
        
        matched = []
        similar = []
        missing = []
        
        for req in required:
            if req in candidate:
                matched.append(req)
            else:
                # 检查相似项
                found_similar = False
                for cand_item in candidate:
                    key1 = (req, cand_item)
                    key2 = (cand_item, req)
                    if key1 in similarity_map:
                        similar.append((req, cand_item, similarity_map[key1]))
                        found_similar = True
                        break
                    elif key2 in similarity_map:
                        similar.append((req, cand_item, similarity_map[key2]))
                        found_similar = True
                        break
                if not found_similar:
                    missing.append(req)
        
        # 计算分数
        score = len(matched) / len(required)
        score += sum(s[2] for s in similar) / len(required) * 0.5  # 相似项算一半分
        
        return min(score, 1.0), {"matched": matched, "similar": similar, "missing": missing}
    
    def _match_seniority(self, required: str, candidate: str) -> Tuple[float, int]:
        """职级匹配"""
        if not required or not candidate:
            return 0.5, 0
        
        try:
            req_idx = self.SENIORITY_ORDER.index(required)
            cand_idx = self.SENIORITY_ORDER.index(candidate)
            gap = cand_idx - req_idx
            
            if gap == 0:
                return 1.0, 0
            elif gap == 1:
                return 0.9, 1  # 候选人稍高
            elif gap == -1:
                return 0.7, -1  # 候选人稍低
            elif gap > 1:
                return 0.6, gap  # 候选人过高
            else:
                return 0.4, gap  # 候选人过低
        except ValueError:
            return 0.5, 0
    
    def _match_education(self, required: dict, candidate: dict) -> float:
        """教育背景匹配"""
        if not required:
            return 1.0
        
        score = 0.5  # 基础分
        
        # 学历匹配
        degree_order = ["本科", "硕士", "博士"]
        req_degree = required.get("degree", "") if isinstance(required, dict) else str(required)
        cand_degree = candidate.get("degree", "") if isinstance(candidate, dict) else ""
        
        try:
            if cand_degree in degree_order and req_degree in degree_order:
                if degree_order.index(cand_degree) >= degree_order.index(req_degree):
                    score += 0.3
        except:
            pass
        
        # 学校层次
        school_order = ["普通本科", "985/211", "海外Top100", "顶级名校"]
        req_school = required.get("school_tier", "") if isinstance(required, dict) else ""
        cand_school = candidate.get("school_tier", "") if isinstance(candidate, dict) else ""
        
        try:
            if cand_school in school_order and req_school in school_order:
                if school_order.index(cand_school) >= school_order.index(req_school):
                    score += 0.2
        except:
            pass
        
        return min(score, 1.0)


def run_matching(job_id: int, top_k: int = 20):
    """运行匹配"""
    import sqlite3
    
    DB_PATH = '/Users/lillianliao/notion_rag/personal-ai-headhunter/data/headhunter_dev.db'
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 获取职位
    cursor.execute("SELECT id, title, structured_tags FROM jobs WHERE id = ?", (job_id,))
    job_row = cursor.fetchone()
    if not job_row or not job_row[2]:
        print(f"职位 {job_id} 未找到或无标签")
        return []
    
    job_tags = json.loads(job_row[2])
    job_title = job_row[1]
    
    # 获取候选人
    cursor.execute("""
        SELECT id, name, structured_tags 
        FROM candidates 
        WHERE structured_tags IS NOT NULL AND structured_tags != 'null'
    """)
    candidates = cursor.fetchall()
    
    print(f"\n=== 职位: {job_title} (ID:{job_id}) ===")
    print(f"职位标签: {json.dumps(job_tags, ensure_ascii=False)[:100]}...")
    print(f"\n共有 {len(candidates)} 个候选人有标签\n")
    
    # 创建模拟候选人对象
    class MockCandidate:
        def __init__(self, id, name, tags):
            self.id = id
            self.name = name
            self.structured_tags = tags
    
    # 匹配引擎
    engine = MatchingEngine(None)
    results = []
    
    for cid, name, tags_str in candidates:
        try:
            cand_tags = json.loads(tags_str)
            mock_cand = MockCandidate(cid, name, cand_tags)
            result = engine._calculate_match(job_tags, cand_tags, mock_cand)
            results.append(result)
        except Exception as e:
            pass
    
    # 排序
    results.sort(key=lambda x: x.total_score, reverse=True)
    results = results[:top_k]
    
    print(f"=== Top {len(results)} 匹配结果 ===\n")
    
    for i, r in enumerate(results, 1):
        print(f"{i}. {r.candidate_name} - {r.total_score}分")
        print(f"   维度: {r.dimension_scores}")
        if r.recommendations:
            print(f"   ✅ {', '.join(r.recommendations)}")
        if r.risks:
            print(f"   ⚠️ {', '.join(r.risks)}")
        print()
    
    conn.close()
    return results


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("用法: python matching_engine.py <job_id> [top_k]")
        sys.exit(1)
    
    job_id = int(sys.argv[1])
    top_k = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    
    run_matching(job_id, top_k)
