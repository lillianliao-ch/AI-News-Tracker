#!/usr/bin/env python3
"""
Notion RAG 系统 API 服务器
提供 Web API 接口
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn
import logging
from datetime import datetime

# 导入我们的模块
from rag_system import RAGSystem
from notion_data_fetcher import NotionDataFetcher
from document_processor import DocumentProcessor
from vector_store import VectorStoreManager
from config import config

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建 FastAPI 应用
app = FastAPI(
    title="Notion RAG API",
    description="基于 Notion 的检索增强生成系统 API",
    version="1.0.0"
)

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局变量
rag_system = None
vector_manager = None

# Pydantic 模型
class QuestionRequest(BaseModel):
    question: str
    k: int = 5
    use_compression: bool = False

class QuestionResponse(BaseModel):
    question: str
    answer: str
    sources: List[Dict[str, Any]]
    confidence: str
    document_count: int
    timestamp: str

class SyncRequest(BaseModel):
    force_sync: bool = False

class SyncResponse(BaseModel):
    success: bool
    message: str
    document_count: int
    timestamp: str

class SystemInfoResponse(BaseModel):
    system_info: Dict[str, Any]
    vector_store_stats: Dict[str, Any]
    config_info: Dict[str, Any]

@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化"""
    global rag_system, vector_manager
    
    try:
        # 验证配置
        if not config.validate():
            logger.error("配置验证失败")
            return
        
        # 创建必要的目录
        config.create_directories()
        
        # 初始化组件
        vector_manager = VectorStoreManager()
        rag_system = RAGSystem()
        
        logger.info("API 服务器初始化完成")
        
    except Exception as e:
        logger.error(f"API 服务器初始化失败: {e}")

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Notion RAG API 服务运行中",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    try:
        if not rag_system:
            raise HTTPException(status_code=503, detail="RAG 系统未初始化")
        
        # 测试连接
        test_result = rag_system.test_connection()
        
        return {
            "status": "healthy" if test_result.get("success") else "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "details": test_result
        }
        
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"健康检查失败: {str(e)}")

@app.get("/system/info", response_model=SystemInfoResponse)
async def get_system_info():
    """获取系统信息"""
    try:
        if not rag_system or not vector_manager:
            raise HTTPException(status_code=503, detail="系统未初始化")
        
        system_info = rag_system.get_system_info()
        vector_stats = vector_manager.get_collection_stats()
        
        config_info = {
            "chunk_size": config.CHUNK_SIZE,
            "chunk_overlap": config.CHUNK_OVERLAP,
            "embedding_model": config.EMBEDDING_MODEL,
            "openai_model": config.OPENAI_MODEL
        }
        
        return SystemInfoResponse(
            system_info=system_info,
            vector_store_stats=vector_stats,
            config_info=config_info
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取系统信息失败: {str(e)}")

@app.post("/question", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    """提问接口"""
    try:
        if not rag_system:
            raise HTTPException(status_code=503, detail="RAG 系统未初始化")
        
        # 提问
        result = rag_system.ask_question(
            question=request.question,
            k=request.k,
            use_compression=request.use_compression
        )
        
        # 添加时间戳
        result["timestamp"] = datetime.now().isoformat()
        
        return QuestionResponse(**result)
        
    except Exception as e:
        logger.error(f"提问失败: {e}")
        raise HTTPException(status_code=500, detail=f"提问失败: {str(e)}")

@app.post("/question/with-sources", response_model=QuestionResponse)
async def ask_question_with_sources(request: QuestionRequest):
    """带详细源信息的提问接口"""
    try:
        if not rag_system:
            raise HTTPException(status_code=503, detail="RAG 系统未初始化")
        
        # 提问（带源信息）
        result = rag_system.ask_with_sources(
            question=request.question,
            k=request.k
        )
        
        # 添加时间戳
        result["timestamp"] = datetime.now().isoformat()
        
        return QuestionResponse(**result)
        
    except Exception as e:
        logger.error(f"提问失败: {e}")
        raise HTTPException(status_code=500, detail=f"提问失败: {str(e)}")

@app.post("/question/batch")
async def batch_ask_questions(questions: List[str], k: int = 5):
    """批量提问接口"""
    try:
        if not rag_system:
            raise HTTPException(status_code=503, detail="RAG 系统未初始化")
        
        # 批量提问
        results = rag_system.batch_ask(questions, k=k)
        
        return {
            "results": results,
            "total_questions": len(questions),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"批量提问失败: {e}")
        raise HTTPException(status_code=500, detail=f"批量提问失败: {str(e)}")

@app.post("/sync", response_model=SyncResponse)
async def sync_notion_data(background_tasks: BackgroundTasks, request: SyncRequest = SyncRequest()):
    """同步 Notion 数据"""
    try:
        # 在后台任务中执行同步
        background_tasks.add_task(sync_notion_data_task, request.force_sync)
        
        return SyncResponse(
            success=True,
            message="数据同步已开始，请稍后查看状态",
            document_count=0,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"启动同步任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"启动同步失败: {str(e)}")

async def sync_notion_data_task(force_sync: bool = False):
    """后台同步任务"""
    try:
        logger.info("开始同步 Notion 数据...")
        
        # 1. 获取 Notion 数据
        fetcher = NotionDataFetcher()
        content_list = fetcher.get_all_content()
        
        if not content_list:
            logger.warning("没有获取到任何内容")
            return
        
        logger.info(f"获取到 {len(content_list)} 个页面内容")
        
        # 2. 处理文档
        processor = DocumentProcessor()
        documents = processor.process_and_split(
            content_list,
            save_path="./data/documents/processed_docs.json"
        )
        
        if not documents:
            logger.warning("没有处理出任何文档")
            return
        
        logger.info(f"处理出 {len(documents)} 个文档块")
        
        # 3. 存储到向量数据库
        if force_sync:
            # 强制同步：重置向量存储
            vector_manager.reset_vector_store()
        
        success = vector_manager.add_documents(documents)
        
        if success:
            logger.info("数据同步完成")
        else:
            logger.error("数据同步失败")
            
    except Exception as e:
        logger.error(f"同步任务失败: {e}")

@app.get("/search")
async def search_documents(query: str, k: int = 5, with_scores: bool = False):
    """文档搜索接口"""
    try:
        if not vector_manager:
            raise HTTPException(status_code=503, detail="向量存储未初始化")
        
        if with_scores:
            results = vector_manager.similarity_search_with_score(query, k=k)
            # 转换结果格式
            formatted_results = []
            for doc, score in results:
                formatted_results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": score
                })
        else:
            results = vector_manager.similarity_search(query, k=k)
            formatted_results = [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata
                }
                for doc in results
            ]
        
        return {
            "query": query,
            "results": formatted_results,
            "count": len(formatted_results),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"文档搜索失败: {e}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")

@app.delete("/vector-store/reset")
async def reset_vector_store():
    """重置向量存储"""
    try:
        if not vector_manager:
            raise HTTPException(status_code=503, detail="向量存储未初始化")
        
        success = vector_manager.reset_vector_store()
        
        if success:
            return {"message": "向量存储已重置", "success": True}
        else:
            raise HTTPException(status_code=500, detail="重置向量存储失败")
            
    except Exception as e:
        logger.error(f"重置向量存储失败: {e}")
        raise HTTPException(status_code=500, detail=f"重置失败: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        "api_server:app",
        host=config.HOST,
        port=config.PORT,
        reload=True,
        log_level="info"
    ) 