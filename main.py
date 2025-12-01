#!/usr/bin/env python3
"""
Notion RAG 系统主程序
用于测试和运行整个 RAG 系统
"""

import os
import sys
from typing import List, Dict, Any
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_environment():
    """设置环境变量（如果未设置）"""
    # 检查必要的环境变量
    required_vars = [
        "NOTION_TOKEN",
        "NOTION_DATABASE_ID", 
        "OPENAI_API_KEY"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"缺少必要的环境变量: {', '.join(missing_vars)}")
        logger.info("请设置以下环境变量:")
        for var in missing_vars:
            logger.info(f"  {var}=your_value")
        return False
    
    return True

def test_notion_connection():
    """测试 Notion 连接"""
    try:
        from notion_data_fetcher import NotionDataFetcher
        
        logger.info("测试 Notion 连接...")
        fetcher = NotionDataFetcher()
        
        # 获取数据库页面
        pages = fetcher.get_database_pages()
        logger.info(f"成功连接到 Notion，获取到 {len(pages)} 个页面")
        
        # 获取第一个页面的内容作为测试
        if pages:
            first_page = pages[0]
            page_content = fetcher.get_page_content(first_page["id"])
            logger.info(f"测试页面: {page_content['title']}")
            
        return True
        
    except Exception as e:
        logger.error(f"Notion 连接测试失败: {e}")
        return False

def test_openai_connection():
    """测试 OpenAI 连接"""
    try:
        from openai import OpenAI
        
        logger.info("测试 OpenAI 连接...")
        client = OpenAI()
        
        # 简单的测试请求
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=10
        )
        
        logger.info("OpenAI 连接测试成功")
        return True
        
    except Exception as e:
        logger.error(f"OpenAI 连接测试失败: {e}")
        return False

def test_vector_store():
    """测试向量存储"""
    try:
        from vector_store import VectorStoreManager
        
        logger.info("测试向量存储...")
        vector_manager = VectorStoreManager()
        
        # 获取统计信息
        stats = vector_manager.get_collection_stats()
        logger.info(f"向量存储统计: {stats}")
        
        return True
        
    except Exception as e:
        logger.error(f"向量存储测试失败: {e}")
        return False

def test_rag_system():
    """测试 RAG 系统"""
    try:
        from rag_system import RAGSystem
        
        logger.info("测试 RAG 系统...")
        rag = RAGSystem()
        
        # 测试系统信息
        system_info = rag.get_system_info()
        logger.info(f"RAG 系统信息: {system_info}")
        
        return True
        
    except Exception as e:
        logger.error(f"RAG 系统测试失败: {e}")
        return False

def run_full_pipeline():
    """运行完整的 RAG 流程"""
    try:
        logger.info("开始运行完整的 RAG 流程...")
        
        # 1. 获取 Notion 数据
        from notion_data_fetcher import NotionDataFetcher
        fetcher = NotionDataFetcher()
        content_list = fetcher.get_all_content()
        
        if not content_list:
            logger.warning("没有获取到任何内容")
            return False
        
        logger.info(f"获取到 {len(content_list)} 个页面内容")
        
        # 2. 处理文档
        from document_processor import DocumentProcessor
        processor = DocumentProcessor()
        documents = processor.process_and_split(
            content_list, 
            save_path="./data/documents/processed_docs.json"
        )
        
        if not documents:
            logger.warning("没有处理出任何文档")
            return False
        
        logger.info(f"处理出 {len(documents)} 个文档块")
        
        # 3. 存储到向量数据库
        from vector_store import VectorStoreManager
        vector_manager = VectorStoreManager()
        success = vector_manager.add_documents(documents)
        
        if not success:
            logger.error("向量存储失败")
            return False
        
        logger.info("文档已存储到向量数据库")
        
        # 4. 测试问答
        from rag_system import RAGSystem
        rag = RAGSystem()
        
        # 测试问题
        test_questions = [
            "这个数据库主要包含什么内容？",
            "有哪些重要的文档？",
            "请总结一下主要内容"
        ]
        
        for question in test_questions:
            logger.info(f"测试问题: {question}")
            result = rag.ask_question(question)
            logger.info(f"回答: {result['answer'][:100]}...")
            logger.info(f"置信度: {result['confidence']}")
            logger.info("---")
        
        return True
        
    except Exception as e:
        logger.error(f"完整流程运行失败: {e}")
        return False

def main():
    """主函数"""
    logger.info("=== Notion RAG 系统测试 ===")
    
    # 1. 检查环境配置
    if not setup_environment():
        logger.error("环境配置检查失败，请先配置必要的环境变量")
        return
    
    # 2. 测试各个组件
    tests = [
        ("Notion 连接", test_notion_connection),
        ("OpenAI 连接", test_openai_connection),
        ("向量存储", test_vector_store),
        ("RAG 系统", test_rag_system)
    ]
    
    all_tests_passed = True
    for test_name, test_func in tests:
        logger.info(f"\n--- 测试 {test_name} ---")
        if not test_func():
            all_tests_passed = False
    
    if not all_tests_passed:
        logger.error("部分测试失败，请检查配置")
        return
    
    # 3. 运行完整流程
    logger.info("\n--- 运行完整 RAG 流程 ---")
    if run_full_pipeline():
        logger.info("✅ 所有测试通过！系统运行正常")
    else:
        logger.error("❌ 完整流程运行失败")

if __name__ == "__main__":
    main() 