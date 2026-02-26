import os
import json
from typing import List, Dict, Any, Optional, Tuple
import chromadb
from chromadb.config import Settings
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document
from config import config
import logging

logger = logging.getLogger(__name__)

class VectorStoreManager:
    """向量数据库管理器"""
    
    def __init__(self):
        """初始化向量数据库管理器"""
        self.vector_db_path = config.VECTOR_DB_PATH
        self.embedding_model = config.EMBEDDING_MODEL
        
        # 确保目录存在
        os.makedirs(self.vector_db_path, exist_ok=True)
        
        # 初始化嵌入模型
        self.embeddings = HuggingFaceEmbeddings(
            model_name=self.embedding_model,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # 初始化 ChromaDB 客户端
        self.chroma_client = chromadb.PersistentClient(
            path=self.vector_db_path,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # 初始化 LangChain 向量存储
        self.vector_store = None
        self._initialize_vector_store()
    
    def _initialize_vector_store(self):
        """初始化向量存储"""
        try:
            # 检查是否已存在集合
            collections = self.chroma_client.list_collections()
            collection_name = "notion_documents"
            
            if any(col.name == collection_name for col in collections):
                # 使用现有集合
                self.vector_store = Chroma(
                    client=self.chroma_client,
                    collection_name=collection_name,
                    embedding_function=self.embeddings
                )
                logger.info(f"使用现有向量存储: {collection_name}")
            else:
                # 创建新集合
                self.vector_store = Chroma(
                    client=self.chroma_client,
                    collection_name=collection_name,
                    embedding_function=self.embeddings
                )
                logger.info(f"创建新的向量存储: {collection_name}")
                
        except Exception as e:
            logger.error(f"初始化向量存储失败: {e}")
            raise
    
    def add_documents(self, documents: List[Document]) -> bool:
        """添加文档到向量数据库"""
        try:
            if not documents:
                logger.warning("没有文档需要添加")
                return False
            
            # 添加文档到向量存储
            self.vector_store.add_documents(documents)
            
            logger.info(f"成功添加 {len(documents)} 个文档到向量数据库")
            return True
            
        except Exception as e:
            logger.error(f"添加文档到向量数据库失败: {e}")
            return False
    
    def similarity_search(self, query: str, k: int = 5, 
                         filter_dict: Optional[Dict[str, Any]] = None) -> List[Document]:
        """相似性搜索"""
        try:
            results = self.vector_store.similarity_search(
                query=query,
                k=k,
                filter=filter_dict
            )
            
            logger.info(f"相似性搜索完成，返回 {len(results)} 个结果")
            return results
            
        except Exception as e:
            logger.error(f"相似性搜索失败: {e}")
            return []
    
    def similarity_search_with_score(self, query: str, k: int = 5,
                                   filter_dict: Optional[Dict[str, Any]] = None) -> List[Tuple[Document, float]]:
        """带分数的相似性搜索"""
        try:
            results = self.vector_store.similarity_search_with_score(
                query=query,
                k=k,
                filter=filter_dict
            )
            
            logger.info(f"带分数的相似性搜索完成，返回 {len(results)} 个结果")
            return results
            
        except Exception as e:
            logger.error(f"带分数的相似性搜索失败: {e}")
            return []
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """获取集合统计信息"""
        try:
            collection = self.chroma_client.get_collection("notion_documents")
            count = collection.count()
            
            return {
                "collection_name": "notion_documents",
                "document_count": count,
                "embedding_model": self.embedding_model,
                "vector_db_path": self.vector_db_path
            }
            
        except Exception as e:
            logger.error(f"获取集合统计信息失败: {e}")
            return {}
    
    def delete_collection(self) -> bool:
        """删除向量数据库集合"""
        try:
            self.chroma_client.delete_collection("notion_documents")
            logger.info("向量数据库集合已删除")
            return True
            
        except Exception as e:
            logger.error(f"删除向量数据库集合失败: {e}")
            return False
    
    def reset_vector_store(self) -> bool:
        """重置向量存储"""
        try:
            # 删除现有集合
            self.delete_collection()
            
            # 重新初始化
            self._initialize_vector_store()
            
            logger.info("向量存储已重置")
            return True
            
        except Exception as e:
            logger.error(f"重置向量存储失败: {e}")
            return False
    
    def search_by_metadata(self, metadata_filter: Dict[str, Any], 
                          query: str = "", k: int = 5) -> List[Document]:
        """根据元数据过滤搜索"""
        try:
            if query:
                results = self.vector_store.similarity_search(
                    query=query,
                    k=k,
                    filter=metadata_filter
                )
            else:
                # 如果没有查询，获取所有匹配的文档
                results = self.vector_store.get(
                    filter=metadata_filter
                )
                # 转换为 Document 对象
                results = [
                    Document(
                        page_content=result["documents"][i],
                        metadata=result["metadatas"][i]
                    )
                    for i in range(len(result["documents"]))
                ]
            
            logger.info(f"元数据过滤搜索完成，返回 {len(results)} 个结果")
            return results
            
        except Exception as e:
            logger.error(f"元数据过滤搜索失败: {e}")
            return []
    
    def get_document_by_id(self, document_id: str) -> Optional[Document]:
        """根据文档ID获取文档"""
        try:
            results = self.vector_store.get(
                ids=[document_id]
            )
            
            if results["documents"]:
                return Document(
                    page_content=results["documents"][0],
                    metadata=results["metadatas"][0]
                )
            
            return None
            
        except Exception as e:
            logger.error(f"根据ID获取文档失败: {e}")
            return None
    
    def update_document(self, document_id: str, new_content: str, 
                       new_metadata: Optional[Dict[str, Any]] = None) -> bool:
        """更新文档"""
        try:
            # 获取现有元数据
            existing_doc = self.get_document_by_id(document_id)
            if not existing_doc:
                logger.warning(f"文档不存在: {document_id}")
                return False
            
            # 合并元数据
            metadata = existing_doc.metadata.copy()
            if new_metadata:
                metadata.update(new_metadata)
            
            # 删除旧文档
            self.vector_store.delete(ids=[document_id])
            
            # 添加新文档
            new_doc = Document(
                page_content=new_content,
                metadata=metadata
            )
            self.vector_store.add_documents([new_doc])
            
            logger.info(f"文档已更新: {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"更新文档失败: {e}")
            return False
    
    def export_metadata(self, filepath: str) -> bool:
        """导出元数据到文件"""
        try:
            collection = self.chroma_client.get_collection("notion_documents")
            results = collection.get()
            
            metadata_list = []
            for i, metadata in enumerate(results["metadatas"]):
                metadata_list.append({
                    "id": results["ids"][i],
                    "metadata": metadata,
                    "content_preview": results["documents"][i][:100] + "..." if len(results["documents"][i]) > 100 else results["documents"][i]
                })
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(metadata_list, f, ensure_ascii=False, indent=2)
            
            logger.info(f"元数据已导出到: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"导出元数据失败: {e}")
            return False 