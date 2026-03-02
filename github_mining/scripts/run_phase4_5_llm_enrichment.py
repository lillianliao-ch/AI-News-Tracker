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
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# 路径配置
SCRIPT_DIR = Path(__file__).parent
BASE_DIR = SCRIPT_DIR / "github_mining"
ROOT_DIR = SCRIPT_DIR.parent.parent
HEADHUNTER_DIR = ROOT_DIR / "personal-ai-headhunter"
INPUT_FILE = BASE_DIR / "phase3_5_enriched.json"
OUTPUT_FILE = BASE_DIR / "phase4_5_llm_enriched.json"
PROGRESS_FILE = BASE_DIR / "phase4_5_progress.json"

# API 配置
API_BASE = "http://localhost:8502"
AUTH_TOKEN = os.environ.get("HEADHUNTER_AUTH_TOKEN")

# 国籍检测配置
sys.path.insert(0, str(HEADHUNTER_DIR / "scripts"))
try:
    from add_nationality_tags import detect_nationality
    NATIONALITY_AVAILABLE = True
except ImportError:
    NATIONALITY_AVAILABLE = False
    log("⚠️  无法导入国籍检测模块，将跳过国籍检测")


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

## 1. 工作履历 (work_history)
提取当前和过往工作经历，格式：
```json
[{{"company": "公司名", "role": "职位", "current": true/false, "source": "website"}}]
```

## 2. 教育背景 (education)
提取学历信息，格式：
```json
[{{"degree": "学位", "field": "专业", "university": "学校", "source": "website"}}]
```

## 3. 技能 (skills)
提取技术技能，格式：
```json
["Python", "Machine Learning", "PyTorch", ...]
```

## 4. 谈话点 (talking_points)
基于提取的信息，生成3-5个外联谈话点，格式：
```json
["看到你在Google做过ML Engineer...", "你的研究重点是..."]
```

## 5. 质量评分 (quality_score)
根据提取信息的完整性和质量打分（0-100）：
- 有工作履历: +25分
- 有教育背景: +20分
- 每个技能: +2分
- 有项目: +15分
- 有论文: +20分

# 返回格式

请直接返回 JSON，不要包含其他文字：
```json
{{
  "work_history": [...],
  "education": [...],
  "skills": [...],
  "talking_points": [...],
  "quality_score": 85
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
    """筛选有个人网站的候选人"""
    filtered = [
        c for c in candidates
        if c.get('personal_website') and c.get('homepage_text')
    ]

    log(f"🌐 有个人网站的候选人: {len(filtered)}/{len(candidates)}")
    return filtered


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


def extract_with_llm(candidate: Dict, auth_token: str) -> Optional[Dict]:
    """使用 LLM 提取候选人信息"""
    name = candidate.get('name', 'Unknown')
    website = candidate.get('personal_website', 'Unknown')
    content = candidate.get('homepage_text', '')[:10000]  # 限制长度

    prompt = EXTRACTION_PROMPT.format(
        name=name,
        website=website,
        content=content
    )

    try:
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(
            f"{API_BASE}/api/generate-website-based-message",
            json={
                "candidate_id": candidate.get('id', 0),
                "prompt": prompt,
                "channel": "linkedin",
                "message_type": "extraction",
            },
            headers=headers,
            timeout=120
        )
        response.raise_for_status()
        data = response.json()

        if not data.get("success"):
            log(f"  ❌ API返回失败: {data.get('detail', 'Unknown')}")
            return None

        llm_response = data.get("message", {}).get("body", "")

        # 提取 JSON
        import re
        json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
        if json_match:
            extracted = json.loads(json_match.group(0))
            return extracted
        else:
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


def main():
    log("=" * 70)
    log("🚀 Phase 4.5: LLM 深度富化")
    log("=" * 70)

    # 1. 加载候选人数据
    candidates = load_candidates()
    if not candidates:
        return

    # 2. 筛选有网站的候选人
    target_candidates = filter_with_websites(candidates)
    if not target_candidates:
        log("⚠️  没有需要处理的候选人")
        return

    # 3. 获取认证token
    auth_token = get_auth_token()
    if not auth_token:
        log("❌ 无法获取认证token，退出")
        return

    log("✅ 认证成功")

    # 4. 加载进度
    progress = load_progress()
    completed_ids = set(progress.get("completed", []))
    stats = progress.get("stats", {"total": len(target_candidates), "success": 0, "failed": 0})

    log(f"📁 进度恢复: 已完成 {len(completed_ids)} 个")

    # 5. 批量处理
    log("=" * 70)
    log("开始批量LLM提取...")
    log("=" * 70)

    results = []
    batch_size = 100

    for i, candidate in enumerate(target_candidates):
        candidate_id = candidate.get('id', i)
        name = candidate.get('name', 'Unknown')

        # 跳过已完成的
        if candidate_id in completed_ids:
            # 保留已处理的数据
            if 'extracted_work_history' in candidate:
                results.append(candidate)
            continue

        log(f"[{len(completed_ids)+1}/{len(target_candidates)}] {name} (ID: {candidate_id})")

        # LLM提取
        extracted = extract_with_llm(candidate, auth_token)

        if extracted:
            # 合并数据
            enriched = merge_candidate_data(candidate, extracted)
            results.append(enriched)
            completed_ids.add(candidate_id)
            stats["success"] += 1

            score = extracted.get("quality_score", 0)
            log(f"  ✅ 提取成功，质量分: {score}")
        else:
            # 保留原始数据
            results.append(candidate)
            stats["failed"] += 1
            log(f"  ⚠️  提取失败，保留原始数据")

        # 每10个保存一次进度
        if (i + 1) % 10 == 0:
            save_progress({
                "completed": list(completed_ids),
                "failed": progress.get("failed", []),
                "stats": stats,
                "last_update": datetime.now().isoformat()
            })

        # 避免请求过快
        time.sleep(0.5)

    # 6. 保存结果
    log(f"💾 保存结果到: {OUTPUT_FILE}")

    # 合并未处理的候选人
    for candidate in candidates:
        if not any(r.get('id') == candidate.get('id') for r in results):
            results.append(candidate)

    with open(OUTPUT_FILE, 'w') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # 7. 最终统计
    log("=" * 70)
    log("📊 最终统计")
    log("=" * 70)
    log(f"总候选人数: {len(results)}")
    log(f"成功提取: {stats['success']} ({stats['success']/len(target_candidates)*100:.1f}%)")
    log(f"提取失败: {stats['failed']} ({stats['failed']/len(target_candidates)*100:.1f}%)")

    # 统计质量分数
    high_quality = sum(1 for r in results if r.get('website_quality_score', 0) >= 90)
    log(f"高质量(90+): {high_quality} 人")

    # 统计国籍分布
    if NATIONALITY_AVAILABLE:
        from collections import Counter
        nat_dist = Counter(r.get('nationality', 'unknown') for r in results)
        log(f"\n📊 国籍分布:")
        log(f"  中国人:     {nat_dist.get('chinese', 0):5,} ({nat_dist.get('chinese', 0)/len(results)*100:.1f}%)")
        log(f"  外国人:     {nat_dist.get('foreign', 0):5,} ({nat_dist.get('foreign', 0)/len(results)*100:.1f}%)")
        log(f"  无法判断:   {nat_dist.get('unknown', 0):5,} ({nat_dist.get('unknown', 0)/len(results)*100:.1f}%)")

    # 清理进度文件
    if PROGRESS_FILE.exists():
        PROGRESS_FILE.unlink()

    log("=" * 70)
    log(f"✅ Phase 4.5 完成！")
    log(f"📁 输出文件: {OUTPUT_FILE}")
    log(f"⏰ 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
