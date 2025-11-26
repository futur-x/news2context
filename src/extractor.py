"""
内容提取模块 - 增强版
负责从文章链接中提取正文内容，支持多种提取策略
"""

import asyncio
from typing import Optional, Dict, Any
from loguru import logger
import aiohttp
import trafilatura
from trafilatura.settings import use_config
from bs4 import BeautifulSoup
from newspaper import Article
import re


class ContentExtractor:
    """网页内容提取器 - 多策略版本"""
    
    def __init__(self):
        self.timeout = 60  # 增加超时时间
        self.max_retries = 2
        
        # 配置 trafilatura
        self.config = use_config()
        self.config.set("DEFAULT", "EXTRACTION_TIMEOUT", "60")
        
        # 真实浏览器 Headers
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        logger.info("ContentExtractor initialized with multi-strategy support")
    
    def _get_domain(self, url: str) -> str:
        """提取域名"""
        from urllib.parse import urlparse
        return urlparse(url).netloc
    
    async def extract_from_url(self, url: str, session: aiohttp.ClientSession) -> Optional[Dict[str, Any]]:
        """
        从 URL 提取正文内容 - 多策略版本
        
        Args:
            url: 文章链接
            session: aiohttp 会话对象
            
        Returns:
            包含标题和正文的字典，失败返回 None
        """
        if not url or url == '#':
            logger.debug(f"Skipping invalid URL: {url}")
            return None
        
        domain = self._get_domain(url)
        
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Extracting content from {url}, attempt {attempt + 1}")
                
                # 获取 HTML 内容
                async with session.get(url, headers=self.headers, timeout=self.timeout, allow_redirects=True) as response:
                    if response.status != 200:
                        logger.warning(f"Failed to fetch {url}: HTTP {response.status}")
                        continue
                    
                    html = await response.text()
                    
                    # 策略1: 检查是否有网站特定提取器
                    if 'yicai.com' in domain:
                        result = self._extract_yicai(html, url)
                        if result:
                            logger.success(f"Successfully extracted content from {url} using yicai extractor")
                            return result
                    
                    if 'gov.cn' in domain:
                        result = self._extract_gov_cn(html, url)
                        if result:
                            logger.success(f"Successfully extracted content from {url} using gov.cn extractor")
                            return result
                    
                    # 策略2: trafilatura (原方法)
                    result = self._extract_with_trafilatura(html, url)
                    if result:
                        logger.success(f"Successfully extracted content from {url} using trafilatura")
                        return result
                    
                    # 策略3: BeautifulSoup 通用提取
                    result = self._extract_with_beautifulsoup(html, url)
                    if result:
                        logger.success(f"Successfully extracted content from {url} using BeautifulSoup")
                        return result
                    
                    # 策略4: newspaper3k
                    result = await self._extract_with_newspaper(url)
                    if result:
                        logger.success(f"Successfully extracted content from {url} using newspaper3k")
                        return result
                    
                    logger.warning(f"All extraction strategies failed for {url}")
                        
            except asyncio.TimeoutError:
                logger.warning(f"Timeout extracting from {url}")
            except Exception as e:
                logger.error(f"Error extracting from {url}: {str(e)}")
            
            if attempt < self.max_retries - 1:
                await asyncio.sleep(1)
        
        logger.error(f"Failed to extract content from {url} after {self.max_retries} attempts")
        return None
    
    def _extract_with_trafilatura(self, html: str, url: str) -> Optional[Dict[str, Any]]:
        """使用 trafilatura 提取"""
        try:
            extracted = trafilatura.extract(
                html,
                config=self.config,
                include_comments=False,
                include_tables=True,
                no_fallback=False,
                favor_precision=True,
                with_metadata=True,
                output_format='json'
            )
            
            if extracted:
                import json
                content_data = json.loads(extracted)
                
                if content_data.get('text') and len(content_data.get('text', '')) > 100:
                    return {
                        'title': content_data.get('title', ''),
                        'content': content_data.get('text', ''),
                        'author': content_data.get('author', ''),
                        'date': content_data.get('date', ''),
                        'url': url
                    }
        except Exception as e:
            logger.debug(f"Trafilatura extraction failed: {str(e)}")
        
        return None
    
    def _extract_with_beautifulsoup(self, html: str, url: str) -> Optional[Dict[str, Any]]:
        """使用 BeautifulSoup 通用提取"""
        try:
            soup = BeautifulSoup(html, 'lxml')
            
            # 移除脚本和样式
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # 提取标题
            title = ''
            title_tags = soup.find_all(['h1', 'title'])
            if title_tags:
                title = title_tags[0].get_text().strip()
            
            # 尝试找到主要内容区域
            content = ''
            
            # 常见的内容容器 class/id
            content_selectors = [
                {'class': re.compile(r'(article|content|post|entry|main|body)', re.I)},
                {'id': re.compile(r'(article|content|post|entry|main|body)', re.I)},
            ]
            
            for selector in content_selectors:
                containers = soup.find_all(['div', 'article', 'section'], selector)
                if containers:
                    # 找到最长的内容
                    for container in containers:
                        text = container.get_text(separator='\n', strip=True)
                        if len(text) > len(content):
                            content = text
            
            # 如果还是没找到，就提取所有段落
            if len(content) < 200:
                paragraphs = soup.find_all('p')
                content = '\n\n'.join([p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 20])
            
            # 清理内容
            content = re.sub(r'\n{3,}', '\n\n', content)
            content = content.strip()
            
            if len(content) > 100:
                return {
                    'title': title,
                    'content': content,
                    'author': '',
                    'date': '',
                    'url': url
                }
        except Exception as e:
            logger.debug(f"BeautifulSoup extraction failed: {str(e)}")
        
        return None
    
    async def _extract_with_newspaper(self, url: str) -> Optional[Dict[str, Any]]:
        """使用 newspaper3k 提取"""
        try:
            article = Article(url, language='zh')
            article.download()
            article.parse()
            
            if article.text and len(article.text) > 100:
                return {
                    'title': article.title or '',
                    'content': article.text,
                    'author': ', '.join(article.authors) if article.authors else '',
                    'date': article.publish_date.strftime('%Y-%m-%d') if article.publish_date else '',
                    'url': url
                }
        except Exception as e:
            logger.debug(f"Newspaper3k extraction failed: {str(e)}")
        
        return None
    
    def _extract_yicai(self, html: str, url: str) -> Optional[Dict[str, Any]]:
        """第一财经专用提取器"""
        try:
            soup = BeautifulSoup(html, 'lxml')
            
            # 提取标题
            title = ''
            title_tag = soup.find('h1') or soup.find('title')
            if title_tag:
                title = title_tag.get_text().strip()
            
            # 第一财经的内容通常在特定的 div 中
            content = ''
            
            # 尝试多种可能的内容容器
            content_containers = [
                soup.find('div', {'class': re.compile(r'(article-content|content-main|post-content)', re.I)}),
                soup.find('div', {'id': re.compile(r'(article|content|main)', re.I)}),
                soup.find('article'),
            ]
            
            for container in content_containers:
                if container:
                    # 移除不需要的元素
                    for tag in container.find_all(['script', 'style', 'nav', 'aside']):
                        tag.decompose()
                    
                    # 提取段落
                    paragraphs = container.find_all('p')
                    if paragraphs:
                        content = '\n\n'.join([p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 10])
                        break
            
            # 如果还是没找到，尝试提取所有段落
            if len(content) < 100:
                all_paragraphs = soup.find_all('p')
                content = '\n\n'.join([p.get_text().strip() for p in all_paragraphs if len(p.get_text().strip()) > 20])
            
            content = content.strip()
            
            if len(content) > 100:
                return {
                    'title': title,
                    'content': content,
                    'author': '',
                    'date': '',
                    'url': url
                }
        except Exception as e:
            logger.debug(f"Yicai extractor failed: {str(e)}")
        
        return None
    
    def _extract_gov_cn(self, html: str, url: str) -> Optional[Dict[str, Any]]:
        """中国政府网专用提取器"""
        try:
            soup = BeautifulSoup(html, 'lxml')
            
            # 提取标题
            title = ''
            title_tag = soup.find('h1') or soup.find('title')
            if title_tag:
                title = title_tag.get_text().strip()
                # 清理标题中的网站名称
                title = re.sub(r'_.*?政府网.*$', '', title).strip()
            
            # 政府网站的内容通常在特定的 div 中
            content = ''
            
            # 尝试多种可能的内容容器
            content_containers = [
                soup.find('div', {'class': re.compile(r'(pages_content|article|content|TRS_Editor)', re.I)}),
                soup.find('div', {'id': re.compile(r'(article|content|UCAP-CONTENT)', re.I)}),
                soup.find('td', {'class': re.compile(r'(article|content)', re.I)}),
            ]
            
            for container in content_containers:
                if container:
                    # 移除不需要的元素
                    for tag in container.find_all(['script', 'style', 'table']):
                        tag.decompose()
                    
                    # 提取文本
                    text = container.get_text(separator='\n', strip=True)
                    
                    # 清理文本
                    lines = [line.strip() for line in text.split('\n') if line.strip() and len(line.strip()) > 10]
                    content = '\n\n'.join(lines)
                    
                    if len(content) > 100:
                        break
            
            # 如果还是没找到，尝试提取所有段落
            if len(content) < 100:
                all_paragraphs = soup.find_all('p')
                content = '\n\n'.join([p.get_text().strip() for p in all_paragraphs if len(p.get_text().strip()) > 20])
            
            content = content.strip()
            
            if len(content) > 100:
                return {
                    'title': title,
                    'content': content,
                    'author': '',
                    'date': '',
                    'url': url
                }
        except Exception as e:
            logger.debug(f"Gov.cn extractor failed: {str(e)}")
        
        return None
    
    async def extract_multiple(self, urls: list, max_concurrent: int = 3) -> Dict[str, Dict[str, Any]]:
        """
        并发提取多个 URL 的内容
        
        Args:
            urls: URL 列表
            max_concurrent: 最大并发数
            
        Returns:
            URL 到内容的映射字典
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        results = {}
        
        async def extract_with_semaphore(url: str, session: aiohttp.ClientSession):
            async with semaphore:
                content = await self.extract_from_url(url, session)
                if content:
                    results[url] = content
        
        # 设置更宽松的连接器配置
        connector = aiohttp.TCPConnector(limit=max_concurrent, limit_per_host=2)
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            tasks = [extract_with_semaphore(url, session) for url in urls if url and url != '#']
            await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.info(f"Extracted content from {len(results)}/{len(urls)} URLs")
        return results


async def main():
    """测试函数"""
    extractor = ContentExtractor()
    
    # 测试 URL - 包括之前失败的网站
    test_urls = [
        'https://wallstreetcn.com/articles/3726891',
        'https://www.yicai.com/news/102928089.html',  # 第一财经
        'https://www.gov.cn/zhengce/content/202511/content_7049204.htm',  # 政府网
    ]
    
    results = await extractor.extract_multiple(test_urls)
    
    for url, content in results.items():
        print(f"\nURL: {url}")
        print(f"标题: {content['title']}")
        print(f"内容长度: {len(content['content'])} 字符")
        print(f"内容预览: {content['content'][:200]}...")


if __name__ == '__main__':
    asyncio.run(main())
