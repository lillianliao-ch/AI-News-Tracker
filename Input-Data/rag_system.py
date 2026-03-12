import os
from typing import List, Dict, Any, Optional, Tuple
from langchain_community.chat_models import ChatOpenAI
from langchain.schema import Document, HumanMessage, SystemMessage
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate
from langchain.chains import RetrievalQA
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor
from vector_store import VectorStoreManager
from config import config
import logging

logger = logging.getLogger(__name__)

class RAGSystem:
    """RAG 检索增强生成系统"""
    
    def __init__(self):
        """初始化 RAG 系统"""
        if not config.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY 未配置")
        
        # 初始化 LLM
        self.llm = ChatOpenAI(
            model_name=config.OPENAI_MODEL,
            temperature=0.1,
            max_tokens=1000
        )
        
        # 初始化向量存储管理器
        self.vector_store_manager = VectorStoreManager()
        
        # 初始化检索器
        self.retriever = self.vector_store_manager.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 5}
        )
        
        # 初始化上下文压缩器（可选）
        self.compressor = LLMChainExtractor.from_llm(self.llm)
        self.compression_retriever = ContextualCompressionRetriever(
            base_retriever=self.retriever,
            base_compressor=self.compressor
        )
        
        # 定义提示模板
        self._setup_prompts()
    
    def _setup_prompts(self):
        """设置提示模板"""
        # 系统提示
        self.system_prompt = """你是一个专业的助手，基于提供的文档内容来回答问题。

请遵循以下原则：
1. 只基于提供的文档内容回答问题，不要编造信息
2. 如果文档中没有相关信息，请明确说明
3. 回答要准确、简洁、有用
4. 如果问题涉及多个文档片段，请整合信息给出完整回答
5. 保持客观和中立的语调

文档内容：
{context}

问题：{question}

请基于上述文档内容回答问题："""

        # 创建提示模板
        self.prompt_template = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(self.system_prompt),
            HumanMessagePromptTemplate.from_template("{question}")
        ])
    
    def search_documents(self, query: str, k: int = 5, 
                        use_compression: bool = False) -> List[Document]:
        """搜索相关文档"""
        try:
            if use_compression:
                results = self.compression_retriever.get_relevant_documents(query)
            else:
                results = self.retriever.get_relevant_documents(query)
            
            logger.info(f"文档搜索完成，返回 {len(results)} 个相关文档")
            return results
            
        except Exception as e:
            logger.error(f"文档搜索失败: {e}")
            return []
    
    def search_with_scores(self, query: str, k: int = 5) -> List[Tuple[Document, float]]:
        """带相似度分数的文档搜索"""
        try:
            results = self.vector_store_manager.similarity_search_with_score(query, k=k)
            logger.info(f"带分数的文档搜索完成，返回 {len(results)} 个结果")
            return results
            
        except Exception as e:
            logger.error(f"带分数的文档搜索失败: {e}")
            return []
    
    def generate_answer(self, query: str, documents: List[Document]) -> Dict[str, Any]:
        """基于文档生成答案"""
        try:
            if not documents:
                return {
                    "answer": "抱歉，我没有找到相关的文档信息来回答这个问题。",
                    "sources": [],
                    "confidence": "low"
                }
            
            # 合并文档内容
            context = "\n\n".join([doc.page_content for doc in documents])
            
            # 创建消息
            messages = [
                SystemMessage(content=self.system_prompt.format(context=context, question=query)),
                HumanMessage(content=query)
            ]
            
            # 生成回答
            response = self.llm(messages)
            answer = response.content
            
            # 准备源文档信息
            sources = []
            for doc in documents:
                source_info = {
                    "title": doc.metadata.get("title", "未知标题"),
                    "url": doc.metadata.get("url", ""),
                    "page_id": doc.metadata.get("page_id", ""),
                    "content_preview": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
                }
                sources.append(source_info)
            
            return {
                "answer": answer,
                "sources": sources,
                "confidence": "high" if len(documents) > 0 else "low",
                "document_count": len(documents)
            }
            
        except Exception as e:
            logger.error(f"生成答案失败: {e}")
            return {
                "answer": f"生成答案时出现错误: {str(e)}",
                "sources": [],
                "confidence": "error"
            }
    
    def ask_question(self, question: str, k: int = 5, 
                    use_compression: bool = False) -> Dict[str, Any]:
        """完整的问答流程"""
        try:
            # 1. 搜索相关文档
            documents = self.search_documents(question, k=k, use_compression=use_compression)
            
            # 2. 生成答案
            result = self.generate_answer(question, documents)
            
            # 3. 添加查询信息
            result["question"] = question
            result["search_k"] = k
            result["use_compression"] = use_compression
            
            logger.info(f"问答完成: {question[:50]}...")
            return result
            
        except Exception as e:
            logger.error(f"问答流程失败: {e}")
            return {
                "question": question,
                "answer": f"处理问题时出现错误: {str(e)}",
                "sources": [],
                "confidence": "error"
            }
    
    def ask_with_sources(self, question: str, k: int = 5) -> Dict[str, Any]:
        """带详细源信息的问答"""
        try:
            # 搜索带分数的文档
            search_results = self.search_with_scores(question, k=k)
            
            if not search_results:
                return {
                    "question": question,
                    "answer": "抱歉，我没有找到相关的文档信息来回答这个问题。",
                    "sources": [],
                    "confidence": "low"
                }
            
            # 提取文档和分数
            documents = [doc for doc, score in search_results]
            scores = [score for doc, score in search_results]
            
            # 生成答案
            result = self.generate_answer(question, documents)
            
            # 添加分数信息
            for i, source in enumerate(result["sources"]):
                source["similarity_score"] = scores[i]
            
            result["question"] = question
            result["search_k"] = k
            result["average_score"] = sum(scores) / len(scores) if scores else 0
            
            return result
            
        except Exception as e:
            logger.error(f"带源信息的问答失败: {e}")
            return {
                "question": question,
                "answer": f"处理问题时出现错误: {str(e)}",
                "sources": [],
                "confidence": "error"
            }
    
    def batch_ask(self, questions: List[str], k: int = 5) -> List[Dict[str, Any]]:
        """批量问答"""
        results = []
        
        for question in questions:
            try:
                result = self.ask_question(question, k=k)
                results.append(result)
            except Exception as e:
                logger.error(f"批量问答中处理问题失败: {question[:50]}... - {e}")
                results.append({
                    "question": question,
                    "answer": f"处理失败: {str(e)}",
                    "sources": [],
                    "confidence": "error"
                })
        
        return results
    
    def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        vector_stats = self.vector_store_manager.get_collection_stats()
        
        return {
            "model": config.OPENAI_MODEL,
            "embedding_model": config.EMBEDDING_MODEL,
            "vector_store_stats": vector_stats,
            "chunk_size": config.CHUNK_SIZE,
            "chunk_overlap": config.CHUNK_OVERLAP
        }
    
    def update_retriever_settings(self, k: int = 5, search_type: str = "similarity"):
        """更新检索器设置"""
        try:
            self.retriever = self.vector_store_manager.vector_store.as_retriever(
                search_type=search_type,
                search_kwargs={"k": k}
            )
            
            # 更新压缩检索器
            self.compression_retriever = ContextualCompressionRetriever(
                base_retriever=self.retriever,
                base_compressor=self.compressor
            )
            
            logger.info(f"检索器设置已更新: k={k}, search_type={search_type}")
            
        except Exception as e:
            logger.error(f"更新检索器设置失败: {e}")
    
    def test_connection(self) -> Dict[str, Any]:
        """测试系统连接"""
        results = {
            "openai_connection": False,
            "vector_store_connection": False,
            "overall_status": "failed"
        }
        
        # 测试 OpenAI 连接
        try:
            test_response = self.llm([HumanMessage(content="Hello")])
            results["openai_connection"] = True
        except Exception as e:
            results["openai_error"] = str(e)
        
        # 测试向量存储连接
        try:
            stats = self.vector_store_manager.get_collection_stats()
            results["vector_store_connection"] = True
            results["vector_store_stats"] = stats
        except Exception as e:
            results["vector_store_error"] = str(e)
        
        # 整体状态
        if results["openai_connection"] and results["vector_store_connection"]:
            results["overall_status"] = "success"
        
        return results 