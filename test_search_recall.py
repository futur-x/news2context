"""
集成测试：验证搜索召回功能
测试场景：搜索到某个 chunk 后，能否召回并拼接整篇文章的所有 chunks
"""

import sys
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.utils.chunker import ArticleChunker
from src.utils.markdown_parser import Article
from src.storage.weaviate_client import CollectionManager
from src.utils.config import get_config


def test_search_recall():
    """测试搜索召回：搜到某个 chunk，返回完整文章"""
    print("\n" + "="*60)
    print("集成测试：搜索召回与拼接功能")
    print("="*60)

    # 初始化
    config = get_config()

    # 获取 Embedding API Key
    embedding_api_key = config.get('embedding.api_key') or config.get('llm.api_key')
    headers = {}
    if embedding_api_key:
        headers["X-OpenAI-Api-Key"] = embedding_api_key

    # 准备 embedding 配置
    embedding_config = {
        'model': config.get('embedding.model', 'text-embedding-3-small'),
        'base_url': config.get('embedding.base_url', 'https://litellm.futurx.cc'),
        'dimensions': config.get('embedding.dimensions', 1536)
    }

    try:
        collection_manager = CollectionManager(
            weaviate_url=config.get('weaviate.url'),
            api_key=config.get('weaviate.api_key'),
            additional_headers=headers,
            embedding_config=embedding_config
        )
    except Exception as e:
        print(f"❌ 无法连接到 Weaviate: {e}")
        print("   请确保 Weaviate 服务正在运行：docker-compose up -d")
        return False

    # 测试 collection 名称
    test_collection = "TestSearchRecall"

    try:
        # 清理可能存在的旧测试数据
        if collection_manager.collection_exists(test_collection):
            print(f"\n清理旧测试数据: {test_collection}")
            collection_manager.delete_collection(test_collection)

        # 创建测试 collection（使用 NewsChunk schema）
        print(f"\n创建测试 collection: {test_collection}")
        collection_manager.create_collection(
            test_collection,
            collection_manager.NEWS_CHUNK_SCHEMA
        )

        # === 第 1 步：准备测试数据 ===
        print("\n=== 第 1 步：准备测试数据 ===")

        # 创建一篇长文章，包含特定关键词在不同位置
        chunker = ArticleChunker(max_tokens=1000)  # 设置较小的值确保切割

        # 文章内容：在第 1、3、5 部分包含不同的关键词
        part1 = "第一部分内容：介绍人工智能的基础概念。" + ("AI技术发展迅速。" * 100)
        part2 = "第二部分内容：深入探讨机器学习算法。" + ("传统算法面临挑战。" * 100)
        part3 = "第三部分内容：讨论深度学习的突破。" + ("神经网络性能优异。" * 100)
        part4 = "第四部分内容：分析自然语言处理进展。" + ("NLP应用广泛。" * 100)
        part5 = "第五部分内容：展望量子计算的未来。" + ("量子优势明显。" * 100)

        long_content = "\n\n".join([part1, part2, part3, part4, part5])

        article = Article(
            title="AI技术全面解析",
            source="科技日报",
            category="科技",
            url="https://test.com/ai-analysis",
            content=long_content,
            char_count=len(long_content)
        )

        # 切割成 chunks
        chunks = chunker.chunk_articles([article], task_name="test_search")

        print(f"文章被切割成: {len(chunks)} 个 chunks")

        # 检查每个 chunk 的内容
        for i, chunk in enumerate(chunks):
            content_preview = chunk.content[:100].replace('\n', ' ')
            print(f"   Chunk {i}: {content_preview}...")

        # === 第 2 步：插入数据到 Weaviate ===
        print(f"\n=== 第 2 步：插入 {len(chunks)} 个 chunks 到 Weaviate ===")

        chunk_data_list = []
        for chunk in chunks:
            chunk_data = {
                "article_id": chunk.article_id,
                "chunk_index": chunk.chunk_index,
                "total_chunks": chunk.total_chunks,
                "title": chunk.title,
                "content": chunk.content,
                "url": chunk.url,
                "source_name": chunk.source_name,
                "source_hashid": chunk.source_hashid,
                "category": chunk.category,
                "published_at": datetime.now().isoformat() + "Z",
                "fetched_at": datetime.now().isoformat() + "Z",
                "task_name": chunk.task_name,
                "excerpt": chunk.excerpt
            }
            chunk_data_list.append(chunk_data)

        inserted_count = collection_manager.batch_insert_chunks(
            collection_name=test_collection,
            chunks=chunk_data_list,
            batch_size=5
        )

        print(f"✓ 成功插入: {inserted_count} 个 chunks")

        # 等待 Weaviate 索引
        import time
        print("等待 Weaviate 索引...")
        time.sleep(2)

        # === 第 3 步：测试不同的搜索关键词 ===
        print("\n=== 第 3 步：测试搜索召回 ===")

        test_queries = [
            ("神经网络", "应该在第 3 部分"),
            ("量子计算", "应该在第 5 部分"),
            ("基础概念", "应该在第 1 部分"),
        ]

        all_passed = True

        for query, expected_location in test_queries:
            print(f"\n🔍 搜索: '{query}' ({expected_location})")

            # 使用统一搜索接口
            results = collection_manager.unified_search(
                collection_name=test_collection,
                query=query,
                limit=5
            )

            if not results:
                print(f"   ❌ 没有搜索到任何结果")
                all_passed = False
                continue

            # 检查第一个结果
            result = results[0]

            print(f"   ✓ 找到结果:")
            print(f"     - 标题: {result.get('title')}")
            print(f"     - Article ID: {result.get('id')}")
            print(f"     - Chunks 数量: {result.get('_additional', {}).get('chunk_count', 'N/A')}")
            print(f"     - 内容长度: {len(result.get('content', ''))} 字符")
            print(f"     - 相关度: {result.get('_additional', {}).get('certainty', 0):.3f}")

            # 验证内容完整性
            content = result.get('content', '')

            # 检查是否包含所有部分的关键词（证明拼接了所有 chunks）
            expected_keywords = [
                "第一部分",
                "第二部分",
                "第三部分",
                "第四部分",
                "第五部分"
            ]

            found_keywords = [kw for kw in expected_keywords if kw in content]

            if len(found_keywords) == len(expected_keywords):
                print(f"   ✅ 验证通过: 包含所有 {len(expected_keywords)} 个部分（完整拼接）")
            else:
                print(f"   ❌ 验证失败: 只找到 {len(found_keywords)}/{len(expected_keywords)} 个部分")
                print(f"      缺失: {set(expected_keywords) - set(found_keywords)}")
                all_passed = False

            # 检查是否包含搜索关键词
            if query in content:
                print(f"   ✅ 包含搜索关键词: '{query}'")
            else:
                print(f"   ⚠️  未找到搜索关键词: '{query}'")

        # === 第 4 步：验证 article_id 关联 ===
        print(f"\n=== 第 4 步：验证 article_id 关联 ===")

        # 直接查询所有 chunks
        all_chunks_query = collection_manager.client.query.get(
            test_collection,
            ["article_id", "chunk_index", "total_chunks", "title"]
        ).with_limit(100).do()

        all_chunks_data = all_chunks_query['data']['Get'].get(test_collection, [])

        # 按 article_id 分组
        from collections import defaultdict
        articles_map = defaultdict(list)

        for chunk_data in all_chunks_data:
            article_id = chunk_data.get('article_id')
            articles_map[article_id].append(chunk_data)

        print(f"数据库中的文章数: {len(articles_map)}")

        for article_id, article_chunks in articles_map.items():
            print(f"\n   Article ID: {article_id}")
            print(f"     - 标题: {article_chunks[0].get('title')}")
            print(f"     - Chunks 数量: {len(article_chunks)}")
            print(f"     - Total chunks (声明): {article_chunks[0].get('total_chunks')}")

            # 验证 chunk_index 连续
            indices = sorted([c.get('chunk_index') for c in article_chunks])
            expected_indices = list(range(len(article_chunks)))

            if indices == expected_indices:
                print(f"     ✅ Chunk 索引连续: {indices}")
            else:
                print(f"     ❌ Chunk 索引不连续: {indices}")
                all_passed = False

        # === 清理测试数据 ===
        print(f"\n=== 清理测试数据 ===")
        collection_manager.delete_collection(test_collection)
        print(f"✓ 已删除测试 collection: {test_collection}")

        # === 测试结果 ===
        print("\n" + "="*60)
        if all_passed:
            print("✅ 所有测试通过！搜索召回功能正常。")
        else:
            print("❌ 部分测试失败，请检查上面的错误信息。")
        print("="*60)

        return all_passed

    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()

        # 清理测试数据
        try:
            if collection_manager.collection_exists(test_collection):
                collection_manager.delete_collection(test_collection)
        except:
            pass

        return False


if __name__ == "__main__":
    success = test_search_recall()
    sys.exit(0 if success else 1)
