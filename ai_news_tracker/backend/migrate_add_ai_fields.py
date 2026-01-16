"""
数据库迁移脚本：添加AI智能分类字段

新增字段：
- ai_category: AI内容分类 (product/model/investment/view/research/application)
- ai_importance: AI分析的重要性 (1-5分)
- ai_classified_at: AI分类时间
"""

from sqlalchemy import create_engine, text
from config.base_config import settings
from loguru import logger

def migrate():
    """添加AI智能分析字段"""
    engine = create_engine(settings.DATABASE_URL)

    with engine.connect() as conn:
        # 检查表结构
        result = conn.execute(text("PRAGMA table_info(ai_news)"))
        columns = [row[1] for row in result]

        logger.info(f"当前数据库字段: {len(columns)}个")

        # 添加 ai_category 字段
        if 'ai_category' not in columns:
            logger.info("✅ 添加 ai_category 字段...")
            conn.execute(text(
                "ALTER TABLE ai_news ADD COLUMN ai_category VARCHAR(50)"
            ))
            conn.commit()
            logger.info("   ✅ ai_category 字段添加成功")
        else:
            logger.info("⊙️  ai_category 字段已存在，跳过")

        # 添加 ai_importance 字段
        if 'ai_importance' not in columns:
            logger.info("✅ 添加 ai_importance 字段...")
            conn.execute(text(
                "ALTER TABLE ai_news ADD COLUMN ai_importance INTEGER DEFAULT 3"
            ))
            conn.commit()
            logger.info("   ✅ ai_importance 字段添加成功")
        else:
            logger.info("⊙️  ai_importance 字段已存在，跳过")

        # 添加 ai_classified_at 字段
        if 'ai_classified_at' not in columns:
            logger.info("✅ 添加 ai_classified_at 字段...")
            conn.execute(text(
                "ALTER TABLE ai_news ADD COLUMN ai_classified_at DATETIME"
            ))
            conn.commit()
            logger.info("   ✅ ai_classified_at 字段添加成功")
        else:
            logger.info("⊙️  ai_classified_at 字段已存在，跳过")

        # 验证结果
        result = conn.execute(text("PRAGMA table_info(ai_news)"))
        new_columns = [row[1] for row in result]

        logger.info(f"✅ 迁移完成！当前数据库字段: {len(new_columns)}个")
        logger.info(f"📊 新增字段: ai_category, ai_importance, ai_classified_at")

if __name__ == "__main__":
    logger.info("🚀 开始数据库迁移：添加AI智能分类字段")
    migrate()
    logger.info("✅ 迁移脚本执行完成！")
