"""
GitHub Hunter 配置文件
参考 MediaCrawler 的配置驱动设计理念
"""

# ===== GitHub API 配置 =====
GITHUB_CONFIG = {
    # GitHub API 基础地址
    "api_base": "https://api.github.com",

    # GitHub Personal Access Token (可选)
    # 获取方式: GitHub Settings -> Developer settings -> Personal access tokens -> Tokens (classic)
    # 建议创建 token 以提升速率限制（5000次/小时 vs 60次/小时）
    "token": None,  # 或填入 "ghp_xxxxxxxxxxxxxxxxxxxx"

    # 请求间隔（秒）- 避免触发速率限制
    "request_delay": 1.0,

    # 超时设置（秒）
    "timeout": 10,

    # 重试次数
    "max_retries": 3,
}

# ===== 数据提取配置 =====
EXTRACTION_CONFIG = {
    # 基本信息字段
    "basic_fields": [
        "github_url", "username", "name", "email", "bio",
        "location", "company", "public_repos", "followers", "following"
    ],

    # 技术信息字段
    "tech_fields": [
        "primary_languages", "language_count", "total_stars",
        "original_repos", "fork_repos", "top_repos"
    ],

    # 时间信息字段
    "time_fields": [
        "created_at", "updated_at"
    ],

    # 邮箱提取配置
    "email_config": {
        "from_profile": True,       # 从个人资料提取
        "from_commits": True,       # 从最近 commits 提取
        "commits_limit": 20,        # 检查最近20个 commits
    },

    # 仓库信息配置
    "repo_config": {
        "limit": 20,                # 获取仓库数量
        "sort_by": "updated",       # updated / stars / forks
        "include_forks": True,      # 是否包含 fork 的仓库
    },
}

# ===== 数据存储配置 =====
STORAGE_CONFIG = {
    # 输出格式: csv, json, excel, database
    "output_formats": ["excel", "json"],

    # 输出文件名（不含扩展名）
    "output_filename": "github_candidates",

    # Excel 配置
    "excel_config": {
        "engine": "openpyxl",
        "index": False,
    },

    # JSON 配置
    "json_config": {
        "ensure_ascii": False,
        "indent": 2,
    },

    # 数据库配置（可选）
    "database_config": {
        "enabled": False,
        "type": "sqlite",  # sqlite / mysql / postgresql
        "connection_string": "sqlite:///candidates.db",
        "table_name": "github_candidates",
    },
}

# ===== 筛选配置 =====
FILTER_CONFIG = {
    # 中国用户识别关键词
    "china_location_keywords": [
        "中国", "china", "beijing", "shanghai", "shenzhen",
        "hangzhou", "chengdu", "北京", "上海", "深圳", "杭州", "成都",
        "guangzhou", "guangzhou", "广州", "nanjing", "南京"
    ],

    "china_company_keywords": [
        "alibaba", "tencent", "bytedance", "baidu", "meituan",
        "didi", "jd", "netease", "huawei", "xiaomi",
        "阿里", "腾讯", "字节", "百度", "美团", "滴滴", "京东", "网易", "华为", "小米"
    ],

    # 最小活跃度要求
    "min_activity": {
        "public_repos": 1,          # 至少1个公开仓库
        "followers": 0,             # 不限制粉丝数
        "total_stars": 0,           # 不限制 star 数
    },

    # 账号年龄要求（天）
    "min_account_age_days": 30,

    # 最后活跃时间（天）
    "max_inactive_days": 365,
}

# ===== 评分配置 =====
SCORING_CONFIG = {
    # 是否启用评分
    "enabled": False,

    # 评分维度和权重
    "dimensions": {
        "activity": {              # 活跃度
            "weight": 0.3,
            "metrics": ["public_repos", "followers", "total_stars"]
        },
        "quality": {               # 质量分
            "weight": 0.4,
            "metrics": ["original_repos", "total_stars", "avg_repo_stars"]
        },
        "experience": {            # 经验分
            "weight": 0.3,
            "metrics": ["language_diversity", "account_age", "repo_quality"]
        }
    },

    # 评分等级
    "score_levels": {
        "excellent": 80,    # 优秀
        "good": 60,         # 良好
        "average": 40,      # 一般
        "below_average": 20 # 低于平均
    }
}

# ===== 日志配置 =====
LOGGING_CONFIG = {
    # 日志级别: DEBUG, INFO, WARNING, ERROR
    "level": "INFO",

    # 是否显示详细进度
    "show_progress": True,

    # 是否保存日志
    "save_log": True,
    "log_file": "github_hunter.log",
}

# ===== 去重配置 =====
DEDUPLICATION_CONFIG = {
    # 是否启用去重
    "enabled": True,

    # 去重字段（优先级从高到低）
    "dedup_fields": ["email", "username", "name"],

    # 保留策略: first（保留第一个）, last（保留最后一个）, best（保留评分最高的）
    "keep_strategy": "best",
}

# ===== 代理配置 =====
PROXY_CONFIG = {
    # 是否启用代理
    "enabled": False,

    # 代理地址
    "proxies": {
        "http": "http://proxy.example.com:8080",
        "https": "https://proxy.example.com:8080",
    },

    # 代理池（多个代理轮换）
    "proxy_pool": [
        "http://proxy1.example.com:8080",
        "http://proxy2.example.com:8080",
    ],
}
