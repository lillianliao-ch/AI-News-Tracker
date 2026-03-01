#!/usr/bin/env python3
"""
测试国籍检测功能

用法:
    cd /Users/lillianliao/notion_rag/github_mining/scripts
    python3 test_nationality_detection.py
"""

import sys
import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
BASE_DIR = SCRIPT_DIR / "github_mining"
HEADHUNTER_DIR = SCRIPT_DIR.parent.parent / "personal-ai-headhunter"
FINAL_OUTPUT = BASE_DIR / "phase4_final_enriched.json"

print("=" * 60)
print("测试国籍检测功能")
print("=" * 60)

# 检查文件是否存在
if not FINAL_OUTPUT.exists():
    print(f"⚠️  文件不存在: {FINAL_OUTPUT}")
    print("尝试查找其他数据文件...")

    # 查找其他可能的文件
    possible_files = [
        BASE_DIR / "phase3_5_enriched.json",
        BASE_DIR / "phase3_from_phase4.json",
        BASE_DIR / "phase4_expanded.json",
    ]

    data_file = None
    for f in possible_files:
        if f.exists():
            data_file = f
            print(f"✅ 找到文件: {f}")
            break

    if not data_file:
        print("❌ 未找到任何数据文件")
        print("\n创建测试数据...")
        # 创建测试数据
        test_users = [
            {
                "username": "test1",
                "name": "Jindong Wang",
                "company": "@microsoft",
                "location": "Beijing, China",
                "bio": "Senior Researcher at Microsoft Research Asia"
            },
            {
                "username": "test2",
                "name": "Andy Wang",
                "company": "@bytedance",
                "location": "Beijing",
                "bio": "AI Engineer at ByteDance"
            },
            {
                "username": "test3",
                "name": "John Smith",
                "company": "@google",
                "location": "San Francisco, CA",
                "bio": "Software Engineer at Google"
            },
            {
                "username": "test4",
                "name": "张三",
                "company": "@huawei",
                "location": "深圳",
                "bio": "AI研究员"
            },
            {
                "username": "test5",
                "name": "Yintong Huo",
                "company": "",
                "location": "",
                "bio": "PhD student in ML"
            },
        ]
        users = test_users
        print(f"✅ 创建了 {len(users)} 个测试用户")
    else:
        print(f"\n读取文件: {data_file}")
        with open(data_file) as f:
            all_users = json.load(f)
        # 只取前50个用户进行测试
        users = all_users[:50]
        print(f"✅ 读取了前 {len(users)} 个用户")
else:
    print(f"读取文件: {FINAL_OUTPUT}")
    with open(FINAL_OUTPUT) as f:
        all_users = json.load(f)
    # 只取前50个用户进行测试
    users = all_users[:50]
    print(f"✅ 读取了前 {len(users)} 个用户")

print("\n" + "=" * 60)
print("开始国籍检测")
print("=" * 60)

# 导入国籍检测函数
sys.path.insert(0, str(HEADHUNTER_DIR / "scripts"))
try:
    from add_nationality_tags import detect_nationality, CHINESE_SURNAMES, CHINESE_COMPANIES
    print(f"✅ 成功导入检测函数")
    print(f"   姓氏列表: {len(CHINESE_SURNAMES)} 个")
    print(f"   中国公司: {len(CHINESE_COMPANIES)} 个")
except Exception as e:
    print(f"❌ 导入失败: {e}")
    sys.exit(1)

# 统计
stats = {"chinese": 0, "foreign": 0, "unknown": 0, "total": 0}
results = []

# 为每个候选人添加国籍
for i, user in enumerate(users, 1):
    name = user.get("name", "")
    company = user.get("company", "")
    if company and company.startswith("@"):
        company = company[1:]

    location = user.get("location", "")
    bio = user.get("bio", "")

    # 基础检测
    nationality, confidence = detect_nationality(name, company)

    # Phase 4 增强检测
    if nationality == "unknown":
        # 利用 location
        if location and "China" in location:
            nationality = "chinese"
            confidence = "medium"
        # 利用 bio 中的中文
        elif bio and any("\u4e00" <= c <= "\u9fff" for c in bio):
            nationality = "chinese"
            confidence = "high"

    # 添加字段
    user["nationality"] = nationality
    user["nationality_confidence"] = confidence

    stats[nationality] += 1
    stats["total"] += 1

    results.append({
        "name": name,
        "company": company,
        "nationality": nationality,
        "confidence": confidence
    })

# 输出统计
print("\n" + "=" * 60)
print("国籍分布统计")
print("=" * 60)
print(f"中国人:     {stats['chinese']:5,} ({stats['chinese']/stats['total']*100:.1f}%)")
print(f"外国人:     {stats['foreign']:5,} ({stats['foreign']/stats['total']*100:.1f}%)")
print(f"无法判断:   {stats['unknown']:5,} ({stats['unknown']/stats['total']*100:.1f}%)")
print(f"总计:       {stats['total']:5,}")

# 显示示例
print("\n" + "=" * 60)
print("检测结果示例（前10个）")
print("=" * 60)
for r in results[:10]:
    company_display = (r['company'] or "")[:25]
    print(f"  {r['name']:30} | {company_display:25} | {r['nationality']:8} ({r['confidence']})")

print("\n" + "=" * 60)
print("✅ 测试完成！")
print("=" * 60)

# 保存测试结果到临时文件
test_output = SCRIPT_DIR / "test_nationality_output.json"
with open(test_output, "w") as f:
    json.dump(users, f, ensure_ascii=False, indent=2)
print(f"\n📄 测试结果已保存到: {test_output}")
