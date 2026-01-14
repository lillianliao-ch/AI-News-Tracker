"""
测试国际媒体源爬取
"""
import asyncio
from config.base_config import SOURCES_CONFIG
from sources.base import SourceFactory
from loguru import logger

async def test_international_sources():
    """测试所有国际媒体源"""
    logger.info("🌍 开始测试国际媒体源")

    # 国际媒体源ID列表
    international_sources = [
        'ai-news',
        'techcrunch-ai',
        'arstechnica',
        'mit-tech-review',
        'the-verge-ai'
    ]

    total_items = 0
    success_count = 0
    failed_sources = []

    for source_id in international_sources:
        if source_id not in SOURCES_CONFIG:
            logger.warning(f"⚠️ 数据源 {source_id} 不在配置中")
            continue

        config = SOURCES_CONFIG[source_id]

        if not config.get('enabled', False):
            logger.info(f"⏭️ 数据源 {config['name']} 未启用，跳过")
            continue

        logger.info(f"\n{'='*60}")
        logger.info(f"测试: {config['name']}")
        logger.info(f"RSS URL: {config['rss_url']}")
        logger.info(f"{'='*60}")

        try:
            # 创建数据源
            source = SourceFactory.create_source(config)

            # 爬取数据
            items = await source.get_data()

            if items:
                logger.success(f"✅ {config['name']}: 成功获取 {len(items)} 条")
                total_items += len(items)
                success_count += 1

                # 显示前3条
                for i, item in enumerate(items[:3], 1):
                    logger.info(f"\n{i}. 标题: {item['title'][:60]}...")
                    logger.info(f"   语言: {item.get('language', 'unknown')} (置信度: {item.get('lang_confidence', 0):.2f})")
                    logger.info(f"   链接: {item['url'][:60]}...")
            else:
                logger.warning(f"⚠️ {config['name']}: 未获取到数据")
                failed_sources.append(config['name'])

        except Exception as e:
            logger.error(f"❌ {config['name']}: 爬取失败 - {e}")
            failed_sources.append(config['name'])

    # 汇总
    logger.info(f"\n{'='*60}")
    logger.info("📊 测试汇总")
    logger.info(f"{'='*60}")
    logger.info(f"成功: {success_count}/{len(international_sources)}")
    logger.info(f"总条数: {total_items}")

    if failed_sources:
        logger.warning(f"失败的数据源: {', '.join(failed_sources)}")

    return success_count > 0

if __name__ == "__main__":
    success = asyncio.run(test_international_sources())
    if success:
        logger.success("✅ 国际媒体源测试完成")
    else:
        logger.error("❌ 国际媒体源测试失败")
