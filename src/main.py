"""
News2Context 主程序
整合所有模块，实现完整的新闻抓取和生成流程
"""

import asyncio
import os
import sys
from datetime import datetime
from typing import Dict, List, Any
import yaml
from loguru import logger
from dotenv import load_dotenv

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.fetcher import TopHubFetcher
from src.extractor import ContentExtractor
from src.markdown_generator import MarkdownGenerator


class News2Context:
    """新闻聚合主程序"""
    
    def __init__(self, config_path: str = 'config/news_sources.yaml'):
        # 加载环境变量
        load_dotenv('config/.env')
        
        # 配置日志
        log_dir = os.getenv('LOG_DIR', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, f"news2context_{datetime.now().strftime('%Y%m%d')}.log")
        logger.add(
            log_file,
            rotation="1 day",
            retention="30 days",
            level="DEBUG",
            encoding="utf-8"
        )
        
        # 加载新闻源配置
        self.config = self._load_config(config_path)
        
        # 初始化模块
        self.fetcher = TopHubFetcher()
        self.extractor = ContentExtractor()
        self.generator = MarkdownGenerator(output_dir=os.getenv('OUTPUT_DIR', 'output'))
        
        logger.info("News2Context initialized successfully")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded config from {config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load config: {str(e)}")
            raise
    
    async def run(self):
        """运行主流程"""
        logger.info("=" * 60)
        logger.info("Starting News2Context daily digest generation")
        logger.info("=" * 60)
        
        start_time = datetime.now()
        
        try:
            # 1. 收集所有新闻源的 hashid
            hashids = []
            category_map = {}  # hashid -> category_name 的映射
            source_map = {}    # hashid -> source_name 的映射
            
            for category in self.config.get('categories', []):
                category_name = category['name']
                for source in category.get('sources', []):
                    hashid = source['hashid']
                    hashids.append(hashid)
                    category_map[hashid] = category_name
                    source_map[hashid] = source['name']
            
            logger.info(f"Total news sources to fetch: {len(hashids)}")
            
            # 2. 并发获取所有新闻源数据
            logger.info("Fetching news from TopHub API...")
            node_results = await self.fetcher.fetch_multiple_nodes(hashids)
            logger.info(f"Successfully fetched {len(node_results)} news sources")
            
            # 3. 提取所有文章
            all_articles = []
            url_to_article = {}  # URL -> article 的映射
            
            for node_data in node_results:
                articles = self.fetcher.extract_articles(node_data)
                hashid = node_data['data']['hashid']
                
                for article in articles:
                    article['category'] = category_map.get(hashid, '其他')
                    article['source_name'] = source_map.get(hashid, article['node_name'])
                    all_articles.append(article)
                    
                    # 记录需要提取内容的 URL
                    if article['url'] and article['url'] != '#':
                        url_to_article[article['url']] = article
            
            logger.info(f"Total articles collected: {len(all_articles)}")
            logger.info(f"URLs to extract content from: {len(url_to_article)}")
            
            # 4. 并发提取文章正文内容
            if url_to_article:
                logger.info("Extracting article content from URLs...")
                extracted_contents = await self.extractor.extract_multiple(
                    list(url_to_article.keys()),
                    max_concurrent=3
                )
                
                # 将提取的内容合并到文章数据中
                for url, content_data in extracted_contents.items():
                    article = url_to_article[url]
                    article['content'] = content_data.get('content', '')
                    article['author'] = content_data.get('author', '')
                    article['date'] = content_data.get('date', '')
                
                logger.info(f"Successfully extracted content from {len(extracted_contents)} articles")
            
            # 5. 按分类组织新闻
            categorized_news = {}
            for article in all_articles:
                category = article['category']
                if category not in categorized_news:
                    categorized_news[category] = []
                categorized_news[category].append(article)
            
            # 6. 生成 Markdown 文件
            logger.info("Generating Markdown digest...")
            output_file = self.generator.generate_daily_digest(categorized_news)
            
            # 7. 统计信息
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            logger.info("=" * 60)
            logger.info("Daily digest generation completed!")
            logger.info(f"Output file: {output_file}")
            logger.info(f"Total categories: {len(categorized_news)}")
            logger.info(f"Total articles: {len(all_articles)}")
            logger.info(f"Articles with extracted content: {len(extracted_contents) if url_to_article else 0}")
            logger.info(f"Time elapsed: {duration:.2f} seconds")
            logger.info("=" * 60)
            
            return output_file
            
        except Exception as e:
            logger.error(f"Error during execution: {str(e)}", exc_info=True)
            raise


async def main():
    """主入口函数"""
    try:
        app = News2Context()
        output_file = await app.run()
        print(f"\n✅ 成功生成每日新闻摘要: {output_file}\n")
        
    except Exception as e:
        print(f"\n❌ 程序执行失败: {str(e)}\n")
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
