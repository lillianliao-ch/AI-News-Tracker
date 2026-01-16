"""
数据库模型 - 使用 SQLAlchemy
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from config.base_config import settings

Base = declarative_base()

# 创建引擎
engine = create_engine(
    settings.DATABASE_URL,
    echo=False
)

# 创建会话工厂
SessionLocal = sessionmaker(bind=engine)


class News(Base):
    """资讯表"""
    __tablename__ = 'ai_news'

    id = Column(Integer, primary_key=True, autoincrement=True)
    news_id = Column(String(200), unique=True, nullable=False, index=True)  # 唯一ID
    title = Column(String(500), nullable=False)
    url = Column(String(1000), nullable=False)
    summary = Column(Text)
    content = Column(Text)

    # 来源信息
    source = Column(String(100))  # 36kr/InfoQ等
    source_url = Column(String(500))
    author = Column(String(200))
    icon = Column(String(500))

    # 语言支持
    language = Column(String(10), default='zh', comment='语言: zh/en')  # zh=中文, en=英文
    lang_confidence = Column(Float, default=0.0, comment='语言检测置信度')

    # 时间
    publish_time = Column(DateTime)
    crawl_time = Column(DateTime, default=datetime.now)

    # 分类信息
    category = Column(String(50))  # 媒体分类：AI新闻、AI技术等（数据源配置）

    # ✨ AI智能分析字段
    ai_category = Column(String(50), comment='AI内容分类: product/model/investment/view/research/application')
    ai_importance = Column(Integer, default=3, comment='AI分析的重要性: 1-5分')
    ai_classified_at = Column(DateTime, comment='AI分类时间')

    # 保留原有字段（兼容）
    tags = Column(String(500))  # JSON: ["GPT-5", "OpenAI"]
    sentiment = Column(String(20))  # positive/neutral/negative
    importance = Column(Integer, default=3)  # 1-5

    # 向量搜索
    vector_id = Column(String(200))

    # 统计
    view_count = Column(Integer, default=0)
    select_count = Column(Integer, default=0)

    # 状态
    is_published = Column(Boolean, default=False)
    is_selected = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关系
    generated_contents = relationship("GeneratedContent", back_populates="news")


class GeneratedContent(Base):
    """生成内容表"""
    __tablename__ = 'generated_contents'

    id = Column(Integer, primary_key=True, autoincrement=True)
    news_id = Column(Integer, ForeignKey('ai_news.id'), nullable=False)
    version = Column(String(10), nullable=False)  # A/B/C

    # 小红书内容
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    hashtags = Column(String(500))  # JSON: ["#AI", "#黑科技"]
    image_prompt = Column(Text)

    # 元数据
    model_used = Column(String(100))
    prompt_template = Column(Text)
    generation_time = Column(DateTime, default=datetime.now)

    # 用户反馈
    is_selected = Column(Boolean, default=False)
    is_published = Column(Boolean, default=False)
    published_platform = Column(String(100))  # xiaohongshu/friend_circle
    published_time = Column(DateTime)

    created_at = Column(DateTime, default=datetime.now)

    # 关系
    news = relationship("News", back_populates="generated_contents")


class UserPreference(Base):
    """用户偏好表"""
    __tablename__ = 'user_preferences'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(100), default='default')
    preference_type = Column(String(50), nullable=False)  # style/length/topic
    preference_value = Column(String(100), nullable=False)
    weight = Column(Float, default=1.0)

    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class SelectionHistory(Base):
    """选择历史表"""
    __tablename__ = 'selection_history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(100), default='default')
    news_id = Column(Integer, ForeignKey('ai_news.id'))
    content_id = Column(Integer, ForeignKey('generated_contents.id'))
    version = Column(String(10), nullable=False)

    selected_at = Column(DateTime, default=datetime.now)


class CrawlerLog(Base):
    """爬虫日志表"""
    __tablename__ = 'crawler_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    platform = Column(String(100), nullable=False)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    status = Column(String(20))  # success/error
    items_crawled = Column(Integer, default=0)
    error_message = Column(Text)
    log_details = Column(Text)  # JSON

    created_at = Column(DateTime, default=datetime.now)


# 导出
__all__ = [
    'Base',
    'engine',
    'SessionLocal',
    'News',
    'GeneratedContent',
    'UserPreference',
    'SelectionHistory',
    'CrawlerLog'
]
