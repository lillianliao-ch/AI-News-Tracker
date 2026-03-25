#!/usr/bin/env python3
"""
Academic LLM Enrichment — 学术人才 LLM 深度富化 (Step 6c)

读取 _deep_cache.json 中的 homepage_text，调用 Qwen API 提取:
  - 工作履历 (current + past)
  - 教育背景 (学位/学校/专业)
  - 技术技能
  - 研究方向摘要
  - 外联谈话点
  - 结构化标签 (structured_tags)

用法:
  python3 academic_llm_enrich.py \
    --deep-cache /path/to/_deep_cache.json \
    --serper-cache /path/to/_serper_cache.json \
    --input /path/to/all_conf_2025_full.json \
    --output /path/to/_llm_enrichment_results.json \
    --workers 5

  # 后台运行
  nohup python3 academic_llm_enrich.py ... > llm_enrich.log 2>&1 &

特性:
  - 断点续传: progress 自动保存/恢复
  - 并发处理: ThreadPoolExecutor (默认 5 workers)
  - 优雅退出: Ctrl+C 保存进度
  - 安全写入: .tmp → rename
  - 跳过无 homepage_text 的人
"""

import os
import re
import sys
import json
import time
import signal
import shutil
import argparse
import functools
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

# 强制刷新输出
print = functools.partial(print, flush=True)

SCRIPT_DIR = Path(__file__).parent
ROOT_DIR = SCRIPT_DIR.parent.parent  # notion_rag

# 全局进度引用 (Ctrl+C 保护)
_global_results = None
_global_output_path = None


def log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")


def safe_save_json(data, path, backup=True):
    path = Path(path)
    if backup and path.exists():
        bak = path.with_suffix(path.suffix + '.bak')
        shutil.copy2(path, bak)
    tmp_path = path.with_suffix(path.suffix + '.tmp')
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    tmp_path.rename(path)


def _graceful_exit(signum, frame):
    global _global_results, _global_output_path
    log("\n⚠️  收到中断信号，正在保存进度...")
    if _global_results and _global_output_path:
        safe_save_json(_global_results, _global_output_path, backup=True)
        completed = sum(1 for v in _global_results.values() if v.get("llm_status") == "done")
        log(f"  💾 进度已保存: {_global_output_path} ({completed} 完成)")
    log("  下次运行将自动从断点继续")
    sys.exit(0)

signal.signal(signal.SIGINT, _graceful_exit)
signal.signal(signal.SIGTERM, _graceful_exit)


# ============================================================
# DashScope API Key
# ============================================================
def _load_api_key() -> str:
    key = os.environ.get("DASHSCOPE_API_KEY")
    if key:
        return key
    try:
        import importlib.util
        config_path = SCRIPT_DIR / "github_hunter_config.py"
        spec = importlib.util.spec_from_file_location("config", config_path)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        key = getattr(m, 'DASHSCOPE_API_KEY', None)
        if key:
            log(f"🔑 从配置文件读取 DashScope API Key")
            return key
    except Exception:
        pass
    log("❌ 未找到 DASHSCOPE_API_KEY，请设置环境变量或配置文件")
    sys.exit(1)


# ============================================================
# LLM Prompt — 学术场景优化
# ============================================================

ACADEMIC_LLM_PROMPT = """你是一个专业的数据提取专家，擅长从学术个人网站中提取结构化信息。

# 候选人信息
- 姓名: {name}
- 已知机构: {affiliation}
- 学术 Tier: {tier}
- 网站: {website}

# 网站内容
```
{content}
```

# 论文信息
{papers_info}

# 提取要求

请从网站内容中提取以下信息，以 JSON 格式返回。如果某项信息没有明确出现在网页中，不要猜测，填 null 或空数组。

```json
{{
  "current_position": {{
    "title": "当前职位 (如 Assistant Professor / PhD Student / Research Scientist)",
    "company": "当前所在机构 (如 Stanford University / Google DeepMind)",
    "department": "所在部门/实验室 (如有)"
  }},
  "work_history": [
    {{"company": "公司/机构", "role": "职位", "current": true/false}}
  ],
  "education": [
    {{"degree": "PhD/Master/Bachelor", "field": "专业", "university": "学校名", "year": "毕业年份(如有)"}}
  ],
  "skills": ["PyTorch", "Reinforcement Learning", "NLP", ...],
  "research_areas": ["具体研究方向1", "研究方向2", ...],
  "research_summary": "一句话总结此人的研究重点和贡献",
  "talking_points": [
    "结合其研究和背景，生成3-5个猎头外联时可用的谈话点/破冰话题"
  ],
  "quality_score": 0-100
}}
```

**质量评分标准**:
- 有明确当前职位: +25
- 有教育背景: +20  
- 有技能/研究方向: +15
- 有工作履历 ≥2 条: +15
- 有论文/项目: +15
- 信息丰富度 (技能多、方向清晰): +10

请直接返回 JSON，不要包含其他文字。"""


# ============================================================
# 单人 LLM 处理
# ============================================================

def extract_with_llm(name: str, homepage_text: str, author_info: dict,
                      api_key: str) -> Optional[Dict]:
    """对单个候选人调用 LLM 提取结构化信息"""
    from openai import OpenAI

    affiliation = author_info.get("affiliation", "") or ""
    tier = author_info.get("_academic_tier", "?")
    website = author_info.get("personal_website", "") or author_info.get("homepage", "")
    
    # 构建论文信息 (papers 可能是 str list 或 dict list)
    papers = author_info.get("papers", [])
    if papers:
        paper_lines = []
        for p in papers[:5]:
            if isinstance(p, dict):
                paper_lines.append(f"  · {p.get('title', '?')} ({p.get('conference', '?')})")
            else:
                paper_lines.append(f"  · {p}")
        papers_info = "已知论文:\n" + "\n".join(paper_lines)
    else:
        papers_info = "无已知论文信息"

    # 限制输入长度
    content = homepage_text[:10000] if len(homepage_text) > 10000 else homepage_text

    prompt = ACADEMIC_LLM_PROMPT.format(
        name=name,
        affiliation=affiliation,
        tier=tier,
        website=website,
        content=content,
        papers_info=papers_info
    )

    try:
        client = OpenAI(
            api_key=api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )

        response = client.chat.completions.create(
            model="qwen-plus",
            messages=[
                {"role": "system", "content": "你是一位专业的数据提取专家，擅长从学术网页内容中提取结构化人才信息。请只返回 JSON。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
        )

        llm_text = response.choices[0].message.content.strip()

        # 提取 JSON
        json_match = re.search(r'\{.*\}', llm_text, re.DOTALL)
        if json_match:
            extracted = json.loads(json_match.group(0))
            return extracted
        else:
            return None

    except Exception as e:
        log(f"  ❌ LLM error ({name}): {e}")
        return None


# ============================================================
# 主流程
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Academic LLM Enrichment — 学术人才 LLM 深度富化")
    parser.add_argument("--deep-cache", required=True,
                       help="_deep_cache.json 路径")
    parser.add_argument("--serper-cache", required=True,
                       help="_serper_cache.json 路径")
    parser.add_argument("--input", required=True,
                       help="all_conf_*_full.json 路径")
    parser.add_argument("--output", default=None,
                       help="输出路径 (默认: 同目录 _llm_enrichment_results.json)")
    parser.add_argument("--workers", type=int, default=5,
                       help="并发 worker 数 (默认: 5)")
    parser.add_argument("--max-users", type=int, default=None,
                       help="限制处理人数 (测试用)")
    parser.add_argument("--min-text-len", type=int, default=100,
                       help="最小 homepage_text 长度 (默认: 100)")
    args = parser.parse_args()

    global _global_results, _global_output_path

    api_key = _load_api_key()

    # 加载数据
    log("=" * 60)
    log("🧠 Academic LLM Enrichment")
    log("=" * 60)

    deep_cache_path = Path(args.deep_cache)
    serper_cache_path = Path(args.serper_cache)
    input_path = Path(args.input)

    if args.output:
        output_path = Path(args.output)
    else:
        output_path = deep_cache_path.parent / "_llm_enrichment_results.json"

    log(f"  Deep cache: {deep_cache_path.name}")
    log(f"  Serper cache: {serper_cache_path.name}")
    log(f"  Input: {input_path.name}")
    log(f"  Output: {output_path.name}")
    log(f"  Workers: {args.workers}")

    # 加载 deep cache
    with open(deep_cache_path) as f:
        deep_cache = json.load(f)
    log(f"  📦 Deep cache: {len(deep_cache)} 条")

    # 加载 serper cache (也可能有 homepage_text)
    with open(serper_cache_path) as f:
        serper_cache = json.load(f)
    log(f"  📦 Serper cache: {len(serper_cache)} 条")

    # 加载 authors
    with open(input_path) as f:
        authors = json.load(f)
    log(f"  📥 Authors: {len(authors)} 人")

    # 构建 name → author_info 映射
    author_map = {}
    for a in authors:
        name = a.get("name", "")
        if name:
            author_map[name] = a

    # 合并所有可用的 homepage_text
    # 来源 1: deep cache
    text_map = {}  # name → (homepage_text, homepage_url)
    for k, v in deep_cache.items():
        if k.startswith("deep_homepage::"):
            parts = k.split("::")
            if len(parts) >= 2:
                name = parts[1]
                text = v.get("homepage_text", "")
                hp = v.get("homepage", "")
                if text and len(text) >= args.min_text_len:
                    text_map[name] = (text, hp)

    # 来源 2: serper cache (新增 homepage_text 字段)
    for k, v in serper_cache.items():
        if k.startswith("serper::"):
            name = k.replace("serper::", "")
            if name not in text_map:
                text = v.get("homepage_text", "")
                hp = v.get("homepage", "")
                if text and len(text) >= args.min_text_len:
                    text_map[name] = (text, hp)

    log(f"  📝 有 homepage_text 的人: {len(text_map)}")

    # 加载已有结果 (断点续传)
    results = {}
    if output_path.exists():
        try:
            with open(output_path) as f:
                results = json.load(f)
            completed = sum(1 for v in results.values() if v.get("llm_status") == "done")
            log(f"  📁 恢复已有结果: {completed}/{len(results)} 完成")
        except Exception:
            results = {}

    _global_results = results
    _global_output_path = output_path

    # 构建待处理列表
    to_process = []
    skipped = 0
    for name, (text, hp) in text_map.items():
        if name in results and results[name].get("llm_status") == "done":
            skipped += 1
            continue
        to_process.append((name, text, hp))

    if args.max_users:
        to_process = to_process[:args.max_users]

    log(f"  📋 待处理: {len(to_process)} 人, 跳过(已完成): {skipped}")

    if not to_process:
        log("✅ 所有目标已完成")
        return

    # 并发处理
    log("=" * 60)
    log(f"🚀 开始 LLM 提取 (workers={args.workers})")
    log("=" * 60)

    stats = {"success": skipped, "failed": 0, "total": len(text_map)}
    progress_lock = threading.Lock()
    processed_count = skipped
    start_time = time.time()

    def process_one(name: str, text: str, hp: str) -> Tuple[str, Optional[Dict]]:
        author_info = author_map.get(name, {})
        author_info["homepage"] = hp
        extracted = extract_with_llm(name, text, author_info, api_key)
        return name, extracted

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {}
        for name, text, hp in to_process:
            future = executor.submit(process_one, name, text, hp)
            futures[future] = name

        for future in as_completed(futures):
            name = futures[future]
            try:
                name, extracted = future.result()
                with progress_lock:
                    processed_count += 1
                    if extracted:
                        result_entry = {
                            "llm_status": "done",
                            "extracted": extracted,
                            "timestamp": datetime.now().isoformat(),
                        }
                        # 合并 author 元数据
                        author_info = author_map.get(name, {})
                        result_entry["tier"] = author_info.get("_academic_tier", "?")
                        result_entry["affiliation"] = author_info.get("affiliation", "")

                        results[name] = result_entry
                        stats["success"] += 1
                        score = extracted.get("quality_score", 0)
                        pos = extracted.get("current_position", {})
                        title = pos.get("title", "-") if isinstance(pos, dict) else "-"
                        company = pos.get("company", "-") if isinstance(pos, dict) else "-"
                        log(f"  ✅ {processed_count}/{stats['total']} {name:25s} | "
                            f"q={score:3d} | {title} @ {company}")
                    else:
                        results[name] = {"llm_status": "failed", "timestamp": datetime.now().isoformat()}
                        stats["failed"] += 1
                        log(f"  ⚠️  {processed_count}/{stats['total']} {name:25s} | 提取失败")

                    # 每 20 人保存一次
                    if processed_count % 20 == 0:
                        safe_save_json(results, output_path, backup=False)
                        elapsed = time.time() - start_time
                        speed = (processed_count - skipped) / max(elapsed, 1)
                        remaining = len(to_process) - (processed_count - skipped)
                        eta_min = remaining / max(speed, 0.01) / 60
                        log(f"  💾 进度: {processed_count}/{stats['total']} "
                            f"({processed_count*100/stats['total']:.0f}%) | "
                            f"成功: {stats['success']} | 失败: {stats['failed']} | "
                            f"ETA: {eta_min:.0f}min")

            except Exception as e:
                log(f"  ❌ {name}: {e}")
                with progress_lock:
                    processed_count += 1
                    results[name] = {"llm_status": "failed", "error": str(e)}
                    stats["failed"] += 1

    # 最终保存
    safe_save_json(results, output_path, backup=True)

    # 统计
    log("=" * 60)
    log("📊 LLM Enrichment Results")
    log("=" * 60)
    log(f"  总人数: {stats['total']}")
    log(f"  成功: {stats['success']}")
    log(f"  失败: {stats['failed']}")

    # Tier 分布
    tier_stats = {}
    for name, res in results.items():
        tier = res.get("tier", "?")
        if tier not in tier_stats:
            tier_stats[tier] = {"total": 0, "done": 0, "has_position": 0}
        tier_stats[tier]["total"] += 1
        if res.get("llm_status") == "done":
            tier_stats[tier]["done"] += 1
            ex = res.get("extracted", {})
            if ex.get("current_position", {}).get("title"):
                tier_stats[tier]["has_position"] += 1

    for tier in ["S", "A+", "A", "B", "C", "?"]:
        if tier in tier_stats:
            t = tier_stats[tier]
            log(f"    {tier:3s}: {t['total']:4d} | done: {t['done']:3d} | "
                f"has_position: {t['has_position']:3d}")

    elapsed_total = (time.time() - start_time) / 60
    log(f"  ⏰ 总耗时: {elapsed_total:.1f} min")
    log(f"  📁 结果: {output_path}")
    log("✅ LLM Enrichment 完成!")


if __name__ == "__main__":
    main()
