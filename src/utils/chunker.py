"""
智能 Chunker
将多篇新闻智能合并成 chunks，每个 chunk ≤ 3000 字
"""

import uuid
from typing import List, Dict, Any
from dataclasses import dataclass
from loguru import logger

from src.utils.markdown_parser import Article


@dataclass
class Chunk:
    """Chunk 数据结构"""
    chunk_id: str           # chunk 唯一 ID
    content: str            # 合并后的内容
    metadata: Dict[str, Any]  # 元数据


class SmartChunker:
    """智能 Chunker"""
    
    def __init__(self, max_chunk_size: int = 3000):
        """
        初始化 Chunker
        
        Args:
            max_chunk_size: 每个 chunk 最大字符数
        """
        self.max_chunk_size = max_chunk_size
        logger.info(f"智能 Chunker 已初始化 (max_chunk_size={max_chunk_size})")
    
    def create_chunks(self, articles: List[Article]) -> List[Chunk]:
        """
        智能切割成 chunks
        
        使用贪心算法，尽量将多篇新闻合并到一个 chunk
        
        Args:
            articles: 文章列表
            
        Returns:
            Chunk 列表
        """
        logger.info(f"开始切割 {len(articles)} 篇文章...")
        
        chunks = []
        current_chunk_articles = []
        current_length = 0
        
        for idx, article in enumerate(articles, 1):
            article_length = article.char_count
            
            # 贪心合并：如果加上当前文章不超过限制，就合并
            if current_length + article_length <= self.max_chunk_size:
                current_chunk_articles.append(article)
                current_length += article_length
                logger.debug(
                    f"文章 #{idx} ({article.title[:20]}...) "
                    f"合并到当前 chunk (当前长度: {current_length})"
                )
            else:
                # 超过限制，保存当前 chunk，开始新 chunk
                if current_chunk_articles:
                    chunk = self._build_chunk(current_chunk_articles)
                    chunks.append(chunk)
                    logger.info(
                        f"Chunk #{len(chunks)} 完成: "
                        f"{len(current_chunk_articles)} 篇文章, "
                        f"{current_length} 字符"
                    )
                
                # 处理超长文章
                if article_length > self.max_chunk_size:
                    logger.warning(
                        f"文章 #{idx} ({article.title[:20]}...) "
                        f"超过限制 ({article_length} > {self.max_chunk_size})，"
                        f"单独成 chunk"
                    )
                    # 超长文章单独成 chunk（可选：进一步切割）
                    chunk = self._build_chunk([article])
                    chunks.append(chunk)
                    current_chunk_articles = []
                    current_length = 0
                else:
                    # 开始新 chunk
                    current_chunk_articles = [article]
                    current_length = article_length
        
        # 保存最后一个 chunk
        if current_chunk_articles:
            chunk = self._build_chunk(current_chunk_articles)
            chunks.append(chunk)
            logger.info(
                f"Chunk #{len(chunks)} 完成: "
                f"{len(current_chunk_articles)} 篇文章, "
                f"{current_length} 字符"
            )
        
        logger.success(
            f"切割完成: {len(articles)} 篇文章 → {len(chunks)} 个 chunks "
            f"(平均 {len(articles)/len(chunks):.1f} 篇/chunk)"
        )
        
        return chunks
    
    def _build_chunk(self, articles: List[Article]) -> Chunk:
        """
        构建 chunk 对象
        
        Args:
            articles: 文章列表
            
        Returns:
            Chunk 对象
        """
        # 合并内容
        content_parts = []
        for article in articles:
            # 保留标题层级信息作为上下文
            content_parts.append(f"## {article.category}")
            content_parts.append(f"### {article.source}")
            content_parts.append(f"#### {article.title}")
            content_parts.append(f"链接: {article.url}")
            content_parts.append(article.content)
            content_parts.append("---")
        
        content = '\n\n'.join(content_parts)
        
        # 提取元数据
        categories = list(set(a.category for a in articles))
        sources = list(set(a.source for a in articles))
        titles = [a.title for a in articles]
        urls = [a.url for a in articles if a.url]
        char_count = sum(a.char_count for a in articles)
        
        return Chunk(
            chunk_id=f"chunk_{uuid.uuid4().hex[:8]}",
            content=content,
            metadata={
                "article_count": len(articles),
                "categories": categories,
                "sources": sources,
                "article_titles": titles,
                "article_urls": urls,
                "char_count": char_count
            }
        )
