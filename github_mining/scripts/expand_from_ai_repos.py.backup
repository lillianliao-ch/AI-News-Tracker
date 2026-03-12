#!/usr/bin/env python3
"""
从顶级AI项目的 Stars 和 Contributors 获取新用户

目标：
1. 获取顶级AI项目的star用户
2. 获取项目的contributors
3. 筛选AI相关的活跃用户
4. 生成高质量种子列表
"""
import os
import sys
import json
import time
import random
from pathlib import Path
from datetime import datetime
from collections import Counter

# 添加scripts目录到路径
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

try:
    from github_network_miner import GitHubNetworkMiner, API_BASE
except ImportError:
    print("❌ 无法导入 GitHubNetworkMiner")
    sys.exit(1)


# 目标AI项目列表
TARGET_REPOS = [
    # 大模型框架
    ("huggingface", "transformers", "LLM框架"),
    ("pytorch", "pytorch", "深度学习框架"),
    ("tensorflow", "tensorflow", "深度学习框架"),

    # AI应用框架
    ("langchain-ai", "langchain", "AI应用框架"),
    ("microsoft", "semantic-kernel", "AI应用框架"),
    ("openai", "gym", "强化学习"),
    ("openai", "tiktoken", "Tokenizer"),

    # AI工具（中国团队）
    ("langgenius", "dify", "AI应用开发平台"),
    ("pymetrics", "guardrails", "AI安全"),
    ("deepset-ai", "haystack", "NLP框架"),

    # AI编程
    ("sourcegraph", "cody", "AI编程助手"),
    ("continuedev", "continue", "VSCode AI助手"),

    # 多模态
    ("opencv", "opencv", "计算机视觉"),
    ("laion-ai", "open-assistant", "开源AI助手"),

    # 数据工程+AI
    ("apache", "superset", "BI+AI"),
    ("mindsdb", "mindsdb", "AI数据库"),
    ("jina-ai", "jina", "AI搜索"),

    # 向量数据库
    ("chroma-core", "chroma", "向量数据库"),
    ("weaviate", "weaviate", "向量数据库"),
    ("qdrant", "qdrant", "向量数据库"),

    # Agent框架
    ("e2b-dev", "awesome-ai-agents", "Agent列表"),
    ("TransformerOptimus", "SuperAGI", "Agent框架"),
]


def print_header(title):
    print(f"\n{'='*70}")
    print(f"🚀 {title}")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")


def get_repo_stars(miner, owner, repo, limit=500, min_stars=10):
    """
    获取仓库的star用户

    策略：获取最近star的用户（更活跃）
    """
    print(f"  📡 获取 {owner}/{repo} 的star用户...")

    users = []
    page = 1
    per_page = 100

    while len(users) < limit:
        stars = miner._request_list(
            f"{API_BASE}/repos/{owner}/{repo}/stargazers",
            {"per_page": per_page, "page": page}
        )

        if not stars:
            break

        for star_user in stars:
            if len(users) >= limit:
                break

            # 基础过滤
            user_info = {
                "username": star_user.get("login", ""),
                "github_url": star_user.get("html_url", ""),
                "source": f"star:{owner}/{repo}",
            }

            # 只保留有活动的用户
            if star_user.get("public_repos", 0) >= min_stars:
                users.append(user_info)

        print(f"    已获取 {len(users)}/{limit} 个用户")
        page += 1
        time.sleep(0.3)

    print(f"  ✅ 获取 {len(users)} 个star用户")
    return users


def get_repo_contributors(miner, owner, repo, limit=300):
    """
    获取仓库的贡献者

    策略：优先获取活跃贡献者
    """
    print(f"  📡 获取 {owner}/{repo} 的contributors...")

    users = []
    contributors = miner._request_list(
        f"{API_BASE}/repos/{owner}/{repo}/contributors",
        {"per_page": 100, "anon": False}  # 不包括匿名用户
    )

    if not contributors:
        print(f"  ⚠️  无contributors")
        return users

    # 按贡献排序
    contributors = sorted(contributors, key=lambda x: x.get("contributions", 0), reverse=True)

    for i, contrib in enumerate(contributors[:limit]):
        user_info = {
            "username": contrib.get("login", ""),
            "github_url": contrib.get("html_url", ""),
            "contributions": contrib.get("contributions", 0),
            "source": f"contributor:{owner}/{repo}",
            "rank": i + 1,
        }
        users.append(user_info)

    print(f"  ✅ 获取 {len(users)} 个contributors")
    return users


def enrich_users(miner, users):
    """
    批量获取用户详细信息

    策略：
    1. 获取基础profile
    2. 计算AI相关性
    3. 过滤低质量用户
    """
    print(f"\n📊 开始批量获取用户信息...")
    print(f"  总用户: {len(users)}")

    enriched = []
    for i, user in enumerate(users):
        if i % 50 == 0:
            print(f"  进度: {i}/{len(users)}")

        username = user.get("username", "")
        profile = miner._request(f"{API_BASE}/users/{username}")

        if not profile:
            continue

        # 基础信息
        user_data = {
            "username": profile.get("login", ""),
            "name": profile.get("name", ""),
            "github_url": profile.get("html_url", ""),
            "email": profile.get("email", ""),
            "bio": profile.get("bio", ""),
            "company": profile.get("company", ""),
            "location": profile.get("location", ""),
            "blog": profile.get("blog", ""),
            "public_repos": profile.get("public_repos", 0),
            "followers": profile.get("followers", 0),
            "following": profile.get("following", 0),
            "created_at": profile.get("created_at", ""),
            "updated_at": profile.get("updated_at", ""),
            "source": user.get("source", ""),
        }

        # 添加contributor特定信息
        if "contributions" in user:
            user_data["contributions"] = user["contributions"]
            user_data["contributor_rank"] = user.get("rank", 0)

        # 计算AI相关性
        ai_score, signals = miner._calculate_ai_score(user_data)
        user_data["ai_score"] = ai_score
        user_data["ai_signals"] = signals

        # 过滤机构账户
        org_keywords = ['org', 'organization', 'team', 'bot', 'ci', 'build', 'release']
        username_lower = user_data.get("username", "").lower()
        name_lower = user_data.get("name", "").lower()
        is_org = any(kw in username_lower or kw in name_lower for kw in org_keywords)

        # 过滤低质量用户
        min_quality = (
            ai_score >= 0.3 and
            not is_org and
            user_data.get("public_repos", 0) >= 2
        )

        if min_quality:
            enriched.append(user_data)

        time.sleep(0.2)

    print(f"  ✅ 完成: {len(enriched)}/{len(users)} 通过质量过滤")
    return enriched


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="从顶级AI项目获取新用户",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--repos-limit",
        type=int,
        default=10,
        help="处理的项目数量（默认：10）"
    )
    parser.add_argument(
        "--stars-per-repo",
        type=int,
        default=300,
        help="每个项目获取star用户数（默认：300）"
    )
    parser.add_argument(
        "--contributors-per-repo",
        type=int,
        default=100,
        help="每个项目获取contributor数（默认：100）"
    )
    parser.add_argument(
        "--output",
        default="github_mining/ai_repo_users.json",
        help="输出文件"
    )

    args = parser.parse_args()

    print_header("从顶级AI项目获取新用户")

    # 初始化miner
    try:
        import importlib.util
        config_path = script_dir / "github_hunter_config.py"
        spec = importlib.util.spec_from_file_location("github_hunter_config", config_path)
        config_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config_module)
        token = config_module.GITHUB_CONFIG.get("token")
    except Exception as e:
        print(f"❌ 无法读取token: {e}")
        sys.exit(1)

    miner = GitHubNetworkMiner(token=token)

    # 限制项目数量
    repos_to_process = TARGET_REPOS[:args.repos_limit]

    print(f"📋 配置:")
    print(f"  项目数量: {len(repos_to_process)}")
    print(f"  每项目stars: {args.stars_per_repo}")
    print(f"  每项目contributors: {args.contributors_per_repo}")
    print(f"  预计API调用: ~{len(repos_to_process) * (args.stars_per_repo + args.contributors_per_repo)} 次")
    print(f"\n📦 项目列表:")
    for owner, repo, desc in repos_to_process:
        print(f"  - {owner}/{repo}: {desc}")

    # 收集用户
    all_users = []
    repo_stats = []

    for i, (owner, repo, desc) in enumerate(repos_to_process):
        print(f"\n【{i+1}/{len(repos_to_process)}】{owner}/{repo} - {desc}")
        print("-" * 70)

        repo_users = []

        # 获取stars
        stars = get_repo_stars(miner, owner, repo, limit=args.stars_per_repo)
        repo_users.extend(stars)

        # 获取contributors
        contributors = get_repo_contributors(miner, owner, repo, limit=args.contributors_per_repo)
        repo_users.extend(contributors)

        # 去重（基于username）
        unique_usernames = {u["username"] for u in repo_users}
        print(f"  📊 本仓库: {len(repo_users)} 用户（去重后 {len(unique_usernames)}）")

        repo_stats.append({
            "repo": f"{owner}/{repo}",
            "stars": len(stars),
            "contributors": len(contributors),
            "unique": len(unique_usernames)
        })

        all_users.extend(repo_users)
        time.sleep(1)

    # 去重
    print(f"\n{'='*70}")
    print(f"📊 总体统计:")
    print(f"  总用户（去重前）: {len(all_users)}")

    unique_users = {}
    for user in all_users:
        username = user["username"]
        if username not in unique_users:
            unique_users[username] = user
        else:
            # 合并source信息
            existing = unique_users[username]
            existing["source"] += f", {user['source']}"

    unique_list = list(unique_users.values())
    print(f"  总用户（去重后）: {len(unique_list)}")

    # 批量获取详细信息
    print(f"\n{'='*70}")
    enriched = enrich_users(miner, unique_list)

    # 排序
    enriched.sort(key=lambda x: x.get("ai_score", 0), reverse=True)

    # 保存结果
    output_path = Path(args.output)
    with open(output_path, 'w') as f:
        json.dump(enriched, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 结果已保存: {output_path}")

    # 统计
    print(f"\n{'='*70}")
    print(f"📊 最终统计:")
    print(f"  高质量用户: {len(enriched)}")

    high_ai = sum(1 for u in enriched if u.get("ai_score", 0) >= 2.0)
    print(f"  高AI相关(≥2.0): {high_ai}")

    has_email = sum(1 for u in enriched if u.get("email"))
    print(f"  有邮箱: {has_email} ({has_email*100//len(enriched) if enriched else 0}%)")

    # 来源分布
    source_counter = Counter()
    for u in enriched:
        source = u.get("source", "").split(":")[0]
        source_counter[source] += 1

    print(f"\n📊 来源分布:")
    for source, count in source_counter.most_common():
        print(f"  {source}: {count} 人")

    # 仓库统计
    print(f"\n📊 仓库统计:")
    for stat in repo_stats:
        print(f"  {stat['repo']}: {stat['stars']} stars + {stat['contributors']} contributors = {stat['unique']} unique")

    print(f"\n🎯 下一步:")
    print(f"  1. 查看结果: cat {output_path}")
    print(f"  2. Phase 3富化: python3 github_network_miner.py --phase3 --input {output_path}")
    print(f"  3. Phase 4.5富化: python3 run_phase4_5_llm_enrichment.py --input phase3_from_ai_repos.json")
    print(f"  4. 合并到主库: python3 merge_to_main.py --new phase4_5_from_repos.json")


if __name__ == "__main__":
    main()
