#!/bin/bash
# =============================================================================
# GitHub人才库扩大 - 从AI项目获取用户（端到端无人值守）
# =============================================================================
#
# 执行流程：
#   Step 1: 从AI项目获取用户（stars + contributors）
#   Step 2: Phase 3 深度富化（获取repos和技术栈）
#   Step 3: Phase 4.5 LLM富化（AI分析和画像）
#   Step 4: 合并到主库
#
# 使用方法：
#   bash run_ai_repo_expansion.sh [--test] [--full]
#
# =============================================================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# 打印标题
print_header() {
    echo ""
    echo "======================================================================"
    echo " $1"
    echo " 时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "======================================================================"
    echo ""
}

# 检查依赖
check_dependencies() {
    log_info "检查依赖..."

    if ! command -v python3 &> /dev/null; then
        log_error "python3 未安装"
        exit 1
    fi

    if [ ! -f "scripts/github_hunter_config.py" ]; then
        log_error "配置文件不存在: scripts/github_hunter_config.py"
        exit 1
    fi

    log_success "依赖检查通过"
}

# 检查Token
check_token() {
    log_info "检查GitHub Token..."

    token=$(python3 -c "
import sys
sys.path.insert(0, 'scripts')
from github_hunter_config import GITHUB_CONFIG
print(GITHUB_CONFIG.get('token', ''))" 2>/dev/null)

    if [ -z "$token" ]; then
        log_error "GitHub Token未配置"
        exit 1
    fi

    token_count=$(echo "$token" | tr ',' '\n' | wc -l | xargs)
    rate_limit=$((token_count * 5000))

    log_success "Token配置正常: $token_count 个token, 预计 $rate_limit 次/小时"
}

# Step 1: 从AI项目获取用户
step1_get_repo_users() {
    print_header "Step 1: 从AI项目获取用户"

    local repos_limit=${1:-10}
    local stars_limit=${2:-300}
    local contributors_limit=${3:-100}

    log_info "配置: $repos_limit 个项目, 每项目 $stars_limit stars + $contributors_limit contributors"

    python3 scripts/expand_from_ai_repos.py \
        --repos-limit $repos_limit \
        --stars-per-repo $stars_limit \
        --contributors-per-repo $contributors_limit \
        --output github_mining/ai_repo_users.json

    if [ $? -eq 0 ]; then
        log_success "Step 1 完成"
        ls -lh github_mining/ai_repo_users.json

        # 显示统计
        python3 << EOF
import json
with open('github_mining/ai_repo_users.json') as f:
    data = json.load(f)
print(f"  获取用户: {len(data)} 人")
high_ai = sum(1 for u in data if u.get('ai_score', 0) >= 2.0)
print(f"  高AI相关: {high_ai} 人")
has_email = sum(1 for u in data if u.get('email'))
print(f"  有邮箱: {has_email} 人")
EOF
    else
        log_error "Step 1 失败"
        exit 1
    fi
}

# Step 2: Phase 3 深度富化
step2_phase3_enrich() {
    print_header "Step 2: Phase 3 深度富化（Repos + 技术栈）"

    python3 scripts/github_network_miner.py \
        --phase3 \
        --input github_mining/ai_repo_users.json \
        --max-users 5000

    if [ $? -eq 0 ]; then
        log_success "Step 2 完成"

        # 重命名输出
        mv github_mining/phase3_enriched.json github_mining/phase3_from_ai_repos.json 2>/dev/null || true

        ls -lh github_mining/phase3_from_ai_repos.json
    else
        log_error "Step 2 失败"
        exit 1
    fi
}

# Step 3: Phase 4.5 LLM富化
step3_phase4_5_enrich() {
    print_header "Step 3: Phase 4.5 LLM富化（AI分析 + 画像）"

    cd personal-ai-headhunter

    python3 ../github_mining/scripts/run_phase4_5_llm_enrichment.py \
        --input ../github_mining/phase3_from_ai_repos.json \
        --output ../github_mining/phase4_5_from_ai_repos.json \
        --batch-size 50

    if [ $? -eq 0 ]; then
        log_success "Step 3 完成"
        ls -lh ../github_mining/phase4_5_from_ai_repos.json
        cd ..
    else
        log_error "Step 3 失败"
        cd ..
        exit 1
    fi
}

# Step 4: 合并到主库
step4_merge_to_main() {
    print_header "Step 4: 合并到主库"

    python3 << EOF
import json
from pathlib import Path

# 加载新数据
new_file = Path('github_mining/phase4_5_from_ai_repos.json')
if not new_file.exists():
    print("⚠️ 新数据文件不存在，跳过合并")
    exit(0)

with open(new_file) as f:
    new_users = json.load(f)

print(f"新用户: {len(new_users)} 人")

# 加载主库
main_file = Path('github_mining/phase4_5_llm_enriched.json')
if not main_file.exists():
    print("⚠️ 主库文件不存在，创建新库")
    main_users = []
else:
    with open(main_file) as f:
        main_users = json.load(f)
    print(f"主库现有: {len(main_users)} 人")

# 去重
existing_usernames = {u.get('username') for u in main_users}
new_unique = [u for u in new_users if u.get('username') not in existing_usernames]

print(f"去重后新增: {len(new_unique)} 人")

# 合并
merged = main_users + new_unique

# 保存
output_file = Path('github_mining/phase4_5_llm_enriched_merged.json')
with open(output_file, 'w') as f:
    json.dump(merged, f, ensure_ascii=False, indent=2)

print(f"✅ 合并完成: {output_file}")
print(f"   总用户: {len(merged)} 人")
print(f"   新增: {len(new_unique)} 人")

# 备份原文件
if main_file.exists():
    import shutil
    backup_file = main_file.with_suffix('.json.bak')
    shutil.copy(main_file, backup_file)
    print(f"✅ 原文件已备份: {backup_file}")
EOF

    log_success "Step 4 完成"
}

# 生成最终报告
generate_report() {
    print_header "最终报告"

    python3 << EOF
import json
from collections import Counter
from pathlib import Path

print("📊 执行结果汇总\n")
print("="*70)

# 检查各阶段文件
files = {
    "AI项目用户": "github_mining/ai_repo_users.json",
    "Phase 3富化": "github_mining/phase3_from_ai_repos.json",
    "Phase 4.5富化": "github_mining/phase4_5_from_ai_repos.json",
    "合并主库": "github_mining/phase4_5_llm_enriched_merged.json",
}

for name, file_path in files.items():
    path = Path(file_path)
    if path.exists():
        with open(path) as f:
            data = json.load(f)
        size_mb = path.stat().st_size / 1024 / 1024
        print(f"✅ {name}: {len(data):,} 人 ({size_mb:.1f} MB)")
    else:
        print(f"❌ {name}: 文件不存在")

# 分析最终数据
final_file = Path("github_mining/phase4_5_llm_enriched_merged.json")
if final_file.exists():
    with open(final_file) as f:
        final_data = json.load(f)

    print(f"\n{'='*70}")
    print(f"📊 最终数据质量:\n")

    # Tier分布
    tiers = []
    for d in final_data:
        score = d.get('final_score_v2', d.get('final_score', 0))
        if score >= 100:
            tiers.append('S')
        elif score >= 80:
            tiers.append('A+')
        elif score >= 60:
            tiers.append('A')
        elif score >= 40:
            tiers.append('B')
        else:
            tiers.append('C')

    tier_dist = Counter(tiers)
    print(f"Tier分布:")
    for tier in ['S', 'A+', 'A', 'B', 'C']:
        count = tier_dist.get(tier, 0)
        pct = count * 100 // len(final_data) if final_data else 0
        print(f"  {tier}级: {count:4d} 人 ({pct}%)")

    # 数据质量
    has_email = sum(1 for d in final_data if d.get('email'))
    has_linkedin = sum(1 for d in final_data if d.get('linkedin_url'))
    has_scholar = sum(1 for d in final_data if d.get('scholar_url'))

    print(f"\n数据质量:")
    print(f"  有邮箱: {has_email:,} 人 ({has_email*100//len(final_data)}%)")
    print(f"  有LinkedIn: {has_linkedin:,} 人 ({has_linkedin*100//len(final_data)}%)")
    print(f"  有Google Scholar: {has_scholar:,} 人 ({has_scholar*100//len(final_data)}%)")

print(f"\n{'='*70}")
print(f"✅ 全部完成！")
print(f"{'='*70}\n")
EOF
}

# =============================================================================
# 主流程
# =============================================================================

main() {
    print_header "GitHub人才库扩大 - AI项目扩展"

    # 解析参数
    MODE="full"
    REPOS_LIMIT=10
    STARS_LIMIT=300
    CONTRIBUTORS_LIMIT=100

    while [[ $# -gt 0 ]]; do
        case $1 in
            --test)
                MODE="test"
                REPOS_LIMIT=3
                STARS_LIMIT=100
                CONTRIBUTORS_LIMIT=30
                shift
                ;;
            --full)
                MODE="full"
                shift
                ;;
            --repos)
                REPOS_LIMIT=$2
                shift 2
                ;;
            *)
                log_error "未知参数: $1"
                echo "使用方法: $0 [--test] [--full] [--repos N]"
                exit 1
                ;;
        esac
    done

    log_info "执行模式: $MODE"
    log_info "配置: $REPOS_LIMIT 个项目"

    # 检查
    check_dependencies
    check_token

    # 执行
    step1_get_repo_users $REPOS_LIMIT $STARS_LIMIT $CONTRIBUTORS_LIMIT
    step2_phase3_enrich
    step3_phase4_5_enrich
    step4_merge_to_main

    # 报告
    generate_report

    log_success "🎉 全部完成！"
}

# 运行
main "$@"
