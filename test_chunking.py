"""
测试智能 Chunking 系统
"""

import asyncio
from pathlib import Path
from loguru import logger

from src.utils.markdown_parser import MarkdownParser
from src.utils.chunker import SmartChunker
from src.storage.weaviate_client import CollectionManager
from src.utils.config import get_config


async def test_chunking():
    """测试智能切割系统"""
    
    logger.info("=" * 60)
    logger.info("智能 Chunking 系统测试")
    logger.info("=" * 60)
    
    # 1. 查找最新的 Markdown 摘要文件
    output_dir = Path("output")
    markdown_files = list(output_dir.glob("**/*_digest.md"))
    
    if not markdown_files:
        logger.error("未找到 Markdown 摘要文件")
        return
    
    # 使用最新的文件
    markdown_path = sorted(markdown_files, key=lambda x: x.stat().st_mtime, reverse=True)[0]
    logger.info(f"使用文件: {markdown_path}")
    
    # 2. 解析 Markdown
    logger.info("\n" + "=" * 60)
    logger.info("步骤 1: 解析 Markdown 文件")
    logger.info("=" * 60)
    
    parser = MarkdownParser()
    articles = parser.parse_digest(str(markdown_path))
    
    logger.info(f"\n提取结果:")
    logger.info(f"  - 总文章数: {len(articles)}")
    logger.info(f"  - 分类: {len(set(a.category for a in articles))}")
    logger.info(f"  - 来源: {len(set(a.source for a in articles))}")
    logger.info(f"  - 总字符数: {sum(a.char_count for a in articles):,}")
    
    # 显示前 5 篇文章
    logger.info(f"\n前 5 篇文章:")
    for i, article in enumerate(articles[:5], 1):
        logger.info(f"  {i}. {article.category} > {article.source} > {article.title[:30]}... ({article.char_count} 字)")
    
    # 3. 智能切割
    logger.info("\n" + "=" * 60)
    logger.info("步骤 2: 智能切割成 Chunks")
    logger.info("=" * 60)
    
    chunker = SmartChunker(max_chunk_size=3000)
    chunks = chunker.create_chunks(articles)
    
    logger.info(f"\n切割结果:")
    logger.info(f"  - Chunk 数量: {len(chunks)}")
    logger.info(f"  - 平均每个 chunk: {len(articles)/len(chunks):.1f} 篇文章")
    logger.info(f"  - 平均字符数: {sum(c.metadata['char_count'] for c in chunks)/len(chunks):.0f}")
    
    # 显示每个 chunk 的统计
    logger.info(f"\nChunk 详情:")
    for i, chunk in enumerate(chunks[:10], 1):  # 只显示前 10 个
        logger.info(
            f"  Chunk {i}: "
            f"{chunk.metadata['article_count']} 篇, "
            f"{chunk.metadata['char_count']} 字, "
            f"分类: {', '.join(chunk.metadata['categories'])}"
        )
    
    if len(chunks) > 10:
        logger.info(f"  ... 还有 {len(chunks) - 10} 个 chunks")
    
    # 4. 测试 Weaviate 连接和 Schema
    logger.info("\n" + "=" * 60)
    logger.info("步骤 3: 测试 Weaviate 连接")
    logger.info("=" * 60)
    
    try:
        config = get_config()
        weaviate_url = config.get('weaviate.url')
        logger.info(f"Weaviate URL: {weaviate_url}")
        
        manager = CollectionManager(weaviate_url)
        
        # 检查 NewsChunk schema
        test_collection = "TestNewsChunk"
        
        # 删除旧的测试 collection
        if manager.collection_exists(test_collection):
            logger.info(f"删除旧的测试 collection: {test_collection}")
            manager.delete_collection(test_collection)
        
        # 创建测试 collection
        logger.info(f"创建测试 collection: {test_collection}")
        schema = manager.NEWS_CHUNK_SCHEMA.copy()
        schema['class'] = test_collection
        manager.client.schema.create_class(schema)
        
        logger.success(f"✓ Collection 创建成功")
        
        # 5. 测试批量插入
        logger.info("\n" + "=" * 60)
        logger.info("步骤 4: 测试批量插入 (前 10 个 chunks)")
        logger.info("=" * 60)
        
        from datetime import datetime
        
        # 准备测试数据
        test_chunks = []
        for chunk in chunks[:10]:  # 只测试前 10 个
            chunk_data = {
                "chunk_id": chunk.chunk_id,
                "content": chunk.content,
                "task_name": "test-task",
                "categories": chunk.metadata["categories"],
                "sources": chunk.metadata["sources"],
                "article_titles": chunk.metadata["article_titles"],
                "article_count": chunk.metadata["article_count"],
                "char_count": chunk.metadata["char_count"],
                "created_at": datetime.now().isoformat() + "Z"
            }
            test_chunks.append(chunk_data)
        
        # 批量插入
        success_count = manager.batch_insert_chunks(
            collection_name=test_collection,
            chunks=test_chunks,
            batch_size=5
        )
        
        logger.success(f"✓ 成功插入 {success_count}/{len(test_chunks)} 个 chunks")
        
        # 6. 测试混合搜索
        logger.info("\n" + "=" * 60)
        logger.info("步骤 5: 测试混合搜索")
        logger.info("=" * 60)
        
        test_queries = [
            "人工智能",
            "经济增长",
            "科技发展"
        ]
        
        for query in test_queries:
            logger.info(f"\n查询: '{query}'")
            results = manager.hybrid_search(
                collection_name=test_collection,
                query=query,
                alpha=0.75,
                limit=3,
                similarity_threshold=0.5
            )
            
            logger.info(f"  找到 {len(results)} 条结果:")
            for i, result in enumerate(results, 1):
                score = float(result['_additional']['score'])  # Convert to float
                article_count = result.get('article_count', 0)
                sources = result.get('sources', [])
                logger.info(f"    {i}. 分数: {score:.3f}, 包含 {article_count} 篇文章, 来源: {', '.join(sources[:2])}")
        
        # 清理测试 collection
        logger.info(f"\n清理测试 collection: {test_collection}")
        manager.delete_collection(test_collection)
        
        logger.success("\n" + "=" * 60)
        logger.success("✓ 所有测试通过！")
        logger.success("=" * 60)
        
    except Exception as e:
        logger.error(f"测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_chunking())
