from database import init_db, engine, Base
import os

def run_migrations():
    """
    简单的数据库迁移脚本。
    在 MVP 阶段，我们主要通过 SQLAlchemy 的 create_all 来创建新表。
    对于字段变更，SQLite 不支持直接 alter column，通常需要重建表。
    这里我们暂时只处理新表创建。
    """
    print(f"Checking database schema at {engine.url}...")
    
    # 创建所有定义的表（如果不存在）
    Base.metadata.create_all(bind=engine)
    
    # 初始化默认数据（如 System Prompts）
    init_db()
    
    print("✅ Database schema and default data initialized.")

if __name__ == "__main__":
    run_migrations()

