#!/usr/bin/env python3
"""
Phase 5: 多轮社交网络扩展

使用S-B级高质量用户作为种子，发现更多AI人才
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
script_dir = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(script_dir))

try:
    from github_network_miner import GitHubNetworkMiner, API_BASE, BASE_DIR
except ImportError:
    print("❌ 无法导入 GitHubNetworkMiner")
    sys.exit(1)


def print_header(title):
    print(f"\n{'='*70}")
    print(f"🚀 {title}")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")


def load_seeds(seeds_file):
    """加载种子用户"""
    with open(seeds_file) as f:
        seed_usernames = json.load(f)

    print(f"📊 种子用户: {len(seed_usernames)} 人")
    return seed_usernames


def check_existing(seeds_file):
    """检查是否已有Phase 5输出"""
    output_file = Path(seeds_file).parent / "phase5_expanded.json"
    if output_file.exists():
        print(f"⚠️  Phase 5输出已存在: {output_file}")
        with open(output_file) as f:
            existing = json.load(f)
        print(f"   已发现: {len(existing)} 人")

        choice = input("是否覆盖？(y/N): ").strip().lower()
        if choice != 'y':
            return None

    return output_file


def expand_network(seeds_file, min_cooccurrence=3, max_seeds=None):
    """执行社交网络扩展"""

    print_header("Phase 5: 社交网络扩展（第2轮）")

    # 加载种子
    seed_usernames = load_seeds(seeds_file)

    # 限制种子数量
    if max_seeds and len(seed_usernames) > max_seeds:
        print(f"⚠️  限制种子数量: {len(seed_usernames)} → {max_seeds}")
        seed_usernames = seed_usernames[:max_seeds]

    print(f"\n📋 扩展参数:")
    print(f"  种子用户: {len(seed_usernames)} 人")
    print(f"  最小共现: {min_cooccurrence} 次")
    print(f"  API预估: ~{len(seed_usernames) * 77} 次")

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
        return None

    miner = GitHubNetworkMiner(token=token)

    # 构造种子数据
    seeds = [{"username": u} for u in seed_usernames]

    # 加载已存在的用户（用于去重）
    existing_usernames = set(seed_usernames)

    print(f"\n🔍 开始扩展...")
    print(f"{'='*70}\n")

    # 统计新用户的共现频率
    cooccurrence = Counter()
    new_user_info = {}

    for i, seed in enumerate(seeds):
        username = seed["username"]
        if i % 20 == 0:
            print(f"  进度: {i}/{len(seeds)} | 已发现: {len(cooccurrence)} | 高共现: {len([v for v in cooccurrence.values() if v >= min_cooccurrence])}")

        # 获取following
        following_count = seed.get("following", 0)
        if following_count > 2000:
            print(f"  ⏭️  跳过 {username} (following {following_count} 太多)")
            continue

        page = 1
        while True:
            following = miner._request_list(
                f"{API_BASE}/users/{username}/following",
                {"per_page": 100, "page": page}
            )
            if not following:
                break

            for f_user in following:
                f_username = f_user.get("login", "")
                if f_username and f_username not in existing_usernames:
                    cooccurrence[f_username] += 1
                    if f_username not in new_user_info:
                        new_user_info[f_username] = {
                            "username": f_username,
                            "github_url": f_user.get("html_url", ""),
                        }

            if len(following) < 100:
                break
            page += 1
            if page > 5:  # 最多取500个
                break

            time.sleep(0.3)

        time.sleep(0.5 + random.uniform(0, 0.3))

        # 定期保存进度
        if (i + 1) % 50 == 0:
            progress = {
                "processed_seeds": i + 1,
                "total_new_users": len(cooccurrence),
                "high_cooccurrence": len([v for v in cooccurrence.values() if v >= min_cooccurrence]),
                "timestamp": datetime.now().isoformat()
            }
            progress_file = BASE_DIR / "phase5_progress.json"
            miner._save_json(progress, progress_file)
            print(f"  💾 进度已保存: {progress_file}")

    # 过滤高共现用户
    high_co = {u: c for u, c in cooccurrence.items() if c >= min_cooccurrence}

    print(f"\n📊 共现统计:")
    print(f"  总新用户: {len(cooccurrence)}")
    print(f"  共现 ≥ {min_cooccurrence}: {len(high_co)}")

    # 获取高共现用户的详细信息
    print(f"\n📡 获取 {len(high_co)} 个高共现用户的详细信息...")

    expanded = []
    for i, (username, co_count) in enumerate(sorted(high_co.items(), key=lambda x: x[1], reverse=True)):
        if i % 50 == 0 and i > 0:
            print(f"  进度: {i}/{len(high_co)}")

        profile = miner._request(f"{API_BASE}/users/{username}")
        if profile:
            user = {
                "username": profile.get("login", ""),
                "name": profile.get("name", ""),
                "github_url": profile.get("html_url", ""),
                "email": profile.get("email", ""),
                "bio": profile.get("bio", ""),
                "company": profile.get("company", ""),
                "location": profile.get("location", ""),
                "blog": profile.get("blog", ""),
                "twitter_username": profile.get("twitter_username", ""),
                "public_repos": profile.get("public_repos", 0),
                "followers": profile.get("followers", 0),
                "following": profile.get("following", 0),
                "created_at": profile.get("created_at", ""),
                "updated_at": profile.get("updated_at", ""),
                "cooccurrence": co_count,
            }

            # 计算AI相关性
            ai_score, signals = miner._calculate_ai_score(user)
            user["ai_score"] = ai_score
            user["ai_signals"] = signals

            # 排除机构账户
            org_keywords = ['org', 'organization', 'team', 'bot', 'ci', 'build', 'release']
            username_lower = user.get("username", "").lower()
            name_lower = user.get("name", "").lower()
            is_org = any(kw in username_lower or kw in name_lower for kw in org_keywords)

            if not is_org and ai_score >= 0.3:  # AI相关性阈值
                expanded.append(user)

        time.sleep(0.3 + random.uniform(0, 0.2))
        if (i + 1) % 100 == 0:
            output_file = BASE_DIR / "phase5_expanded.json"
            miner._save_json(expanded, output_file)
            print(f"  💾 已保存: {output_file}")

    # 排序
    expanded.sort(key=lambda x: (x["cooccurrence"], x["ai_score"]), reverse=True)

    # 保存最终结果
    output_file = BASE_DIR / "phase5_expanded.json"
    miner._save_json(expanded, output_file)

    print(f"\n✅ Phase 5 扩展完成！")
    print(f"   输出文件: {output_file}")
    print(f"   发现用户: {len(expanded)} 人")

    # 统计
    ai_scores = [u.get("ai_score", 0) for u in expanded]
    high_ai = sum(1 for s in ai_scores if s >= 2.0)
    print(f"\n📊 质量统计:")
    print(f"   高AI相关(≥2.0): {high_ai} 人")
    print(f"   平均AI分: {sum(ai_scores)/len(ai_scores):.2f}")

    # 共现分布
    co_dist = Counter(u.get("cooccurrence", 0) for u in expanded)
    print(f"\n🔗 共现分布:")
    for co in sorted(co_dist.keys(), reverse=True)[:5]:
        count = co_dist[co]
        print(f"   共现{co}次: {count} 人")

    return expanded


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Phase 5: 多轮社交网络扩展",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--seeds-file",
        default="github_mining/phase5_seed_usernames_sb.json",
        help="种子用户文件"
    )
    parser.add_argument(
        "--min-cooccurrence",
        type=int,
        default=3,
        help="最小共现次数（默认：3）"
    )
    parser.add_argument(
        "--max-seeds",
        type=int,
        default=None,
        help="最大种子数量"
    )

    args = parser.parse_args()

    if not Path(args.seeds_file).exists():
        print(f"❌ 种子文件不存在: {args.seeds_file}")
        sys.exit(1)

    # 执行扩展
    expanded = expand_network(
        seeds_file=args.seeds_file,
        min_cooccurrence=args.min_cooccurrence,
        max_seeds=args.max_seeds
    )

    if expanded:
        print_header("✅ Phase 5 完成")
        print(f"\n📋 下一步:")
        print(f"  1. 查看结果: cat github_mining/phase5_expanded.json")
        print(f"  2. Phase 3富化: cd scripts && python3 github_network_miner.py --phase3 --input github_mining/phase5_expanded.json")
        print(f"  3. Phase 4.5富化: python3 run_phase4_5_llm_enrichment.py --input github_mining/phase3_from_phase5.json")
        print(f"  4. 合并到主库: python3 merge_phase5_to_main.py")


if __name__ == "__main__":
    main()
