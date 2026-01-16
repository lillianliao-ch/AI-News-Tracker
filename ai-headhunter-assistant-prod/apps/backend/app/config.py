"""
配置管理
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""
    
    # 基础配置
    APP_NAME: str = "AI Headhunter API"
    APP_VERSION: str = "1.0.0-mvp"
    DEBUG: bool = True
    
    # API 配置
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # AI 配置
    AI_PROVIDER: str = "qwen"  # qwen | openai
    AI_MODEL: str = "qwen-turbo"
    AI_API_KEY: str = ""  # 从环境变量读取
    
    # 飞书配置
    FEISHU_APP_ID: str = ""  # 飞书应用 ID
    FEISHU_APP_SECRET: str = ""  # 飞书应用密钥
    FEISHU_APP_TOKEN: str = ""  # 飞书多维表格 App Token
    FEISHU_TABLE_ID: str = ""  # 飞书具体表格 ID
    FEISHU_ENABLED: bool = False  # 是否启用飞书集成
    
    # CORS 配置
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "chrome-extension://*",
        "*"  # MVP 阶段允许所有来源
    ]
    
    # 数据目录
    DATA_DIR: str = "data"
    RESUME_DIR: str = "data/resumes"
    CACHE_DIR: str = "data/cache"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 全局配置实例
settings = Settings()


def get_ai_api_key() -> str:
    """获取 AI API Key"""
    # 优先从环境变量读取
    api_key = os.getenv("AI_API_KEY") or settings.AI_API_KEY
    
    if not api_key:
        raise ValueError(
            "AI API Key 未配置！请设置环境变量 AI_API_KEY 或在 .env 文件中配置"
        )
    
    return api_key


def get_ai_config() -> dict:
    """获取 AI 配置"""
    return {
        "provider": settings.AI_PROVIDER,
        "model": settings.AI_MODEL,
        "api_key": get_ai_api_key()
    }


def get_feishu_config() -> dict:
    """获取飞书配置"""
    app_id = os.getenv("FEISHU_APP_ID") or settings.FEISHU_APP_ID
    app_secret = os.getenv("FEISHU_APP_SECRET") or settings.FEISHU_APP_SECRET
    app_token = os.getenv("FEISHU_APP_TOKEN") or settings.FEISHU_APP_TOKEN
    table_id = os.getenv("FEISHU_TABLE_ID") or settings.FEISHU_TABLE_ID
    
    return {
        "app_id": app_id,
        "app_secret": app_secret,
        "app_token": app_token,
        "table_id": table_id,
        "enabled": settings.FEISHU_ENABLED and bool(app_id) and bool(app_secret) and bool(app_token)
    }

