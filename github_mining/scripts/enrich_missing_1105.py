#!/usr/bin/env python3
"""
富化缺失的 1,105 名候选人
"""

import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path

# 添加 scripts 目录到路径
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

# 导入 LLM 提取函数
from run_phase4_5_llm_enrichment import (
    log,
    extract_with_llm,
    merge_candidate_data,
    DASHSCOPE_API_KEY,
    load_progress,
    save_progress
)

def main():
    log("=" * 70)
    log("🚀 富化缺失的 1,105 名候选人")
    log("=" * 70)
    
    # 输入/输出文件
    INPUT_FILE = SCRIPT_DIR / "github_mining" / "phase45_missing_1105.json"
    OUTPUT_FILE = SCRIPT_DIR / "github_mining" / "phase45_missing_1105_enriched.json"
    PROGRESS_FILE = SCRIPT_DIR / "github_mining" / "phase45_missing_1105_progress.json"
    
    # 加载候选人
    log(f"📖 读取输入文件: {INPUT_FILE}")
    if not INPUT_FILE.exists():
        log(f"❌ 错误: 输入文件不存在: {INPUT_FILE}")
        return
    
    with open(INPUT_FILE) as f:
        candidates = json.load(f)
    
    log(f"✅ 加载 {len(candidates)} 个候选人")
    
    # 检查 API Key
    if not DASHSCOPE_API_KEY:
        log("❌ 错误: 未配置 DASHSCOPE_API_KEY")
        return
    
    log(f"✅ API Key 已配置")
    
    # 加载进度
    progress = load_progress()
    if progress.get("completed"):
        # 重置进度（因为这是新的文件）
        progress = {"completed": [], "failed": [], "stats": {"total": len(candidates), "success": 0, "failed": 0}}
    
    completed_ids = set(progress.get("completed", []))
    stats = progress.get("stats", {"total": len(candidates), "success": 0, "failed": 0})
    
    log(f"📁 进度恢复: 已完成 {len(completed_ids)} 个")
    
    # 批量处理
    log("=" * 70)
    log("开始批量LLM提取...")
    log("=" * 70)
    
    results = []
    
    for i, candidate in enumerate(candidates):
        candidate_id = candidate.get('id', i)
        name = candidate.get('name', 'Unknown')
        
        # 跳过已完成的
        if candidate_id in completed_ids:
            if 'extracted_work_history' in candidate:
                results.append(candidate)
            continue
        
        log(f"[{len(completed_ids)+1}/{len(candidates)}] {name}")
        
        # LLM提取
        extracted = extract_with_llm(candidate)
        
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
    
    # 保存结果
    log(f"💾 保存结果到: {OUTPUT_FILE}")
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # 最终统计
    log("=" * 70)
    log("📊 最终统计")
    log("=" * 70)
    log(f"总候选人数: {len(results)}")
    log(f"成功提取: {stats['success']} ({stats['success']/len(candidates)*100:.1f}%)")
    log(f"提取失败: {stats['failed']} ({stats['failed']/len(candidates)*100:.1f}%)")
    
    # 统计质量分数
    high_quality = sum(1 for r in results if r.get('website_quality_score', 0) >= 90)
    medium_quality = sum(1 for r in results if 60 <= r.get('website_quality_score', 0) < 90)
    low_quality = sum(1 for r in results if 30 <= r.get('website_quality_score', 0) < 60)
    
    log(f"\n📊 质量分布:")
    log(f"   高质量(90-100): {high_quality} 人")
    log(f"   中等质量(60-89): {medium_quality} 人")
    log(f"   基础质量(30-59): {low_quality} 人")
    
    # 清理进度文件
    if PROGRESS_FILE.exists():
        PROGRESS_FILE.unlink()
    
    log("=" * 70)
    log(f"✅ 富化完成！")
    log(f"📁 输出文件: {OUTPUT_FILE}")
    log(f"⏰ 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
