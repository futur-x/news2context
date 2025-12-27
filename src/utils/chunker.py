"""
单篇新闻智能切割器
将单篇长文章切割成多个 chunks，确保每个 chunk 不超过 embedding 模型的 token 限制
"""

import hashlib
from typing import List, Dict, Any
from dataclasses import dataclass
from loguru import logger

try:
    import tiktoken
except ImportError:
    logger.warning("tiktoken 未安装，将使用字符数估算（1 token ≈ 1.5 字符）")
    tiktoken = None

from src.utils.markdown_parser import Article


@dataclass
class ArticleChunk:
    """单篇文章的 Chunk 数据结构"""
    article_id: str          # 文章唯一 ID（基于 URL hash）
    chunk_index: int         # Chunk 索引（从 0 开始）
    total_chunks: int        # 该文章总共的 chunks 数量
    title: str               # 文章标题
    content: str             # Chunk 内容（包含标题和索引）
    url: str                 # 原文链接
    source_name: str         # 新闻源名称
    source_hashid: str       # 新闻源 hashid
    category: str            # 分类
    published_at: str        # 发布时间
    fetched_at: str          # 抓取时间
    excerpt: str             # 摘要
    task_name: str           # 任务名称


class ArticleChunker:
    """单篇新闻智能切割器"""

    def __init__(self, max_tokens: int = 6000):
        """
        初始化 Chunker

        Args:
            max_tokens: 每个 chunk 最大 token 数（默认 6000，为 8192 留 buffer）
        """
        self.max_tokens = max_tokens

        # 初始化 tiktoken（text-embedding-3-large 使用 cl100k_base）
        if tiktoken:
            try:
                self.encoding = tiktoken.get_encoding("cl100k_base")
                logger.info(f"使用 tiktoken 精确计算 token (max_tokens={max_tokens})")
            except Exception as e:
                logger.warning(f"tiktoken 初始化失败: {e}，将使用字符数估算")
                self.encoding = None
        else:
            self.encoding = None

    def count_tokens(self, text: str) -> int:
        """
        计算文本的 token 数

        Args:
            text: 文本内容

        Returns:
            token 数量
        """
        if self.encoding:
            try:
                return len(self.encoding.encode(text))
            except Exception as e:
                logger.warning(f"Token 计算失败: {e}，使用字符数估算")

        # 回退：使用字符数估算（1 token ≈ 1.5 字符，中文约 1 token ≈ 0.5 字）
        # 为安全起见，使用保守估算：1 token = 1 字符
        return len(text)

    def generate_article_id(self, url: str) -> str:
        """
        生成文章唯一 ID（基于 URL hash）

        Args:
            url: 文章 URL

        Returns:
            文章 ID（16位 hex）
        """
        return hashlib.md5(url.encode('utf-8')).hexdigest()[:16]

    def chunk_article(self, article: Article, task_name: str) -> List[ArticleChunk]:
        """
        切割单篇文章

        Args:
            article: 文章对象
            task_name: 任务名称

        Returns:
            ArticleChunk 列表
        """
        # 生成文章 ID
        article_id = self.generate_article_id(article.url)

        # 构建元数据头（会被包含在每个 chunk 中）
        metadata_header = self._build_metadata_header(article)
        metadata_tokens = self.count_tokens(metadata_header)

        # 可用于正文的 token 数
        available_tokens = self.max_tokens - metadata_tokens - 50  # 额外留 50 token buffer

        # 计算正文 token 数
        content_tokens = self.count_tokens(article.content)

        logger.debug(
            f"文章 [{article.title[:30]}...] "
            f"token 统计: 元数据={metadata_tokens}, 正文={content_tokens}, "
            f"可用={available_tokens}"
        )

        # 判断是否需要切割
        if content_tokens <= available_tokens:
            # 不需要切割，返回单个 chunk
            logger.debug(f"文章无需切割 (tokens={content_tokens} < {available_tokens})")
            return self._create_single_chunk(
                article, article_id, metadata_header, task_name
            )
        else:
            # 需要切割
            logger.info(
                f"文章需要切割: tokens={content_tokens} > {available_tokens}, "
                f"预计切成 {(content_tokens // available_tokens) + 1} 个 chunks"
            )
            return self._create_multiple_chunks(
                article, article_id, metadata_header, available_tokens, task_name
            )

    def _build_metadata_header(self, article: Article) -> str:
        """
        构建元数据头（包含标题、来源、时间等信息）

        Args:
            article: 文章对象

        Returns:
            元数据头字符串
        """
        header_parts = [
            f"# {article.title}",
            f"",
            f"**来源**: {article.source} | **分类**: {article.category}",
        ]

        # published_at 字段可能不存在（从 Markdown 解析的 Article 没有此字段）
        published_at = getattr(article, 'published_at', None)
        if published_at:
            header_parts.append(f"**发布时间**: {published_at}")

        header_parts.extend([
            f"**链接**: {article.url}",
            f"",
        ])

        return "\n".join(header_parts)

    def _create_single_chunk(
        self,
        article: Article,
        article_id: str,
        metadata_header: str,
        task_name: str
    ) -> List[ArticleChunk]:
        """
        创建单个 chunk（文章无需切割）

        Args:
            article: 文章对象
            article_id: 文章 ID
            metadata_header: 元数据头
            task_name: 任务名称

        Returns:
            包含单个 ArticleChunk 的列表
        """
        content = f"{metadata_header}\n{article.content}"

        chunk = ArticleChunk(
            article_id=article_id,
            chunk_index=0,
            total_chunks=1,
            title=article.title,
            content=content,
            url=article.url,
            source_name=article.source,
            source_hashid=getattr(article, 'source_hashid', ''),
            category=article.category,
            published_at=getattr(article, 'published_at', ''),
            fetched_at=getattr(article, 'fetched_at', ''),
            excerpt=getattr(article, 'excerpt', ''),
            task_name=task_name
        )

        return [chunk]

    def _create_multiple_chunks(
        self,
        article: Article,
        article_id: str,
        metadata_header: str,
        available_tokens: int,
        task_name: str
    ) -> List[ArticleChunk]:
        """
        创建多个 chunks（文章需要切割）

        Args:
            article: 文章对象
            article_id: 文章 ID
            metadata_header: 元数据头
            available_tokens: 每个 chunk 可用的 token 数
            task_name: 任务名称

        Returns:
            ArticleChunk 列表
        """
        # 按段落切割正文
        paragraphs = article.content.split('\n\n')

        chunks = []
        current_paragraphs = []
        current_tokens = 0

        for para in paragraphs:
            para_tokens = self.count_tokens(para)

            # 如果加上当前段落不超过限制，就合并
            if current_tokens + para_tokens + 2 <= available_tokens:  # +2 for \n\n
                current_paragraphs.append(para)
                current_tokens += para_tokens + 2
            else:
                # 超过限制，保存当前 chunk
                if current_paragraphs:
                    chunks.append('\n\n'.join(current_paragraphs))

                # 处理超长段落（单个段落就超过限制）
                if para_tokens > available_tokens:
                    logger.warning(
                        f"段落过长 ({para_tokens} tokens)，强制切割"
                    )
                    # 强制按 token 切割
                    sub_chunks = self._split_long_paragraph(para, available_tokens)
                    chunks.extend(sub_chunks)
                    current_paragraphs = []
                    current_tokens = 0
                else:
                    # 开始新 chunk
                    current_paragraphs = [para]
                    current_tokens = para_tokens + 2

        # 保存最后一个 chunk
        if current_paragraphs:
            chunks.append('\n\n'.join(current_paragraphs))

        # 构建 ArticleChunk 对象
        total_chunks = len(chunks)
        result = []

        for idx, chunk_content in enumerate(chunks):
            # 添加索引信息
            index_info = f"【第 {idx + 1}/{total_chunks} 部分】\n\n"
            full_content = f"{metadata_header}\n{index_info}{chunk_content}"

            chunk = ArticleChunk(
                article_id=article_id,
                chunk_index=idx,
                total_chunks=total_chunks,
                title=article.title,
                content=full_content,
                url=article.url,
                source_name=article.source,
                source_hashid=getattr(article, 'source_hashid', ''),
                category=article.category,
                published_at=getattr(article, 'published_at', ''),
                fetched_at=getattr(article, 'fetched_at', ''),
                excerpt=getattr(article, 'excerpt', ''),
                task_name=task_name
            )
            result.append(chunk)

        logger.info(
            f"文章 [{article.title[:30]}...] 切割完成: {total_chunks} 个 chunks"
        )

        return result

    def _split_long_paragraph(self, paragraph: str, max_tokens: int) -> List[str]:
        """
        强制切割超长段落

        Args:
            paragraph: 段落文本
            max_tokens: 最大 token 数

        Returns:
            切割后的段落列表
        """
        # 按句子切割（简单处理：按句号、问号、感叹号）
        sentences = []
        current = ""

        for char in paragraph:
            current += char
            if char in ['。', '！', '？', '.', '!', '?']:
                sentences.append(current)
                current = ""

        if current:
            sentences.append(current)

        # 贪心合并句子
        chunks = []
        current_chunk = ""
        current_tokens = 0

        for sentence in sentences:
            sentence_tokens = self.count_tokens(sentence)

            if current_tokens + sentence_tokens <= max_tokens:
                current_chunk += sentence
                current_tokens += sentence_tokens
            else:
                if current_chunk:
                    chunks.append(current_chunk)

                # 如果单个句子就超过限制，强制切割
                if sentence_tokens > max_tokens:
                    # 按字符强制切割
                    chunk_size = int(max_tokens * 0.9)  # 保守估算
                    for i in range(0, len(sentence), chunk_size):
                        chunks.append(sentence[i:i+chunk_size])
                    current_chunk = ""
                    current_tokens = 0
                else:
                    current_chunk = sentence
                    current_tokens = sentence_tokens

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def chunk_articles(self, articles: List[Article], task_name: str) -> List[ArticleChunk]:
        """
        批量切割文章

        Args:
            articles: 文章列表
            task_name: 任务名称

        Returns:
            所有 ArticleChunk 列表
        """
        logger.info(f"开始处理 {len(articles)} 篇文章...")

        all_chunks = []

        for idx, article in enumerate(articles, 1):
            try:
                chunks = self.chunk_article(article, task_name)
                all_chunks.extend(chunks)

                if len(chunks) > 1:
                    logger.info(
                        f"[{idx}/{len(articles)}] {article.title[:30]}... "
                        f"→ {len(chunks)} chunks"
                    )
                else:
                    logger.debug(
                        f"[{idx}/{len(articles)}] {article.title[:30]}... "
                        f"→ 1 chunk (无需切割)"
                    )
            except Exception as e:
                logger.error(f"处理文章失败 [{article.title[:30]}...]: {e}")
                continue

        logger.success(
            f"切割完成: {len(articles)} 篇文章 → {len(all_chunks)} 个 chunks "
            f"(平均 {len(all_chunks)/len(articles):.1f} chunks/篇)"
        )

        return all_chunks
