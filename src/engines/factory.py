"""
新闻源引擎工厂
负责根据配置创建对应的引擎实例
"""

from typing import Dict, Any
from loguru import logger

from .base import NewsSourceEngine
from .tophub_engine import TopHubEngine


class EngineFactory:
    """新闻源引擎工厂"""
    
    # 注册的引擎类
    _engines = {
        'tophub': TopHubEngine,
        # 未来可以添加更多引擎
        # 'newsapi': NewsAPIEngine,
        # 'custom_rss': CustomRSSEngine,
    }
    
    @classmethod
    def create_engine(cls, config: Dict[str, Any]) -> NewsSourceEngine:
        """
        根据配置创建引擎实例
        
        Args:
            config: 完整配置字典
            
        Returns:
            引擎实例
            
        Raises:
            ValueError: 引擎未启用或不存在
        """
        news_sources_config = config.get('news_sources', {})
        active_engine = news_sources_config.get('active_engine')
        
        if not active_engine:
            raise ValueError("未指定活跃的新闻源引擎")
        
        engines_config = news_sources_config.get('engines', {})
        engine_config = engines_config.get(active_engine)
        
        if not engine_config:
            raise ValueError(f"引擎 {active_engine} 配置不存在")
        
        if not engine_config.get('enabled', False):
            raise ValueError(f"引擎 {active_engine} 未启用")
        
        engine_class = cls._engines.get(active_engine)
        
        if not engine_class:
            raise ValueError(
                f"未知的引擎: {active_engine}。"
                f"可用引擎: {list(cls._engines.keys())}"
            )
        
        logger.info(f"创建引擎实例: {active_engine}")
        return engine_class(engine_config)
    
    @classmethod
    def register_engine(cls, name: str, engine_class: type):
        """
        注册新的引擎类
        
        Args:
            name: 引擎名称
            engine_class: 引擎类
        """
        if not issubclass(engine_class, NewsSourceEngine):
            raise TypeError(f"{engine_class} 必须继承自 NewsSourceEngine")
        
        cls._engines[name] = engine_class
        logger.info(f"注册新引擎: {name}")
    
    @classmethod
    def list_engines(cls) -> list:
        """列出所有可用的引擎"""
        return list(cls._engines.keys())
