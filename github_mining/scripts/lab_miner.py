#!/usr/bin/env python3
"""
Professor-Student Sourcing (Dimension 2: Lab Miner)
通过 Semantic Scholar 的共引图谱，精准挖掘顶尖教授实验室的核心博士生/博士后。

支持两种模式：
1. Top-Down: 给出教授名字和学校，挖掘嫡系。
2. Bottom-Up: 给出已知优质学者名单，反查背后的 Boss 导师，再挖掘整个同门。
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple

import requests

SCRIPT_DIR = Path(__file__).parent.absolute()
BASE_DIR = SCRIPT_DIR.parent
DATA_DIR = BASE_DIR / "data" / "academic" / "lab_miner"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# 尝试复用 academic_miner 里的打分和国籍过滤功能
sys.path.append(str(SCRIPT_DIR))
try:
    from academic_miner import score_academic_quality, link_github_from_homepage
except ImportError:
    print("❌ 找不到 academic_miner.py，请确保它和当前脚本在同一目录下。")
    sys.exit(1)

try:
    from personal_ai_headhunter_sys.add_nationality_tags import detect_nationality
except ImportError:
    import sys
    sys.path.append(str(BASE_DIR.parent / "personal-ai-headhunter"))
    from add_nationality_tags import detect_nationality

# ============================================================
# 日志配置
# ============================================================
def log(msg: str):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {msg}")

# ============================================================
# API 请求工具
# ============================================================
def s2_request(endpoint: str, params: Dict = None) -> Dict:
    """Semantic Scholar API 请求辅助，带重试机制"""
    base_url = "https://api.semanticscholar.org/graph/v1"
    url = f"{base_url}/{endpoint}"
    
    for attempt in range(3):
        try:
            time.sleep(1.5)  # Semantic Scholar 免费 API 限流很严 (1qps)
            resp = requests.get(url, params=params, timeout=15)
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 429:
                log(f"  ⚠️  S2 Rate limit, retrying in {5 + attempt*2}s...")
                time.sleep(5 + attempt * 2)
            else:
                log(f"  ❌ S2 API Error {resp.status_code} for {url}")
                return {}
        except Exception as e:
            log(f"  ❌ Request failed: {e}")
            time.sleep(2)
    return {}

# ============================================================
# 核心逻辑
# ============================================================
def search_professor(name: str, affiliation: str = None) -> Dict:
    """按名字搜索并锁定教授的主页 Author ID"""
    log(f"🔍 正在 Semantic Scholar 搜索主席会议/教授: {name}")
    query = name
    if affiliation:
        # S2 的 author 搜索只支持简单的名称搜索，affiliation 可以在取回后过滤，或者拼接到 query 里
        query = f"{name} {affiliation}"
        
    data = s2_request("author/search", {
        "query": query,
        "fields": "authorId,name,affiliations,hIndex,paperCount,citationCount,url",
        "limit": 5
    })
    
    if not data or not data.get("data"):
        log(f"  ❌ 未找到教授: {name}")
        return None
        
    # 启发式选择最匹配的那一个 (一般取 hIndex 最高，或者 paperCount 最多的，因为是大牛)
    authors = data["data"]
    authors.sort(key=lambda x: x.get("hIndex", 0) + x.get("citationCount", 0)/1000, reverse=True)
    
    best_match = authors[0]
    log(f"  ✅ 锁定目标导师: {best_match['name']} (ID: {best_match['authorId']}) | h-index: {best_match.get('hIndex')} | 机构: {best_match.get('affiliations')}")
    return best_match


def get_proteges(author_id: str, mentor_name: str, years: int = 5, min_coauth: int = 2) -> List[Dict]:
    """提取该导师的嫡系核心学生"""
    log(f"\n🕸️  正在抓取导师 {mentor_name} 近 {years} 年的全部发文图谱...")
    
    # 1. 抓取该导师所有的文章，限定年份，带回 authors 列表
    current_year = datetime.now().year
    start_year = current_year - years
    
    data = s2_request(f"author/{author_id}/papers", {
        "fields": "paperId,title,year,authors,authors.authorId,authors.name",
        "limit": 1000  # 假设最多拉取最近1000篇
    })
    
    if not data or not data.get("data"):
        log(f"  ❌ 无法获取该导师的论文档案")
        return []
        
    papers = data["data"]
    log(f"  📄 共拉取到 {len(papers)} 篇历史论文 (准备过滤 {start_year}-{current_year} 的论文)")
    
    # 2. 统计共现，寻找核心苦力 (一作/二作)
    coauthor_counts = {}
    
    for p in papers:
        pyear = p.get("year")
        if not pyear or int(pyear) < start_year:
            continue
            
        authors = p.get("authors", [])
        if not authors or len(authors) < 2:
            continue
            
        # 往往学生是一作/二作，导师在最后
        # 我们捕捉前两名作者
        for i, a in enumerate(authors[:2]):
            aid = a.get("authorId")
            aname = a.get("name")
            if not aid or aid == author_id:  # 跳过自己
                continue
                
            if aid not in coauthor_counts:
                coauthor_counts[aid] = {"name": aname, "count": 0, "papers": []}
            coauthor_counts[aid]["count"] += 1
            coauthor_counts[aid]["papers"].append(p.get("title"))

    # 3. 筛选嫡系 (频次 >= min_coauth)
    proteges = []
    for aid, info in coauthor_counts.items():
        if info["count"] >= min_coauth:
            proteges.append({
                "authorId": aid,
                "name": info["name"],
                "co_papers_count": info["count"],
                "sample_papers": info["papers"][:3]
            })
            
    # 按共写论文数量降序
    proteges.sort(key=lambda x: x["co_papers_count"], reverse=True)
    log(f"  🎯 识别到 {len(proteges)} 名在近 {years} 年内共发文 ≥{min_coauth} 篇的核心学生/合作者！")
    
    return proteges


def enrich_and_filter_proteges(proteges: List[Dict], mentor_name: str) -> List[Dict]:
    """获取学生的详细学术档案，打分并提取邮箱"""
    log(f"\n🔬 开始二次过滤并评估这 {len(proteges)} 名学者的质量...")
    results = []
    
    for i, p in enumerate(proteges):
        aname = p["name"]
        aid = p["authorId"]
        
        # 1. 国籍初筛
        nat_tag = detect_nationality(aname)
        if nat_tag == "foreigner":
            continue
            
        # 2. 查询详细档案
        detail = s2_request(f"author/{aid}", {
            "fields": "url,hIndex,paperCount,citationCount,homepage"
        })
        if not detail:
            continue
            
        # 3. 构建类似于 academic_miner 的结构体
        author_record = {
            "name": aname,
            "email": None,
            "github_url": None,
            "personal_website": detail.get("homepage"),
            "source": f"lab_{mentor_name.replace(' ', '_').lower()}",
            "conference": "Lab Target",
            "paper_title": f"Co-authored {p['co_papers_count']} recent papers with mentor (e.g. {p['sample_papers'][0]})",
            "affiliation": None,  # 需要后续完善
            "h_index": detail.get("hIndex", 0),
            "citation_count": detail.get("citationCount", 0),
            "paper_count": detail.get("paperCount", 0)
        }
        
        # 4. 打分
        score = score_academic_quality(
            h_index=author_record["h_index"], 
            citations=author_record["citation_count"], 
            venues_count=0  # 因为通过嫡系挖掘，放宽对特定顶会的硬指标限制
        )
        author_record["academic_tier"] = score
        
        results.append(author_record)
        log(f"  学者 {aname} ({nat_tag}) -> Tier: {score} | h-index: {author_record['h_index']} | citations: {author_record['citation_count']}")
        
    # 5. 联系方式深度挖掘
    log(f"\n📧 正在深入抓取嫡系学生的联系方式...")
    # 复用 academic_miner 中刚刚接入了 extract_paper_email 逻辑的这套方法
    results = link_github_from_homepage(results)
    
    return results


def find_bosses_bottom_up(seed_file: str) -> List[Tuple[str, int]]:
    """自下而上反查 Boss"""
    log(f"🚀 发动 Bottom-up 策略：读取之前挖掘出来的种子文件 {seed_file} 反查导师")
    # TODO: 实现读取之前的 raw json 结果，反向向 Semantic Scholar 查询他们的论文的最后一位作者
    # 统计出现频次最高的通讯作者，返回
    log("  [待实现] 该策略非常强大，但由于涉及到读取大量的底层论文作者图谱，留在下一个优化迭代实现。")
    return []

# ============================================================
# 保存和主入口
# ============================================================
def save_results(authors: List[Dict], prefix: str):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    github_pipeline = []
    direct_import = []

    for author in authors:
        candidate = {
            "name": author["name"],
            "email": author.get("email"),
            "extra_emails": author.get("extra_emails", []),
            "github_url": author.get("github_url"),
            "linkedin_url": author.get("linkedin_url"),
            "twitter_url": author.get("twitter_url"),
            "personal_website": author.get("personal_website"),
            "bio": f"Academic Miner (Dimension 2: Lab Miner). Tier: {author.get('academic_tier')}. "
                   f"h-index: {author.get('h_index')}. Citations: {author.get('citation_count')}. "
                   f"Paper: {author.get('paper_title')}.",
            "company": author.get("affiliation"),
            "source": author["source"],
            "academic_tier": author.get("academic_tier"),
            "h_index": author.get("h_index"),
            "citation_count": author.get("citation_count"),
            "paper_count": author.get("paper_count")
        }
        
        if candidate["github_url"]:
            github_pipeline.append(candidate)
        else:
            direct_import.append(candidate)

    prefix_clean = prefix.replace(" ", "_").lower()
    
    github_file = DATA_DIR / f"{prefix_clean}_{timestamp}_github_pipeline.json"
    direct_file = DATA_DIR / f"{prefix_clean}_{timestamp}_direct_import.json"
    
    with open(github_file, 'w', encoding='utf-8') as f:
        json.dump(github_pipeline, f, ensure_ascii=False, indent=2)
        
    with open(direct_file, 'w', encoding='utf-8') as f:
        json.dump(direct_import, f, ensure_ascii=False, indent=2)

    log(f"\n============================================================")
    log(f"📊 挖猎结果: 教授门派挖掘成功")
    log(f"============================================================")
    log(f"  截获嫡系门生:     {len(authors)} 人")
    log(f"  → 有 GitHub URL: {len(github_pipeline)} 人 (流入 github pipeline)")
    log(f"  → 纯联系人资料:  {len(direct_import)} 人 (直接入库)")
    log(f"\n✅ 完毕！")


def main():
    parser = argparse.ArgumentParser(description="Lab Miner - 教授门派精准挖掘")
    parser.add_argument("--professors", type=str, required=True,
                       help="目标教授姓名列表，逗号分隔 (如 'Andrew Ng,Jitendra Malik')")
    parser.add_argument("--years", type=int, default=5,
                       help="回查近期论文的年限 (默认: 5年内)")
    parser.add_argument("--min-coauth", type=int, default=2,
                       help="被判定为嫡系学生的最低同框发文次数 (默认: 2)")
    
    args = parser.parse_args()
    prof_names = [p.strip() for p in args.professors.split(",")]
    
    all_final_proteges = []
    
    for pname in prof_names:
        log(f"\n\n{'='*70}")
        log(f"🏫 开始执行: 定向门派抓捕作战 - {pname}")
        log(f"{'='*70}")
        
        # 1. 找教授
        prof = search_professor(pname)
        if not prof:
            continue
            
        # 2. 找学生
        proteges = get_proteges(prof["authorId"], prof["name"], years=args.years, min_coauth=args.min_coauth)
        if not proteges:
            log(f"  ⚠️  未能提取到任何嫡系学生...")
            continue
            
        # 3. 过滤并提取邮箱
        final_list = enrich_and_filter_proteges(proteges, mentor_name=prof["name"])
        all_final_proteges.extend(final_list)
        
    if all_final_proteges:
        # 保存这个批次挖掘出的所有学生
        prefix = "lab_miner_" + "_".join([p[:5] for p in prof_names])
        save_results(all_final_proteges, prefix)
    else:
        log("❌ 没有找到符合条件的人选。")

if __name__ == "__main__":
    main()
