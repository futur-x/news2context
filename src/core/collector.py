"""
新闻采集核心逻辑
"""

import asyncio
import aiohttp
from datetime import datetime, date
from typing import List, Dict, Any
from datetime import datetime
from loguru import logger

from src.utils.markdown_parser import MarkdownParser
from src.utils.chunker import SmartChunker

from src.core.task_manager import TaskManager
from src.storage.weaviate_client import CollectionManager
from src.engines.factory import EngineFactory
from src.extractor import ContentExtractor
from src.utils.config import get_config

class NewsCollector:
    """新闻采集器"""
    
    def __init__(self):
        self.config = get_config()
        self.task_manager = TaskManager()
        self.collection_manager = CollectionManager(
            weaviate_url=self.config.get('weaviate.url'),
            api_key=self.config.get('weaviate.api_key')
        )
        self.engine = EngineFactory.create_engine(self.config.config)
        self.extractor = ContentExtractor()

    async def collect_task(self, task_name: str) -> int:
        """
        执行指定任务的采集
        
        Args:
            task_name: 任务名称
            
        Returns:
            采集数量
        """
        logger.info(f"开始执行采集任务: {task_name}")
        
        task = self.task_manager.get_task(task_name)
        if not task:
            logger.error(f"任务不存在: {task_name}")
            return 0
            
        # 确保 Collection 存在
        collection_name = task.weaviate['collection']
        if not self.collection_manager.collection_exists(collection_name):
            logger.info(f"创建 Collection: {collection_name}")
            self.collection_manager.create_collection(collection_name)
            
        # 从配置读取参数
        max_news_per_source = self.config.get('collector.max_news_per_source', 15)
        early_stop_threshold = self.config.get('collector.early_stop_threshold', 3)
        
        logger.info(f"采集配置: 每源最多 {max_news_per_source} 条, 连续失败 {early_stop_threshold} 次跳过")
        
        # 用于暂存所有采集的新闻
        all_news_items = []
        source_stats = {}  # 统计每个源的采集情况
        
        logger.info(f"开始采集最新新闻（共 {len(task.sources)} 个源）")
        
        async with aiohttp.ClientSession() as session:
            for source in task.sources:
                source_name = source['name']
                source_stats[source_name] = {'total': 0, 'success': 0, 'failed': 0, 'skipped': 0}
                
                try:
                    # 获取最新新闻列表
                    news_items = await self.engine.fetch_news(source['hashid'])
                    
                    if not news_items:
                        logger.warning(f"源 {source_name} 没有新闻数据，跳过")
                        continue
                    
                    # 限制每个源的新闻数量
                    original_count = len(news_items)
                    news_items = news_items[:max_news_per_source]
                    
                    source_stats[source_name]['total'] = len(news_items)
                    
                    if original_count > max_news_per_source:
                        logger.info(
                            f"源 {source_name} 原有 {original_count} 条新闻，"
                            f"限制为 {max_news_per_source} 条"
                        )
                    else:
                        logger.info(f"源 {source_name} 获取到 {len(news_items)} 条新闻")
                        
                    # 处理每条新闻，带早停机制
                    consecutive_failures = 0  # 连续失败计数
                    
                    for idx, item in enumerate(news_items, 1):
                        # 早停检查
                        if consecutive_failures >= early_stop_threshold:
                            skipped = len(news_items) - idx + 1
                            source_stats[source_name]['skipped'] = skipped
                            logger.warning(
                                f"源 {source_name} 连续 {early_stop_threshold} 条提取失败，"
                                f"跳过剩余 {skipped} 条新闻"
                            )
                            break
                        
                        # 提取正文
                        content_data = await self.extractor.extract_from_url(item['url'], session)
                        
                        if not content_data:
                            # 提取失败，增加失败计数
                            consecutive_failures += 1
                            source_stats[source_name]['failed'] += 1
                            logger.debug(f"第 {idx} 条提取失败，连续失败: {consecutive_failures}/{early_stop_threshold}")
                            continue
                        
                        # 提取成功，重置失败计数
                        consecutive_failures = 0
                        source_stats[source_name]['success'] += 1
                        
                        # 格式化时间 (RFC3339)
                        current_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
                        
                        news_data = {
                            "task_name": task_name,
                            "title": item['title'],
                            "content": content_data.get('content', '') if content_data else item.get('excerpt', ''),
                            "url": item['url'],
                            "source_name": source_name,
                            "source_hashid": source['hashid'],
                            "published_at": current_time,
                            "fetched_at": current_time,
                            "category": source.get('category', '综合'),
                            "excerpt": item.get('excerpt', '')
                        }
                        
                        all_news_items.append(news_data)
                    
                    logger.info(
                        f"源 {source_name} 完成: "
                        f"成功 {source_stats[source_name]['success']} 条, "
                        f"失败 {source_stats[source_name]['failed']} 条, "
                        f"跳过 {source_stats[source_name]['skipped']} 条"
                    )
                        
                except Exception as e:
                    logger.error(f"处理源 {source_name} 失败: {str(e)}")
        
        # 5. 生成 Markdown 摘要文件
        logger.info("正在生成 Markdown 摘要文件...")
        markdown_path = self._generate_markdown_digest(task_name, all_news_items, source_stats)
        logger.success(f"Markdown 摘要已生成: {markdown_path}")
        
        # 6. 智能切割成 chunks
        if self.config.get('weaviate.chunking.enabled', True):
            logger.info("开始智能切割...")
            
            # 解析 Markdown，提取文章
            parser = MarkdownParser()
            articles = parser.parse_digest(markdown_path)
            
            # 智能切割成 chunks
            max_chunk_size = self.config.get('weaviate.chunking.max_chunk_size', 3000)
            chunker = SmartChunker(max_chunk_size=max_chunk_size)
            chunks = chunker.create_chunks(articles)
            
            logger.info(f"切割完成: {len(articles)} 篇新闻 → {len(chunks)} 个 chunks")
            
            # 准备 chunk 数据
            chunk_data_list = []
            for chunk in chunks:
                chunk_data = {
                    "chunk_id": chunk.chunk_id,
                    "content": chunk.content,
                    "task_name": task_name,
                    "categories": chunk.metadata["categories"],
                    "sources": chunk.metadata["sources"],
                    "article_titles": chunk.metadata["article_titles"],
                    "article_count": chunk.metadata["article_count"],
                    "char_count": chunk.metadata["char_count"],
                    "created_at": datetime.now().isoformat() + "Z"
                }
                chunk_data_list.append(chunk_data)
            
            # 批量插入 chunks
            batch_size = self.config.get('weaviate.batch.size', 5)
            total_chunks = self.collection_manager.batch_insert_chunks(
                collection_name=collection_name,
                chunks=chunk_data_list,
                batch_size=batch_size
            )
            
            logger.success(f"✓ 成功入库 {total_chunks} 个 chunks")
            
            # 更新任务状态
            self.task_manager.update_task_status(
                task_name,
                last_run=datetime.now()
            )
            logger.success(f"任务 {task_name} 采集完成，共入库 {total_chunks} 个 chunks")
            return total_chunks
        else:
            # 降级方案：直接插入新闻（旧逻辑）
            logger.warning("智能切割已禁用，使用旧的直接插入方式")
            total_news = self.collection_manager.batch_insert_news(collection_name, all_news_items)
            logger.success(f"✓ 成功入库 {total_news} 条新闻")
            
            # 更新任务状态
            self.task_manager.update_task_status(
                task_name,
                last_run=datetime.now()
            )
            logger.success(f"任务 {task_name} 采集完成，共入库 {total_news} 条新闻")
            return total_news
    
    def _parse_date_range(self, date_range: str, custom_range: Dict[str, Any] = None) -> List[date]:
        """
        解析日期范围配置
        
        Args:
            date_range: 日期范围类型 (today, yesterday, last_3_days, last_7_days, custom)
            custom_range: 自定义日期范围 {'start': 'YYYY-MM-DD', 'end': 'YYYY-MM-DD'}
            
        Returns:
            日期列表
        """
        from datetime import timedelta
        
        today = date.today()
        
        # TopHub API 仅支持昨天及以前的数据
        if date_range == 'yesterday' or date_range == 'last_1_days':
            # 最近1天 = 昨天
            return [today - timedelta(days=1)]
    
    def _generate_markdown_digest(
        self, 
        task_name: str, 
        news_items: List[Dict[str, Any]], 
        source_stats: Dict[str, Dict[str, int]]
    ) -> None:
        """
        生成新闻摘要 Markdown 文件
        
        Args:
            task_name: 任务名称
            news_items: 所有采集的新闻列表
            source_stats: 每个源的统计信息
        """
        from pathlib import Path
        from collections import defaultdict
        
        # 创建输出目录
        today = datetime.now().strftime('%Y-%m-%d')
        output_dir = Path('output') / today
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / f'{task_name}_digest.md'
        
        # 按分类和来源组织新闻
        news_by_category = defaultdict(lambda: defaultdict(list))
        for item in news_items:
            category = item.get('category', '其他')
            source = item.get('source_name', '未知来源')
            news_by_category[category][source].append(item)
        
        # 生成 Markdown 内容
        lines = []
        lines.append(f"# {task_name} 新闻摘要 - {today}\n")
        lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        lines.append(f"**总计**: {len(news_items)} 条新闻\n")
        lines.append("---\n")
        
        # 生成目录
        lines.append("## 📑 目录\n")
        for category in sorted(news_by_category.keys()):
            lines.append(f"- [{category}](#{category.replace(' ', '-')})")
        lines.append("\n---\n")
        
        # 生成统计信息
        lines.append("## 📊 采集统计\n")
        lines.append("| 新闻源 | 获取 | 成功 | 失败 | 跳过 |")
        lines.append("|--------|------|------|------|------|")
        for source, stats in source_stats.items():
            lines.append(
                f"| {source} | {stats['total']} | {stats['success']} | "
                f"{stats['failed']} | {stats['skipped']} |"
            )
        lines.append("\n---\n")
        
        # 生成各分类的新闻内容
        for category in sorted(news_by_category.keys()):
            lines.append(f"## {category}\n")
            
            for source in sorted(news_by_category[category].keys()):
                news_list = news_by_category[category][source]
                lines.append(f"### 📰 {source}\n")
                lines.append(f"**文章数量**: {len(news_list)}\n")
                
                for idx, news in enumerate(news_list, 1):
                    lines.append(f"#### {idx}. {news['title']}\n")
                    lines.append(f"**原文链接**: [{news['url']}]({news['url']})\n")
                    
                    if news.get('content'):
                        lines.append("**正文内容**:\n")
                        lines.append(f"{news['content']}\n")
                    elif news.get('excerpt'):
                        lines.append("**摘要**:\n")
                        lines.append(f"{news['excerpt']}\n")
                    
                    lines.append("---\n")
        
        # 保存文件
        content = '\n'.join(lines)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.success(f"新闻摘要已保存到: {output_file}")
        return str(output_file)  # 返回文件路径
