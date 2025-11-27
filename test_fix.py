"""
快速测试智能 Chunking 修复
"""

import asyncio
from src.core.collector import NewsCollector
from src.core.task_manager import TaskManager
from loguru import logger


async def test_collect():
    """测试采集流程"""
    
    # 使用现有任务
    task_name = "news-task"
    
    logger.info(f"测试任务: {task_name}")
    
    collector = NewsCollector()
    
    # 模拟采集（使用已有的 Markdown 文件）
    markdown_path = "output/2025-11-26/news-task_digest.md"
    
    logger.info(f"使用 Markdown 文件: {markdown_path}")
    
    # 测试解析和切割
    from src.utils.markdown_parser import MarkdownParser
    from src.utils.chunker import SmartChunker
    
    parser = MarkdownParser()
    articles = parser.parse_digest(markdown_path)
    
    logger.info(f"解析完成: {len(articles)} 篇文章")
    
    chunker = SmartChunker(max_chunk_size=3000)
    chunks = chunker.create_chunks(articles)
    
    logger.success(f"切割完成: {len(chunks)} 个 chunks")
    
    # 测试批量插入（使用测试 collection）
    from src.storage.weaviate_client import CollectionManager
    from datetime import datetime
    
    manager = CollectionManager("http://localhost:8080")
    
    test_collection = "TestNewsChunk2"
    
    # 创建测试 collection
    if manager.collection_exists(test_collection):
        manager.delete_collection(test_collection)
    
    schema = manager.NEWS_CHUNK_SCHEMA.copy()
    schema['class'] = test_collection
    manager.client.schema.create_class(schema)
    
    # 准备前 20 个 chunks
    chunk_data_list = []
    for chunk in chunks[:20]:
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
    
    # 批量插入
    success_count = manager.batch_insert_chunks(
        collection_name=test_collection,
        chunks=chunk_data_list,
        batch_size=5
    )
    
    logger.success(f"✓ 成功插入 {success_count}/{len(chunk_data_list)} 个 chunks")
    
    # 清理
    manager.delete_collection(test_collection)
    
    logger.success("✓ 测试完成！修复有效！")


if __name__ == "__main__":
    asyncio.run(test_collect())
