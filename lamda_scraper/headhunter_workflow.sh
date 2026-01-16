#!/bin/bash
# LAMDA 猎头工作流 - 一键采集与分析
# 作者: Claude AI
# 日期: 2026-01-07

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查 Python 环境
check_python() {
    log_info "检查 Python 环境..."

    if ! command -v python3 &> /dev/null; then
        log_error "未找到 Python3，请先安装"
        exit 1
    fi

    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    log_success "Python 版本: $PYTHON_VERSION"
}

# 检查依赖
check_dependencies() {
    log_info "检查 Python 依赖..."

    REQUIRED_PACKAGES=("requests" "bs4")
    MISSING_PACKAGES=()

    for package in "${REQUIRED_PACKAGES[@]}"; do
        if ! python3 -c "import ${package}" 2>/dev/null; then
            MISSING_PACKAGES+=($package)
        fi
    done

    if [ ${#MISSING_PACKAGES[@]} -ne 0 ]; then
        log_warning "缺少依赖: ${MISSING_PACKAGES[*]}"
        log_info "安装命令: pip3 install requests beautifulsoup4"
        read -p "是否立即安装? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            pip3 install requests beautifulsoup4
        else
            log_error "缺少必需依赖，退出"
            exit 1
        fi
    fi

    log_success "所有依赖已满足"
}

# 显示菜单
show_menu() {
    echo ""
    echo "========================================"
    echo "   LAMDA 猎头工作流 - 主菜单"
    echo "========================================"
    echo ""
    echo "1. 快速测试 (10人，5分钟)"
    echo "2. 标准采集 (100人，30分钟)"
    echo "3. 完整采集 (全量 462+ 人，2-3小时)"
    echo "4. 分析现有数据"
    echo "5. 深度采集优先联系人"
    echo "6. 查看统计报告"
    echo "0. 退出"
    echo ""
    read -p "请选择 [0-6]: " choice
    echo ""
}

# 快速测试
quick_test() {
    log_info "开始快速测试 (10人)..."

    OUTPUT_NAME="lamda_quick_test"
    LIMIT=10
    DELAY=1.0

    log_info "运行爬虫..."
    python3 lamda_scraper.py --limit $LIMIT --output $OUTPUT_NAME --delay $DELAY

    if [ -f "$OUTPUT_NAME.json" ]; then
        log_success "数据采集完成"

        log_info "开始评分分析..."
        python3 talent_analyzer.py --input $OUTPUT_NAME.json --output ${OUTPUT_NAME}_scored.csv

        log_success "分析完成！"
        echo ""
        echo "输出文件:"
        echo "  - $OUTPUT_NAME.csv (原始数据)"
        echo "  - $OUTPUT_NAME.json (结构化数据)"
        echo "  - ${OUTPUT_NAME}_scored.csv (评分结果)"
        echo ""
        log_info "可以用 Excel 打开查看"
    else
        log_error "采集失败，请检查网络连接"
    fi
}

# 标准采集
standard_collection() {
    log_info "开始标准采集 (100人)..."

    OUTPUT_NAME="lamda_standard"
    LIMIT=100
    DELAY=1.5

    log_info "预计耗时: 30-40 分钟"
    read -p "是否继续? (y/n) " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "运行爬虫..."
        python3 lamda_scraper.py --limit $LIMIT --output $OUTPUT_NAME --delay $DELAY

        if [ -f "$OUTPUT_NAME.json" ]; then
            log_success "数据采集完成"

            log_info "开始评分分析..."
            python3 talent_analyzer.py --input $OUTPUT_NAME.json --output ${OUTPUT_NAME}_scored.csv

            log_success "分析完成！"
            echo ""
            echo "输出文件:"
            echo "  - $OUTPUT_NAME.csv"
            echo "  - $OUTPUT_NAME.json"
            echo "  - ${OUTPUT_NAME}_scored.csv"
        else
            log_error "采集失败"
        fi
    else
        log_warning "已取消"
    fi
}

# 完整采集
full_collection() {
    log_info "开始完整采集 (全量 462+ 人)..."

    OUTPUT_NAME="lamda_full"
    DELAY=1.5

    log_warning "预计耗时: 2-3 小时"
    log_warning "建议在后台运行"
    read -p "是否继续? (y/n) " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "运行爬虫（无限制）..."
        python3 lamda_scraper.py --output $OUTPUT_NAME --delay $DELAY

        if [ -f "$OUTPUT_NAME.json" ]; then
            log_success "数据采集完成"

            log_info "开始评分分析..."
            python3 talent_analyzer.py --input $OUTPUT_NAME.json --output ${OUTPUT_NAME}_scored.csv

            log_success "分析完成！"
            echo ""
            echo "输出文件:"
            echo "  - $OUTPUT_NAME.csv"
            echo "  - $OUTPUT_NAME.json"
            echo "  - ${OUTPUT_NAME}_scored.csv"
        else
            log_error "采集失败"
        fi
    else
        log_warning "已取消"
    fi
}

# 分析现有数据
analyze_existing() {
    log_info "分析现有数据..."

    echo ""
    echo "可用的 JSON 文件:"
    ls -1 *.json 2>/dev/null || echo "  (无)"

    echo ""
    read -p "请输入文件名 (不含 .json): " filename

    if [ -f "${filename}.json" ]; then
        log_info "开始分析 ${filename}.json..."
        python3 talent_analyzer.py --input ${filename}.json --output ${filename}_scored.csv
        log_success "分析完成！"
    else
        log_error "文件不存在: ${filename}.json"
    fi
}

# 深度采集优先联系人
deep_enrichment() {
    log_info "深度采集优先联系人..."

    echo ""
    echo "可用的 JSON 文件:"
    ls -1 *.json 2>/dev/null || echo "  (无)"

    echo ""
    read -p "请输入文件名 (不含 .json): " filename

    if [ -f "${filename}.json" ]; then
        log_info "开始深度采集..."
        python3 tier_b_scraper.py --input ${filename}.json --output priority_contacts.csv
        log_success "深度采集完成！"
        echo ""
        echo "输出文件: priority_contacts.csv"
    else
        log_error "文件不存在: ${filename}.json"
    fi
}

# 查看统计报告
show_statistics() {
    log_info "生成统计报告..."

    echo ""
    echo "可用的 JSON 文件:"
    ls -1 *.json 2>/dev/null || echo "  (无)"

    echo ""
    read -p "请输入文件名 (不含 .json): " filename

    if [ -f "${filename}.json" ]; then
        python3 << EOF
import json
import csv

# 读取数据
with open('${filename}.json', 'r', encoding='utf-8') as f:
    candidates = json.load(f)

print(f"\n{'='*60}")
print(f"数据统计报告: ${filename}")
print(f"{'='*60}\n")

print(f"总人数: {len(candidates)}")

# 按类型统计
by_type = {}
for c in candidates:
    t = c.get('source_type', 'unknown')
    by_type[t] = by_type.get(t, 0) + 1

print(f"\n按类型分布:")
for t, count in sorted(by_type.items(), key=lambda x: x[1], reverse=True):
    print(f"  {t}: {count} 人")

# 按数据质量统计
by_quality = {}
for c in candidates:
    q = c.get('data_quality', 'unknown')
    by_quality[q] = by_quality.get(q, 0) + 1

print(f"\n按数据质量分布:")
for q, count in sorted(by_quality.items(), key=lambda x: x[1], reverse=True):
    print(f"  {q}: {count} 人")

# 有邮箱的
with_email = sum(1 for c in candidates if c.get('email'))
print(f"\n有邮箱: {with_email} 人 ({with_email/len(candidates)*100:.1f}%)")

# 有论文的
with_pubs = sum(1 for c in candidates if c.get('top_venues'))
print(f"有顶会论文: {with_pubs} 人 ({with_pubs/len(candidates)*100:.1f}%)")

# 有当前工作的
with_job = sum(1 for c in candidates if c.get('current_position'))
print(f"有职位信息: {with_job} 人 ({with_job/len(candidates)*100:.1f}%)")

# LinkedIn
with_linkedin = sum(1 for c in candidates if c.get('linkedin'))
print(f"有 LinkedIn: {with_linkedin} 人 ({with_linkedin/len(candidates)*100:.1f}%)")

# GitHub
with_github = sum(1 for c in candidates if c.get('github'))
print(f"有 GitHub: {with_github} 人 ({with_github/len(candidates)*100:.1f}%)")

# Scholar
with_scholar = sum(1 for c in candidates if c.get('google_scholar'))
print(f"有 Google Scholar: {with_scholar} 人 ({with_scholar/len(candidates)*100:.1f}%)")

# 如果有评分文件，显示评分统计
import os
score_file = '${filename}_scored.csv'
if os.path.exists(score_file):
    print(f"\n{'='*60}")
    print(f"评分统计 (从 {score_file})")
    print(f"{'='*60}\n")

    with open(score_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if rows:
        # Tier 统计
        tier_counts = {'A': 0, 'B': 0, 'C': 0}
        priority_counts = {'Hot': 0, 'Warm': 0, 'Pool': 0}

        for row in rows:
            tier = row.get('Tier', 'C')
            priority = row.get('优先级', 'Pool')
            tier_counts[tier] = tier_counts.get(tier, 0) + 1
            priority_counts[priority] = priority_counts.get(priority, 0) + 1

        print(f"Tier 分布:")
        print(f"  Tier A (顶级): {tier_counts['A']} 人")
        print(f"  Tier B (优质): {tier_counts['B']} 人")
        print(f"  Tier C (普通): {tier_counts['C']} 人")

        print(f"\n优先级分布:")
        print(f"  Hot (立即联系): {priority_counts['Hot']} 人")
        print(f"  Warm (建立联系): {priority_counts['Warm']} 人")
        print(f"  Pool (长期追踪): {priority_counts['Pool']} 人")

        # Hot + A/B 统计
        hot_ab = sum(1 for row in rows if row.get('Tier') in ['A', 'B'] and row.get('优先级') == 'Hot')
        print(f"\n🔥 优先联系人 (Tier A/B + Hot): {hot_ab} 人")

print(f"\n{'='*60}\n")

EOF
    else
        log_error "文件不存在: ${filename}.json"
    fi
}

# 主程序
main() {
    # 检查环境
    check_python
    check_dependencies

    # 主循环
    while true; do
        show_menu

        case $choice in
            1)
                quick_test
                ;;
            2)
                standard_collection
                ;;
            3)
                full_collection
                ;;
            4)
                analyze_existing
                ;;
            5)
                deep_enrichment
                ;;
            6)
                show_statistics
                ;;
            0)
                log_info "退出程序"
                exit 0
                ;;
            *)
                log_error "无效选择，请重新输入"
                ;;
        esac

        echo ""
        read -p "按 Enter 键继续..."
    done
}

# 运行主程序
main
