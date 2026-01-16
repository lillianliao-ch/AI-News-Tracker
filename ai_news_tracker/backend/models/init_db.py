"""
数据库初始化脚本
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.database import Base
from config.base_config import settings

def init_db():
    """初始化数据库"""
    # 创建同步引擎
    engine = create_engine(
        settings.DATABASE_URL,
        echo=True
    )

    # 创建所有表
    Base.metadata.create_all(engine)
    print("✅ 数据库表创建成功")

    # 创建会话工厂
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal

if __name__ == "__main__":
    init_db()
