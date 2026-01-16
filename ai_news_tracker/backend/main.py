"""
FastAPI 主应用 - 提供 API 接口
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import asyncio

from config.base_config import settings, SOURCES_CONFIG
from sources.base import SourceFactory
from services.ai_service import AIService
from models.database import Base, engine, SessionLocal, News
from sqlalchemy.orm import Session

# 创建应用
app = FastAPI(
    title="AI News Tracker API",
    description="AI 资讯追踪与内容生成系统",
    version="0.1.0"
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局依赖
ai_service = AIService()

# ==================== 分类映射配置 ====================
# 将前端显示的分类映射到数据库中的实际分类
CATEGORY_MAP = {
    "产品": "AI产品",
    "模型": ["AI技术", "AI研究"],
    "融资": ["AI创投", "AI商业"],
    "观点": ["AI新闻", "AI社区", "技术文章", "科技新闻"]
}


# ==================== 基础路由 ====================

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "AI News Tracker API",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """健康检查端点（用于Railway等平台）"""
    return {
        "status": "healthy",
        "service": "ai-news-tracker",
        "version": "0.1.0"
    }


# ==================== API 路由 ====================

# Pydantic 模型
class NewsItem(BaseModel):
    id: int
    news_id: str
    title: str
    url: str
    summary: str
    content: str
    source: str
    source_url: str
    category: str
    icon: str
    publish_time: datetime
    crawl_time: datetime

    class Config:
        from_attributes = True


class GenerateRequest(BaseModel):
    news_id: str
    versions: List[str] = ['A', 'B', 'C']  # 默认生成3个版本


class GenerateResponse(BaseModel):
    news_id: str
    version: str
    title: str
    content: str
    hashtags: List[str]
    image_prompt: str


# 数据库依赖
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动时的操作"""
    # 创建数据库表
    Base.metadata.create_all(bind=engine)
    print("✅ 数据库初始化成功")


# ==================== API 路由 ====================

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "AI News Tracker API",
        "version": "0.1.0",
        "docs": "/docs",
        "endpoints": {
            "GET /api/news": "获取所有资讯",
            "GET /api/news/{news_id}": "获取单条资讯",
            "POST /api/generate": "生成小红书内容",
            "POST /api/crawl": "手动触发爬虫",
            "GET /api/stats": "获取统计信息"
        }
    }


@app.get("/api/news", response_model=List[NewsItem])
async def get_news(
    category: Optional[str] = None,
    source: Optional[str] = None,
    language: Optional[str] = None,  # 新增：语言筛选
    limit: int = 50,
    offset: int = 0
):
    """
    获取资讯列表

    参数:
    - category: 筛选分类
    - source: 筛选来源
    - language: 筛选语言 (zh/en) - 新增
    - limit: 限制数量（默认50）
    - offset: 偏移量（分页用）
    """
    db = SessionLocal()
    try:
        query = db.query(News)

        # 分类筛选（支持映射）
        if category:
            if category in CATEGORY_MAP:
                # 使用映射关系
                mapped_categories = CATEGORY_MAP[category]
                if isinstance(mapped_categories, str):
                    # 单个分类
                    query = query.filter(News.category == mapped_categories)
                else:
                    # 多个分类（使用 IN 查询）
                    query = query.filter(News.category.in_(mapped_categories))
            else:
                # 直接使用原始分类名（兼容性）
                query = query.filter(News.category == category)

        # 其他筛选
        if source:
            query = query.filter(News.source == source)
        if language:  # 语言筛选
            query = query.filter(News.language == language)

        # 排序和分页
        query = query.order_by(News.publish_time.desc())
        query = query.offset(offset).limit(limit)

        news_list = query.all()

        return news_list
    finally:
        db.close()


@app.get("/api/news/{news_id}", response_model=NewsItem)
async def get_news_detail(news_id: str):
    """获取单条资讯详情"""
    db = SessionLocal()
    try:
        news = db.query(News).filter(News.news_id == news_id).first()

        if not news:
            raise HTTPException(status_code=404, detail="资讯不存在")

        return news
    finally:
        db.close()


@app.post("/api/generate", response_model=List[GenerateResponse])
async def generate_content(request: GenerateRequest):
    """
    生成小红书内容

    参数:
    - news_id: 资讯ID
    - versions: 需要生成的版本列表 ['A', 'B', 'C']
    """
    db = SessionLocal()
    try:
        # 查询资讯
        news = db.query(News).filter(News.news_id == request.news_id).first()

        if not news:
            raise HTTPException(status_code=404, detail="资讯不存在")

        # 生成3个版本
        results = []
        for version in request.versions:
            # 转换为字典
            news_dict = {
                'title': news.title,
                'summary': news.summary,
                'content': news.content,
                'url': news.url
            }

            # 调用 AI 生成
            generated = await ai_service.generate_xiaohongshu_content(news_dict, version)

            results.append(GenerateResponse(
                news_id=request.news_id,
                version=version,
                title=generated['title'],
                content=generated['content'],
                hashtags=generated['hashtags'],
                image_prompt=generated.get('image_prompt', '')
            ))

        return results
    finally:
        db.close()


@app.post("/api/crawl")
async def trigger_crawl(background_tasks: BackgroundTasks):
    """
    手动触发爬虫（异步后台任务）

    返回立即响应，爬虫在后台运行
    """
    from tasks.crawler import crawl_all_sources

    # 添加后台任务
    background_tasks.add_task(crawl_all_sources)

    return {
        "message": "爬虫任务已启动，正在后台运行",
        "status": "running"
    }


@app.get("/api/stats")
async def get_stats():
    """获取统计信息"""
    db = SessionLocal()
    try:
        total_news = db.query(News).count()
        today_news = db.query(News).filter(
            News.crawl_time >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        ).count()

        # 按4大分类统计（使用映射）
        category_stats = {}
        for display_name, db_categories in CATEGORY_MAP.items():
            if isinstance(db_categories, str):
                # 单个分类
                count = db.query(News).filter(News.category == db_categories).count()
            else:
                # 多个分类（使用 IN 查询）
                count = db.query(News).filter(News.category.in_(db_categories)).count()
            category_stats[display_name] = count

        # 添加"全部"
        category_stats["全部"] = total_news

        # 按来源统计
        source_stats = {}
        for source_id, config in SOURCES_CONFIG.items():
            if config['enabled']:
                count = db.query(News).filter(News.source == config['name']).count()
                source_stats[config['name']] = count

        return {
            "total_news": total_news,
            "today_news": today_news,
            "category_stats": category_stats,
            "source_stats": source_stats,
            "last_crawl": db.query(News).order_by(News.crawl_time.desc()).first().crawl_time if total_news > 0 else None
        }
    finally:
        db.close()


if __name__ == "__main__":
    import uvicorn

    print("🚀 启动 AI News Tracker API")
    print(f"📊 API 文档: http://localhost:8000/docs")

    uvicorn.run(app, host="0.0.0.0", port=8000)
