#!/bin/bash
# Serper 全 tier 链式执行脚本
# 用两个 key 的 5000 credits 覆盖 S/A+/A/B 四个 tier
# 支持断点续传（缓存文件自动恢复）

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")"; pwd)"
INPUT="$SCRIPT_DIR/../data/academic/runs/conference_full_20260311_131547/outputs/all_conf_2025_20260312_133211_full.json"
OUTPUT_DIR="$SCRIPT_DIR/../data/academic/runs/conference_full_20260311_131547/outputs/"
LOG_DIR="$SCRIPT_DIR/../data/academic/runs/conference_full_20260311_131547/logs/"
CACHE="$OUTPUT_DIR/_serper_cache.json"

KEY1="54b047a2bd3fe61b9a060237540bb72d7e96ae4b"
KEY2="ec66c2ea352436642e0c7470b752d01bb582b982"

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
