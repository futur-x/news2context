"""
TopHub API 数据获取模块
负责从 TopHub Data API 获取新闻源数据
"""

import asyncio
import os
from typing import List, Dict, Any, Optional
from loguru import logger
import aiohttp
from dotenv import load_dotenv

# 加载环境变量
load_dotenv('config/.env')


class TopHubFetcher:
    """TopHub API 数据获取器"""
    
    def __init__(self):
        self.api_key = os.getenv('TOPHUB_API_KEY')
        self.base_url = os.getenv('TOPHUB_API_BASE_URL', 'https://api.tophubdata.com')
        self.timeout = int(os.getenv('REQUEST_TIMEOUT', '30'))
        self.max_retries = int(os.getenv('MAX_RETRIES', '3'))
        
        if not self.api_key:
            raise ValueError("TOPHUB_API_KEY not found in environment variables")
        
        logger.info(f"TopHubFetcher initialized with base_url: {self.base_url}")
    
    async def fetch_node(self, hashid: str, session: aiohttp.ClientSession) -> Optional[Dict[str, Any]]:
        """
        获取单个新闻源的数据
        
        Args:
            hashid: 新闻源的唯一标识
            session: aiohttp 会话对象
            
        Returns:
            新闻源数据字典，失败返回 None
        """
        url = f"{self.base_url}/nodes/{hashid}"
        headers = {'Authorization': self.api_key}
        
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Fetching node {hashid}, attempt {attempt + 1}/{self.max_retries}")
                
                async with session.get(url, headers=headers, timeout=self.timeout) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.success(f"Successfully fetched node {hashid}")
                        return data
                    else:
                        logger.warning(f"Failed to fetch node {hashid}: HTTP {response.status}")
                        
            except asyncio.TimeoutError:
                logger.warning(f"Timeout fetching node {hashid}, attempt {attempt + 1}")
            except Exception as e:
                logger.error(f"Error fetching node {hashid}: {str(e)}")
            
            if attempt < self.max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # 指数退避
        
        logger.error(f"Failed to fetch node {hashid} after {self.max_retries} attempts")
        return None
    
    async def fetch_multiple_nodes(self, hashids: List[str]) -> List[Dict[str, Any]]:
        """
        并发获取多个新闻源的数据
        
        Args:
            hashids: 新闻源 hashid 列表
            
        Returns:
            新闻源数据列表
        """
        max_concurrent = int(os.getenv('MAX_CONCURRENT_REQUESTS', '5'))
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def fetch_with_semaphore(hashid: str, session: aiohttp.ClientSession):
            async with semaphore:
                return await self.fetch_node(hashid, session)
        
        async with aiohttp.ClientSession() as session:
            tasks = [fetch_with_semaphore(hashid, session) for hashid in hashids]
            results = await asyncio.gather(*tasks)
        
        # 过滤掉失败的请求
        valid_results = [r for r in results if r is not None]
        logger.info(f"Fetched {len(valid_results)}/{len(hashids)} nodes successfully")
        
        return valid_results
    
    def extract_articles(self, node_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        从节点数据中提取文章列表
        
        Args:
            node_data: TopHub API 返回的节点数据
            
        Returns:
            文章列表
        """
        articles = []
        
        try:
            # TopHub API 返回的数据结构
            if 'data' in node_data and 'items' in node_data['data']:
                for item in node_data['data']['items']:
                    article = {
                        'title': item.get('title', ''),
                        'url': item.get('url', ''),
                        'excerpt': item.get('excerpt', ''),
                        'extra': item.get('extra', {}),
                        'node_name': node_data['data'].get('name', ''),
                        'node_hashid': node_data['data'].get('hashid', ''),
                    }
                    articles.append(article)
            
            logger.debug(f"Extracted {len(articles)} articles from node")
            
        except Exception as e:
            logger.error(f"Error extracting articles: {str(e)}")
        
        return articles


async def main():
    """测试函数"""
    fetcher = TopHubFetcher()
    
    # 测试单个新闻源
    test_hashids = ['G2me3ndwjq', '1Vd5rL8e85']
    
    results = await fetcher.fetch_multiple_nodes(test_hashids)
    
    for result in results:
        articles = fetcher.extract_articles(result)
        print(f"\n新闻源: {result['data']['name']}")
        print(f"文章数量: {len(articles)}")
        if articles:
            print(f"第一篇文章: {articles[0]['title']}")


if __name__ == '__main__':
    asyncio.run(main())
