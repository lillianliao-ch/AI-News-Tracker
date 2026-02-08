#!/usr/bin/env python3
"""
有效工作年限计算工具
排除实习、创业等非正式工作经历
"""

import re
from datetime import datetime
from typing import List, Dict, Tuple


def parse_time_range(time_str: str) -> Tuple[datetime, datetime]:
    """
    解析时间范围字符串
    支持格式: 
        - "2023.05-2024.07"
        - "2023.05-至今"
        - "2023/05-2024/07"
        - "2023年5月-2024年7月"
    """
    if not time_str:
        return None, None
    
    # 统一格式
    time_str = time_str.replace('/', '.').replace('年', '.').replace('月', '')
    
    # 处理"至今"
    time_str = time_str.replace('至今', datetime.now().strftime('%Y.%m'))
    time_str = time_str.replace('present', datetime.now().strftime('%Y.%m'))
    time_str = time_str.replace('现在', datetime.now().strftime('%Y.%m'))
    
    # 尝试匹配 YYYY.MM-YYYY.MM 格式
    match = re.search(r'(\d{4})\.(\d{1,2}).*?(\d{4})\.(\d{1,2})', time_str)
    if match:
        start_year, start_month, end_year, end_month = match.groups()
        try:
            start_date = datetime(int(start_year), int(start_month), 1)
            end_date = datetime(int(end_year), int(end_month), 1)
            return start_date, end_date
        except ValueError:
            pass
    
    # 尝试匹配只有年份的格式 YYYY-YYYY
    match = re.search(r'(\d{4}).*?(\d{4})', time_str)
    if match:
        start_year, end_year = match.groups()
        try:
            start_date = datetime(int(start_year), 1, 1)
            end_date = datetime(int(end_year), 12, 31)
            return start_date, end_date
        except ValueError:
            pass
    
    return None, None


def calculate_months(start: datetime, end: datetime) -> float:
    """计算两个日期之间的月数"""
    if not start or not end:
        return 0
    
    # 确保不会计算未来的时间
    now = datetime.now()
    if end > now:
        end = now
    
    if start > end:
        return 0
    
    months = (end.year - start.year) * 12 + (end.month - start.month)
    return max(0, months)


def is_internship(title: str) -> bool:
    """判断是否为实习岗位"""
    if not title:
        return False
    
    internship_keywords = ['实习', 'intern', 'Intern', 'INTERN', '见习', '助理实习']
    return any(kw in title for kw in internship_keywords)


def is_entrepreneurship(title: str, company: str = "") -> bool:
    """判断是否为创业经历"""
    if not title:
        return False
    
    entrepreneurship_keywords = [
        '创始人', '联合创始人', 'CEO', 'CTO', 'Founder', 'Co-Founder',
        '合伙人', '创业', '自主创业'
    ]
    
    full_text = f"{title} {company}".lower()
    return any(kw.lower() in full_text for kw in entrepreneurship_keywords)


def calculate_effective_years(
    work_experiences: List[Dict],
    exclude_internship: bool = True,
    exclude_entrepreneurship: bool = True,
    min_months: int = 3  # 少于3个月的不计入
) -> Dict:
    """
    计算有效工作年限
    
    Args:
        work_experiences: 工作经历列表
        exclude_internship: 是否排除实习
        exclude_entrepreneurship: 是否排除创业
        min_months: 最少工作月数（默认3个月）
    
    Returns:
        {
            "effective_years": 3.5,           # 有效年限
            "total_years": 7.0,               # 总年限（含实习创业）
            "excluded_experiences": [...],    # 排除的经历
            "included_experiences": [...],    # 计入的经历
            "breakdown": {...}                # 详细分解
        }
    """
    if not work_experiences:
        return {
            "effective_years": 0,
            "total_years": 0,
            "excluded_experiences": [],
            "included_experiences": [],
            "breakdown": {}
        }
    
    included = []
    excluded = []
    total_months = 0
    effective_months = 0
    
    for exp in work_experiences:
        title = exp.get('title', '')
        company = exp.get('company', '')
        time_range = exp.get('time', '')
        
        start_date, end_date = parse_time_range(time_range)
        months = calculate_months(start_date, end_date)
        
        exp_info = {
            "title": title,
            "company": company,
            "time": time_range,
            "months": round(months, 1)
        }
        
        total_months += months
        
        # 检查是否应该排除
        exclude_reason = None
        
        if exclude_internship and is_internship(title):
            exclude_reason = "实习"
        elif exclude_entrepreneurship and is_entrepreneurship(title, company):
            exclude_reason = "创业"
        elif months < min_months:
            exclude_reason = f"少于{min_months}个月"
        
        if exclude_reason:
            exp_info["exclude_reason"] = exclude_reason
            excluded.append(exp_info)
        else:
            included.append(exp_info)
            effective_months += months
    
    return {
        "effective_years": round(effective_months / 12, 1),
        "total_years": round(total_months / 12, 1),
        "excluded_experiences": excluded,
        "included_experiences": included,
        "breakdown": {
            "total_months": round(total_months, 1),
            "effective_months": round(effective_months, 1),
            "excluded_months": round(total_months - effective_months, 1)
        }
    }


def update_candidate_effective_years(candidate_id: int, db_session=None) -> Dict:
    """
    更新单个候选人的有效年限
    
    Returns:
        计算结果字典
    """
    from database import SessionLocal, Candidate
    
    close_session = False
    if db_session is None:
        db_session = SessionLocal()
        close_session = True
    
    try:
        cand = db_session.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not cand:
            return {"error": "候选人不存在"}
        
        work_exps = cand.work_experiences or []
        result = calculate_effective_years(work_exps)
        
        # 更新 structured_tags
        import json
        tags = {}
        if cand.structured_tags:
            if isinstance(cand.structured_tags, str):
                try:
                    tags = json.loads(cand.structured_tags)
                except:
                    tags = {}
            else:
                tags = cand.structured_tags
        
        tags["effective_years"] = result["effective_years"]
        tags["total_years"] = result["total_years"]
        
        cand.structured_tags = json.dumps(tags, ensure_ascii=False)
        
        # 同时更新 experience_years 字段为有效年限
        cand.experience_years = result["effective_years"]
        
        db_session.commit()
        
        result["candidate_name"] = cand.name
        result["candidate_id"] = cand.id
        return result
        
    finally:
        if close_session:
            db_session.close()


def batch_update_effective_years(limit: int = None) -> Dict:
    """
    批量更新所有候选人的有效年限
    
    Returns:
        {"updated": n, "errors": [...]}
    """
    from database import SessionLocal, Candidate
    
    session = SessionLocal()
    
    try:
        query = session.query(Candidate).filter(
            Candidate.work_experiences != None
        )
        
        if limit:
            query = query.limit(limit)
        
        candidates = query.all()
        
        updated = 0
        errors = []
        
        for cand in candidates:
            try:
                result = update_candidate_effective_years(cand.id, session)
                if "error" not in result:
                    updated += 1
                    print(f"✅ {cand.name}: {result['effective_years']}年 (原{result['total_years']}年)")
                else:
                    errors.append({"id": cand.id, "error": result["error"]})
            except Exception as e:
                errors.append({"id": cand.id, "error": str(e)})
        
        return {"updated": updated, "errors": errors}
        
    finally:
        session.close()


# CLI 测试
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "batch":
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else None
            result = batch_update_effective_years(limit)
            print(f"\n✅ 更新完成: {result['updated']} 人")
            if result['errors']:
                print(f"⚠️ 错误: {len(result['errors'])} 人")
        elif sys.argv[1] == "test":
            # 测试王朔
            result = update_candidate_effective_years(1205)
            print(f"\n=== {result.get('candidate_name', 'Unknown')} ===")
            print(f"有效年限: {result['effective_years']} 年")
            print(f"总年限: {result['total_years']} 年")
            print(f"\n计入的经历:")
            for exp in result['included_experiences']:
                print(f"  ✅ {exp['title']} ({exp['months']}个月)")
            print(f"\n排除的经历:")
            for exp in result['excluded_experiences']:
                print(f"  ❌ {exp['title']} ({exp['months']}个月) - {exp['exclude_reason']}")
        else:
            print("用法:")
            print("  python calc_years.py test     # 测试王朔")
            print("  python calc_years.py batch    # 批量更新所有人")
            print("  python calc_years.py batch 10 # 批量更新前10人")
    else:
        # 默认测试
        print("测试时间解析:")
        test_cases = [
            "2023.05-2024.07",
            "2023.05-至今",
            "2021.10-2022.10",
        ]
        for tc in test_cases:
            start, end = parse_time_range(tc)
            months = calculate_months(start, end)
            print(f"  {tc} -> {months}个月")
