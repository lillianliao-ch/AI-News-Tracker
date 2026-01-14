"""
数据源抽象层 - 参考 newsnow 的数据源设计
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import datetime
from loguru import logger
import feedparser
import httpx

class BaseSource(ABC):
    """数据源基类 - 参考 newsnow 的 Source 接口"""

    def __init__(self, config: Dict[str, Any]):
        self.id = config['id']
        self.name = config['name']
        self.home_url = config['home_url']
        self.rss_url = config.get('rss_url')
        self.enabled = config.get('enabled', True)
        self.icon = config.get('icon', '')
        self.category = config.get('category', 'AI')
        self.limit = config.get('limit', 50)  # 数据源限制

    @abstractmethod
    async def get_data(self) -> List[Dict[str, Any]]:
        """获取数据 - 必须实现"""
        pass

    def normalize(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        标准化数据格式

        Args:
            raw_data: 原始数据

        Returns:
            标准化后的数据
        """
        return {
            'id': f"{self.id}_{raw_data.get('id', raw_data.get('link', ''))}",
            'title': raw_data.get('title', ''),
            'url': raw_data.get('link', raw_data.get('url', '')),
            'summary': raw_data.get('summary', raw_data.get('description', '')),
            'content': raw_data.get('content', ''),
            'source': self.name,
            'source_url': self.home_url,
            'category': self.category,
            'icon': self.icon,
            'publish_time': self.parse_time(raw_data.get('published', raw_data.get('time'))),
            'crawl_time': datetime.now(),
            'extra': raw_data
        }

    def parse_time(self, time_str: Any) -> datetime:
        """解析时间"""
        if isinstance(time_str, datetime):
            return time_str

        if not time_str:
            return datetime.now()

        try:
            if isinstance(time_str, str):
                # 尝试多种时间格式
                formats = [
                    '%a, %d %b %Y %H:%M:%S %z',
                    '%a, %d %b %Y %H:%M:%S %Z',
                    '%Y-%m-%dT%H:%M:%S%z',
                    '%Y-%m-%d %H:%M:%S',
                    '%Y-%m-%d'
                ]

                for fmt in formats:
                    try:
                        return datetime.strptime(time_str, fmt)
                    except:
                        continue

            return datetime.now()
        except:
            return datetime.now()


class RSSSource(BaseSource):
    """RSS 数据源 - 安全且稳定"""

    async def get_data(self) -> List[Dict[str, Any]]:
        """从 RSS 获取数据"""
        if not self.enabled:
            logger.info(f"数据源 {self.name} 未启用")
            return []

        if not self.rss_url:
            logger.warning(f"数据源 {self.name} 没有配置 RSS URL")
            return []

        try:
            logger.info(f"开始爬取 {self.name} RSS: {self.rss_url}")

            # 解析 RSS
            feed = feedparser.parse(self.rss_url)

            if not feed or not feed.entries:
                logger.warning(f"RSS {self.name} 解析失败或无数据")
                return []

            results = []
            # 使用配置的limit值
            limit = self.limit if hasattr(self, 'limit') else 50
            logger.info(f"数据源 {self.name} 配置限制: {limit}条")

            for entry in feed.entries[:limit]:
                try:
                    normalized = self.normalize({
                        'id': entry.get('id', entry.get('link')),
                        'title': entry.get('title'),
                        'link': entry.get('link'),
                        'summary': entry.get('summary', ''),
                        'description': entry.get('description', ''),
                        'content': self._extract_content(entry),
                        'published': entry.get('published'),
                        'time': entry.get('updated')
                    })
                    results.append(normalized)
                except Exception as e:
                    logger.error(f"处理条目失败: {e}")
                    continue

            logger.info(f"成功爬取 {self.name} {len(results)} 条数据")
            return results

        except Exception as e:
            logger.error(f"爬取 {self.name} 失败: {e}")
            return []

    def _extract_content(self, entry) -> str:
        """提取内容"""
        # 优先使用 content
        if hasattr(entry, 'content') and entry.content:
            if isinstance(entry.content, list):
                return entry.content[0].get('value', '')
            return entry.content

        # 其次使用 description
        if hasattr(entry, 'description') and entry.description:
            return entry.description

        # 最后使用 summary
        if hasattr(entry, 'summary') and entry.summary:
            return entry.summary

        return ''


class HTTPSource(BaseSource):
    """HTTP API 数据源"""

    async def get_data(self) -> List[Dict[str, Any]]:
        """从 HTTP API 获取数据"""
        if not self.enabled:
            return []

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(self.rss_url)
                response.raise_for_status()

                data = response.json()
                return self._parse_response(data)

        except Exception as e:
            logger.error(f"HTTP 请求失败 {self.name}: {e}")
            return []

    def _parse_response(self, data: Dict) -> List[Dict]:
        """解析响应 - 需要子类实现"""
        raise NotImplementedError


class SourceFactory:
    """数据源工厂"""

    @staticmethod
    def create_source(config: Dict[str, Any]) -> BaseSource:
        """根据配置创建数据源"""
        source_type = config.get('type', 'rss')

        if source_type == 'rss':
            return RSSSource(config)
        elif source_type == 'http':
            return HTTPSource(config)
        else:
            raise ValueError(f"不支持的数据源类型: {source_type}")

    @staticmethod
    def create_all_sources(configs: Dict[str, Dict]) -> List[BaseSource]:
        """创建所有数据源"""
        sources = []
        for source_id, config in configs.items():
            if config.get('enabled', True):
                source = SourceFactory.create_source(config)
                sources.append(source)

        return sources


# 导出
__all__ = [
    'BaseSource',
    'RSSSource',
    'HTTPSource',
    'SourceFactory'
]
