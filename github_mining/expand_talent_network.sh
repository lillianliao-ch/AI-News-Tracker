#!/bin/bash
# GitHub AI人才网络扩展 - 综合执行脚本
# 创建时间: 2026-03-08

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "🚀 GitHub AI人才网络扩展"
echo "⏰ $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 参数解析
MODE=${1:-"both"}  # both, repos, following
REPOS_LIMIT=${2:-10}
STARS_PER_REPO=${3:-300}
CONTRIBUTORS_PER_REPO=${4:-100}

echo "📋 执行模式: $MODE"
echo ""

# ===== 方案1: 从AI项目挖掘 =====
if [[ "$MODE" == "repos" || "$MODE" == "both" ]]; then
    echo "=========================================="
    echo "📦 方案1: 从顶级AI项目挖掘"
    echo "=========================================="
    echo ""
    echo "配置:"
    echo "  - 项目数量: $REPOS_LIMIT"
    echo "  - 每项目Stars: $STARS_PER_REPO"
    echo "  - 每项目Contributors: $CONTRIBUTORS_PER_REPO"
    echo ""

    TIMESTAMP=$(date '+%m%d')
    OUTPUT_FILE="github_mining/ai_repo_users_${TIMESTAMP}.json"

    echo "▶️  Step 1: 获取AI项目用户..."
    python3 scripts/expand_from_ai_repos.py \
        --repos-limit $REPOS_LIMIT \
        --stars-per-repo $STARS_PER_REPO \
        --contributors-per-repo $CONTRIBUTORS_PER_REPO \
        --output "$OUTPUT_FILE"

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Step 1 完成${NC}"
        echo "   输出: $OUTPUT_FILE"

        # 统计
        USER_COUNT=$(python3 -c "import json; print(len(json.load(open('$OUTPUT_FILE'))))")
        echo "   用户数: $USER_COUNT"
        echo ""

        # Phase 3 富化
        echo "▶️  Step 2: Phase 3 深度富化..."
        PHASE3_OUTPUT="github_mining/phase3_from_ai_repos_${TIMESTAMP}.json"

        cd scripts
        python3 github_network_miner.py --phase3 --input "../$OUTPUT_FILE" --output "../$PHASE3_OUTPUT"
        cd ..

        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ Step 2 完成${NC}"
            echo "   输出: $PHASE3_OUTPUT"

            PHASE3_COUNT=$(python3 -c "import json; print(len(json.load(open('$PHASE3_OUTPUT'))))")
            echo "   富化后: $PHASE3_COUNT 人"
            echo ""

            # Phase 4.5 LLM富化
            echo "▶️  Step 3: Phase 4.5 LLM富化..."
            PHASE45_OUTPUT="github_mining/phase45_from_ai_repos_${TIMESTAMP}.json"

            python3 scripts/run_phase4_5_llm_enrichment.py \
                --input "$PHASE3_OUTPUT" \
                --output "$PHASE45_OUTPUT"

            if [ $? -eq 0 ]; then
                echo -e "${GREEN}✅ Step 3 完成${NC}"
                echo "   输出: $PHASE45_OUTPUT"

                PHASE45_COUNT=$(python3 -c "import json; print(len(json.load(open('$PHASE45_OUTPUT'))))")
                echo "   最终: $PHASE45_COUNT 人"
                echo ""

                echo -e "${GREEN}🎉 方案1执行成功！${NC}"
                echo ""
                echo "📊 结果汇总:"
                echo "  - 原始用户: $USER_COUNT"
                echo "  - Phase 3: $PHASE3_COUNT"
                echo "  - Phase 4.5: $PHASE45_COUNT"
                echo ""
            else
                echo -e "${RED}❌ Phase 4.5富化失败${NC}"
                exit 1
            fi
        else
            echo -e "${RED}❌ Phase 3富化失败${NC}"
            exit 1
        fi
    else
        echo -e "${RED}❌ AI项目用户获取失败${NC}"
        exit 1
    fi
fi

# ===== 方案2: 从Following网络扩展 =====
if [[ "$MODE" == "following" || "$MODE" == "both" ]]; then
    echo "=========================================="
    echo "🔗 方案2: 从Following网络扩展"
    echo "=========================================="
    echo ""

    SEEDS_FILE="github_mining/phase5_seed_usernames_sb.json"

    if [ ! -f "$SEEDS_FILE" ]; then
        echo -e "${RED}❌ 种子文件不存在: $SEEDS_FILE${NC}"
        exit 1
    fi

    SEED_COUNT=$(python3 -c "import json; print(len(json.load(open('$SEEDS_FILE'))))")
    echo "📊 种子用户: $SEED_COUNT 人"
    echo ""

    echo "▶️  Step 1: 社交网络扩展..."
    TIMESTAMP=$(date '+%m%d')
    PHASE5_OUTPUT="github_mining/phase5_expanded_${TIMESTAMP}.json"

    python3 scripts/run_phase5_expansion.py \
        --seeds-file "$SEEDS_FILE" \
        --min-cooccurrence 3 \
        --max-seeds 200

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Step 1 完成${NC}"

        # 重命名输出文件
        if [ -f "github_mining/phase5_expanded.json" ]; then
            mv "github_mining/phase5_expanded.json" "$PHASE5_OUTPUT"
            echo "   输出: $PHASE5_OUTPUT"

            PHASE5_COUNT=$(python3 -c "import json; print(len(json.load(open('$PHASE5_OUTPUT'))))")
            echo "   发现: $PHASE5_COUNT 人"
            echo ""

            # Phase 3 富化
            echo "▶️  Step 2: Phase 3 深度富化..."
            PHASE3_OUTPUT="github_mining/phase3_from_phase5_${TIMESTAMP}.json"

            cd scripts
            python3 github_network_miner.py --phase3 --input "../$PHASE5_OUTPUT" --output "../$PHASE3_OUTPUT"
            cd ..

            if [ $? -eq 0 ]; then
                echo -e "${GREEN}✅ Step 2 完成${NC}"
                echo "   输出: $PHASE3_OUTPUT"

                PHASE3_COUNT=$(python3 -c "import json; print(len(json.load(open('$PHASE3_OUTPUT'))))")
                echo "   富化后: $PHASE3_COUNT 人"
                echo ""

                # Phase 4.5 LLM富化
                echo "▶️  Step 3: Phase 4.5 LLM富化..."
                PHASE45_OUTPUT="github_mining/phase45_from_phase5_${TIMESTAMP}.json"

                python3 scripts/run_phase4_5_llm_enrichment.py \
                    --input "$PHASE3_OUTPUT" \
                    --output "$PHASE45_OUTPUT"

                if [ $? -eq 0 ]; then
                    echo -e "${GREEN}✅ Step 3 完成${NC}"
                    echo "   输出: $PHASE45_OUTPUT"

                    PHASE45_COUNT=$(python3 -c "import json; print(len(json.load(open('$PHASE45_OUTPUT'))))")
                    echo "   最终: $PHASE45_COUNT 人"
                    echo ""

                    echo -e "${GREEN}🎉 方案2执行成功！${NC}"
                    echo ""
                    echo "📊 结果汇总:"
                    echo "  - 种子用户: $SEED_COUNT"
                    echo "  - Phase 5扩展: $PHASE5_COUNT"
                    echo "  - Phase 3: $PHASE3_COUNT"
                    echo "  - Phase 4.5: $PHASE45_COUNT"
                    echo ""
                else
                    echo -e "${RED}❌ Phase 4.5富化失败${NC}"
                    exit 1
                fi
            else
                echo -e "${RED}❌ Phase 3富化失败${NC}"
                exit 1
            fi
        else
            echo -e "${RED}❌ Phase 5输出文件未找到${NC}"
            exit 1
        fi
    else
        echo -e "${RED}❌ 社交网络扩展失败${NC}"
        exit 1
    fi
fi

# ===== 最终汇总 =====
echo "=========================================="
echo "✅ 扩展完成"
echo "=========================================="
echo ""
echo "📂 输出文件位置: github_mining/"
echo ""
echo "🎯 下一步操作:"
echo ""
echo "1. 查看结果:"
echo "   ls -lh github_mining/*_${TIMESTAMP}.json"
echo ""
echo "2. 导入数据库:"
echo "   cd ../personal-ai-headhunter"
echo "   python3 import_github_candidates.py --file ../github_mining/phase45_from_*_${TIMESTAMP}.json"
echo ""
echo "3. 更新Tier评级:"
echo "   python3 scripts/batch_update_tiers.py"
echo ""
echo "4. 生成触达邮件:"
echo "   python3 scripts/batch_ai_outreach.py --tiers S,A+,A"
echo ""
echo "=========================================="
