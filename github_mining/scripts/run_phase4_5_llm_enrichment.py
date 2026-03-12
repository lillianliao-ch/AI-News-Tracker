#!/usr/bin/env python3
"""
Phase 4.5: LLM 深度富化 + 国籍检测

功能:
  1. 从 Phase 3.5 输出读取有个人网站的候选人
  2. 批量调用 LLM API 提取结构化信息:
     - 工作履历 (公司、职位、是否当前)
     - 教育背景 (学位、专业、学校)
     - 技能列表 (技术栈)
     - 外联谈话点 (个性化生成)
  3. 计算质量分数并过滤
  4. 自动检测国籍 (基于姓名/公司/Location/LLM提取履历)
  5. 输出完整的 JSON 用于数据库导入

插入位置: Phase 3.5 之后，数据库导入之前

使用方法:
  cd github_mining/scripts
  python3 run_phase4_5_llm_enrichment.py

  # 自动重启模式
  nohup python3 auto_restart_wrapper.py -- python3 run_phase4_5_llm_enrichment.py > phase4_5.log 2>&1 &
"""

import os
import sys
import json
import time
import requests
import urllib3
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from bs4 import BeautifulSoup

# 禁用 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 路径配置
SCRIPT_DIR = Path(__file__).parent
BASE_DIR = SCRIPT_DIR.parent  # github_mining 目录
ROOT_DIR = BASE_DIR.parent  # notion_rag 目录
HEADHUNTER_DIR = ROOT_DIR / "personal-ai-headhunter"
# ✅ 使用 Phase 4 的最新输出 (11,976 人)，而不是旧的 phase3_5_enriched.json (3,723 人)
INPUT_FILE = SCRIPT_DIR / "github_mining" / "phase4_final_enriched.json"
OUTPUT_FILE = BASE_DIR / "phase4_5_llm_enriched.json"
PROGRESS_FILE = BASE_DIR / "phase4_5_progress.json"

# API 配置
API_BASE = "http://localhost:8502"
AUTH_TOKEN = os.environ.get("HEADHUNTER_AUTH_TOKEN")

# LLM API 配置（直接调用）
DASHSCOPE_API_KEY = os.environ.get("DASHSCOPE_API_KEY")
print(f"Debug: 初始 DASHSCOPE_API_KEY = {repr(DASHSCOPE_API_KEY)}")

# 从配置文件读取 API Key（如果环境变量未设置）
if not DASHSCOPE_API_KEY:
    print(f"Debug: 尝试从配置文件读取...")
    try:
        import importlib.util
        config_path = SCRIPT_DIR / "github_hunter_config.py"
        spec = importlib.util.spec_from_file_location("github_hunter_config", config_path)
        config_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config_module)
        DASHSCOPE_API_KEY = getattr(config_module, 'DASHSCOPE_API_KEY', None)
        print(f"Debug: 读取到的 API Key: {DASHSCOPE_API_KEY}")
        if DASHSCOPE_API_KEY:
            print(f"🔑 从配置文件读取到 DashScope API Key")
    except Exception as e:
        pass

# 国籍检测配置
if str(HEADHUNTER_DIR / "scripts" / "extract") not in sys.path:
    sys.path.insert(0, str(HEADHUNTER_DIR / "scripts" / "extract"))
try:
    from add_nationality_tags import detect_nationality
    NATIONALITY_AVAILABLE = True
except ImportError:
    NATIONALITY_AVAILABLE = False
    print("⚠️  无法导入国籍检测模块，将跳过国籍检测")

# 导入标签体系（用于structured_tags提取）
if str(HEADHUNTER_DIR) not in sys.path:
    sys.path.insert(0, str(HEADHUNTER_DIR))
try:
    from extract_tags import TAG_SCHEMA
    TAGS_AVAILABLE = True
except ImportError:
    TAG_SCHEMA = ""
    TAGS_AVAILABLE = False
    print("⚠️  无法导入 TAG_SCHEMA，将跳过 structured_tags 提取")



# ============================================================================
# 国籍检测函数
# ============================================================================

def add_nationality_to_candidate(candidate: Dict) -> Tuple[str, str]:
    """
    为候选人添加国籍检测

    Returns:
        (nationality, confidence)
        - nationality: 'chinese', 'foreign', 'unknown'
        - confidence: 'high', 'medium', 'low'
    """
    if not NATIONALITY_AVAILABLE:
        return 'unknown', 'low'

    name = candidate.get('name', '')
    company = candidate.get('company', '')

    # 去掉 @ 前缀
    if company and company.startswith('@'):
        company = company[1:]

    # 基础检测
    nationality, confidence = detect_nationality(name, company)

    # Phase 4.5 增强检测
    if nationality == "unknown":
        # 利用 location
        location = candidate.get('location', '')
        if location and "China" in location:
            nationality = "chinese"
            confidence = "medium"
        else:
            # 利用 bio 中的中文
            bio = candidate.get('bio', '')
            if bio and any('\u4e00' <= c <= '\u9fff' for c in bio):
                nationality = "chinese"
                confidence = "high"

        # 利用 LLM 提取的工作履历
        work_history_json = candidate.get('extracted_work_history', '[]')
        try:
            work_history = json.loads(work_history_json) if isinstance(work_history_json, str) else work_history_json
            for job in work_history:
                job_company = job.get('company', '')
                # 检查是否在中国公司工作过
                for keyword in ['字节', 'ByteDance', '阿里巴巴', 'Alibaba', '腾讯', 'Tencent',
                               '百度', 'Baidu', '华为', 'Huawei', '清华', 'Tsinghua', '北大', 'Peking']:
                    if keyword.lower() in job_company.lower():
                        nationality = "chinese"
                        confidence = "medium"
                        break
                if nationality != "unknown":
                    break
        except:
            pass

    return nationality, confidence

# LLM 提取 Prompt
EXTRACTION_PROMPT = """你是一个专业的数据提取专家。请从以下个人网站内容中提取结构化信息。

# 候选人信息
- 姓名: {name}
- 网站: {website}

# 网站内容
```
{content}
```

# 提取要求

请提取以下信息，并以 JSON 格式返回：

## A. 基础信息提取

### 1. 工作履历 (work_history)
提取当前和过往工作经历，格式：
```json
[{{"company": "公司名", "role": "职位", "current": true/false, "source": "website"}}]
```

### 2. 教育背景 (education)
提取学历信息，格式：
```json
[{{"degree": "学位", "field": "专业", "university": "学校", "source": "website"}}]
```

### 3. 技能 (skills)
提取技术技能，格式：
```json
["Python", "Machine Learning", "PyTorch", ...]
```

### 4. 谈话点 (talking_points)
基于提取的信息，生成3-5个外联谈话点，格式：
```json
["看到你在Google做过ML Engineer...", "你的研究重点是..."]
```

### 5. 质量评分 (quality_score)
根据提取信息的完整性和质量打分（0-100）：
- 有工作履历: +25分
- 有教育背景: +20分
- 每个技能: +2分
- 有项目: +15分
- 有论文: +20分

## B. 结构化标签提取 (10个维度) ⭐ 新增

{tag_schema}

# 返回格式

请直接返回 JSON，不要包含其他文字：
```json
{{
  "work_history": [...],
  "education": [...],
  "skills": [...],
  "talking_points": [...],
  "quality_score": 85,
  "structured_tags": {{
    "tech_domain": ["技术方向"],
    "core_specialty": ["核心专长"],
    "tech_skills": ["技术技能"],
    "role_type": "岗位类型",
    "role_orientation": ["角色定位"],
    "tech_stack": ["技术栈"],
    "industry_exp": ["行业背景"],
    "seniority": "职级层次",
    "education": {{"degree": "学历", "school_tier": "学校层次"}},
    "academic_highlight": ["学术亮点"]
  }}
}}
```
"""


def log(msg: str):
    """日志输出"""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def load_candidates() -> List[Dict]:
    """加载 Phase 3.5 输出的候选人数据"""
    log(f"📖 读取输入文件: {INPUT_FILE}")

    if not INPUT_FILE.exists():
        log(f"❌ 错误: 输入文件不存在: {INPUT_FILE}")
        log(f"   请先运行 Phase 3.5 (run_phase4_enrichment.py)")
        return []

    with open(INPUT_FILE) as f:
        data = json.load(f)

    log(f"✅ 加载 {len(data)} 个候选人")
    return data


def filter_with_websites(candidates: List[Dict]) -> List[Dict]:
    """筛选有可爬取网站的候选人（已爬取的 homepage 或有 blog URL）"""
    filtered = []
    already_scraped = 0
    blog_only = 0
    for c in candidates:
        if c.get('homepage_scraped') and c.get('homepage_url'):
            filtered.append(c)
            already_scraped += 1
        elif c.get('blog'):
            # 设置 homepage_url 以便后续爬取
            if not c.get('homepage_url'):
                c['homepage_url'] = c['blog']
            filtered.append(c)
            blog_only += 1

    log(f"🌐 有网站的候选人: {len(filtered)}/{len(candidates)} (已爬取: {already_scraped}, blog待爬: {blog_only})")
    return filtered


def scrape_website_content(url: str) -> Optional[str]:
    """
    爬取网站内容

    Args:
        url: 网站 URL

    Returns:
        网站文本内容，失败返回 None
    """
    try:
        # 规范化 URL
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        url_lower = url.lower()

        # 跳过纯社交/视频平台（保留 github.io、CSDN、博客园等有内容的站点）
        skip_domains = ['twitter.com/', 'x.com/', 'linkedin.com/',
                       'weibo.com/', 'bilibili.com/', 'youtube.com/',
                       'facebook.com/', 'instagram.com/']
        if any(d in url_lower for d in skip_domains):
            return None

        # github.com profile/repo 页面跳过，但保留 github.io 个人站
        if 'github.com/' in url_lower and '.github.io' not in url_lower:
            return None

        # 发送请求
        resp = requests.get(url, timeout=15, verify=False,
                           headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'},
                           allow_redirects=True)
        resp.encoding = resp.apparent_encoding or 'utf-8'

        if resp.status_code == 200:
            # 提取文本内容
            soup = BeautifulSoup(resp.text, 'html.parser')
            # 移除 script/style 标签
            for tag in soup(['script', 'style', 'nav', 'footer']):
                tag.decompose()
            text_content = soup.get_text(separator='\n', strip=True)

            # 过滤太短的内容（可能是空页面或登录页）
            if len(text_content) < 50:
                return None

            # 限制长度
            if len(text_content) > 10000:
                text_content = text_content[:10000] + '...[truncated]'

            return text_content
        else:
            return None

    except Exception as e:
        return None


def get_auth_token() -> Optional[str]:
    """获取认证 token"""
    if AUTH_TOKEN:
        return AUTH_TOKEN

    try:
        response = requests.post(
            f"{API_BASE}/api/auth/login",
            json={"username": "admin", "password": "headhunter2026"},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        if data.get("success") and data.get("token"):
            return data["token"]
    except Exception as e:
        log(f"❌ 获取认证token失败: {e}")
        return None


def extract_with_llm(candidate: Dict, auth_token: str = None) -> Optional[Dict]:
    """使用 LLM 提取候选人信息（直接调用 LLM API）"""
    name = candidate.get('name', 'Unknown')

    # 获取网站内容
    # 优先使用已有的 homepage_text，如果没有则重新爬取
    content = candidate.get('homepage_text', '')
    website = candidate.get('homepage_url', candidate.get('personal_website', 'Unknown'))

    if not content or len(content) < 100:
        # 重新爬取网站内容
        content = scrape_website_content(website)
        if content:
            log(f"  📥 重新爬取网站内容成功 ({len(content)} 字符)")
            # 保存到候选数据中（确保不重复爬取）
            candidate['homepage_text'] = content
        else:
            log(f"  ⚠️  无法获取网站内容")
            return None
    else:
        log(f"  📄 使用已有网站内容 ({len(content)} 字符)")

    # 限制长度
    content = content[:10000]

    prompt = EXTRACTION_PROMPT.format(
        name=name,
        website=website,
        content=content,
        tag_schema=TAG_SCHEMA if TAGS_AVAILABLE else "\n# 结构化标签提取功能未启用\n"
    )

    try:
        # 直接调用通义千问 API
        from openai import OpenAI

        if not DASHSCOPE_API_KEY:
            log(f"  ❌ 未设置 DASHSCOPE_API_KEY 环境变量")
            return None

        client = OpenAI(
            api_key=DASHSCOPE_API_KEY,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )

        response = client.chat.completions.create(
            model="qwen-plus",  # 或 qwen-max
            messages=[
                {"role": "system", "content": "你是一位专业的数据提取专家，擅长从网页内容中提取结构化信息。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,  # 降低温度以获得更确定的输出
        )

        llm_response = response.choices[0].message.content.strip()

        # 提取 JSON
        import re
        json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
        if json_match:
            extracted = json.loads(json_match.group(0))
            return extracted
        else:
            log(f"  ⚠️  LLM未返回有效JSON")
            return None

    except Exception as e:
        log(f"  ❌ LLM提取失败: {e}")
        return None


def merge_candidate_data(original: Dict, extracted: Dict) -> Dict:
    """合并原始数据和LLM提取数据"""
    result = original.copy()

    # 添加LLM提取的字段
    result['extracted_work_history'] = json.dumps(extracted.get("work_history", []), ensure_ascii=False)
    result['extracted_education'] = json.dumps(extracted.get("education", []), ensure_ascii=False)

    skills_list = extracted.get("skills", [])
    result['extracted_skills'] = ", ".join(skills_list) if isinstance(skills_list, list) else str(skills_list)

    talking_points_list = extracted.get("talking_points", [])
    result['talking_points'] = "\n".join(talking_points_list) if isinstance(talking_points_list, list) else str(talking_points_list)

    result['website_quality_score'] = extracted.get("quality_score", 0)

    # 添加国籍检测
    nationality, confidence = add_nationality_to_candidate(result)
    result['nationality'] = nationality
    result['nationality_confidence'] = confidence

    # 添加来源标记
    result['data_source'] = original.get('data_source', '') + ',llm_enriched'

    return result


def load_progress() -> Dict:
    """加载进度"""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {"completed": [], "failed": [], "stats": {"total": 0, "success": 0, "failed": 0}}


def save_progress(progress: Dict):
    """保存进度"""
    progress_file = PROGRESS_FILE
    with open(progress_file, 'w') as f:
        json.dump(progress, f, indent=2)


import argparse

# ============================================================================
# 并发处理单个候选人（线程安全）
# ============================================================================
def process_single_candidate(candidate: Dict, auth_token: str) -> Tuple[str, Dict, bool]:
    """
    处理单个候选人的 LLM 富化（线程安全）。

    Returns:
        (candidate_id, result_dict, success)
    """
    candidate_id = candidate.get('username', 'unknown')
    name = candidate.get('name', 'Unknown')

    try:
        extracted = extract_with_llm(candidate, auth_token)
        if extracted:
            enriched = merge_candidate_data(candidate, extracted)
            score = extracted.get("quality_score", 0)
            log(f"  ✅ {name} ({candidate_id}) — 质量分: {score}")
            return candidate_id, enriched, True
        else:
            log(f"  ⚠️  {name} ({candidate_id}) — 提取失败，保留原始数据")
            return candidate_id, candidate, False
    except Exception as e:
        log(f"  ❌ {name} ({candidate_id}) — 异常: {e}")
        return candidate_id, candidate, False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, help="Input JSON file path")
    parser.add_argument("--output", type=str, help="Output JSON file path")
    parser.add_argument("--workers", type=int, default=5, help="并发 worker 数(default: 5)")
    args = parser.parse_args()

    global INPUT_FILE, OUTPUT_FILE, PROGRESS_FILE
    if args.input:
        INPUT_FILE = Path(args.input)
    if args.output:
        OUTPUT_FILE = Path(args.output)
        PROGRESS_FILE = OUTPUT_FILE.parent / "phase4_5_progress.json"

    MAX_WORKERS = args.workers

    log("=" * 70)
    log(f"🚀 Phase 4.5: LLM 深度富化 (并发={MAX_WORKERS})")
    log("=" * 70)

    # 1. 加载候选人数据
    candidates = load_candidates()
    if not candidates:
        return

    # 2. 筛选有网站的候选人（扩大范围：含 blog URL）
    target_candidates = filter_with_websites(candidates)

    if not target_candidates:
        log("⚠️  没有需要处理的候选人 (无网站)")
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(candidates, f, indent=2, ensure_ascii=False)
        return

    # 3. 获取认证token
    auth_token = get_auth_token()
    if not auth_token:
        log("❌ 无法获取认证token")
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(candidates, f, indent=2, ensure_ascii=False)
        return
    log("✅ 认证成功")

    # 4. 加载进度 & 清理过期数据
    progress = load_progress()
    completed_ids = set(progress.get("completed", []))

    # 只保留在当前 target 中的 completed IDs（修复进度追踪 Bug）
    target_ids = {c.get('username') for c in target_candidates}
    stale = completed_ids - target_ids
    if stale:
        log(f"🧹 清理过期进度: {len(stale)} 条旧记录")
        completed_ids = completed_ids & target_ids
    log(f"📁 进度恢复: 已完成 {len(completed_ids)}/{len(target_candidates)}")

    # 5. 分出待处理列表
    to_process = []
    skipped_results = []  # 已完成的直接加入结果
    for c in target_candidates:
        cid = c.get('username')
        if cid in completed_ids:
            skipped_results.append(c)
        else:
            to_process.append(c)

    log(f"📋 待处理: {len(to_process)} 人，跳过(已完成): {len(skipped_results)} 人")

    if not to_process:
        log("✅ 所有目标已完成，直接合并输出")
    else:
        # 6. 并发批量处理
        log("=" * 70)
        log(f"开始并发LLM提取 (workers={MAX_WORKERS})...")
        log("=" * 70)

        stats = {"success": len(completed_ids), "failed": 0}
        progress_lock = threading.Lock()
        results_lock = threading.Lock()
        concurrent_results = []

        processed_count = len(completed_ids)
        total_target = len(target_candidates)

        def on_complete(candidate_id, result, success):
            nonlocal processed_count
            with progress_lock:
                if success:
                    completed_ids.add(candidate_id)
                    stats["success"] += 1
                else:
                    stats["failed"] += 1
                processed_count += 1

                # 每完成 20 个保存一次进度
                if processed_count % 20 == 0:
                    save_progress({
                        "completed": list(completed_ids),
                        "stats": stats,
                        "last_update": datetime.now().isoformat()
                    })
                    log(f"  💾 进度: {processed_count}/{total_target} ({processed_count*100/total_target:.1f}%) | 成功: {stats['success']} | 失败: {stats['failed']}")

            with results_lock:
                concurrent_results.append(result)

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {}
            for candidate in to_process:
                future = executor.submit(process_single_candidate, candidate, auth_token)
                futures[future] = candidate

            for future in as_completed(futures):
                try:
                    candidate_id, result, success = future.result()
                    on_complete(candidate_id, result, success)
                except Exception as e:
                    candidate = futures[future]
                    log(f"  ❌ 并发异常 ({candidate.get('username')}): {e}")
                    on_complete(candidate.get('username', 'unknown'), candidate, False)

        # 合并跳过的和并发处理的结果
        skipped_results.extend(concurrent_results)

        # 最终保存进度
        save_progress({
            "completed": list(completed_ids),
            "stats": stats,
            "last_update": datetime.now().isoformat()
        })

    # 7. 保存最终结果
    all_results = skipped_results
    processed_usernames = {r.get('username') for r in all_results}
    for candidate in candidates:
        if candidate.get('username') not in processed_usernames:
            all_results.append(candidate)

    log(f"💾 保存最终结果到: {OUTPUT_FILE} ({len(all_results)} 人)")
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    # 8. 最终统计
    log("=" * 70)
    log("📊 最终统计")
    log("=" * 70)
    log(f"总候选人数: {len(all_results)}")
    log(f"参与富化人数: {len(target_candidates)}")
    log(f"成功提取: {stats.get('success', len(completed_ids))}")
    log(f"提取失败: {stats.get('failed', 0)}")

    if NATIONALITY_AVAILABLE:
        try:
            from collections import Counter
            counts = Counter(r.get('_prefilter_nationality', 'unknown') for r in all_results)
            log(f"国籍预估分布: {dict(counts)}")
        except:
            pass

    log("=" * 70)
    log(f"✅ Phase 4.5 完成！")
    log(f"📁 输出文件: {OUTPUT_FILE}")
    log(f"⏰ 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
