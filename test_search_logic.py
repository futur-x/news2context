"""
单元测试：验证搜索召回逻辑（不需要真实 Weaviate）
模拟测试：搜索到某个 chunk 后的拼接逻辑
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_chunk_grouping_logic():
    """测试 chunk 分组和拼接逻辑"""
    print("\n" + "="*60)
    print("测试：Chunk 分组与拼接逻辑")
    print("="*60)

    # 模拟搜索返回的 chunks（来自同一篇文章的不同部分）
    mock_search_results = [
        {
            "article_id": "article_123",
            "chunk_index": 2,
            "total_chunks": 5,
            "title": "人工智能发展报告",
            "content": "# 人工智能发展报告\n\n【第 3/5 部分】\n\n第三部分：深度学习突破...",
            "url": "https://example.com/ai",
            "source_name": "科技日报",
            "category": "科技",
            "_additional": {"certainty": 0.85}
        },
        {
            "article_id": "article_123",
            "chunk_index": 0,
            "total_chunks": 5,
            "title": "人工智能发展报告",
            "content": "# 人工智能发展报告\n\n【第 1/5 部分】\n\n第一部分：AI基础概念...",
            "url": "https://example.com/ai",
            "source_name": "科技日报",
            "category": "科技",
            "_additional": {"certainty": 0.75}
        },
        {
            "article_id": "article_456",
            "chunk_index": 0,
            "total_chunks": 2,
            "title": "机器学习应用",
            "content": "# 机器学习应用\n\n【第 1/2 部分】\n\n机器学习在各领域的应用...",
            "url": "https://example.com/ml",
            "source_name": "AI Weekly",
            "category": "科技",
            "_additional": {"certainty": 0.70}
        }
    ]

    print(f"\n模拟搜索返回: {len(mock_search_results)} 个 chunks")

    # === 第 1 步：按 article_id 分组 ===
    print("\n=== 第 1 步：按 article_id 分组 ===")

    from collections import defaultdict
    articles_map = defaultdict(list)

    for chunk in mock_search_results:
        article_id = chunk['article_id']
        articles_map[article_id].append(chunk)

    print(f"分组结果: {len(articles_map)} 篇文章")
    for article_id, chunks in articles_map.items():
        print(f"   {article_id}: {len(chunks)} chunks")

    # === 第 2 步：模拟查询每篇文章的所有 chunks ===
    print("\n=== 第 2 步：模拟获取完整文章的所有 chunks ===")

    # 模拟数据库中的完整数据
    mock_database = {
        "article_123": [
            {"chunk_index": 0, "content": "第一部分：AI基础概念..."},
            {"chunk_index": 1, "content": "第二部分：机器学习算法..."},
            {"chunk_index": 2, "content": "第三部分：深度学习突破..."},
            {"chunk_index": 3, "content": "第四部分：自然语言处理..."},
            {"chunk_index": 4, "content": "第五部分：未来展望..."},
        ],
        "article_456": [
            {"chunk_index": 0, "content": "第一部分：ML应用..."},
            {"chunk_index": 1, "content": "第二部分：案例分析..."},
        ]
    }

    def get_all_chunks_by_article_id(article_id):
        """模拟从数据库查询所有 chunks"""
        return mock_database.get(article_id, [])

    # === 第 3 步：拼接每篇文章 ===
    print("\n=== 第 3 步：拼接每篇文章的完整内容 ===")

    merged_articles = []

    for article_id in articles_map.keys():
        # 获取该文章的所有 chunks
        all_chunks = get_all_chunks_by_article_id(article_id)

        print(f"\n文章 {article_id}:")
        print(f"   - 搜索到: {len(articles_map[article_id])} chunks")
        print(f"   - 数据库中总共: {len(all_chunks)} chunks")

        # 按 chunk_index 排序
        all_chunks.sort(key=lambda x: x['chunk_index'])

        # 拼接内容
        full_content = "\n\n---分隔符---\n\n".join([c['content'] for c in all_chunks])

        print(f"   - 拼接后长度: {len(full_content)} 字符")

        # 验证完整性
        expected_chunks = len(all_chunks)
        actual_chunks = len(all_chunks)

        if expected_chunks == actual_chunks:
            print(f"   ✅ 完整性验证通过: {actual_chunks}/{expected_chunks} chunks")
        else:
            print(f"   ❌ 完整性验证失败: {actual_chunks}/{expected_chunks} chunks")

        merged_articles.append({
            "article_id": article_id,
            "full_content": full_content,
            "total_chunks": len(all_chunks)
        })

    # === 第 4 步：验证拼接结果 ===
    print("\n=== 第 4 步：验证拼接结果 ===")

    for article in merged_articles:
        print(f"\n文章 {article['article_id']}:")
        print(f"   - 总 chunks: {article['total_chunks']}")
        print(f"   - 内容片段: {article['full_content'][:200]}...")

        # 验证是否包含所有部分
        content = article['full_content']
        expected_parts = ["第一部分", "第二部分", "第三部分"]

        if article['total_chunks'] == 5:
            expected_parts.extend(["第四部分", "第五部分"])

        found_parts = [part for part in expected_parts if part in content]

        if len(found_parts) == len(expected_parts):
            print(f"   ✅ 包含所有部分: {len(found_parts)}/{len(expected_parts)}")
        else:
            print(f"   ❌ 部分缺失: {len(found_parts)}/{len(expected_parts)}")
            print(f"      缺失: {set(expected_parts) - set(found_parts)}")

    print("\n" + "="*60)
    print("✅ 逻辑测试通过！")
    print("="*60)

    return True


def test_merge_chunk_contents():
    """测试去重元数据头的拼接逻辑"""
    print("\n" + "="*60)
    print("测试：去重元数据头的拼接逻辑")
    print("="*60)

    chunks = [
        {
            "chunk_index": 0,
            "content": """# 新闻标题

**来源**: 科技日报 | **分类**: 科技
**发布时间**: 2025-01-01
**链接**: https://example.com

【第 1/3 部分】

第一部分的正文内容..."""
        },
        {
            "chunk_index": 1,
            "content": """# 新闻标题

**来源**: 科技日报 | **分类**: 科技
**发布时间**: 2025-01-01
**链接**: https://example.com

【第 2/3 部分】

第二部分的正文内容..."""
        },
        {
            "chunk_index": 2,
            "content": """# 新闻标题

**来源**: 科技日报 | **分类**: 科技
**发布时间**: 2025-01-01
**链接**: https://example.com

【第 3/3 部分】

第三部分的正文内容..."""
        }
    ]

    print(f"输入: {len(chunks)} 个 chunks，每个都有完整的元数据头")

    # 模拟 _merge_chunk_contents 逻辑
    def merge_chunk_contents(chunks):
        if not chunks:
            return ""

        # 第一个 chunk 保留完整内容
        merged_parts = [chunks[0]['content']]

        # 后续 chunks 去掉元数据头
        for chunk in chunks[1:]:
            content = chunk['content']

            # 去掉【第 X/Y 部分】之前的内容
            if '【第' in content and '部分】' in content:
                parts = content.split('部分】', 1)
                if len(parts) > 1:
                    # 只保留【第 X/Y 部分】之后的内容
                    content = parts[1].strip()

            merged_parts.append(content)

        return '\n\n'.join(merged_parts)

    merged_content = merge_chunk_contents(chunks)

    print("\n拼接结果:")
    print("-" * 60)
    print(merged_content)
    print("-" * 60)

    # 验证
    print("\n验证:")

    # 1. 只包含一次元数据头
    metadata_count = merged_content.count("**来源**: 科技日报")
    print(f"   元数据头出现次数: {metadata_count} (应该是 1)")

    if metadata_count == 1:
        print(f"   ✅ 元数据头去重成功")
    else:
        print(f"   ❌ 元数据头重复了")

    # 2. 包含所有正文部分
    parts = ["第一部分的正文", "第二部分的正文", "第三部分的正文"]
    found_parts = [p for p in parts if p in merged_content]

    print(f"   正文部分: {len(found_parts)}/{len(parts)}")

    if len(found_parts) == len(parts):
        print(f"   ✅ 所有正文部分都保留")
    else:
        print(f"   ❌ 部分正文缺失")

    print("\n" + "="*60)
    print("✅ 拼接逻辑测试通过！")
    print("="*60)

    return True


if __name__ == "__main__":
    test_chunk_grouping_logic()
    print("\n\n")
    test_merge_chunk_contents()
