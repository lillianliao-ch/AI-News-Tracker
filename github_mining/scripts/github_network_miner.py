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
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple
from collections import Counter

# 导入缓存管理器
try:
    from github_cache_manager import GitHubCacheManager
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False
    print("⚠️  缓存管理器未找到，将不使用缓存功能")

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

# 组织账号黑名单（避免爬取组织账号）
KNOWN_ORG_BLACKLIST = [
    # 官方组织
    'tensorflow', 'keras', 'pytorch', 'kubernetes', 'cursor',
    'meta-pytorch', 'google-research-datasets', 'huggingface',
    'microsoft', 'google', 'facebook', 'amazonaws', 'alibaba',
    'apache', 'elastic', 'nv-tlabs', 'tensorflow', 'pytorch',
    'open-mmlab', 'rust-lang', 'golang', 'nodejs', 'vuejs',
    'react', 'angular', 'facebookincubator', 'uber', 'netflix',
    'airbnb', 'spotify', 'twitter', 'instagram', 'linkedin',
    'xai-org', 'openai', 'anthropic',
    # 添加更多已知的组织账号
    'kubernetes-sigs', 'kubernetes-sigs', 'googleprojectzero',
    'MicrosoftCopilot', 'Netflix', 'spotify', 'vuejs', 'rust-lang',
    'golang', 'Amazon-FAR', 'Alibaba-NLP', 'TencentAILabHealthcare'
]


def is_organization_account(user: Dict) -> bool:
    """
    检查是否为组织账号

    Args:
        user: GitHub 用户信息字典

    Returns:
        True 如果是组织账号，False 否则
    """
    username = user.get('login', '').lower()
    name = (user.get('name') or '').lower()
    bio = (user.get('bio') or '').lower()
    user_type = user.get('type', '')

    # 检查1: GitHub API 返回的 type 字段
    if user_type == 'Organization':
        return True

    # 检查2: 在已知黑名单中
    if username in KNOWN_ORG_BLACKLIST:
        return True

    # 检查3: 可疑组织特征
    # 特征A: name 等于 username
    if name and name == username:
        # 特征B: 无 bio 或 bio 很短
        if not bio or len(bio) < 20:
            # 特征C: 官方词汇
            official_keywords = ['official', 'repo', 'repository', 'project', 'team', 'org', 'organization']
            if any(kw in bio for kw in official_keywords):
                return True

    return False


class GitHubNetworkMiner:
    """GitHub 社交网络挖掘器 (支持多 Token 池轮询)"""

    def __init__(self, token: str = None, cache_days: int = 30, use_cache: bool = True):
        self.tokens = []
        self.current_token_idx = 0
        self.session = requests.Session()

        if token:
            # 支持传入单个 token 或多个 token (逗号分隔)，并严格清理空白符
            self.tokens = [t.strip().replace('\n', '').replace('\r', '') for t in token.split(",") if t.strip()]

        if self.tokens:
            new_token = self.tokens[self.current_token_idx]
            self.session.headers["Authorization"] = f"token {new_token}"
            self.session.headers["Accept"] = "application/vnd.github.v3+json"
            print(f"🔑 已加载 {len(self.tokens)} 个 GitHub Token 进入轮询池")
        else:
            self.session.headers.update({
                "Accept": "application/vnd.github.v3+json",
            })
            print("⚠️ 未加载任何 Token，将受到严格的未授权速率限制")

        self.request_count = 0

        # 初始化缓存管理器
        self.use_cache = use_cache and CACHE_AVAILABLE
        if self.use_cache:
            self.cache = GitHubCacheManager(cache_days=cache_days, verbose=True)
            print(f"💾 缓存管理器已启用 (缓存期: {cache_days} 天)")
        else:
            self.cache = None
            if CACHE_AVAILABLE and not use_cache:
                print("⚠️  缓存功能已手动禁用")
            elif not CACHE_AVAILABLE:
                print("⚠️  缓存管理器不可用")

    def _rotate_token(self):
        """切换到下一个 token"""
        if not self.tokens or len(self.tokens) <= 1:
            return False
            
        self.current_token_idx = (self.current_token_idx + 1) % len(self.tokens)
        new_token = self.tokens[self.current_token_idx]
        
        # 必须显式覆盖 Authorization 头，防止堆叠或格式错误
        self.session.headers["Authorization"] = f"token {new_token}"
        
        print(f"\n🔄 [Token 池轮询] 正在切换到备用 Token (索引: {self.current_token_idx + 1}/{len(self.tokens)})")
        return True

    def _request(self, url: str, params: dict = None) -> Optional[dict]:
        """发送 API 请求（带速率控制、重试和多 Token 轮询）"""
        # 修改重试逻辑：如果配置了多个token，允许更多的重试次数以耗尽整个池子
        max_retries = max(3, len(self.tokens) * 2 if self.tokens else 3)
        
        for retry in range(max_retries):
            try:
                self.request_count += 1
                resp = self.session.get(url, params=params, timeout=15)

                # 检查速率限制预警
                remaining = int(resp.headers.get("X-RateLimit-Remaining", 999))
                if remaining < 10:
                    if self._rotate_token():
                        # 成功切换 Token，直接在此次请求循环中重试，不需等待
                        continue
                        
                    # 如果不能切换（只有单 token），则严格等待
                    reset_time = int(resp.headers.get("X-RateLimit-Reset", 0))
                    wait = max(reset_time - time.time(), 0) + 5
                    print(f"⚠️ 速率限制即将触发，且无备用 Token。等待 {wait:.0f}s...")
                    time.sleep(wait)

                if resp.status_code == 200:
                    return resp.json()
                elif resp.status_code == 403:
                    # 获取限流原因
                    is_rate_limit = "rate limit" in resp.json().get('message', '').lower()
                    
                    if is_rate_limit:
                        if self._rotate_token():
                            # 被限流且成功切到备用 token，立刻重新发送当前请求
                            print("🚀 切换 Token 成功，立刻重试请求...")
                            continue
                        
                        reset_time = int(resp.headers.get("X-RateLimit-Reset", 0))
                        wait = max(reset_time - time.time(), 0) + 5
                        print(f"🚫 速率限制，且 Token 池均已耗尽。等待 {wait:.0f}s 后重试...")
                        time.sleep(wait)
                    else:
                        print(f"❌ HTTP 403 Forbidden (非限流): {url}")
                        return None
                        
                elif resp.status_code == 404:
                    return None
                else:
                    print(f"❌ HTTP {resp.status_code}: {url}")
                    time.sleep(2 ** retry)

            except Exception as e:
                print(f"❌ 请求错误 ({url}): {e}")
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
            print(f"  - {s['username']:25s} | {(s.get('name') or ''):20s} | {(s.get('company') or ''):30s} | {s.get('location') or ''}")
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
        org_accounts = []  # 组织账号（新增）

        for user in users:
            # 过滤组织账号（在最前面检查）
            if is_organization_account(user):
                user["skip_reason"] = "组织账号"
                org_accounts.append(user)
                continue

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
        print(f"  🏢 组织账号已过滤:     {len(org_accounts)}")
        print(f"  📈 AI 人才总计:        {len(ai_candidates)} / {len(users) - len(org_accounts)}")

        # 如果有组织账号被过滤，显示前几个
        if org_accounts:
            print(f"\n🚫 已过滤的组织账号（前10个）:")
            for org in org_accounts[:10]:
                username = org.get('login', 'Unknown')
                reason = org.get('skip_reason', '组织账号')
                print(f"  • {username} ({reason})")
            if len(org_accounts) > 10:
                print(f"  ... 还有 {len(org_accounts) - 10} 个")

        # 保存
        self._save_json(ai_candidates, BASE_DIR / "phase2_ai_filtered.json")
        self._save_csv(ai_candidates, BASE_DIR / "phase2_ai_filtered.csv")
        self._save_json(rejected, BASE_DIR / "phase2_rejected.json")
        self._save_json(org_accounts, BASE_DIR / "phase2_org_accounts_filtered.json")  # 保存被过滤的组织账号

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
            bio = (s.get('bio') or '')[:60]
            print(f"  {i:2d}. {s['username']:25s} | Score: {s['ai_score']:5.1f} | {bio}")
            print(f"      Signals: {', '.join(s.get('ai_signals', []))}")
            print(f"      URL: https://github.com/{s['username']}")

        # Rejected 抽样（召回率验证）
        if rejected:
            print(f"\n🎲 Rejected 随机抽样 20 人 (检查是否有漏判的 AI 人才):")
            samples_r = rnd.sample(rejected, min(20, len(rejected)))
            for i, s in enumerate(samples_r, 1):
                bio = (s.get('bio') or '')[:60]
                company = (s.get('company') or '')
                print(f"  {i:2d}. {s['username']:25s} | {company:20s} | {bio}")
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
    def phase3_enrich(self, max_users: int = None, resume: bool = False, input_file: str = None, output_file: str = None):
        """深度信息提取和评分

        Args:
            max_users: 最大处理人数
            resume: 是否断点续传
            input_file: 外部输入文件路径（支持Phase 4输出）
        """
        print(f"\n{'='*60}")
        print(f"📊 Phase 3: 深度信息提取 + 评分")
        print(f"{'='*60}\n")

        # 支持从外部文件输入（如Phase 4输出）
        if input_file:
            src_path = Path(input_file)
            if not src_path.exists():
                print(f"❌ 未找到输入文件: {input_file}")
                return
            candidates = self._load_json(src_path)
            print(f"📡 从外部文件加载: {len(candidates)} 人")
            print(f"   文件: {input_file}")
        else:
            ai_file = BASE_DIR / "phase2_ai_filtered.json"
            if not ai_file.exists():
                print("❌ 未找到 phase2 数据")
                return
            candidates = self._load_json(ai_file)

        if max_users:
            candidates = candidates[:max_users]

        # 确定输出文件名
        if output_file:
            # batch_runner.py 明确指定输出路径 → 最安全模式
            output_json = Path(output_file)
            output_json.parent.mkdir(parents=True, exist_ok=True)
            output_csv = output_json.with_suffix(".csv")
            print(f"📂 输出路径(batch模式): {output_json}")
        elif input_file:
            if "phase4_expanded" in input_file:
                output_json = BASE_DIR / "phase3_from_phase4.json"
                output_csv = BASE_DIR / "phase3_from_phase4.csv"
            else:
                output_json = BASE_DIR / "phase3_enriched.json"
                output_csv = BASE_DIR / "phase3_enriched.csv"
        else:
            output_json = BASE_DIR / "phase3_enriched.json"
            output_csv = BASE_DIR / "phase3_enriched.csv"

        # 断点续传：加载已处理的数据
        enriched = []
        already_done = set()
        if resume and output_json.exists():
            existing = self._load_json(output_json)
            enriched = existing
            already_done = {u['username'] for u in existing if u.get('total_stars') is not None}
            print(f"📂 断点续传: 已处理 {len(already_done)} 人")

        print(f"📡 准备对 {len(candidates)} 人进行深度信息提取...")

        for i, user in enumerate(candidates):
            username = user["username"]

            # 跳过已处理的
            if username in already_done:
                if i % 50 == 0 and i > 0:
                    print(f"  进度: {i}/{len(candidates)} ({i*100//len(candidates)}%) [跳过已处理]")
                continue

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

            # 定期保存（每50人保存一次，防止崩溃丢失数据）
            if (len(enriched) % 50) == 0:
                self._save_json(enriched, output_json)
                self._save_csv(enriched, output_csv)

        # 排序
        enriched.sort(key=lambda x: x["final_score"], reverse=True)

        # 最终保存（使用 safe 版本，备份一次旧文件）
        self._save_json_safe(enriched, output_json)
        self._save_csv(enriched, output_csv)

        print(f"\n✅ Phase 3 完成!")
        print(f"   总人数: {len(enriched)}")
        print(f"   有邮箱: {sum(1 for e in enriched if e.get('all_emails'))}")
        print(f"   Top 10 候选人:")
        for i, c in enumerate(enriched[:10], 1):
            username = str(c.get('username') or '')
            company = str(c.get('company') or '')
            emails = str(c.get('all_emails') or 'N/A')
            print(f"     {i}. {username:20s} | Score: {c['final_score']:.1f} | {company:20s} | Emails: {emails[:40]}")

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
            emails_str = s.get("all_emails") or ""
            is_valid = "noreply" not in emails_str and "@users" not in emails_str
            status = "✅" if is_valid else "❌"
            valid += 1 if is_valid else 0
            username = str(s.get('username') or '')
            emails = str(s.get('all_emails') or '')
            print(f"  {status} {username:20s}: {emails[:60]}")
        print(f"  有效率: {valid}/{len(samples)}")

        # Top 20 候选人展示
        print(f"\n🏆 Top 20 候选人 (请人工审核质量):")
        for i, c in enumerate(candidates[:20], 1):
            username = str(c.get('username') or '')
            print(f"  {i:2d}. {username:20s} | Score: {c['final_score']:5.1f} | {c.get('tier','?')} | {(c.get('company') or ''):20s}")
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
    # Phase 3.5: 个人主页深度数据提取
    # ============================================================
    def phase3_5_enrich(self, top: int = None, resume: bool = False, input_file: str = None, output_file: str = None):
        """爬取个人主页，提取结构化信息（职位、经历、论文、邮箱等）

        Args:
            top: 只处理Top N个
            resume: 是否断点续传
            input_file: 输入文件路径（支持Phase 3输出）
        """
        from bs4 import BeautifulSoup
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        print("\n" + "=" * 60)
        print("🌐 Phase 3.5/V3-Phase4: 个人主页深度数据提取")
        print("=" * 60)

        # 加载输入结果 - 支持从Phase 3输出或Phase 4输出
        if input_file:
            enriched_path = Path(input_file)
        else:
            enriched_path = BASE_DIR / "phase3_enriched.json"

        if not enriched_path.exists():
            print(f"❌ 找不到输入文件: {enriched_path}")
            return
        users = self._load_json(enriched_path)

        # 限制处理数量
        if top:
            users_to_process = users[:top]
            print(f"\n📡 准备处理 Top {top} 候选人的个人主页...")
        else:
            users_to_process = users
            print(f"\n📡 准备处理全部 {len(users)} 候选人的个人主页...")

        # 确定输出路径
        if output_file:
            # batch_runner.py 明确指定输出路径
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_csv = output_path.with_suffix(".csv")
            print(f"📂 输出路径(batch模式): {output_path}")
        elif input_file and ("phase4_expanded" in input_file or "phase3_from_phase4" in input_file):
            output_path = BASE_DIR / "phase4_final_enriched.json"
            output_csv = BASE_DIR / "phase4_final_enriched.csv"
        else:
            output_path = BASE_DIR / "phase3_5_enriched.json"
            output_csv = BASE_DIR / "phase3_5_enriched.csv"

        # 断点续传
        already_done = set()
        if resume and output_path.exists():
            existing = self._load_json(output_path)
            already_done = {u['username'] for u in existing if u.get('homepage_scraped')}
            print(f"📂 断点续传: 已处理 {len(already_done)} 人")

        # 统计
        has_blog = sum(1 for u in users_to_process if u.get('blog'))
        print(f"   有个人网站: {has_blog} 人")
        print(f"   无个人网站: {len(users_to_process) - has_blog} 人\n")

        scraped = 0
        failed = 0
        skipped = 0

        for idx, user in enumerate(users_to_process):
            username = user['username']

            # 跳过已处理的
            if username in already_done:
                skipped += 1
                continue

            blog = user.get('blog', '')
            if not blog:
                user['homepage_scraped'] = False
                continue

            # 规范化 URL
            if not blog.startswith(('http://', 'https://')):
                blog = 'https://' + blog

            # 跳过非个人网站的 URL
            skip_domains = ['github.com/', 'twitter.com/', 'x.com/', 'linkedin.com/',
                           'zhihu.com/', 'weibo.com/', 'bilibili.com/', 'medium.com/']
            if any(d in blog.lower() for d in skip_domains):
                # 但可以提取 LinkedIn URL
                if 'linkedin.com/' in blog.lower():
                    user['linkedin_url'] = blog
                user['homepage_scraped'] = False
                continue

            try:
                resp = requests.get(blog, timeout=10, verify=False,
                                   headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'})
                resp.encoding = resp.apparent_encoding or 'utf-8'

                if resp.status_code == 200:
                    extracted = self._extract_profile_from_page(resp.text, blog)
                    # 保存原始网页文本（用于导入时的 website_content）
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    text_content = soup.get_text(separator='\n', strip=True)
                    # 限制文本长度，避免数据过大
                    if len(text_content) > 10000:
                        text_content = text_content[:10000] + '...[truncated]'
                    user['homepage_text'] = text_content
                    # 合并提取的结构化数据
                    for key, val in extracted.items():
                        if val:  # 只合并非空值
                            user[key] = val
                    user['homepage_scraped'] = True
                    user['homepage_url'] = blog
                    scraped += 1
                else:
                    user['homepage_scraped'] = False
                    failed += 1
            except Exception as e:
                user['homepage_scraped'] = False
                failed += 1

            # 进度报告
            processed = idx + 1 - skipped
            if processed > 0 and processed % 10 == 0:
                total_target = has_blog - len(already_done)
                print(f"  进度: {processed}/{total_target} | 成功: {scraped} | 失败: {failed}")

            # 中间保存
            if processed > 0 and processed % 50 == 0:
                self._save_json(users_to_process if top else users, output_path)
                print(f"  💾 中间保存: {scraped} 人已提取")

            # 爬取间隔（避免被封）
            time.sleep(0.3)

        # Google Scholar 数据提取
        scholar_users = [u for u in users_to_process if u.get('scholar_url')]
        if scholar_users:
            print(f"\n🎓 提取 Google Scholar 数据 ({len(scholar_users)} 人)...")
            for u in scholar_users:
                scholar_data = self._fetch_scholar_data(u['scholar_url'])
                if scholar_data:
                    u.update(scholar_data)

        # 更新评分
        print("\n📊 更新评分...")
        for user in users_to_process if top else users:
            if user.get('homepage_scraped'):
                bonus = self._calculate_enrichment_bonus(user)
                user['enrichment_bonus'] = bonus
                user['final_score_v2'] = round(user.get('final_score', 0) + bonus, 1)
            else:
                user['final_score_v2'] = user.get('final_score', 0)

        # 按新评分排序
        result = users_to_process if top else users
        result.sort(key=lambda x: x.get('final_score_v2', 0), reverse=True)

        # 统计报告
        print(f"\n✅ Phase 3.5 完成!")
        print(f"   总处理: {scraped + failed} 人")
        print(f"   成功爬取: {scraped} 人")
        print(f"   失败: {failed} 人")

        # 提取统计
        has_title = sum(1 for u in result if u.get('current_title'))
        has_exp = sum(1 for u in result if u.get('work_experience'))
        has_edu = sum(1 for u in result if u.get('education'))
        has_pubs = sum(1 for u in result if u.get('top_venues_count', 0) > 0)
        has_extra_email = sum(1 for u in result if u.get('extra_emails'))
        has_linkedin = sum(1 for u in result if u.get('linkedin_url'))
        has_scholar = sum(1 for u in result if u.get('scholar_url'))
        has_twitter = sum(1 for u in result if u.get('twitter_url') or u.get('twitter_username'))

        print(f"\n📊 数据增强统计:")
        print(f"   当前职位: {has_title} 人")
        print(f"   工作经历: {has_exp} 人")
        print(f"   教育背景: {has_edu} 人")
        print(f"   顶会论文: {has_pubs} 人")
        print(f"   额外邮箱: {has_extra_email} 人")
        print(f"   LinkedIn: {has_linkedin} 人")
        print(f"   Scholar:  {has_scholar} 人")
        print(f"   Twitter:  {has_twitter} 人")

        # Top 10
        print(f"\n🌟 更新后 Top 10:")
        for i, c in enumerate(result[:10], 1):
            company = str(c.get('current_title') or c.get('company') or '')[:30]
            score_old = c.get('final_score', 0)
            score_new = c.get('final_score_v2', 0)
            bonus = c.get('enrichment_bonus', 0)
            username = str(c.get('username') or '')
            print(f"  {i:2d}. {username:20s} | {score_old:.1f}→{score_new:.1f} (+{bonus:.1f}) | {company}")

        # 最终保存
        self._save_json(result, output_path)
        self._save_csv(result, output_csv)
        print(f"\n💾 最终保存: {output_path} ({len(result)} 人)")

        return result

    def _extract_profile_from_page(self, html: str, url: str) -> Dict:
        """从网页 HTML 中提取结构化信息"""
        from bs4 import BeautifulSoup
        import re

        result = {}
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text(separator='\n', strip=True)

        # === 邮箱提取 ===
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        # 从 mailto 链接
        mailto_emails = [a['href'].replace('mailto:', '') for a in soup.find_all('a', href=True)
                        if 'mailto:' in a['href']]
        # 从 [at] 格式
        at_pattern = r'([a-zA-Z0-9._%+-]+)\s*\[at\]\s*([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
        at_emails = [f"{m.group(1)}@{m.group(2)}" for m in re.finditer(at_pattern, text)]
        # 从纯文本
        text_emails = re.findall(email_pattern, text)
        # 排除 noreply 和常见噪声
        all_emails = set(mailto_emails + at_emails + text_emails)
        all_emails = {e for e in all_emails if 'noreply' not in e and 'example.com' not in e
                     and '@scdn.' not in e and 'wixpress' not in e and '.png' not in e
                     and '@w3.org' not in e and 'schema.org' not in e}
        if all_emails:
            result['extra_emails'] = list(all_emails)

        # === 社交链接提取 ===
        all_links = [a.get('href', '') for a in soup.find_all('a', href=True)]

        # LinkedIn
        linkedin = [l for l in all_links if 'linkedin.com/in/' in l]
        if linkedin:
            result['linkedin_url'] = linkedin[0]

        # Twitter
        twitter = [l for l in all_links if 'twitter.com/' in l or 'x.com/' in l]
        if twitter:
            result['twitter_url'] = twitter[0]

        # Google Scholar
        scholar = [l for l in all_links if 'scholar.google' in l]
        if scholar:
            result['scholar_url'] = scholar[0]

        # 知乎
        zhihu = [l for l in all_links if 'zhihu.com/people/' in l]
        if zhihu:
            result['zhihu_url'] = zhihu[0]

        # === 当前职位提取 ===
        title_patterns = [
            r'(?:I am|I\'m|currently|现在)\s+(?:a |an )?((?:Staff |Senior |Principal |Lead |Chief )?(?:Research(?:er|ier)? (?:Scientist|Engineer)|Software Engineer|Professor|Assistant Professor|Associate Professor|Engineer|Scientist|Developer|CTO|CEO|VP|Director|Manager|Architect|Fellow))',
            r'((?:Staff |Senior |Principal |Lead |Chief )?(?:Research(?:er|ier)? (?:Scientist|Engineer)|Software Engineer|Professor|Assistant Professor|Associate Professor|Fellow))\s+(?:at|@)\s+(\S+(?:\s\S+){0,4})',
        ]
        for pat in title_patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                result['current_title'] = m.group(0)[:100]
                break

        # === 工作经历提取 ===
        exp_patterns = [
            # "2020-2023 Researcher at Company" 格式
            r'(\d{4})\s*[-–—~至]\s*((?:\d{4}|present|now|至今|Present|Now))\s*[,\s:]*([^.\n]{5,80})',
            # "[2020-2023] Company" 格式
            r'\[(\d{4})\s*[-–—]\s*((?:\d{4}|present|Present))\]\s*([^.\n]{5,80})',
        ]
        experiences = []
        for pat in exp_patterns:
            for m in re.finditer(pat, text):
                exp_text = m.group(0).strip()
                if len(exp_text) > 10:
                    experiences.append(exp_text)
        if experiences:
            result['work_experience'] = experiences[:5]  # 最多保留 5 条

        # === 教育背景提取 ===
        edu_keywords = ['Ph.D', 'PhD', 'B.S', 'B.Eng', 'M.S', 'M.Eng', 'Master', 'Bachelor',
                       'Doctor', '博士', '硕士', '学士', 'Postdoc']
        edu_items = []
        for line in text.split('\n'):
            if any(kw.lower() in line.lower() for kw in edu_keywords):
                line_clean = line.strip()
                if 10 < len(line_clean) < 200:
                    edu_items.append(line_clean)
        if edu_items:
            result['education'] = edu_items[:3]  # 最多保留 3 条

        # === 论文/顶会统计 ===
        top_venues = ['ICLR', 'NeurIPS', 'ICML', 'ACL', 'EMNLP', 'NAACL',
                      'CVPR', 'ICCV', 'ECCV', 'AAAI', 'IJCAI', 'KDD',
                      'SIGIR', 'COLING', 'WWW', 'ICASSP', 'INTERSPEECH']
        venue_counts = {}
        for venue in top_venues:
            count = len(re.findall(rf'\b{venue}\b', text))
            if count > 0:
                venue_counts[venue] = count
        if venue_counts:
            result['top_venues'] = venue_counts
            result['top_venues_count'] = sum(venue_counts.values())

        # === 研究方向提取 ===
        research_kw = ['natural language processing', 'computer vision', 'machine learning',
                      'deep learning', 'reinforcement learning', 'generative ai',
                      'large language model', 'foundation model', 'transfer learning',
                      'reasoning', 'multimodal', 'diffusion', 'transformer',
                      'autonomous', 'robotics', 'speech', 'recommendation',
                      'NLP', 'CV', 'ML', 'DL', 'RL', 'LLM', 'AGI']
        found_topics = []
        for kw in research_kw:
            if re.search(rf'\b{kw}\b', text, re.IGNORECASE):
                found_topics.append(kw)
        if found_topics:
            result['research_topics'] = found_topics

        # === 正在招聘检测 ===
        hire_patterns = [r'(?:we are |we\'re )?hiring', r'招聘', r'looking for',
                        r'open position', r'join\s+(?:us|my|our)\s+team']
        for pat in hire_patterns:
            if re.search(pat, text, re.IGNORECASE):
                result['is_hiring'] = True
                break

        return result

    def _fetch_scholar_data(self, scholar_url: str) -> Dict:
        """从 Google Scholar 页面提取引用数据"""
        try:
            resp = requests.get(scholar_url, timeout=10, verify=False,
                              headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'})
            if resp.status_code != 200:
                return {}

            import re
            text = resp.text

            # 提取引用数
            citations_match = re.search(r'Citations.*?(\d+)', text)
            h_index_match = re.search(r'h-index.*?(\d+)', text)

            result = {}
            if citations_match:
                result['scholar_citations'] = int(citations_match.group(1))
            if h_index_match:
                result['scholar_h_index'] = int(h_index_match.group(1))

            return result
        except Exception:
            return {}

    def _calculate_enrichment_bonus(self, user: Dict) -> float:
        """计算主页丰富后的评分加成"""
        bonus = 0.0

        # 顶会论文加成 (最多 +10)
        venues_count = user.get('top_venues_count', 0)
        if venues_count > 0:
            bonus += min(venues_count * 0.5, 10)

        # 额外邮箱加成 (+3)
        if user.get('extra_emails'):
            bonus += 3

        # 完整工作经历加成 (+3)
        if user.get('work_experience'):
            bonus += 3

        # 教育背景加成 (+2)
        if user.get('education'):
            bonus += 2

        # LinkedIn 加成 (+2)
        if user.get('linkedin_url'):
            bonus += 2

        # Scholar 引用数加成 (最多 +5)
        citations = user.get('scholar_citations', 0)
        if citations > 0:
            bonus += min(citations / 1000, 5)

        # 正在招聘标记 (+1 - 方便后续精准推荐)
        if user.get('is_hiring'):
            bonus += 1

        return round(bonus, 1)

    # ============================================================
    # Phase 4: 社交网络扩展
    # ============================================================
    def phase4_expand(
        self,
        seed_top: int = 300,
        seeds_file: str = None,
        seed_tier: str = None,
        min_cooccurrence: int = 2
    ):
        """从种子用户的 following 中发现新人才

        Args:
            seed_top: 从 phase3_enriched.json 取前 N 个作为种子
            seeds_file: 从外部文件加载种子（JSON array of usernames）
            seed_tier: 从数据库按 tier 选择种子（逗号分隔，如 "S,A+,A"）
            min_cooccurrence: 最小共现次数

        种子来源优先级: seeds_file > seed_tier > seed_top
        """
        print(f"\n{'='*60}")
        print(f"🌐 Phase 4: 社交网络扩展")
        print(f"{'='*60}\n")

        seeds = []
        existing_usernames = set()

        # 优先级 1: 从外部文件加载种子
        if seeds_file:
            seeds_path = Path(seeds_file)
            if not seeds_path.exists():
                print(f"❌ 种子文件不存在: {seeds_file}")
                return

            with open(seeds_path) as f:
                seed_usernames = json.load(f)

            # 构造种子数据结构（只需要 username）
            seeds = [{"username": u} for u in seed_usernames]
            print(f"📡 从文件加载种子: {len(seeds)} 人")
            print(f"   文件: {seeds_file}")

        # 优先级 2: 从数据库按 tier 选择种子
        elif seed_tier:
            try:
                # 添加父目录到路径以导入 database
                import sys
                headhunter_dir = Path(__file__).parent.parent.parent / "personal-ai-headhunter"
                sys.path.insert(0, str(headhunter_dir))

                # 切换到 headhunter 目录以确保相对路径正确
                original_dir = Path.cwd()
                os.chdir(headhunter_dir)

                from database import SessionLocal, Candidate

                session = SessionLocal()
                tiers = [t.strip() for t in seed_tier.split(',')]
                candidates = session.query(Candidate).filter(
                    Candidate.source == 'github',
                    Candidate.talent_tier.in_(tiers),
                    Candidate.github_url.isnot(None)
                ).all()

                # 从 GitHub URL 提取 username
                for c in candidates:
                    if c.github_url:
                        username = c.github_url.strip('/').split('/')[-1]
                        seeds.append({"username": username})
                        # 记录已有的 username 用于去重
                        existing_usernames.add(username)

                session.close()

                # 恢复原目录
                os.chdir(original_dir)

                print(f"📡 从数据库加载种子: {len(seeds)} 人")
                print(f"   Tier: {', '.join(tiers)}")

            except ImportError as e:
                print(f"❌ 无法导入数据库模块: {e}")
                print(f"   请确保在正确的环境中运行")
                return
            except Exception as e:
                print(f"❌ 从数据库加载种子失败: {e}")
                return

        # 优先级 3: 从 phase3_enriched.json 取前 N 个
        else:
            enriched_file = BASE_DIR / "phase3_enriched.json"
            if not enriched_file.exists():
                print("❌ 未找到 phase3 数据")
                return

            candidates = self._load_json(enriched_file)
            seeds = candidates[:seed_top]
            existing_usernames = {c["username"] for c in candidates}

            print(f"📡 从 phase3_enriched.json 加载种子: {len(seeds)} 人")
            print(f"   取前 {seed_top} 个")

        print(f"   (要求共现 ≥ {min_cooccurrence} 次)\n")

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
            username = str(c.get('username') or '')
            bio = str(c.get('bio') or '')
            company = str(c.get('company') or '')
            print(f"  {i:2d}. {username:20s} | Co: {c['cooccurrence']} | AI: {(c.get('ai_score') or 0.0):.1f} | {company:20s} | {bio[:40]}")

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
            comp_str = str(comp or '')
            print(f"  {comp_str:40s}: {count}")

        # 抽样验证
        print(f"\n🎲 随机抽样 30 人 (验证 AI 相关性):")
        import random as rnd
        samples = rnd.sample(expanded, min(30, total))
        for i, s in enumerate(samples, 1):
            username = str(s.get('username') or '')
            company = str(s.get('company') or '')
            bio = str(s.get('bio') or '')
            print(f"  {i:2d}. {username:20s} | Co: {s.get('cooccurrence',0)} | {company:20s} | {bio[:50]}")
            print(f"      URL: https://github.com/{username}")

    # ============================================================
    # 工具方法
    # ============================================================
    def _save_json(self, data, path: Path):
        """JSON 保存（中间保存用，高频调用，不备份）"""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _save_json_safe(self, data, path: Path):
        """JSON 安全保存（最终输出用，写入前备份已有文件）"""
        if path.exists():
            import shutil as _shutil
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            bak = path.with_name(f"{path.stem}.bak_{ts}{path.suffix}")
            _shutil.copy2(path, bak)
            print(f"  💾 备份旧文件: {bak.name}")
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
    # V3 Pipeline: Phase 2 全量轻富化 (不做 AI 过滤!)
    # ============================================================
    def phase2_v3_light_enrich(self, input_file: str = None, resume: bool = True):
        """V3: 对全部种子用户做轻量级富化（Repos + 网站探活 + Scholar + 邮箱）"""
        print(f"\n{'='*60}")
        print(f"📦 Phase 2 V3: 全量轻富化 (不过滤, 只补数据)")
        print(f"{'='*60}\n")

        src = Path(input_file) if input_file else BASE_DIR / "phase1_seed_users.json"
        if not src.exists():
            print(f"❌ 未找到种子数据: {src}")
            return

        users = self._load_json(src)
        output_path = BASE_DIR / "phase2_v3_enriched.json"

        # 断点续传: 加载已处理的数据
        processed = {}
        if resume and output_path.exists():
            existing = self._load_json(output_path)
            processed = {u["username"]: u for u in existing}
            print(f"  ⏩ 已有 {len(processed)} 人的数据，断点续传")

        enriched = list(processed.values())
        skipped = 0

        for i, user in enumerate(users):
            username = user["username"]
            if username in processed:
                skipped += 1
                continue

            # 检查数据库缓存
            if self.cache and self.cache.is_cached(username):
                cached_data = self.cache.get_cached_data(username)
                if cached_data:
                    # 使用缓存的数据构建 enriched_user
                    enriched_user = {
                        **user,
                        "primary_languages": "",  # 缓存中没有此信息，留空
                        "total_stars": 0,
                        "ai_repo_count": 0,
                        "top_repos": "",
                        "all_emails": cached_data.get("email", "") or user.get("email", ""),
                        "website_status": "active" if cached_data.get("personal_website") else "none",
                        "has_scholar": False,
                        "has_python": False,
                        "_from_cache": True,  # 标记来自缓存
                    }
                    enriched.append(enriched_user)
                    processed[username] = enriched_user
                    continue
                # 如果缓存检查失败，继续正常爬取

            if (i - skipped) % 50 == 0 and (i - skipped) > 0:
                print(f"  进度: {i}/{len(users)} ({i*100//len(users)}%)")

            # 1. Top 5 Repos 扫描
            repos = self._request_list(
                f"{API_BASE}/users/{username}/repos",
                {"sort": "stars", "direction": "desc", "per_page": 5}
            )

            languages = Counter()
            total_stars = 0
            ai_repo_count = 0
            top_repo_names = []

            for repo in repos:
                lang = repo.get("language")
                if lang:
                    languages[lang] += 1
                stars = repo.get("stargazers_count", 0)
                total_stars += stars
                if not repo.get("fork", False):
                    top_repo_names.append(f"{repo['name']} ({stars}★)")

                # 检查 repo 是否 AI 相关
                repo_text = f"{repo.get('name', '')} {repo.get('description', '')}".lower()
                for kw in AI_KEYWORDS_STRONG[:20]:
                    if kw.lower() in repo_text:
                        ai_repo_count += 1
                        break

            # 2. 网站探活
            blog = user.get("blog", "")
            website_status = "none"
            has_scholar = False
            if blog:
                blog_lower = blog.lower()
                if "scholar.google" in blog_lower:
                    has_scholar = True
                    website_status = "scholar"
                else:
                    try:
                        resp = requests.head(
                            blog if blog.startswith("http") else f"https://{blog}",
                            timeout=5, allow_redirects=True,
                            headers={"User-Agent": "Mozilla/5.0"}
                        )
                        website_status = "active" if resp.status_code < 400 else "dead"
                    except:
                        website_status = "dead"

            # 3. 邮箱提取 (从 events)
            emails = set()
            if user.get("email"):
                emails.add(user["email"])
            try:
                events = self._request_list(
                    f"{API_BASE}/users/{username}/events/public",
                    {"per_page": 10}
                )
                for event in events:
                    if event.get("type") == "PushEvent":
                        commits = event.get("payload", {}).get("commits", [])
                        for commit in commits:
                            email = commit.get("author", {}).get("email", "")
                            if email and "noreply" not in email and "@" in email:
                                emails.add(email)
            except:
                pass

            # 4. 判定主语言是否可能与 AI 相关
            has_python = "Python" in languages or "Jupyter Notebook" in languages

            enriched_user = {
                **user,
                "primary_languages": ", ".join(l for l, _ in languages.most_common(5)),
                "total_stars": total_stars,
                "ai_repo_count": ai_repo_count,
                "top_repos": "; ".join(top_repo_names[:5]),
                "all_emails": ", ".join(emails) if emails else "",
                "website_status": website_status,
                "has_scholar": has_scholar,
                "has_python": has_python,
                "_from_cache": False,  # 标记新爬取的数据
            }
            enriched.append(enriched_user)

            # 标记为已爬取（用于缓存统计）
            if self.cache:
                self.cache.mark_as_crawled(username)

            time.sleep(0.5 + random.uniform(0, 0.3))

            # 定期保存
            if (len(enriched)) % 200 == 0:
                self._save_json(enriched, output_path)
                print(f"  💾 已保存 {len(enriched)} 人")

        # 最终保存
        self._save_json(enriched, output_path)
        self._save_csv(enriched, BASE_DIR / "phase2_v3_enriched.csv")

        # 统计
        with_email = sum(1 for e in enriched if e.get("all_emails"))
        with_scholar = sum(1 for e in enriched if e.get("has_scholar"))
        with_website = sum(1 for e in enriched if e.get("website_status") == "active")
        with_python = sum(1 for e in enriched if e.get("has_python"))
        with_ai_repo = sum(1 for e in enriched if e.get("ai_repo_count", 0) > 0)
        from_cache = sum(1 for e in enriched if e.get("_from_cache"))

        print(f"\n✅ Phase 2 V3 轻富化完成!")
        print(f"   总人数: {len(enriched)}")
        print(f"   从缓存读取: {from_cache} ({from_cache*100//max(len(enriched),1)}%)")
        print(f"   有邮箱: {with_email} ({with_email*100//max(len(enriched),1)}%)")
        print(f"   有 Scholar: {with_scholar}")
        print(f"   有活跃网站: {with_website}")
        print(f"   有 Python 项目: {with_python}")
        print(f"   有 AI Repo: {with_ai_repo}")

        # 打印缓存统计
        if self.cache:
            self.cache.print_stats()
            # 保存缓存统计到文件
            cache_stats_path = BASE_DIR / "phase2_cache_stats.json"
            self.cache.save_stats(str(cache_stats_path))

    # ============================================================
    # V3 Pipeline: Phase 3 统一 AI 判定 (用富化后数据)
    # ============================================================
    def phase3_v3_unified_filter(self):
        """V3: 基于富化后的多维数据，做一次终极 AI 相关性判定"""
        print(f"\n{'='*60}")
        print(f"🧠 Phase 3 V3: 统一 AI 判定 (多维信号)")
        print(f"{'='*60}\n")

        src = BASE_DIR / "phase2_v3_enriched.json"
        if not src.exists():
            print("❌ 未找到 Phase 2 V3 数据，请先运行 phase2_v3")
            return

        users = self._load_json(src)

        ai_candidates = []
        rejected = []

        for user in users:
            score = 0.0
            signals = []

            # 合并所有文本
            bio = (user.get("bio") or "").lower()
            company = (user.get("company") or "").lower()
            location = (user.get("location") or "").lower()
            blog = (user.get("blog") or "").lower()
            all_text = f"{bio} {company} {location} {blog}"

            # 1. Bio 强关键词 (+1.0/个, max 5)
            bio_hits = 0
            for kw in AI_KEYWORDS_STRONG:
                if kw.lower() in all_text:
                    bio_hits += 1
                    if bio_hits <= 3:
                        signals.append(f"keyword:{kw}")
            score += min(bio_hits * 1.0, 5.0)

            # 2. Bio 弱关键词 (+0.3/个, max 1.5)
            weak_hits = 0
            for kw in AI_KEYWORDS_WEAK:
                if kw.lower() in all_text:
                    weak_hits += 1
                    if weak_hits <= 2:
                        signals.append(f"weak:{kw}")
            score += min(weak_hits * 0.3, 1.5)

            # 3. AI 公司 (+2.0)
            for comp in AI_COMPANIES:
                if comp.lower() in all_text:
                    score += 2.0
                    signals.append(f"company:{comp}")
                    break

            # 4. 顶尖学校 (+1.5)
            for school in AI_SCHOOLS:
                if school.lower() in all_text:
                    score += 1.5
                    signals.append(f"school:{school}")
                    break

            # === V3 新增信号 ===

            # 5. Repo 语言为 Python/Jupyter (+1.5)
            if user.get("has_python"):
                score += 1.5
                signals.append("lang:python/jupyter")

            # 6. 有 AI 关键词的 Repo (+2.0)
            ai_repos = user.get("ai_repo_count", 0)
            if ai_repos > 0:
                score += 2.0
                signals.append(f"ai_repos:{ai_repos}")

            # 7. 有 Google Scholar (+3.0)
            if user.get("has_scholar"):
                score += 3.0
                signals.append("has_scholar")

            # 8. 影响力
            followers = user.get("followers", 0)
            if followers >= 1000:
                score += 1.0
                signals.append(f"followers:{followers}")
            elif followers >= 100:
                score += 0.3

            user["ai_score_v3"] = round(score, 2)
            user["ai_signals_v3"] = signals

            if score >= 1.5:
                ai_candidates.append(user)
            else:
                rejected.append(user)

        # 排序
        ai_candidates.sort(key=lambda x: x["ai_score_v3"], reverse=True)

        # 保存
        self._save_json(ai_candidates, BASE_DIR / "phase3_v3_ai_candidates.json")
        self._save_csv(ai_candidates, BASE_DIR / "phase3_v3_ai_candidates.csv")
        self._save_json(rejected, BASE_DIR / "phase3_v3_rejected.json")

        print(f"📊 V3 统一判定结果:")
        print(f"  ✅ AI 相关: {len(ai_candidates)} 人 ({len(ai_candidates)*100//max(len(users),1)}%)")
        print(f"  ❌ 非 AI:   {len(rejected)} 人")
        print(f"\n🔍 新旧对比 (预计):")
        print(f"  旧 Phase 2 只靠 bio: 过滤出约 3,723 人")
        print(f"  新 V3 多维信号:      过滤出 {len(ai_candidates)} 人")
        newly_found = len(ai_candidates) - 3723
        if newly_found > 0:
            print(f"  🆕 预计新发现约 {newly_found} 人 (之前被 bio 误杀)")

        # Top 10 预览
        print(f"\n  Top 10 候选人:")
        for i, c in enumerate(ai_candidates[:10], 1):
            username = str(c.get('username') or '')
            signals_str = ", ".join(c.get("ai_signals_v3", [])[:3])
            print(f"    {i}. {username:20s} | Score: {c['ai_score_v3']:.1f} | {signals_str}")



# ============================================================
# CLI 入口
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="GitHub 社交网络挖掘 AI 人才")
    parser.add_argument("command", choices=[
        "phase1", "phase1_resume", "verify1",
        "phase2", "verify2",
        "phase2_v3", "phase3_v3",
        "phase3", "verify3",
        "phase3_5",
        "phase4", "verify4",
    ], help="执行的阶段")
    parser.add_argument("--target", default="Neal12332", help="目标用户名")
    parser.add_argument("--token", default=None, help="GitHub Token")
    parser.add_argument("--seed-top", type=int, default=300, help="Phase 4 种子数量（从 phase3_enriched.json 取前 N 个）")
    parser.add_argument("--seeds-file", type=str, default=None, help="Phase 4 种子文件（JSON array of usernames）")
    parser.add_argument("--seed-tier", type=str, default=None, help="Phase 4 从数据库按 tier 选择种子（逗号分隔，如 S,A+,A）")
    parser.add_argument("--min-cooccurrence", type=int, default=3, help="Phase 4 最小共现次数")
    parser.add_argument("--top", type=int, default=None, help="Phase 3.5 只处理 Top N")
    parser.add_argument("--resume", action="store_true", help="Phase 3.5/Phase2 V3 断点续传")
    parser.add_argument("--max-users", type=int, default=None, help="Phase 3 最大处理人数")
    parser.add_argument("--input", type=str, default=None, help="Phase 3/Phase 3.5 输入文件路径 (支持Phase 4输出)")
    parser.add_argument("--output", type=str, default=None, help="Phase 3 输出文件路径（指定后直接写到该路径，适合 batch_runner.py 调用）")

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

    if not token and args.command not in ["verify1", "verify2", "verify3", "verify4", "phase3_5"]:
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
        miner.phase3_enrich(max_users=args.max_users, resume=args.resume, input_file=args.input, output_file=getattr(args, 'output', None))
    elif args.command == "verify3":
        miner.verify3()
    elif args.command == "phase3_5":
        miner.phase3_5_enrich(top=args.top, resume=args.resume, input_file=args.input, output_file=getattr(args, 'output', None))
    elif args.command == "phase4":
        miner.phase4_expand(
            seed_top=args.seed_top,
            seeds_file=args.seeds_file,
            seed_tier=args.seed_tier,
            min_cooccurrence=args.min_cooccurrence
        )
    elif args.command == "verify4":
        miner.verify4()
    elif args.command == "phase2_v3":
        miner.phase2_v3_light_enrich(input_file=args.input, resume=args.resume)
    elif args.command == "phase3_v3":
        miner.phase3_v3_unified_filter()


if __name__ == "__main__":
    main()
