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

