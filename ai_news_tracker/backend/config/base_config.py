"""
配置文件 - 参考 MediaCrawler 的配置驱动设计
"""
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """基础配置"""

    # API Keys
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"  # 支持 OpenAI 兼容接口（如千问）
    ANTHROPIC_API_KEY: str = ""

    # Database
    DATABASE_URL: str = "sqlite:///./data/ai_news.db"

    # Cache
    ENABLE_CACHE: bool = True
    CACHE_TTL: int = 1800  # 30分钟

    # Crawler
    CRAWL_INTERVAL: int = 7200  # 2小时
    MIN_REQUEST_INTERVAL: float = 2.0  # 秒
    MAX_RETRIES: int = 3

    # AI Models
    CLASSIFY_MODEL: str = "qwen-max"  # 分类模型（可用 qwen-max、qwen-plus）
    SUMMARY_MODEL: str = "qwen-plus"  # 摘要模型
    GENERATE_MODEL: str = "qwen-max"  # 生成模型

    # Storage
    DATA_DIR: Path = Path("./data")
    CACHE_DIR: Path = Path("./data/cache")

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "ai_news_tracker.log"

    # Application
    PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:4321"
    DEBUG: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # 允许额外字段

# 全局配置实例
settings = Settings()

# 数据源配置
SOURCES_CONFIG = {
    # === AI专门媒体（主力，高优先级） ===
    "qbitai": {
        "id": "qbitai",
        "name": "量子位",
        "home_url": "https://www.qbitai.com",
        "rss_url": "https://www.qbitai.com/feed",
        "enabled": True,
        "icon": "/icons/qbitai.png",
        "category": "AI新闻",
        "priority": 10,
        "limit": 10,  # RSS只提供10条，已达到上限
        "ai_related_rate": 0.95
    },

    "jiqizhixin": {
        "id": "jiqizhixin",
        "name": "机器之心",
        "home_url": "https://www.jiqizhixin.com",
        "rss_url": "https://www.jiqizhixin.com/feed",
        "enabled": False,  # RSS失效（0条），暂时禁用
        "icon": "/icons/jiqizhixin.png",
        "category": "AI新闻",
        "priority": 9,
        "limit": 50,
        "ai_related_rate": 0.95,
        "disabled_reason": "RSS解析返回0条，需要修复RSS URL"
    },

    "leiphone": {
        "id": "leiphone",
        "name": "雷锋网",
        "home_url": "https://www.leiphone.com",
        "rss_url": "https://www.leiphone.com/feed",
        "enabled": True,  # 新增
        "icon": "/icons/leiphone.png",
        "category": "AI技术",
        "priority": 9,
        "limit": 20,  # RSS提供20条
        "ai_related_rate": 0.85,
        "note": "AI专业媒体，专注技术报道"
    },

    "tmtpost": {
        "id": "tmtpost",
        "name": "钛媒体",
        "home_url": "https://www.tmtpost.com",
        "rss_url": "https://www.tmtpost.com/rss",
        "enabled": True,  # 新增
        "icon": "/icons/tmtpost.png",
        "category": "AI商业",
        "priority": 8,
        "limit": 17,  # RSS提供17条
        "ai_related_rate": 1.00,  # 测试显示100% AI相关
        "note": "AI相关率极高，专注商业分析"
    },

    "infoq": {
        "id": "infoq",
        "name": "InfoQ",
        "home_url": "https://www.infoq.cn",
        "rss_url": "https://www.infoq.cn/feed",
        "enabled": True,
        "icon": "/icons/infoq.png",
        "category": "AI技术",
        "priority": 8,
        "limit": 20,  # RSS提供20条，全部使用
        "ai_related_rate": 0.80
    },

    # === AI社区 ===
    "reddit-ai": {
        "id": "reddit-ai",
        "name": "Reddit AI",
        "home_url": "https://reddit.com/r/artificial",
        "rss_url": "https://www.reddit.com/r/artificial/.rss",
        "enabled": True,
        "icon": "/icons/reddit.png",
        "category": "AI社区",
        "priority": 6,
        "limit": 25,  # RSS提供25条，全部使用
        "ai_related_rate": 0.68
    },

    # === 综合科技媒体（限制使用） ===
    "36kr-ai": {
        "id": "36kr-ai",
        "name": "36氪",
        "home_url": "https://36kr.com",
        "rss_url": "https://36kr.com/feed",
        "enabled": True,
        "icon": "/icons/36kr.png",
        "category": "AI创投",
        "priority": 3,  # 降低优先级
        "limit": 10,  # 严格限制到10条（虽然RSS有30条）
        "ai_related_rate": 0.30
    },

    # === 国际AI媒体（新增） ===
    "ai-news": {
        "id": "ai-news",
        "name": "AI News",
        "home_url": "https://artificialintelligence-news.com",
        "rss_url": "https://artificialintelligence-news.com/feed/",
        "enabled": True,
        "icon": "/icons/ai-news.png",
        "category": "国际AI新闻",
        "priority": 10,
        "limit": 12,
        "ai_related_rate": 1.00,
        "language": "en",
        "note": "专业AI新闻媒体，AI相关率100%"
    },

    "techcrunch-ai": {
        "id": "techcrunch-ai",
        "name": "TechCrunch AI",
        "home_url": "https://techcrunch.com",
        "rss_url": "https://techcrunch.com/category/artificial-intelligence/feed/",
        "enabled": True,
        "icon": "/icons/techcrunch.png",
        "category": "AI创投",
        "priority": 8,
        "limit": 20,
        "ai_related_rate": 0.67,
        "language": "en",
        "note": "专注AI初创公司和投资"
    },

    "arstechnica": {
        "id": "arstechnica",
        "name": "Ars Technica",
        "home_url": "https://arstechnica.com",
        "rss_url": "https://feeds.arstechnica.com/arstechnica/technology-lab",
        "enabled": True,
        "icon": "/icons/arstechnica.png",
        "category": "AI技术",
        "priority": 8,
        "limit": 20,
        "ai_related_rate": 0.67,
        "language": "en",
        "note": "深度技术报道"
    },

    "mit-tech-review": {
        "id": "mit-tech-review",
        "name": "MIT Tech Review",
        "home_url": "https://www.technologyreview.com",
        "rss_url": "https://www.technologyreview.com/feed/",
        "enabled": True,
        "icon": "/icons/mit.png",
        "category": "AI研究",
        "priority": 7,
        "limit": 10,
        "ai_related_rate": 0.33,
        "language": "en",
        "note": "MIT出品，涵盖技术趋势"
    },

    "the-verge-ai": {
        "id": "the-verge-ai",
        "name": "The Verge AI",
        "home_url": "https://www.theverge.com",
        "rss_url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
        "enabled": True,
        "icon": "/icons/verge.png",
        "category": "AI产品",
        "priority": 7,
        "limit": 10,
        "ai_related_rate": 0.33,
        "language": "en",
        "note": "消费科技和AI产品"
    },

    # === 旧版国际媒体（暂时禁用，使用新的techcrunch-ai） ===
    "techcrunch": {
        "id": "techcrunch",
        "name": "TechCrunch (旧)",
        "home_url": "https://techcrunch.com",
        "rss_url": "https://techcrunch.com/feed/",
        "enabled": False,  # 使用techcrunch-ai替代
        "icon": "/icons/techcrunch.png",
        "category": "国际科技",
        "priority": 2,
        "limit": 5,
        "ai_related_rate": 0.50,
        "disabled_reason": "使用techcrunch-ai替代，AI相关率更高"
    },

    "venturebeat-ai": {
        "id": "venturebeat-ai",
        "name": "VentureBeat AI",
        "home_url": "https://venturebeat.com/ai",
        "rss_url": "https://venturebeat.com/ai/feed/",
        "enabled": False,  # RSS失效
        "icon": "/icons/vb.png",
        "category": "AI国际",
        "priority": 7,
        "limit": 20,
        "ai_related_rate": 0.85,
        "disabled_reason": "RSS解析失败"
    }
}

# AI 分类配置
AI_CATEGORIES = {
    "product": "新产品发布",
    "model": "新模型发布",
    "investment": "投融资",
    "view": "行业观点",
    "research": "学术论文",
    "application": "AI应用"
}

# 小红书内容生成配置
XIAOHONGSHU_STYLES = {
    "A": {
        "name": "硬核技术风",
        "description": "专业但不晦涩，用数据说话",
        "target_audience": "技术人员、开发者"
    },
    "B": {
        "name": "轻松科普风",
        "description": "口语化，多用表情，亲切如朋友",
        "target_audience": "AI兴趣爱好者"
    },
    "C": {
        "name": "热点观点风",
        "description": "有观点有立场，引发讨论",
        "target_audience": "行业观察者"
    }
}
