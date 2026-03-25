#!/bin/bash
# Serper 全 tier 链式执行脚本
# 用两个 key 的 5000 credits 覆盖 S/A+/A/B 四个 tier
# 支持断点续传（缓存文件自动恢复）
# 支持环境变量覆盖（复用于不同批次）：
#   INPUT OUTPUT_DIR LOG_DIR KEY1 KEY2 KEY3 KEY4
#
# 用法示例（2019-2022 批次）:
#   INPUT=.../serper_input.json OUTPUT_DIR=.../outputs \
#   KEY1=xxx KEY2=xxx KEY3=xxx KEY4=xxx \
#   bash run_serper_all_tiers.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")"; pwd)"

# 路径：环境变量优先，否则用 2025 默认值（向后兼容）
INPUT="${INPUT:-$SCRIPT_DIR/../data/academic/runs/conference_full_20260311_131547/outputs/all_conf_2025_20260312_133211_full.json}"
OUTPUT_DIR="${OUTPUT_DIR:-$SCRIPT_DIR/../data/academic/runs/conference_full_20260311_131547/outputs/}"
LOG_DIR="${LOG_DIR:-$SCRIPT_DIR/../data/academic/runs/conference_full_20260311_131547/logs/}"
CACHE="${CACHE:-$OUTPUT_DIR/_serper_cache.json}"

# Keys：环境变量优先，否则用原有默认值
KEY1="${KEY1:-54b047a2bd3fe61b9a060237540bb72d7e96ae4b}"
KEY2="${KEY2:-ec66c2ea352436642e0c7470b752d01bb582b982}"
KEY3="${KEY3:-}"  # 第三个 Key（可选，有则并行加速 A tier）
KEY4="${KEY4:-}"  # 第四个 Key（可选，有则并行加速 A tier）


echo "=============================="
echo "Serper 全 Tier 链式执行"
echo "  输入: $INPUT"
echo "  缓存: $CACHE"
echo "=============================="

# Batch 1: S,A+ (Key2, ~1,076 人)
# 如果已经跑过，缓存会自动跳过
echo ""
echo "[Batch 1] S,A+ tier (Key 2)"
python3 "$SCRIPT_DIR/academic_contact_enricher.py" \
  --input "$INPUT" \
  --output "$OUTPUT_DIR" \
  --serper-only \
  --serper-key "$KEY2" \
  --serper-tiers "S,A+" \
  --cache "$CACHE" \
  2>&1 | tee -a "$LOG_DIR/serper_all_tiers.log"

# Batch 2: A tier (Key2 剩余 + Key1, ~1,617 人)  
echo ""
echo "[Batch 2] A tier (Key 2)"
python3 "$SCRIPT_DIR/academic_contact_enricher.py" \
  --input "$INPUT" \
  --output "$OUTPUT_DIR" \
  --serper-only \
  --serper-key "$KEY2" \
  --serper-tiers "A" \
  --cache "$CACHE" \
  2>&1 | tee -a "$LOG_DIR/serper_all_tiers.log"

# Key2 应该还剩一些 credits，但可能不够跑完 A tier
# 如果 Key2 耗尽，用 Key1 继续 A tier (缓存自动跳过已完成的)
echo ""
echo "[Batch 2b] A tier 续跑 (Key 1)"
python3 "$SCRIPT_DIR/academic_contact_enricher.py" \
  --input "$INPUT" \
  --output "$OUTPUT_DIR" \
  --serper-only \
  --serper-key "$KEY1" \
  --serper-tiers "A" \
  --cache "$CACHE" \
  2>&1 | tee -a "$LOG_DIR/serper_all_tiers.log"

# Batch 3: B tier (Key1 剩余, ~2,374 人，可能跑不完)
echo ""
echo "[Batch 3] B tier (Key 1)"
python3 "$SCRIPT_DIR/academic_contact_enricher.py" \
  --input "$INPUT" \
  --output "$OUTPUT_DIR" \
  --serper-only \
  --serper-key "$KEY1" \
  --serper-tiers "B" \
  --cache "$CACHE" \
  2>&1 | tee -a "$LOG_DIR/serper_all_tiers.log"

echo ""
echo "=============================="
echo "✅ Serper 全 Tier 执行完成!"
echo "=============================="
