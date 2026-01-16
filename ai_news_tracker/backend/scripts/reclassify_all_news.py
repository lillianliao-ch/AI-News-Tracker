"""
批量重新分类脚本 - 对现有274条新闻进行AI智能分类

功能：
1. 读取所有现有新闻
2. 逐条调用AI分类API
3. 更新数据库中的ai_category、ai_importance、ai_classified_at字段
4. 显示进度和统计信息

预计时间：10-15分钟（274条 × 2-3秒/条）
预计成本：约2.74元（千问API）
"""

import asyncio
import sys
from datetime import datetime
from loguru import logger

# 添加父目录到路径
sys.path.insert(0, '..')

from models.database import SessionLocal, News
from services.ai_service import AIService


async def reclassify_all_news():
    """批量重新分类所有现有新闻"""
    db = SessionLocal()
    ai_service = AIService()

    try:
        # 获取所有新闻
        news_list = db.query(News).all()
        total = len(news_list)

        logger.info(f"=" * 60)
        logger.info(f"🚀 开始批量重新分类 {total} 条新闻")
        logger.info(f"=" * 60)
        logger.info(f"⏱️  预计时间: {total * 2 // 60}分钟")
        logger.info(f"💰 预计成本: ~{total * 500 * 0.02 / 1000:.2f}元（千问API）")
        logger.info(f"=" * 60)
        logger.info("")

        # 统计信息
        success_count = 0
        error_count = 0
        category_stats = {}
        start_time = datetime.now()

        for index, news in enumerate(news_list, 1):
            try:
                # 调用AI分类
                result = await ai_service.classify_news({
                    'title': news.title,
                    'summary': news.summary or ''
                })

                # 更新字段
                news.ai_category = result.get('category', 'view')
                confidence = result.get('confidence', 0.5)
                news.ai_importance = int(confidence * 5) if confidence > 0 else 3
                news.ai_classified_at = datetime.now()

                # 统计
                category = news.ai_category
                category_stats[category] = category_stats.get(category, 0) + 1
                success_count += 1

                # 每处理10条提交一次
                if index % 10 == 0:
                    db.commit()
                    progress = index * 100 // total
                    logger.info(f"✅ 进度: {index}/{total} ({progress}%) - 成功:{success_count} 失败:{error_count}")

                # 每条间隔1秒（避免API限流）
                await asyncio.sleep(1)

            except Exception as e:
                error_count += 1
                logger.error(f"❌ 分类失败 ({index}/{total}): {news.title[:40]}... - {e}")

                # 失败时使用默认值
                news.ai_category = 'view'
                news.ai_importance = 3
                news.ai_classified_at = datetime.now()

                # 每10条提交一次（包括失败的）
                if index % 10 == 0:
                    db.commit()
                continue

        # 最终提交
        db.commit()

        # 计算用时
        elapsed = (datetime.now() - start_time).total_seconds()

        logger.info("")
        logger.info(f"=" * 60)
        logger.info(f"✅ 重新分类完成！")
        logger.info(f"=" * 60)
        logger.info(f"📊 统计信息:")
        logger.info(f"  总数: {total}条")
        logger.info(f"  成功: {success_count}条 ({success_count*100//total}%)")
        logger.info(f"  失败: {error_count}条 ({error_count*100//total}%)")
        logger.info(f"  用时: {elapsed:.1f}秒 ({elapsed/60:.1f}分钟)")
        logger.info(f"")
        logger.info(f"📊 AI分类分布:")
        for cat, count in sorted(category_stats.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"  {cat}: {count}条")
        logger.info(f"=" * 60)

    except Exception as e:
        logger.error(f"❌ 批量分类失败: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("AI News Tracker - 批量重新分类脚本")
    logger.info("")

    # 运行
    asyncio.run(reclassify_all_news())

    logger.info("")
    logger.info("✅ 脚本执行完成！")
