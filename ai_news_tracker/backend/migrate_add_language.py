"""
数据库迁移脚本：添加language字段
"""
from sqlalchemy import create_engine, text
from config.base_config import settings

def migrate():
    """添加language和lang_confidence字段"""
    engine = create_engine(settings.DATABASE_URL)

    with engine.connect() as conn:
        # 检查字段是否已存在
        result = conn.execute(text("PRAGMA table_info(ai_news)"))
        columns = [row[1] for row in result]

        if 'language' not in columns:
            print("添加language字段...")
            conn.execute(text(
                "ALTER TABLE ai_news ADD COLUMN language VARCHAR(10) DEFAULT 'zh'"
            ))
            conn.commit()
            print("✅ language字段添加成功")
        else:
            print("ℹ️ language字段已存在")

        if 'lang_confidence' not in columns:
            print("添加lang_confidence字段...")
            conn.execute(text(
                "ALTER TABLE ai_news ADD COLUMN lang_confidence FLOAT DEFAULT 0.0"
            ))
            conn.commit()
            print("✅ lang_confidence字段添加成功")
        else:
            print("ℹ️ lang_confidence字段已存在")

    print("✅ 数据库迁移完成")

if __name__ == "__main__":
    migrate()
