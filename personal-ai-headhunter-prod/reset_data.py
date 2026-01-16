import os
from sqlalchemy import text
from database import SessionLocal, engine, Base

def reset_business_data():
    """
    清空业务数据 (候选人、职位、匹配记录)，保留系统配置 (System Prompts)
    """
    print("⚠️ 警告：此操作将永久删除所有候选人、职位和匹配记录！")
    confirm = input("确认执行？(输入 'yes' 继续): ")
    if confirm != 'yes':
        print("操作已取消")
        return

    session = SessionLocal()
    try:
        # 清空业务表
        print("正在清空 Candidates...")
        session.execute(text("DELETE FROM candidates"))
        print("正在清空 Jobs...")
        session.execute(text("DELETE FROM jobs"))
        print("正在清空 Match Records...")
        session.execute(text("DELETE FROM match_records"))
        
        # 重置自增 ID (SQLite specific)
        session.execute(text("DELETE FROM sqlite_sequence WHERE name IN ('candidates', 'jobs', 'match_records')"))
        
        session.commit()
        print("✅ 业务数据已重置，系统配置保留。")
        
        # 清理向量库 (ChromaDB)
        # 注意：ChromaDB 文件删除比较彻底，建议直接删除目录
        chroma_path = "personal-ai-headhunter/data/chroma_db"
        if os.path.exists(chroma_path):
            import shutil
            shutil.rmtree(chroma_path)
            print("✅ 向量数据库已清空")
            
    except Exception as e:
        session.rollback()
        print(f"❌ 重置失败: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    reset_business_data()







