"""
新闻源引擎抽象基类
定义所有新闻源引擎必须实现的接口
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import date


class NewsSourceEngine(ABC):
    """新闻源引擎抽象基类"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化引擎
        
        Args:
            config: 引擎配置
        """
        self.config = config
    
    @abstractmethod
    async def get_all_sources(self) -> List[Dict[str, Any]]:
        """
        获取所有可用的新闻源列表
        
        Returns:
            新闻源列表，每个新闻源包含:
            {
                "id": "unique_id",          # 唯一标识
                "name": "新闻源名称",
                "category": "分类",
                "description": "描述"
            }
        """
        pass
    
    @abstractmethod
    async def fetch_news(
        self, 
        source_id: str, 
        target_date: date
    ) -> List[Dict[str, Any]]:
        """
        获取指定新闻源在指定日期的新闻列表
        
        Args:
            source_id: 新闻源 ID
            target_date: 目标日期
            
        Returns:
            新闻列表，每篇新闻包含:
            {
                "title": "标题",
                "url": "链接",
                "content": "正文"（可选，如果引擎已提取）,
                "excerpt": "摘要"（可选）,
                "published_at": "发布时间",
                "source_name": "来源名称",
                "source_id": "来源ID"
            }
        """
        pass
    
    @abstractmethod
    def get_categories(self) -> List[str]:
        """
        获取支持的分类列表
        
        Returns:
            分类列表
        """
        pass
    
    def get_engine_name(self) -> str:
        """
        获取引擎名称
        
        Returns:
            引擎名称
        """
        return self.__class__.__name__.replace('Engine', '').lower()
