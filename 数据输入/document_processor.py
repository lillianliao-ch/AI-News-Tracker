import os
import json
from typing import List, Dict, Any, Optional
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from config import config
import logging

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """文档处理器 - 负责文档分块和预处理"""
    
    def __init__(self):
        """初始化文档处理器"""
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.CHUNK_SIZE,
            chunk_overlap=config.CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?", " ", ""]
        )
    
    def process_notion_content(self, content_list: List[Dict[str, Any]]) -> List[Document]:
        """处理 Notion 内容并转换为 LangChain Document 对象"""
        documents = []
        
        for content in content_list:
            try:
                # 创建文档元数据
                metadata = {
                    "page_id": content["page_id"],
                    "title": content["title"],
                    "url": content.get("url", ""),
                    "created_time": content.get("created_time", ""),
                    "last_edited_time": content.get("last_edited_time", ""),
                    "source": "notion"
                }
                
                # 创建 LangChain Document
                doc = Document(
                    page_content=content["content"],
                    metadata=metadata
                )
                
                documents.append(doc)
                
            except Exception as e:
                logger.error(f"处理文档失败: {e}")
                continue
        
        logger.info(f"成功创建 {len(documents)} 个文档")
        return documents
    
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """将文档分割成更小的块"""
        try:
            split_docs = self.text_splitter.split_documents(documents)
            logger.info(f"文档分割完成: {len(documents)} -> {len(split_docs)} 个块")
            return split_docs
            
        except Exception as e:
            logger.error(f"文档分割失败: {e}")
            raise
    
    def save_documents(self, documents: List[Document], filepath: str):
        """保存文档到文件"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # 转换为可序列化的格式
            serializable_docs = []
            for doc in documents:
                serializable_docs.append({
                    "page_content": doc.page_content,
                    "metadata": doc.metadata
                })
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(serializable_docs, f, ensure_ascii=False, indent=2)
            
            logger.info(f"文档已保存到: {filepath}")
            
        except Exception as e:
            logger.error(f"保存文档失败: {e}")
            raise
    
    def load_documents(self, filepath: str) -> List[Document]:
        """从文件加载文档"""
        try:
            if not os.path.exists(filepath):
                logger.warning(f"文档文件不存在: {filepath}")
                return []
            
            with open(filepath, 'r', encoding='utf-8') as f:
                serializable_docs = json.load(f)
            
            documents = []
            for doc_data in serializable_docs:
                doc = Document(
                    page_content=doc_data["page_content"],
                    metadata=doc_data["metadata"]
                )
                documents.append(doc)
            
            logger.info(f"从 {filepath} 加载了 {len(documents)} 个文档")
            return documents
            
        except Exception as e:
            logger.error(f"加载文档失败: {e}")
            raise
    
    def get_document_stats(self, documents: List[Document]) -> Dict[str, Any]:
        """获取文档统计信息"""
        if not documents:
            return {"total_docs": 0, "total_chars": 0, "avg_chars": 0}
        
        total_chars = sum(len(doc.page_content) for doc in documents)
        avg_chars = total_chars / len(documents)
        
        # 统计来源
        sources = {}
        for doc in documents:
            source = doc.metadata.get("source", "unknown")
            sources[source] = sources.get(source, 0) + 1
        
        return {
            "total_docs": len(documents),
            "total_chars": total_chars,
            "avg_chars": round(avg_chars, 2),
            "sources": sources
        }
    
    def filter_documents(self, documents: List[Document], 
                        min_length: int = 10,
                        max_length: int = 10000) -> List[Document]:
        """过滤文档（按长度）"""
        filtered_docs = []
        
        for doc in documents:
            content_length = len(doc.page_content)
            if min_length <= content_length <= max_length:
                filtered_docs.append(doc)
        
        logger.info(f"文档过滤: {len(documents)} -> {len(filtered_docs)}")
        return filtered_docs
    
    def clean_content(self, text: str) -> str:
        """清理文本内容"""
        import re
        
        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text)
        
        # 移除特殊字符（保留中文、英文、数字、标点）
        text = re.sub(r'[^\w\s\u4e00-\u9fff.,!?;:()\[\]{}"\'-]', '', text)
        
        # 移除空行
        text = re.sub(r'\n\s*\n', '\n', text)
        
        return text.strip()
    
    def process_and_split(self, content_list: List[Dict[str, Any]], 
                         save_path: Optional[str] = None) -> List[Document]:
        """完整的处理流程：处理内容 -> 分块 -> 过滤 -> 保存"""
        
        # 1. 处理 Notion 内容
        logger.info("开始处理 Notion 内容...")
        documents = self.process_notion_content(content_list)
        
        # 2. 清理内容
        logger.info("清理文档内容...")
        for doc in documents:
            doc.page_content = self.clean_content(doc.page_content)
        
        # 3. 过滤空文档
        documents = [doc for doc in documents if doc.page_content.strip()]
        
        # 4. 分割文档
        logger.info("分割文档...")
        split_docs = self.split_documents(documents)
        
        # 5. 过滤过短或过长的块
        logger.info("过滤文档块...")
        filtered_docs = self.filter_documents(split_docs)
        
        # 6. 保存文档（如果指定了路径）
        if save_path:
            self.save_documents(filtered_docs, save_path)
        
        # 7. 输出统计信息
        stats = self.get_document_stats(filtered_docs)
        logger.info(f"处理完成，统计信息: {stats}")
        
        return filtered_docs 