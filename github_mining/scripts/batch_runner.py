#!/usr/bin/env python3
"""
GitHub Mining Batch Runner — 批次管理器 v1.0

设计原则:
  - 每次跑批创建独立的带时间戳文件夹
  - 所有阶段的 input/output 完整保存到批次文件夹
  - 不同批次绝对隔离，不覆盖历史数据
  - 最终写文件前备份旧文件（_save_json_safe）
  - 断点续传在批次内工作
  - 完整血缘追踪记录在 batch_meta.json

用法:
  # 完整端到端流程（含30人验证）
  python3 batch_runner.py --input phase5_pre_filtered_input.json \\
    --phases prefilter,phase3,phase3_5,phase4_5,db_import \\
    --max-users 30 --batch-name "e2e_validation"

  # 续传中断批次
  python3 batch_runner.py --resume-batch runs/20260311_080000_e2e_validation

  # 查看历史批次
  python3 batch_runner.py --list
"""

import os
import sys
import json
import shutil
import argparse
import subprocess
from datetime import datetime
from pathlib import Path

# ===== 路径配置 =====
SCRIPT_DIR = Path(__file__).parent
GITHUB_MINING_DIR = SCRIPT_DIR / "github_mining"
PERSONAL_AI_DIR = SCRIPT_DIR.parent.parent / "personal-ai-headhunter"
RUNS_DIR = SCRIPT_DIR / "runs"
RUNS_DIR.mkdir(exist_ok=True)

# 强制刷新输出（nohup 模式）
import functools
print = functools.partial(print, flush=True)


# ============================================================
# 工具函数
# ============================================================

def log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")


def save_meta(batch_dir: Path, meta: dict):
    """保存批次元数据"""
    with open(batch_dir / "batch_meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


def load_meta(batch_dir: Path) -> dict:
    meta_path = batch_dir / "batch_meta.json"
    if meta_path.exists():
        with open(meta_path) as f:
            return json.load(f)
    return {}


def safe_copy_input(src: Path, batch_dir: Path) -> Path:
    """复制 input 文件到批次 inputs/ 目录（只复制，不动原文件）"""
    dst = batch_dir / "inputs" / src.name
    if not dst.exists():
        shutil.copy2(src, dst)
        size_mb = dst.stat().st_size / 1024 / 1024
        log(f"  📁 input 副本: {dst.name} ({size_mb:.1f} MB)")
    return dst


def update_latest_symlink(target: Path, link_name: Path):
    """更新 _latest 软链接，指向最新批次的输出文件"""
    if link_name.exists() or link_name.is_symlink():
        link_name.unlink()
    link_name.symlink_to(target.resolve())
    log(f"  🔗 latest 链接: {link_name.name} → {target}")


def load_json(path: Path) -> list:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def count_json(path: Path) -> int:
    if not path.exists():
        return 0
    try:
        return len(load_json(path))
    except Exception:
        return 0


# ============================================================
# Pre-filter 逻辑
# ============================================================

def detect_nationality_simple(name: str, company: str, bio: str) -> str:
    """
    简单国籍检测（不依赖外部模块）
    返回: 'chinese' / 'foreign' / 'unknown'
    只排除确定外国人，unknown 保留
    """
    # 先尝试导入精确版本
    try:
        sys.path.insert(0, str(PERSONAL_AI_DIR / "scripts"))
        from add_nationality_tags import detect_nationality
        nationality, _ = detect_nationality(name, company)
        return nationality
    except ImportError:
        pass

    # 兜底：简单规则
    text = f"{name} {company} {bio}".lower()

    # 明确中文标记
    chinese_markers = ["中国", "北京", "上海", "深圳", "杭州", "成都", "阿里", "腾讯",
                       "字节", "百度", "华为", "清华", "北大", "复旦", "浙大"]
    for m in chinese_markers:
        if m in text:
            return "chinese"

    # 明确外国标记（只排除确定外国人）
    # 使用姓名规则：如果全是 ASCII 且公司不含中国关键词，才判为 foreign
    if name and all(ord(c) < 128 for c in name):
        company_lower = company.lower()
        cn_companies = ["alibaba", "tencent", "bytedance", "baidu", "huawei",
                        "didi", "meituan", "jd.com", "netease", "xiaomi",
                        "deepseek", "minimax", "moonshot", "zhipu", "01.ai"]
        if not any(c in company_lower for c in cn_companies):
            return "foreign"

    return "unknown"


def run_prefilter(input_file: Path, output_file: Path, max_users: int = None) -> dict:
    """
    Pre-filter: 过滤机构账户和确定外国人
    保留: chinese + unknown 国籍
    返回统计数据
    """
    log(f"\n{'='*60}")
    log("🔍 Pre-filter: 过滤机构账户 + 外国人")
    log(f"{'='*60}")

    candidates = load_json(input_file)
    input_count = len(candidates)
    log(f"  输入: {input_count} 人")

    # 机构账户过滤规则
    org_keywords = ["-bot", "-team", "-org", "-official", "-project",
                    "-ci", "-cd", "-action", "-app", "-sdk", "-api"]

    stats = {
        "input_count": input_count,
        "org_filtered": 0,
        "foreign_filtered": 0,
        "chinese": 0,
        "unknown": 0,
        "output_count": 0,
    }

    kept = []
    for c in candidates:
        username = (c.get("username") or "").lower()
        user_type = c.get("type", "").lower()
        name = c.get("name") or ""
        company = c.get("company") or ""
        bio = c.get("bio") or ""

        # 1. 机构账户
        if user_type == "organization":
            stats["org_filtered"] += 1
            continue
        if any(kw in username for kw in org_keywords):
            stats["org_filtered"] += 1
            continue

        # 2. 国籍过滤
        nationality = detect_nationality_simple(name, company, bio)
        c["_prefilter_nationality"] = nationality  # 保存供分析

        if nationality == "foreign":
            stats["foreign_filtered"] += 1
            continue
        elif nationality == "chinese":
            stats["chinese"] += 1
        else:
            stats["unknown"] += 1

        kept.append(c)

    # 截取 max_users（Pre-filter 之后再截，确保样本质量）
    if max_users and len(kept) > max_users:
        kept = kept[:max_users]
        log(f"  ✂️  截取前 {max_users} 人用于测试")

    stats["output_count"] = len(kept)

    # 保存
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(kept, f, ensure_ascii=False, indent=2)

    log(f"\n  📊 Pre-filter 统计:")
    log(f"     输入:       {stats['input_count']} 人")
    log(f"     机构过滤:   {stats['org_filtered']} 人")
    log(f"     外国人过滤: {stats['foreign_filtered']} 人")
    log(f"     中文:       {stats['chinese']} 人")
    log(f"     Unknown:    {stats['unknown']} 人")
    log(f"     输出:       {stats['output_count']} 人 ✅")

    return stats


def run_db_dedup(input_file: Path, output_file: Path) -> dict:
    """
    DB Dedup: 查询数据库中已存在的用户，提前过滤掉重复人选
    节约 GitHub API 和 LLM token
    """
    log(f"\n{'='*60}")
    log("🗂️  DB Dedup: 提前过滤数据库已有人选")
    log(f"{'='*60}")

    candidates = load_json(input_file)
    input_count = len(candidates)

    # 尝试连接数据库
    import sqlite3
    db_path = PERSONAL_AI_DIR / "data" / "headhunter_dev.db"
    if not db_path.exists():
        log(f"  ⚠️  数据库不存在: {db_path}，跳过 DB Dedup")
        import shutil
        shutil.copy2(input_file, output_file)
        return {"input_count": input_count, "existing_count": 0,
                "output_count": input_count, "skipped_db": True}

    # 查询已存在的 github_url
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT github_url FROM candidates WHERE github_url IS NOT NULL")
        existing_urls = {row[0].rstrip('/') for row in cur.fetchall()}
        conn.close()
    except Exception as e:
        log(f"  ⚠️  DB 查询失败: {e}，跳过 DB Dedup")
        import shutil
        shutil.copy2(input_file, output_file)
        return {"input_count": input_count, "existing_count": 0,
                "output_count": input_count, "error": str(e)}

    log(f"  🗄️  DB 中已有记录: {len(existing_urls)} 人")

    kept = []
    skipped = []
    for c in candidates:
        url = (c.get("github_url") or f"https://github.com/{c.get('username', '')}").rstrip('/')
        if url in existing_urls:
            skipped.append(c.get("username", "?"))
        else:
            kept.append(c)

    stats = {
        "input_count": input_count,
        "existing_in_db": len(skipped),
        "output_count": len(kept),
        "skipped_usernames_sample": skipped[:20],  # 记录前20个，供回溄3
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(kept, f, ensure_ascii=False, indent=2)

    log(f"\n  📊 DB Dedup 统计:")
    log(f"     输入:       {input_count} 人")
    log(f"     DB已存在: {len(skipped)} 人 ← 节省这些人的 API 和 token")
    log(f"     输出:       {len(kept)} 人 ✅")

    return stats


def run_phase3(input_file: Path, output_file: Path, batch_dir: Path,
               resume: bool = True, max_users: int = None) -> dict:
    """运行 Phase 3 GitHub repos 深度富化"""
    log(f"\n{'='*60}")
    log("📊 Phase 3: GitHub repos 深度富化")
    log(f"{'='*60}")

    log_file = batch_dir / "logs" / f"phase3_{datetime.now().strftime('%H%M%S')}.log"

    cmd = [
        sys.executable,
        str(SCRIPT_DIR / "github_network_miner.py"),
        "phase3",
        "--input", str(input_file),
        "--output", str(output_file),
    ]
    if resume:
        cmd.append("--resume")
    if max_users:
        cmd += ["--max-users", str(max_users)]

    log(f"  🚀 启动 Phase 3，日志: {log_file.name}")
    with open(log_file, "w") as lf:
        proc = subprocess.run(
            cmd, cwd=str(SCRIPT_DIR),
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        lf.write(proc.stdout)

    # 打印最后 15 行
    for line in proc.stdout.splitlines()[-15:]:
        print(f"    {line}")

    return {
        "input": count_json(input_file),
        "output": count_json(output_file),
        "exit_code": proc.returncode,
    }


def run_phase3_5(input_file: Path, output_file: Path, batch_dir: Path,
                 resume: bool = True) -> dict:
    """运行 Phase 3.5 个人主页爬取"""
    log(f"\n{'='*60}")
    log("🌐 Phase 3.5: 个人主页爬取")
    log(f"{'='*60}")

    log_file = batch_dir / "logs" / f"phase3_5_{datetime.now().strftime('%H%M%S')}.log"

    cmd = [
        sys.executable,
        str(SCRIPT_DIR / "github_network_miner.py"),
        "phase3_5",
        "--input", str(input_file),
        "--output", str(output_file),
    ]
    if resume:
        cmd.append("--resume")

    log(f"  🚀 启动 Phase 3.5，日志: {log_file.name}")
    with open(log_file, "w") as lf:
        proc = subprocess.run(
            cmd, cwd=str(SCRIPT_DIR),
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        lf.write(proc.stdout)

    for line in proc.stdout.splitlines()[-15:]:
        print(f"    {line}")

    data = load_json(output_file) if output_file.exists() else []
    with_homepage = sum(1 for d in data if d.get("homepage_scraped"))
    return {
        "input": count_json(input_file),
        "output": len(data),
        "with_homepage": with_homepage,
        "exit_code": proc.returncode,
    }


def run_phase4_5(input_file: Path, output_file: Path, batch_dir: Path) -> dict:
    """运行 Phase 4.5 LLM 深度富化"""
    log(f"\n{'='*60}")
    log("🤖 Phase 4.5: LLM 深度富化")
    log(f"{'='*60}")

    log_file = batch_dir / "logs" / f"phase4_5_{datetime.now().strftime('%H%M%S')}.log"

    cmd = [
        sys.executable,
        str(SCRIPT_DIR / "run_phase4_5_llm_enrichment.py"),
        "--input", str(input_file),
        "--output", str(output_file),
    ]

    log(f"  🚀 启动 Phase 4.5，日志: {log_file.name}")
    with open(log_file, "w") as lf:
        proc = subprocess.run(
            cmd, cwd=str(SCRIPT_DIR),
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        lf.write(proc.stdout)

    for line in proc.stdout.splitlines()[-15:]:
        print(f"    {line}")

    return {
        "input": count_json(input_file),
        "output": count_json(output_file),
        "exit_code": proc.returncode,
    }


def run_db_import(input_file: Path, batch_dir: Path, dry_run: bool = False) -> dict:
    """运行数据库导入（幂等，按 github_url 去重）"""
    log(f"\n{'='*60}")
    log(f"💾 DB Import{'（dry-run）' if dry_run else ''}")
    log(f"{'='*60}")

    log_file = batch_dir / "logs" / f"db_import_{datetime.now().strftime('%H%M%S')}.log"
    import_script = PERSONAL_AI_DIR / "import_github_candidates.py"

    if not import_script.exists():
        log(f"  ❌ 找不到导入脚本: {import_script}")
        return {"error": f"script not found: {import_script}"}

    cmd = [sys.executable, str(import_script), "--file", str(input_file)]
    if dry_run:
        cmd.append("--dry-run")

    with open(log_file, "w") as lf:
        proc = subprocess.run(
            cmd, cwd=str(PERSONAL_AI_DIR),
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        lf.write(proc.stdout)

    for line in proc.stdout.splitlines()[-20:]:
        print(f"    {line}")

    # 解析导入统计
    stats = {"dry_run": dry_run, "exit_code": proc.returncode}
    for line in proc.stdout.splitlines():
        if "新增" in line or "新建" in line:
            import re
            nums = re.findall(r'\d+', line)
            if nums:
                stats["new"] = int(nums[0])
        if "更新" in line:
            import re
            nums = re.findall(r'\d+', line)
            if nums:
                stats["update"] = int(nums[0])
        if "跳过" in line or "重复" in line:
            import re
            nums = re.findall(r'\d+', line)
            if nums:
                stats["skipped"] = int(nums[0])

    return stats


# ============================================================
# 批次主控
# ============================================================

def create_batch(batch_name: str) -> Path:
    """创建带时间戳的批次目录"""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    name = f"{ts}_{batch_name}" if batch_name else ts
    batch_dir = RUNS_DIR / name
    batch_dir.mkdir(parents=True, exist_ok=True)
    (batch_dir / "inputs").mkdir(exist_ok=True)
    (batch_dir / "outputs").mkdir(exist_ok=True)
    (batch_dir / "logs").mkdir(exist_ok=True)
    
    # 归档设计文档到本批次目录，确保永久可追溯
    doc_src = SCRIPT_DIR.parent / "docs" / "pipeline_design_v3.md"
    if doc_src.exists():
        shutil.copy2(doc_src, batch_dir / f"pipeline_design_{name}.md")
        
    log(f"📁 批次目录: {batch_dir}")
    return batch_dir


def run_batch(input_file: Path, phases: list, batch_dir: Path,
              max_users: int = None, resume: bool = True,
              skip_prefilter: bool = False, skip_db_dedup: bool = False,
              db_dry_run_first: bool = True,
              seed_users: list = None) -> dict:
    """执行完整批次"""

    outputs = batch_dir / "outputs"
    meta = load_meta(batch_dir)
    lineage = meta.get("lineage", {})

    # 记录种子用户（如有）
    if seed_users:
        lineage["seed_users"] = seed_users

    current_input = input_file

    for phase in phases:
        phase = phase.strip().lower()

        if phase == "prefilter" and not skip_prefilter:
            out = outputs / "pre_filtered.json"
            if out.exists() and resume:
                log(f"⏭️  pre_filtered.json 已存在，跳过 Pre-filter")
            else:
                stats = run_prefilter(current_input, out, max_users=max_users)
                lineage["prefilter"] = stats
                meta["lineage"] = lineage
                save_meta(batch_dir, meta)
            current_input = out

        elif phase == "db_dedup" and not skip_db_dedup:
            out = outputs / "db_deduped.json"
            if out.exists() and resume:
                log(f"⏭️  db_deduped.json 已存在，跳过 DB Dedup")
            else:
                stats = run_db_dedup(current_input, out)
                lineage["db_dedup"] = stats
                meta["lineage"] = lineage
                save_meta(batch_dir, meta)
            current_input = out

        elif phase == "phase3":
            out = outputs / "phase3_enriched.json"
            stats = run_phase3(current_input, out, batch_dir, resume=resume,
                               max_users=max_users if "prefilter" not in phases else None)
            lineage["phase3"] = stats
            meta["lineage"] = lineage
            save_meta(batch_dir, meta)
            if out.exists():
                update_latest_symlink(out, GITHUB_MINING_DIR / "phase3_enriched_latest.json")
            current_input = out

        elif phase == "phase3_5":
            out = outputs / "phase3_5_enriched.json"
            stats = run_phase3_5(current_input, out, batch_dir, resume=resume)
            lineage["phase3_5"] = stats
            meta["lineage"] = lineage
            save_meta(batch_dir, meta)
            if out.exists():
                update_latest_symlink(out, GITHUB_MINING_DIR / "phase3_5_enriched_latest.json")
            current_input = out

        elif phase == "phase4_5":
            out = outputs / "phase45_final.json"
            stats = run_phase4_5(current_input, out, batch_dir)
            lineage["phase4_5"] = stats
            meta["lineage"] = lineage
            save_meta(batch_dir, meta)
            if out.exists():
                update_latest_symlink(out, GITHUB_MINING_DIR / "phase45_final_latest.json")
            current_input = out

        elif phase == "db_import":
            if db_dry_run_first:
                log("  🔍 先执行 dry-run...")
                dry_stats = run_db_import(current_input, batch_dir, dry_run=True)
                lineage.setdefault("db_import", {})["dry_run"] = dry_stats
                meta["lineage"] = lineage
                save_meta(batch_dir, meta)
                log(f"\n  ⚠️  Dry-run 完成。正式导入前请检查 batch_meta.json 确认数据")
                log(f"     dry_run 统计: {dry_stats}")
                # 延迟 5 秒确认
                import time; time.sleep(5)

            actual_stats = run_db_import(current_input, batch_dir, dry_run=False)
            lineage.setdefault("db_import", {})["actual"] = actual_stats
            meta["lineage"] = lineage
            save_meta(batch_dir, meta)

        else:
            log(f"⚠️  未知阶段: {phase}，跳过")

    return lineage


# ============================================================
# 历史批次查看
# ============================================================

def list_batches():
    batches = sorted([b for b in RUNS_DIR.iterdir() if b.is_dir()], reverse=True)
    if not batches:
        print("📂 尚无批次记录")
        return

    print(f"\n{'='*60}")
    print(f"📋 历史批次 ({len(batches)} 个)")
    print(f"{'='*60}")
    for b in batches[:20]:
        meta = load_meta(b)
        status = meta.get("status", "?")
        start = meta.get("start_time", "?")[:19]
        phases = ",".join(meta.get("phases", []))
        lineage = meta.get("lineage", {})

        output_count = 0
        if "phase3" in lineage:
            output_count = lineage["phase3"].get("output", 0)
        elif "prefilter" in lineage:
            output_count = lineage["prefilter"].get("output_count", 0)

        icon = "✅" if status == "done" else ("❌" if status == "error" else "🔄")
        print(f"\n  {icon} {b.name}")
        print(f"     开始: {start}  状态: {status}  阶段: {phases}")
        if output_count:
            print(f"     共处理: {output_count} 人")


# ============================================================
# 业务统计汇总 (Rich Summary)
# ============================================================

def generate_rich_summary(batch_dir: Path):
    """
    基于最终的 phase45_final.json (或阶段中能找到的最深文件) 
    生成业务统计汇总（级别统计、联系方式、数据富化质量统计）
    """
    meta = load_meta(batch_dir)
    final_json = None
    
    # 获取最深层文件
    for filename in ["phase45_final.json", "phase3_5_enriched.json", "phase3_enriched.json"]:
        p = batch_dir / "outputs" / filename
        if p.exists():
            final_json = p
            break
            
    if not final_json:
        return
        
    candidates = load_json(final_json)
    if not candidates:
        return
        
    stats = {
        "total_candidates": len(candidates),
        "tiers_approx": {"S": 0, "A+": 0, "A": 0, "B+": 0, "B": 0, "C": 0, "D": 0},
        "contact_info": {"has_email": 0, "has_linkedin": 0, "has_website": 0},
        "enrichment_quality": {
            "has_llm_work_history": 0,
            "has_llm_skills": 0,
            "has_talking_points": 0,
            "high_quality_site_ge_70": 0,
            "mid_quality_site_50_69": 0,
            "low_quality_site_lt_50": 0
        }
    }
    
    for c in candidates:
        # 联系方式
        if c.get("email") or c.get("extra_emails") or c.get("all_emails"):
            stats["contact_info"]["has_email"] += 1
            
        linkedin_url = c.get("linkedin_url") or c.get("linkedin")
        if linkedin_url or c.get("linkedin_career"):
            stats["contact_info"]["has_linkedin"] += 1
            
        if c.get("blog") or c.get("homepage_url") or c.get("homepage_text"):
            stats["contact_info"]["has_website"] += 1
            
        # 质量统计
        if c.get("extracted_work_history"):
            stats["enrichment_quality"]["has_llm_work_history"] += 1
            
        if c.get("extracted_skills"):
            stats["enrichment_quality"]["has_llm_skills"] += 1
            
        if c.get("talking_points"):
            stats["enrichment_quality"]["has_talking_points"] += 1
            
        qs = c.get("website_quality_score")
        if qs is not None:
            if qs >= 70:
                stats["enrichment_quality"]["high_quality_site_ge_70"] += 1
            elif qs >= 50:
                stats["enrichment_quality"]["mid_quality_site_50_69"] += 1
            else:
                stats["enrichment_quality"]["low_quality_site_lt_50"] += 1
                
        # Tiers approx (根据 reference 文档简化预估)
        score = c.get("final_score_v2") or c.get("final_score") or 0
        followers = c.get("followers", 0)
        stars = c.get("total_stars", 0)
        
        if followers > 5000 or stars > 5000:
            stats["tiers_approx"]["S"] += 1
        elif score >= 80:
            stats["tiers_approx"]["A"] += 1
        elif score >= 60:
            stats["tiers_approx"]["B+"] += 1
        elif followers > 500 or score >= 40:
            stats["tiers_approx"]["B"] += 1
        else:
            stats["tiers_approx"]["C"] += 1
            
    meta["rich_summary"] = stats
    save_meta(batch_dir, meta)
    
    log(f"\n{'='*60}")
    log(f"📈 批次业务终态统计 (Rich Summary)")
    log(f"   总人数: {stats['total_candidates']}")
    log(f"   [预估评级] S:{stats['tiers_approx']['S']}  A:{stats['tiers_approx']['A']}  B+:{stats['tiers_approx']['B+']}  B:{stats['tiers_approx']['B']}  C:{stats['tiers_approx']['C']}")
    log(f"   [联系方式] 邮箱:{stats['contact_info']['has_email']}  LinkedIn:{stats['contact_info']['has_linkedin']}  个人网站:{stats['contact_info']['has_website']}")
    log(f"   [AI富化] 高质量简历:{stats['enrichment_quality']['high_quality_site_ge_70']}  含破冰话题:{stats['enrichment_quality']['has_talking_points']}")
    log(f"{'='*60}")


# ============================================================
# CLI 入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="GitHub Mining Batch Runner")
    parser.add_argument("--input", help="原始 input 文件路径")
    parser.add_argument("--phases", default="prefilter,phase3,phase3_5,phase4_5,db_import",
                        help="要运行的阶段（逗号分隔）")
    parser.add_argument("--batch-name", help="批次名称")
    parser.add_argument("--max-users", type=int, help="测试用：限制处理人数（Pre-filter 后截取）")
    parser.add_argument("--no-resume", action="store_true", help="不使用断点续传")
    parser.add_argument("--skip-prefilter", action="store_true", help="跳过 Pre-filter")
    parser.add_argument("--skip-db-dedup", action="store_true", help="跳过 DB去重")
    parser.add_argument("--db-dry-run-first", action="store_true", default=True,
                        help="DB import 前先 dry-run（默认开启）")
    parser.add_argument("--resume-batch", help="续传指定批次目录路径")
    parser.add_argument("--list", action="store_true", help="查看历史批次")
    args = parser.parse_args()

    if args.list:
        list_batches()
        return

    if args.resume_batch:
        batch_dir = Path(args.resume_batch)
        if not batch_dir.exists():
            print(f"❌ 批次目录不存在: {batch_dir}")
            sys.exit(1)
        meta = load_meta(batch_dir)
        input_file = Path(meta["input_file"])
        phases = meta["phases"]
        log(f"▶️  续传批次: {batch_dir.name}")
    else:
        if not args.input:
            parser.error("必须指定 --input 或 --resume-batch")
        input_file = Path(args.input)
        if not input_file.is_absolute():
            input_file = SCRIPT_DIR / input_file
        if not input_file.exists():
            print(f"❌ 输入文件不存在: {input_file}")
            sys.exit(1)
        phases = [p.strip() for p in args.phases.split(",")]
        batch_dir = create_batch(args.batch_name or input_file.stem)

    resume = not args.no_resume

    # 初始化 batch_meta
    meta = {
        "batch_id": batch_dir.name,
        "start_time": datetime.now().isoformat(),
        "status": "running",
        "input_file": str(input_file),
        "phases": phases,
        "max_users": args.max_users,
        "lineage": {},
    }
    save_meta(batch_dir, meta)

    # 复制 input 文件
    safe_copy_input(input_file, batch_dir)

    log(f"\n🚀 批次启动")
    log(f"   输入: {input_file.name} ({input_file.stat().st_size/1024/1024:.1f} MB)")
    log(f"   阶段: {phases}")
    log(f"   断点续传: {resume}")
    if args.max_users:
        log(f"   测试模式: 最多 {args.max_users} 人（Pre-filter 后截取）")

    try:
        lineage = run_batch(
            input_file=input_file,
            phases=phases,
            batch_dir=batch_dir,
            max_users=args.max_users,
            resume=resume,
            skip_prefilter=args.skip_prefilter,
            skip_db_dedup=args.skip_db_dedup,
            db_dry_run_first=args.db_dry_run_first,
        )
        meta["status"] = "done"
        meta["end_time"] = datetime.now().isoformat()
        meta["lineage"] = lineage
        save_meta(batch_dir, meta)
        
        # 批次完成后生成增强统计汇总
        generate_rich_summary(batch_dir)

        log(f"\n{'='*60}")
        log(f"✅ 批次完成: {batch_dir.name}")
        log(f"{'='*60}")
        list_batches()

    except Exception as e:
        meta["status"] = "error"
        meta["error"] = str(e)
        meta["end_time"] = datetime.now().isoformat()
        save_meta(batch_dir, meta)
        log(f"\n❌ 批次出错: {e}")
        import traceback; traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
