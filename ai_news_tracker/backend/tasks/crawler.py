"""
爬虫任务 - 定时爬取资讯
"""
import asyncio
from datetime import datetime
from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from config.base_config import settings, SOURCES_CONFIG
from sources.base import SourceFactory
from services.ai_service import AIService
from models.database import News, CrawlerLog
from config.prompts import is_ai_related

# 创建同步引擎（用于写入数据库）
engine = create_engine(
    settings.DATABASE_URL,
    echo=False
)
SessionLocal = sessionmaker(bind=engine)


async def crawl_all_sources():
    """爬取所有数据源"""
    logger.info("🚀 开始爬取所有数据源")

    # 创建所有数据源
    sources = SourceFactory.create_all_sources(SOURCES_CONFIG)
    logger.info(f"📊 共 {len(sources)} 个数据源")

    total_crawled = 0

    for source in sources:
        try:
            # 记录开始时间
            start_time = datetime.now()
            logger.info(f"开始爬取: {source.name}")

            # 爬取数据
            items = await source.get_data()
            logger.info(f"{source.name} 爬取到 {len(items)} 条")

            # 保存到数据库
            saved_count = await save_news_items(items, source.name)
            total_crawled += saved_count

            # 记录日志
            end_time = datetime.now()
            await save_crawl_log(
                platform=source.name,
                start_time=start_time,
                end_time=end_time,
                status='success',
                items_crawled=saved_count
            )

        except Exception as e:
            logger.error(f"爬取 {source.name} 失败: {e}")

            # 记录错误日志
            await save_crawl_log(
                platform=source.name,
                start_time=start_time,
                end_time=datetime.now(),
                status='error',
                items_crawled=0,
                error_message=str(e)
            )

    logger.info(f"✅ 爬虫任务完成，共 {total_crawled} 条新数据")


async def save_news_items(items: list, source_name: str) -> int:
    """保存资讯到数据库"""
    if not items:
        return 0

    db = SessionLocal()
    ai_service = AIService()

    saved_count = 0

    try:
        for item in items:
            try:
                # 检查是否已存在
                existing = db.query(News).filter(
                    News.news_id == item['id']
                ).first()

                if existing:
                    logger.debug(f"资讯已存在，跳过: {item['title'][:30]}...")
                    continue

                # AI 相关性过滤（支持多语言）
                language = item.get('language', 'zh')
                if not is_ai_related(item['title'], item.get('summary', ''), language):
                    logger.info(f"跳过非AI资讯: {item['title'][:50]}...")
                    continue

                # ✨ AI智能分类（新增）
                try:
                    classify_result = await ai_service.classify_news(item)
                    item['ai_category'] = classify_result.get('category', 'view')
                    # 将confidence转换为1-5分的重要性评分
                    confidence = classify_result.get('confidence', 0.5)
                    item['ai_importance'] = int(confidence * 5) if confidence > 0 else 3
                    item['ai_classified_at'] = datetime.now()
                    logger.info(f"🤖 AI分类: {item['title'][:30]}... → {item['ai_category']} ({item['ai_importance']}分)")
                except Exception as e:
                    logger.warning(f"⚠️  AI分类失败: {e}，使用默认值")
                    item['ai_category'] = 'view'
                    item['ai_importance'] = 3
                    item['ai_classified_at'] = datetime.now()

                # 创建新记录
                news = News(
                    news_id=item['id'],
                    title=item['title'],
                    url=item['url'],
                    summary=item.get('summary', ''),
                    content=item.get('content', ''),
                    source=source_name,
                    source_url=item.get('source_url', ''),
                    icon=item.get('icon', ''),
                    category=item.get('category', 'view'),  # 媒体分类（保留）
                    ai_category=item.get('ai_category', 'view'),  # ✨ AI内容分类（新增）
                    ai_importance=item.get('ai_importance', 3),  # ✨ 重要性（新增）
                    ai_classified_at=item.get('ai_classified_at'),  # ✨ 分类时间（新增）
                    publish_time=item.get('publish_time', datetime.now()),
                    crawl_time=item.get('crawl_time', datetime.now()),
                    language=item.get('language', 'zh'),
                    lang_confidence=item.get('lang_confidence', 0.0)
                )

                db.add(news)
                saved_count += 1

                logger.info(f"✅ 保存成功: {item['title'][:30]}... [媒体:{item.get('category')}] [AI:{item.get('ai_category')}]")

            except Exception as e:
                logger.error(f"保存资讯失败: {e}")
                continue

        # 提交事务
        db.commit()
        logger.info(f"💾 成功保存 {saved_count} 条新资讯到数据库")

    except Exception as e:
        logger.error(f"数据库操作失败: {e}")
        db.rollback()
    finally:
        db.close()

    return saved_count


async def save_crawl_log(
    platform: str,
    start_time: datetime,
    end_time: datetime,
    status: str,
    items_crawled: int = 0,
    error_message: str = None
):
    """保存爬虫日志"""
    db = SessionLocal()

    try:
        log = CrawlerLog(
            platform=platform,
            start_time=start_time,
            end_time=end_time,
            status=status,
            items_crawled=items_crawled,
            error_message=error_message
        )

        db.add(log)
        db.commit()

    except Exception as e:
        logger.error(f"保存日志失败: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    """直接运行此脚本进行手动爬取"""
    import asyncio
    asyncio.run(crawl_all_sources())
