import os
from typing import List, Dict, Any, Optional
from notion_client import Client
from config import config
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NotionDataFetcher:
    """Notion 数据获取器"""
    
    def __init__(self):
        """初始化 Notion 客户端"""
        if not config.NOTION_TOKEN:
            raise ValueError("NOTION_TOKEN 未配置")
        
        self.client = Client(auth=config.NOTION_TOKEN)
        self.database_id = config.NOTION_DATABASE_ID
        
    def get_database_pages(self) -> List[Dict[str, Any]]:
        """获取数据库中的所有页面"""
        try:
            pages = []
            query = self.client.databases.query(database_id=self.database_id)
            
            # 获取所有页面
            while True:
                pages.extend(query.get("results", []))
                
                # 检查是否有更多页面
                if not query.get("has_more"):
                    break
                    
                # 获取下一页
                query = self.client.databases.query(
                    database_id=self.database_id,
                    start_cursor=query.get("next_cursor")
                )
            
            logger.info(f"成功获取 {len(pages)} 个页面")
            return pages
            
        except Exception as e:
            logger.error(f"获取数据库页面失败: {e}")
            raise
    
    def get_page_content(self, page_id: str) -> Dict[str, Any]:
        """获取单个页面的详细内容"""
        try:
            # 获取页面基本信息
            page = self.client.pages.retrieve(page_id)
            
            # 获取页面内容块
            blocks = self._get_page_blocks(page_id)
            
            return {
                "page_id": page_id,
                "title": self._extract_title(page),
                "properties": page.get("properties", {}),
                "content": blocks,
                "created_time": page.get("created_time"),
                "last_edited_time": page.get("last_edited_time")
            }
            
        except Exception as e:
            logger.error(f"获取页面内容失败 {page_id}: {e}")
            raise
    
    def _get_page_blocks(self, page_id: str) -> List[Dict[str, Any]]:
        """获取页面的所有内容块"""
        blocks = []
        
        try:
            query = self.client.blocks.children.list(block_id=page_id)
            
            while True:
                blocks.extend(query.get("results", []))
                
                if not query.get("has_more"):
                    break
                    
                query = self.client.blocks.children.list(
                    block_id=page_id,
                    start_cursor=query.get("next_cursor")
                )
            
            return blocks
            
        except Exception as e:
            logger.error(f"获取页面块失败 {page_id}: {e}")
            return []
    
    def _extract_title(self, page: Dict[str, Any]) -> str:
        """从页面属性中提取标题"""
        properties = page.get("properties", {})
        
        # 尝试不同的标题字段
        title_fields = ["title", "Name", "name", "Title"]
        
        for field in title_fields:
            if field in properties:
                prop = properties[field]
                if prop.get("type") == "title":
                    title_parts = prop.get("title", [])
                    if title_parts:
                        return " ".join([part.get("plain_text", "") for part in title_parts])
        
        return "无标题"
    
    def extract_text_from_blocks(self, blocks: List[Dict[str, Any]]) -> str:
        """从内容块中提取纯文本"""
        text_parts = []
        
        for block in blocks:
            block_type = block.get("type")
            
            if block_type == "paragraph":
                text = self._extract_rich_text(block.get("paragraph", {}).get("rich_text", []))
                if text:
                    text_parts.append(text)
                    
            elif block_type == "heading_1":
                text = self._extract_rich_text(block.get("heading_1", {}).get("rich_text", []))
                if text:
                    text_parts.append(f"# {text}")
                    
            elif block_type == "heading_2":
                text = self._extract_rich_text(block.get("heading_2", {}).get("rich_text", []))
                if text:
                    text_parts.append(f"## {text}")
                    
            elif block_type == "heading_3":
                text = self._extract_rich_text(block.get("heading_3", {}).get("rich_text", []))
                if text:
                    text_parts.append(f"### {text}")
                    
            elif block_type == "bulleted_list_item":
                text = self._extract_rich_text(block.get("bulleted_list_item", {}).get("rich_text", []))
                if text:
                    text_parts.append(f"• {text}")
                    
            elif block_type == "numbered_list_item":
                text = self._extract_rich_text(block.get("numbered_list_item", {}).get("rich_text", []))
                if text:
                    text_parts.append(f"1. {text}")
                    
            elif block_type == "quote":
                text = self._extract_rich_text(block.get("quote", {}).get("rich_text", []))
                if text:
                    text_parts.append(f"> {text}")
                    
            elif block_type == "code":
                code_block = block.get("code", {})
                text = self._extract_rich_text(code_block.get("rich_text", []))
                language = code_block.get("language", "")
                if text:
                    text_parts.append(f"```{language}\n{text}\n```")
        
        return "\n\n".join(text_parts)
    
    def _extract_rich_text(self, rich_text: List[Dict[str, Any]]) -> str:
        """从富文本数组中提取纯文本"""
        return " ".join([item.get("plain_text", "") for item in rich_text])
    
    def get_all_content(self) -> List[Dict[str, Any]]:
        """获取所有页面的完整内容"""
        pages = self.get_database_pages()
        content_list = []
        
        for page in pages:
            try:
                page_id = page.get("id")
                page_content = self.get_page_content(page_id)
                
                # 提取文本内容
                text_content = self.extract_text_from_blocks(page_content["content"])
                
                if text_content.strip():  # 只添加有内容的页面
                    content_list.append({
                        "page_id": page_id,
                        "title": page_content["title"],
                        "content": text_content,
                        "created_time": page_content["created_time"],
                        "last_edited_time": page_content["last_edited_time"],
                        "url": page.get("url", "")
                    })
                    
            except Exception as e:
                logger.error(f"处理页面失败 {page.get('id', 'unknown')}: {e}")
                continue
        
        logger.info(f"成功处理 {len(content_list)} 个有内容的页面")
        return content_list 