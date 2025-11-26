"""
TopHub 新闻源引擎实现
"""

import aiohttp
from typing import List, Dict, Any, Optional
from datetime import date
from loguru import logger

from .base import NewsSourceEngine


class TopHubEngine(NewsSourceEngine):
    """TopHub 新闻源引擎"""
    
    # TopHub 分类映射
    CATEGORIES = {
        1: "综合",
        2: "科技",
        3: "娱乐",
        4: "社区",
        5: "购物",
        6: "财经",
        7: "开发者",
        8: "大学",
        9: "政务",
        10: "博客专栏",
        11: "微信公众号",
        12: "电子报",
        13: "设计",
        0: "其他",
        -1: "小工具"
    }
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get('api_key')
        self.base_url = config.get('base_url', 'https://api.tophubdata.com')
        self.timeout = config.get('timeout', 30)
        self.max_retries = config.get('max_retries', 3)
        self.allowed_sources = config.get('allowed_sources', [])
        
        if not self.api_key:
            raise ValueError("TopHub API Key 未配置")
        
        logger.info(f"TopHub 引擎已初始化: {self.base_url}")
    
    async def get_all_sources(self) -> List[Dict[str, Any]]:
        """
        获取所有 TopHub 榜单列表
        
        Returns:
            榜单列表
        """
        all_sources = []
        page = 1
        
        async with aiohttp.ClientSession() as session:
            while True:
                url = f"{self.base_url}/nodes"
                params = {'p': page}
                headers = {'Authorization': self.api_key}
                
                try:
                    async with session.get(
                        url, 
                        params=params, 
                        headers=headers,
                        timeout=self.timeout
                    ) as response:
                        if response.status != 200:
                            logger.error(f"获取榜单列表失败: HTTP {response.status}")
                            break
                        
                        data = await response.json()
                        
                        if data.get('error'):
                            logger.error(f"API 返回错误: {data}")
                            break
                        
                        nodes = data.get('data', [])
                        
                        if not nodes:
                            break
                        
                        # 转换为统一格式
                        for node in nodes:
                            # 如果配置了白名单，只返回白名单中的源
                            if self.allowed_sources and node['hashid'] not in self.allowed_sources:
                                continue
                            
                            source = {
                                'id': node['hashid'],
                                'name': node['name'],
                                'display': node.get('display', ''),
                                'category': self.CATEGORIES.get(node.get('cid'), '其他'),
                                'domain': node.get('domain', ''),
                                'description': f"{node['name']} - {node.get('display', '')}"
                            }
                            all_sources.append(source)
                        
                        # 如果返回数量 < 100，说明已经是最后一页
                        if len(nodes) < 100:
                            break
                        
                        page += 1
                
                except Exception as e:
                    logger.error(f"获取榜单列表异常: {str(e)}")
                    break
        
        logger.info(f"获取到 {len(all_sources)} 个 TopHub 榜单")
        return all_sources
    
    async def fetch_news(
        self, 
        source_id: str, 
        target_date: date
    ) -> List[Dict[str, Any]]:
        """
        获取指定榜单在指定日期的新闻
        
        Args:
            source_id: 榜单 hashid
            target_date: 目标日期
            
        Returns:
            新闻列表
        """
        url = f"{self.base_url}/nodes/{source_id}/historys"
        params = {'date': target_date.strftime('%Y-%m-%d')}
        headers = {'Authorization': self.api_key}
        
        news_list = []
        
        async with aiohttp.ClientSession() as session:
            for attempt in range(self.max_retries):
                try:
                    async with session.get(
                        url,
                        params=params,
                        headers=headers,
                        timeout=self.timeout
                    ) as response:
                        if response.status != 200:
                            logger.warning(
                                f"获取新闻失败 ({source_id}): HTTP {response.status}, "
                                f"尝试 {attempt + 1}/{self.max_retries}"
                            )
                            continue
                        
                        data = await response.json()
                        
                        if data.get('error'):
                            logger.error(f"API 返回错误: {data}")
                            break
                        
                        items = data.get('data', [])
                        
                        # 转换为统一格式
                        for item in items:
                            news = {
                                'title': item.get('title', ''),
                                'url': item.get('url', ''),
                                'content': None,  # TopHub 不提供正文，需要后续提取
                                'excerpt': item.get('description', ''),
                                'published_at': item.get('time'),  # Unix 时间戳
                                'source_name': '',  # 需要从 source 信息补充
                                'source_id': source_id,
                                'extra': item.get('extra', '')  # 热度等额外信息
                            }
                            news_list.append(news)
                        
                        logger.success(
                            f"成功获取 {len(news_list)} 条新闻 "
                            f"({source_id}, {target_date})"
                        )
                        break
                
                except Exception as e:
                    logger.error(
                        f"获取新闻异常 ({source_id}): {str(e)}, "
                        f"尝试 {attempt + 1}/{self.max_retries}"
                    )
                    
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(1)
        
        return news_list
    
    def get_categories(self) -> List[str]:
        """获取支持的分类"""
        return list(set(self.CATEGORIES.values()))


# 需要导入 asyncio
import asyncio
