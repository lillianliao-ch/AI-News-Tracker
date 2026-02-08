#!/usr/bin/env python3
"""
GitHub 社交网络挖掘 AI 人才工具
从目标用户的 Following 网络中发现、过滤、评分 AI 人才

用法:
    python github_network_miner.py phase1 --target Neal12332
    python github_network_miner.py verify1
    python github_network_miner.py phase2
    python github_network_miner.py verify2
    python github_network_miner.py phase3
    python github_network_miner.py verify3
    python github_network_miner.py phase4 --seed-top 300 --min-cooccurrence 3
    python github_network_miner.py verify4
"""

import requests
import json
import csv
import time
import random
import sys
import os
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple
from collections import Counter

# 强制刷新输出（nohup 模式下需要）
import functools
print = functools.partial(print, flush=True)

# ===== 配置 =====
BASE_DIR = Path(__file__).parent / "github_mining"
BASE_DIR.mkdir(exist_ok=True)
(BASE_DIR / "verification").mkdir(exist_ok=True)
(BASE_DIR / "screenshots").mkdir(exist_ok=True)

API_BASE = "https://api.github.com"

# AI 关键词集（用于 bio / repo description 匹配）
AI_KEYWORDS_STRONG = [
    # English - Core AI/ML
    "llm", "large language model", "nlp", "natural language processing",
    "computer vision", "deep learning", "machine learning",
    "transformer", "diffusion", "generative ai", "aigc",
    "reinforcement learning", "rlhf", "dpo", "ppo",
    "multimodal", "multi-modal", "speech recognition", "asr", "tts",
    "text-to-speech", "text-to-image", "text-to-video",
    "neural network", "gpt", "bert", "llama", "chatgpt",
    "langchain", "rag", "retrieval augmented", "vector database",
    "agent", "ai agent", "autonomous agent",
    "pre-training", "pretraining", "fine-tuning", "finetuning",
    "inference engine", "model serving", "model deployment",
    "cuda", "tensorrt", "triton", "vllm", "deepspeed",
    "pytorch", "tensorflow", "jax",
    "attention mechanism", "embedding", "tokenizer",
    "stable diffusion", "midjourney", "dall-e",
    "object detection", "image segmentation", "image generation",
    "knowledge graph", "information extraction",
    "recommendation system", "search engine",
    "mlops", "ml engineer", "ai researcher", "research scientist",
    "data scientist", "applied scientist",
    # Chinese - Core AI/ML
    "大模型", "语言模型", "大语言模型", "预训练", "微调",
    "自然语言处理", "计算机视觉", "深度学习", "机器学习",
    "多模态", "强化学习", "对齐", "智能体",
    "文生图", "文生视频", "语音识别", "语音合成",
    "推理优化", "训练框架", "算子优化",
    "人工智能", "神经网络", "生成式",
    "向量数据库", "知识图谱", "信息抽取",
    "推荐系统", "搜索引擎",
    "算法工程师", "算法专家", "研究员",
]

AI_KEYWORDS_WEAK = [
    "python", "data", "research", "algorithm", "optimization",
    "distributed", "parallel", "high performance",
    "数据", "研究", "算法", "优化", "分布式", "高性能",
]

# AI 公司集
AI_COMPANIES = [
    # Chinese AI companies
    "bytedance", "字节跳动", "字节", "tiktok", "douyin", "抖音",
    "alibaba", "阿里巴巴", "阿里", "alicloud", "aliyun", "达摩院", "damo", "通义",
    "tencent", "腾讯", "wechat", "微信",
    "baidu", "百度", "文心",
    "huawei", "华为", "昇腾", "ascend",
    "meituan", "美团",
    "jd.com", "京东",
    "netease", "网易",
    "xiaomi", "小米",
    "kuaishou", "快手",
    "didi", "滴滴",
    "sensetime", "商汤", "shangtang",
    "megvii", "旷视", "face++",
    "cloudwalk", "云从",
    "yitu", "依图",
    "zhipu", "智谱", "glm", "chatglm",
    "moonshot", "月之暗面", "kimi",
    "baichuan", "百川",
    "minimax",
    "01.ai", "零一万物", "yi-",
    "stepfun", "阶跃星辰",
    "modelbest", "面壁",
    "deepseek", "深度求索",
    "zhijiang", "之江实验室", "zhejiang lab",
    "westlake", "西湖大学",
    "peng cheng", "鹏城实验室",
    "shanghai ai", "上海人工智能",
    # International AI companies
    "openai", "anthropic", "deepmind", "google brain", "google research",
    "meta ai", "fair", "facebook ai",
    "microsoft research", "msra", "微软亚洲研究院",
    "apple", "nvidia", "intel",
    "amazon", "aws",
    "stability ai", "midjourney", "cohere", "mistral",
    "hugging face", "huggingface",
]

# 顶尖学校集
AI_SCHOOLS = [
    # Chinese universities
    "tsinghua", "清华", "thu",
    "peking university", "pku", "北大", "北京大学",
    "zhejiang university", "zju", "浙大", "浙江大学",
    "nanjing university", "nju", "南大", "南京大学",
    "shanghai jiao tong", "sjtu", "上交", "上海交通",
    "ustc", "中科大", "中国科学技术大学", "中国科技大学",
    "fudan", "复旦",
    "harbin institute", "hit", "哈工大", "哈尔滨工业",
    "beihang", "buaa", "北航",
    "renmin", "人大", "人民大学",
    "wuhan university", "武大", "武汉大学",
    "huazhong", "hust", "华中科技",
    "xi'an jiaotong", "xjtu", "西安交通",
    "sun yat-sen", "sysu", "中山大学",
    "nankai", "南开",
    "tianjin university", "天大", "天津大学",
    "cas", "中科院", "中国科学院", "chinese academy of sciences",
    "ucas", "国科大",
    # International universities
    "stanford", "mit", "cmu", "carnegie mellon",
    "berkeley", "ucb",
    "harvard", "princeton", "yale", "columbia",
    "caltech",
    "oxford", "cambridge",
    "eth zurich", "eth",
    "ucsd", "ucla", "uiuc",
    "georgia tech", "gatech",
    "cornell", "nyu",
    "university of washington", "uw",
    "university of toronto", "uoft",
    "university of michigan", "umich",
    # Labs
    "lamda", "thunlp", "nlplab", "ailab", "aalab",
    "cvlab", "mllab", "deep learning lab",
]


class GitHubNetworkMiner:
    """GitHub 社交网络挖掘器"""

    def __init__(self, token: str = None):
        self.token = token
        self.session = requests.Session()
        if token:
            self.session.headers.update({
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json",
            })
        else:
            self.session.headers.update({
                "Accept": "application/vnd.github.v3+json",
            })
        self.request_count = 0

    def _request(self, url: str, params: dict = None) -> Optional[dict]:
        """发送 API 请求（带速率控制和重试）"""
        for retry in range(3):
            try:
                self.request_count += 1
                resp = self.session.get(url, params=params, timeout=15)

                # 检查速率限制
                remaining = int(resp.headers.get("X-RateLimit-Remaining", 999))
                if remaining < 10:
                    reset_time = int(resp.headers.get("X-RateLimit-Reset", 0))
                    wait = max(reset_time - time.time(), 0) + 5
                    print(f"⚠️ 速率限制即将触发，等待 {wait:.0f}s...")
                    time.sleep(wait)

                if resp.status_code == 200:
                    return resp.json()
                elif resp.status_code == 403:
                    reset_time = int(resp.headers.get("X-RateLimit-Reset", 0))
                    wait = max(reset_time - time.time(), 0) + 5
                    print(f"🚫 速率限制，等待 {wait:.0f}s 后重试...")
                    time.sleep(wait)
                elif resp.status_code == 404:
                    return None
                else:
                    print(f"❌ HTTP {resp.status_code}: {url}")
                    time.sleep(2 ** retry)

            except Exception as e:
                print(f"❌ 请求错误: {e}")
                time.sleep(2 ** retry)

        return None

    def _request_list(self, url: str, params: dict = None) -> list:
        """发送 API 请求，返回列表"""
        result = self._request(url, params)
        if isinstance(result, list):
            return result
        return []

    # ============================================================
    # Phase 1: 种子采集
    # ============================================================
    def phase1_collect_following(self, target: str) -> List[Dict]:
        """采集目标用户的全部 following 列表"""
        print(f"\n{'='*60}")
        print(f"📡 Phase 1: 采集 {target} 的 Following 列表")
        print(f"{'='*60}\n")

        all_users = []
        page = 1
        per_page = 100

        while True:
            url = f"{API_BASE}/users/{target}/following"
            params = {"page": page, "per_page": per_page}

            users = self._request_list(url, params)
            if not users:
                break

            for user in users:
                all_users.append({
                    "username": user.get("login", ""),
                    "github_url": user.get("html_url", ""),
                    "avatar_url": user.get("avatar_url", ""),
                    "type": user.get("type", ""),
                })

            print(f"  📄 Page {page}: 获取 {len(users)} 人 (累计: {len(all_users)})")

            if len(users) < per_page:
                break
            page += 1
            time.sleep(0.5)

        print(f"\n✅ 共采集 {len(all_users)} 个 Following 用户")

        # 保存原始列表
        self._save_json(all_users, BASE_DIR / "phase1_following_list.json")
        self._save_csv(all_users, BASE_DIR / "phase1_following_list.csv")

        # 逐个获取详细信息
        print(f"\n📊 开始获取详细用户资料...")
        detailed_users = []
        for i, user in enumerate(all_users):
            username = user["username"]
            if i % 50 == 0 and i > 0:
                print(f"  进度: {i}/{len(all_users)} ({i*100//len(all_users)}%)")

            profile = self._request(f"{API_BASE}/users/{username}")
            if profile:
                detailed_users.append({
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
                })
            else:
                detailed_users.append({
                    "username": username,
                    "name": "",
                    "github_url": user["github_url"],
                    "email": "",
                    "bio": "",
                    "company": "",
                    "location": "",
                    "blog": "",
                    "twitter_username": "",
                    "public_repos": 0,
                    "followers": 0,
                    "following": 0,
                    "created_at": "",
                    "updated_at": "",
                })

            # 自适应延迟
            time.sleep(0.3 + random.uniform(0, 0.2))

            # 定期保存（防止中断丢失）
            if (i + 1) % 200 == 0:
                self._save_json(detailed_users, BASE_DIR / "phase1_seed_users.json")
                print(f"  💾 中间保存: {len(detailed_users)} 人")

        # 最终保存
        self._save_json(detailed_users, BASE_DIR / "phase1_seed_users.json")
        self._save_csv(detailed_users, BASE_DIR / "phase1_seed_users.csv")
        print(f"\n✅ Phase 1 完成! 共 {len(detailed_users)} 人详细资料已保存")
        print(f"   API 请求总数: {self.request_count}")

        return detailed_users

    def phase1_collect_following_resume(self, target: str) -> List[Dict]:
        """断点续传: 从已有数据继续采集"""
        following_file = BASE_DIR / "phase1_following_list.json"
        seed_file = BASE_DIR / "phase1_seed_users.json"

        if not following_file.exists():
            print("❌ 未找到 following 列表，请先完整运行 phase1")
            return []

        all_users = self._load_json(following_file)
        existing = self._load_json(seed_file) if seed_file.exists() else []
        existing_usernames = {u["username"] for u in existing}

        remaining = [u for u in all_users if u["username"] not in existing_usernames]
        print(f"📡 断点续传: 已有 {len(existing)}, 剩余 {len(remaining)}")

        detailed_users = list(existing)  # 从已有数据开始
        for i, user in enumerate(remaining):
            username = user["username"]
            if i % 50 == 0:
                print(f"  进度: {len(detailed_users)}/{len(all_users)} ({len(detailed_users)*100//len(all_users)}%)")

            profile = self._request(f"{API_BASE}/users/{username}")
            if profile:
                detailed_users.append({
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
                })
            else:
                detailed_users.append({
                    "username": username,
                    "name": "",
                    "github_url": user["github_url"],
                    **{k: "" for k in ["email", "bio", "company", "location", "blog", "twitter_username", "created_at", "updated_at"]},
                    **{k: 0 for k in ["public_repos", "followers", "following"]},
                })

            time.sleep(0.3 + random.uniform(0, 0.2))
            if (len(detailed_users)) % 200 == 0:
                self._save_json(detailed_users, seed_file)
                print(f"  💾 中间保存: {len(detailed_users)} 人")

        self._save_json(detailed_users, seed_file)
        self._save_csv(detailed_users, BASE_DIR / "phase1_seed_users.csv")
        print(f"\n✅ 断点续传完成! 共 {len(detailed_users)} 人")
        return detailed_users

    def verify1(self):
        """Phase 1 验证"""
        print(f"\n{'='*60}")
        print(f"🔍 Phase 1 验证报告")
        print(f"{'='*60}\n")

        seed_file = BASE_DIR / "phase1_seed_users.json"
        if not seed_file.exists():
            print("❌ 未找到 phase1 数据，请先运行 phase1")
            return

        users = self._load_json(seed_file)
        total = len(users)

        # 1. 总数
        print(f"📊 总数: {total} (预期 ~6,100)")
        if abs(total - 6100) > 200:
            print(f"  ⚠️ 偏差较大，请检查")
        else:
            print(f"  ✅ 数量合理")

        # 2. 去重
        usernames = [u["username"] for u in users]
        unique = len(set(usernames))
        print(f"\n🔗 去重: {unique} 唯一用户 / {total} 总数")
        if unique < total:
            print(f"  ⚠️ 有 {total - unique} 个重复")
        else:
            print(f"  ✅ 无重复")

        # 3. 字段完整率
        print(f"\n📋 字段完整率:")
        fields = ["username", "name", "email", "bio", "company", "location", "blog"]
        for field in fields:
            non_empty = sum(1 for u in users if u.get(field))
            rate = non_empty * 100 // total if total else 0
            bar = "█" * (rate // 5) + "░" * (20 - rate // 5)
            print(f"  {field:20s}: {bar} {rate}% ({non_empty}/{total})")

        # 4. 公司分布 Top 10
        companies = [u["company"] for u in users if u.get("company")]
        company_counter = Counter(companies)
        print(f"\n🏢 公司分布 Top 15:")
        for company, count in company_counter.most_common(15):
            print(f"  {company:40s}: {count}")

        # 5. 地域分布 Top 10
        locations = [u["location"] for u in users if u.get("location")]
        location_counter = Counter(locations)
        print(f"\n📍 地域分布 Top 15:")
        for loc, count in location_counter.most_common(15):
            print(f"  {loc:40s}: {count}")

        # 6. 随机抽样 10 人
        print(f"\n🎲 随机抽样 10 人（请手动验证）:")
        import random as rnd
        samples = rnd.sample(users, min(10, total))
        for s in samples:
            print(f"  - {s['username']:25s} | {s.get('name',''):20s} | {s.get('company',''):30s} | {s.get('location','')}")
            print(f"    URL: https://github.com/{s['username']}")

        # 保存报告
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_users": total,
            "unique_users": unique,
            "field_rates": {f: sum(1 for u in users if u.get(f)) / total for f in fields},
            "top_companies": company_counter.most_common(20),
            "top_locations": location_counter.most_common(20),
            "samples": [s["username"] for s in samples],
        }
        self._save_json(report, BASE_DIR / "verification" / "verify1_report.json")
        print(f"\n📄 报告已保存到 github_mining/verification/verify1_report.json")

    # ============================================================
    # Phase 2: AI 相关性过滤
    # ============================================================
    def phase2_filter_ai(self) -> Tuple[List[Dict], List[Dict]]:
        """从种子用户中过滤 AI 相关人才"""
        print(f"\n{'='*60}")
        print(f"🧠 Phase 2: AI 相关性过滤")
        print(f"{'='*60}\n")

        seed_file = BASE_DIR / "phase1_seed_users.json"
        if not seed_file.exists():
            print("❌ 未找到 phase1 数据")
            return [], []

        users = self._load_json(seed_file)
        tier_a = []  # 强 AI 信号
        tier_b = []  # 中 AI 信号
        tier_c = []  # 弱 AI 信号
        rejected = []  # 非 AI

        for user in users:
            score, signals = self._calculate_ai_score(user)
            user["ai_score"] = score
            user["ai_signals"] = signals

            if score >= 3:
                tier_a.append(user)
            elif score >= 1.5:
                tier_b.append(user)
            elif score >= 0.5:
                tier_c.append(user)
            else:
                rejected.append(user)

        # 排序
        tier_a.sort(key=lambda x: x["ai_score"], reverse=True)
        tier_b.sort(key=lambda x: x["ai_score"], reverse=True)
        tier_c.sort(key=lambda x: x["ai_score"], reverse=True)

        # 合并 AI 候选人
        ai_candidates = tier_a + tier_b + tier_c
        for c in ai_candidates:
            if c in tier_a:
                c["tier"] = "A"
            elif c in tier_b:
                c["tier"] = "B"
            else:
                c["tier"] = "C"

        print(f"📊 过滤结果:")
        print(f"  🏆 Tier A (强 AI 信号): {len(tier_a)}")
        print(f"  🥈 Tier B (中 AI 信号): {len(tier_b)}")
        print(f"  🥉 Tier C (弱 AI 信号): {len(tier_c)}")
        print(f"  ❌ 非 AI 相关:         {len(rejected)}")
        print(f"  📈 AI 人才总计:        {len(ai_candidates)} / {len(users)}")

        # 保存
        self._save_json(ai_candidates, BASE_DIR / "phase2_ai_filtered.json")
        self._save_csv(ai_candidates, BASE_DIR / "phase2_ai_filtered.csv")
        self._save_json(rejected, BASE_DIR / "phase2_rejected.json")

        # 保存分层文件
        self._save_json(tier_a, BASE_DIR / "phase2_tier_a.json")
        self._save_json(tier_b, BASE_DIR / "phase2_tier_b.json")

        print(f"\n✅ Phase 2 完成!")
        return ai_candidates, rejected

    def _calculate_ai_score(self, user: Dict) -> Tuple[float, List[str]]:
        """计算用户的 AI 相关性得分"""
        score = 0.0
        signals = []

        # 合并所有文本用于匹配
        bio = (user.get("bio") or "").lower()
        company = (user.get("company") or "").lower()
        location = (user.get("location") or "").lower()
        name = (user.get("name") or "").lower()
        blog = (user.get("blog") or "").lower()

        all_text = f"{bio} {company} {location} {name} {blog}"

        # 1. Bio 强关键词匹配 (+1.0 each, 最高 +5)
        bio_hits = 0
        for kw in AI_KEYWORDS_STRONG:
            if kw.lower() in all_text:
                bio_hits += 1
                if bio_hits <= 3:
                    signals.append(f"keyword:{kw}")
        score += min(bio_hits * 1.0, 5.0)

        # 2. Bio 弱关键词匹配 (+0.3 each, 最高 +1.5)
        weak_hits = 0
        for kw in AI_KEYWORDS_WEAK:
            if kw.lower() in all_text:
                weak_hits += 1
                if weak_hits <= 2:
                    signals.append(f"weak:{kw}")
        score += min(weak_hits * 0.3, 1.5)

        # 3. AI 公司匹配 (+2.0)
        for comp in AI_COMPANIES:
            if comp.lower() in all_text:
                score += 2.0
                signals.append(f"company:{comp}")
                break

        # 4. 顶尖学校匹配 (+1.5)
        for school in AI_SCHOOLS:
            if school.lower() in all_text:
                score += 1.5
                signals.append(f"school:{school}")
                break

        # 5. 影响力加分
        followers = user.get("followers", 0)
        if followers >= 1000:
            score += 1.0
            signals.append(f"followers:{followers}")
        elif followers >= 100:
            score += 0.3

        return round(score, 2), signals

    def verify2(self):
        """Phase 2 验证"""
        print(f"\n{'='*60}")
        print(f"🔍 Phase 2 验证报告")
        print(f"{'='*60}\n")

        ai_file = BASE_DIR / "phase2_ai_filtered.json"
        rejected_file = BASE_DIR / "phase2_rejected.json"

        if not ai_file.exists():
            print("❌ 未找到 phase2 数据")
            return

        ai_candidates = self._load_json(ai_file)
        rejected = self._load_json(rejected_file) if rejected_file.exists() else []

        tier_a = [c for c in ai_candidates if c.get("tier") == "A"]
        tier_b = [c for c in ai_candidates if c.get("tier") == "B"]
        tier_c = [c for c in ai_candidates if c.get("tier") == "C"]

        print(f"📊 总览:")
        print(f"  Tier A: {len(tier_a)}")
        print(f"  Tier B: {len(tier_b)}")
        print(f"  Tier C: {len(tier_c)}")
        print(f"  Rejected: {len(rejected)}")

        # 公司分布
        print(f"\n🏢 AI 候选人公司分布 Top 20:")
        companies = [c["company"] for c in ai_candidates if c.get("company")]
        for comp, count in Counter(companies).most_common(20):
            print(f"  {comp:40s}: {count}")

        # AI 信号分布
        all_signals = []
        for c in ai_candidates:
            all_signals.extend(c.get("ai_signals", []))
        print(f"\n🏷️ AI 信号分布 Top 20:")
        for sig, count in Counter(all_signals).most_common(20):
            print(f"  {sig:40s}: {count}")

        # 地域分布
        print(f"\n📍 AI 候选人地域分布 Top 15:")
        locations = [c["location"] for c in ai_candidates if c.get("location")]
        for loc, count in Counter(locations).most_common(15):
            print(f"  {loc:40s}: {count}")

        # Tier A 抽样
        print(f"\n🎲 Tier A 随机抽样 20 人 (请手动验证是否确实做 AI):")
        import random as rnd
        samples_a = rnd.sample(tier_a, min(20, len(tier_a)))
        for i, s in enumerate(samples_a, 1):
            print(f"  {i:2d}. {s['username']:25s} | Score: {s['ai_score']:5.1f} | {s.get('bio','')[:60]}")
            print(f"      Signals: {', '.join(s.get('ai_signals', []))}")
            print(f"      URL: https://github.com/{s['username']}")

        # Rejected 抽样（召回率验证）
        if rejected:
            print(f"\n🎲 Rejected 随机抽样 20 人 (检查是否有漏判的 AI 人才):")
            samples_r = rnd.sample(rejected, min(20, len(rejected)))
            for i, s in enumerate(samples_r, 1):
                print(f"  {i:2d}. {s['username']:25s} | {s.get('company',''):20s} | {s.get('bio','')[:60]}")
                print(f"      URL: https://github.com/{s['username']}")

        # 保存报告
        report = {
            "timestamp": datetime.now().isoformat(),
            "tier_a_count": len(tier_a),
            "tier_b_count": len(tier_b),
            "tier_c_count": len(tier_c),
            "rejected_count": len(rejected),
            "top_companies": Counter(companies).most_common(20),
            "top_signals": Counter(all_signals).most_common(20),
            "tier_a_samples": [s["username"] for s in samples_a],
        }
        self._save_json(report, BASE_DIR / "verification" / "verify2_report.json")
        print(f"\n📄 报告已保存")

    # ============================================================
    # Phase 3: 深度信息提取 + 评分
    # ============================================================
    def phase3_enrich(self, max_users: int = None):
        """深度信息提取和评分"""
        print(f"\n{'='*60}")
        print(f"📊 Phase 3: 深度信息提取 + 评分")
        print(f"{'='*60}\n")

        ai_file = BASE_DIR / "phase2_ai_filtered.json"
        if not ai_file.exists():
            print("❌ 未找到 phase2 数据")
            return

        candidates = self._load_json(ai_file)
        if max_users:
            candidates = candidates[:max_users]

        print(f"📡 准备对 {len(candidates)} 人进行深度信息提取...")

        enriched = []
        for i, user in enumerate(candidates):
            username = user["username"]
            if i % 50 == 0 and i > 0:
                print(f"  进度: {i}/{len(candidates)} ({i*100//len(candidates)}%)")

            # 获取用户的 Top 仓库
            repos = self._request_list(
                f"{API_BASE}/users/{username}/repos",
                {"sort": "stars", "direction": "desc", "per_page": 10}
            )

            # 统计语言
            languages = Counter()
            top_repos = []
            total_stars = 0
            original_repos = 0
            ai_repo_count = 0

            for repo in repos:
                lang = repo.get("language")
                if lang:
                    languages[lang] += 1
                stars = repo.get("stargazers_count", 0)
                total_stars += stars
                if not repo.get("fork", False):
                    original_repos += 1
                    top_repos.append(f"{repo['name']} ({stars}★)")

                # 检查仓库是否 AI 相关
                repo_text = f"{repo.get('name', '')} {repo.get('description', '')}".lower()
                for kw in AI_KEYWORDS_STRONG[:20]:
                    if kw.lower() in repo_text:
                        ai_repo_count += 1
                        break

            # 尝试从 commit 提取邮箱
            emails = set()
            if user.get("email"):
                emails.add(user["email"])

            # 从最近的 event 中提取邮箱
            events = self._request_list(
                f"{API_BASE}/users/{username}/events/public",
                {"per_page": 30}
            )
            for event in events:
                if event.get("type") == "PushEvent":
                    commits = event.get("payload", {}).get("commits", [])
                    for commit in commits:
                        author = commit.get("author", {})
                        email = author.get("email", "")
                        if email and "noreply" not in email and "@" in email:
                            emails.add(email)

            # 综合评分
            final_score = self._calculate_final_score(user, total_stars, ai_repo_count, list(emails))

            enriched_user = {
                **user,
                "primary_languages": ", ".join(l for l, _ in languages.most_common(5)),
                "total_stars": total_stars,
                "original_repos": original_repos,
                "top_repos": "; ".join(top_repos[:5]),
                "ai_repo_count": ai_repo_count,
                "all_emails": ", ".join(emails) if emails else "",
                "final_score": final_score,
            }
            enriched.append(enriched_user)

            time.sleep(0.5 + random.uniform(0, 0.3))

            # 定期保存
            if (i + 1) % 100 == 0:
                self._save_json(enriched, BASE_DIR / "phase3_enriched.json")

        # 排序
        enriched.sort(key=lambda x: x["final_score"], reverse=True)

        # 保存
        self._save_json(enriched, BASE_DIR / "phase3_enriched.json")
        self._save_csv(enriched, BASE_DIR / "phase3_enriched.csv")

        print(f"\n✅ Phase 3 完成!")
        print(f"   总人数: {len(enriched)}")
        print(f"   有邮箱: {sum(1 for e in enriched if e.get('all_emails'))}")
        print(f"   Top 10 候选人:")
        for i, c in enumerate(enriched[:10], 1):
            print(f"     {i}. {c['username']:20s} | Score: {c['final_score']:.1f} | {c.get('company',''):20s} | Emails: {c.get('all_emails','N/A')[:40]}")

        return enriched

    def _calculate_final_score(self, user: Dict, total_stars: int, ai_repo_count: int, emails: list) -> float:
        """计算综合评分 (0-100)"""
        score = 0.0

        # AI 相关度 (30%)
        ai_score = min(user.get("ai_score", 0) * 6, 30)
        score += ai_score

        # 技术影响力 (25%)
        followers = user.get("followers", 0)
        influence = min(followers / 40, 15) + min(total_stars / 100, 10)
        score += influence

        # 活跃度 (20%)
        repos = user.get("public_repos", 0)
        activity = min(repos / 5, 10) + min(ai_repo_count * 3, 10)
        score += activity

        # 可联系性 (15%)
        contact = 0
        if emails:
            contact += 10
        if user.get("blog"):
            contact += 3
        if user.get("twitter_username"):
            contact += 2
        score += min(contact, 15)

        # 地域匹配 (10%) - 优先中国
        location = (user.get("location") or "").lower()
        company = (user.get("company") or "").lower()
        china_kw = ["china", "beijing", "shanghai", "shenzhen", "hangzhou",
                     "chengdu", "guangzhou", "nanjing", "中国", "北京", "上海",
                     "深圳", "杭州", "成都", "广州", "南京"]
        for kw in china_kw:
            if kw in location or kw in company:
                score += 10
                break

        return round(score, 1)

    def verify3(self):
        """Phase 3 验证"""
        print(f"\n{'='*60}")
        print(f"🔍 Phase 3 验证报告")
        print(f"{'='*60}\n")

        enriched_file = BASE_DIR / "phase3_enriched.json"
        if not enriched_file.exists():
            print("❌ 未找到 phase3 数据")
            return

        candidates = self._load_json(enriched_file)
        total = len(candidates)

        # 邮箱统计
        has_email = sum(1 for c in candidates if c.get("all_emails"))
        has_profile_email = sum(1 for c in candidates if c.get("email"))
        has_blog = sum(1 for c in candidates if c.get("blog"))
        has_twitter = sum(1 for c in candidates if c.get("twitter_username"))

        print(f"📊 联系信息恢复率:")
        print(f"  Email (总计):     {has_email}/{total} ({has_email*100//total}%)")
        print(f"  Email (Profile):  {has_profile_email}/{total} ({has_profile_email*100//total}%)")
        print(f"  Blog/Website:     {has_blog}/{total} ({has_blog*100//total}%)")
        print(f"  Twitter:          {has_twitter}/{total} ({has_twitter*100//total}%)")

        # 邮箱质量
        print(f"\n📧 邮箱质量抽检:")
        email_users = [c for c in candidates if c.get("all_emails")]
        import random as rnd
        samples = rnd.sample(email_users, min(20, len(email_users)))
        valid = 0
        for s in samples:
            emails = s["all_emails"]
            is_valid = "noreply" not in emails and "@users" not in emails
            status = "✅" if is_valid else "❌"
            valid += 1 if is_valid else 0
            print(f"  {status} {s['username']:20s}: {emails[:60]}")
        print(f"  有效率: {valid}/{len(samples)}")

        # Top 20 候选人展示
        print(f"\n🏆 Top 20 候选人 (请人工审核质量):")
        for i, c in enumerate(candidates[:20], 1):
            print(f"  {i:2d}. {c['username']:20s} | Score: {c['final_score']:5.1f} | {c.get('tier','?')} | {c.get('company',''):20s}")
            print(f"      Bio: {(c.get('bio') or '')[:70]}")
            print(f"      Emails: {c.get('all_emails', 'N/A')[:50]}")
            print(f"      URL: https://github.com/{c['username']}")

        # 分数分布
        score_ranges = [(80, 100), (60, 80), (40, 60), (20, 40), (0, 20)]
        print(f"\n📈 评分分布:")
        for low, high in score_ranges:
            count = sum(1 for c in candidates if low <= c.get("final_score", 0) < high)
            bar = "█" * (count // max(total // 40, 1))
            print(f"  {low:3d}-{high:3d}: {bar} {count}")

        report = {
            "timestamp": datetime.now().isoformat(),
            "total": total,
            "email_rate": has_email / total if total else 0,
            "blog_rate": has_blog / total if total else 0,
        }
        self._save_json(report, BASE_DIR / "verification" / "verify3_report.json")

    # ============================================================
    # Phase 4: 社交网络扩展
    # ============================================================
    def phase4_expand(self, seed_top: int = 300, min_cooccurrence: int = 3):
        """从种子用户的 following 中发现新人才"""
        print(f"\n{'='*60}")
        print(f"🌐 Phase 4: 社交网络扩展")
        print(f"{'='*60}\n")

        enriched_file = BASE_DIR / "phase3_enriched.json"
        if not enriched_file.exists():
            print("❌ 未找到 phase3 数据")
            return

        candidates = self._load_json(enriched_file)
        seeds = candidates[:seed_top]
        existing_usernames = {c["username"] for c in candidates}

        print(f"📡 从 Top {len(seeds)} 种子用户的 following 中发现新人才...")
        print(f"   (要求共现 ≥ {min_cooccurrence} 次)")

        # 统计新用户的共现频率
        cooccurrence = Counter()
        new_user_info = {}

        for i, seed in enumerate(seeds):
            username = seed["username"]
            if i % 20 == 0:
                print(f"  进度: {i}/{len(seeds)} | 已发现新用户: {len(cooccurrence)}")

            # 获取此种子的 following（只取前500个，太多的跳过以节省 API）
            following_count = seed.get("following", 0)
            if following_count > 2000:
                print(f"  ⏭️ 跳过 {username} (following {following_count} 太多)")
                continue

            page = 1
            while True:
                following = self._request_list(
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
                }
                self._save_json(progress, BASE_DIR / "phase4_progress.json")

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

            profile = self._request(f"{API_BASE}/users/{username}")
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

                # 计算 AI 相关性
                ai_score, signals = self._calculate_ai_score(user)
                user["ai_score"] = ai_score
                user["ai_signals"] = signals

                if ai_score >= 0.5:  # 只保留有 AI 信号的
                    expanded.append(user)

            time.sleep(0.3 + random.uniform(0, 0.2))
            if (i + 1) % 100 == 0:
                self._save_json(expanded, BASE_DIR / "phase4_expanded.json")

        expanded.sort(key=lambda x: (x["cooccurrence"], x["ai_score"]), reverse=True)

        self._save_json(expanded, BASE_DIR / "phase4_expanded.json")
        self._save_csv(expanded, BASE_DIR / "phase4_expanded.csv")

        # 共现 Top 50
        print(f"\n🏆 共现 Top 30 新发现人才:")
        for i, c in enumerate(expanded[:30], 1):
            print(f"  {i:2d}. {c['username']:20s} | Co: {c['cooccurrence']} | AI: {c['ai_score']:.1f} | {c.get('company',''):20s} | {(c.get('bio') or '')[:40]}")

        print(f"\n✅ Phase 4 完成! 新发现 AI 人才: {len(expanded)}")
        return expanded

    def verify4(self):
        """Phase 4 验证"""
        print(f"\n{'='*60}")
        print(f"🔍 Phase 4 验证报告")
        print(f"{'='*60}\n")

        expanded_file = BASE_DIR / "phase4_expanded.json"
        if not expanded_file.exists():
            print("❌ 未找到 phase4 数据")
            return

        expanded = self._load_json(expanded_file)
        total = len(expanded)

        # 共现分布
        print(f"📊 共现频率分布:")
        co_ranges = [(10, 999), (5, 10), (3, 5)]
        for low, high in co_ranges:
            count = sum(1 for c in expanded if low <= c.get("cooccurrence", 0) < high)
            print(f"  共现 {low}-{high}: {count}")

        # 公司分布
        print(f"\n🏢 新发现人才公司 Top 15:")
        companies = [c["company"] for c in expanded if c.get("company")]
        for comp, count in Counter(companies).most_common(15):
            print(f"  {comp:40s}: {count}")

        # 抽样验证
        print(f"\n🎲 随机抽样 30 人 (验证 AI 相关性):")
        import random as rnd
        samples = rnd.sample(expanded, min(30, total))
        for i, s in enumerate(samples, 1):
            print(f"  {i:2d}. {s['username']:20s} | Co: {s.get('cooccurrence',0)} | {s.get('company',''):20s} | {(s.get('bio') or '')[:50]}")
            print(f"      URL: https://github.com/{s['username']}")

    # ============================================================
    # 工具方法
    # ============================================================
    def _save_json(self, data, path: Path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _load_json(self, path: Path) -> list:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_csv(self, data: List[Dict], path: Path):
        if not data:
            return
        # 排除复杂类型字段
        simple_keys = []
        for k in data[0].keys():
            if k not in ["ai_signals"]:
                simple_keys.append(k)

        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=simple_keys, extrasaction="ignore")
            writer.writeheader()
            for row in data:
                # 处理列表类型
                clean_row = {}
                for k in simple_keys:
                    val = row.get(k, "")
                    if isinstance(val, list):
                        val = ", ".join(str(v) for v in val)
                    clean_row[k] = val
                writer.writerow(clean_row)


# ============================================================
# CLI 入口
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="GitHub 社交网络挖掘 AI 人才")
    parser.add_argument("command", choices=[
        "phase1", "phase1_resume", "verify1",
        "phase2", "verify2",
        "phase3", "verify3",
        "phase4", "verify4",
    ], help="执行的阶段")
    parser.add_argument("--target", default="Neal12332", help="目标用户名")
    parser.add_argument("--token", default=None, help="GitHub Token")
    parser.add_argument("--seed-top", type=int, default=300, help="Phase 4 种子数量")
    parser.add_argument("--min-cooccurrence", type=int, default=3, help="Phase 4 最小共现次数")
    parser.add_argument("--max-users", type=int, default=None, help="Phase 3 最大处理人数")

    args = parser.parse_args()

    # 尝试从环境变量读取 token
    token = args.token or os.environ.get("GITHUB_TOKEN")
    if not token:
        # 尝试从配置文件读取
        try:
            from github_hunter_config import GITHUB_CONFIG
            token = GITHUB_CONFIG.get("token")
        except ImportError:
            pass

    if not token and args.command not in ["verify1", "verify2", "verify3", "verify4"]:
        print("⚠️ 未提供 GitHub Token，API 速率限制为 60次/小时")
        print("   建议: python github_network_miner.py phase1 --token ghp_xxxxx")
        print("   或设置环境变量: export GITHUB_TOKEN=ghp_xxxxx\n")

    miner = GitHubNetworkMiner(token=token)

    if args.command == "phase1":
        miner.phase1_collect_following(args.target)
    elif args.command == "phase1_resume":
        miner.phase1_collect_following_resume(args.target)
    elif args.command == "verify1":
        miner.verify1()
    elif args.command == "phase2":
        miner.phase2_filter_ai()
    elif args.command == "verify2":
        miner.verify2()
    elif args.command == "phase3":
        miner.phase3_enrich(max_users=args.max_users)
    elif args.command == "verify3":
        miner.verify3()
    elif args.command == "phase4":
        miner.phase4_expand(seed_top=args.seed_top, min_cooccurrence=args.min_cooccurrence)
    elif args.command == "verify4":
        miner.verify4()


if __name__ == "__main__":
    main()
