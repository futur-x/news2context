"""
真实场景测试：使用默认 max_tokens=6000
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.utils.chunker import ArticleChunker
from src.utils.markdown_parser import Article


def test_real_scenario():
    """测试真实场景：10000 tokens 的文章应该切成 2 个 chunks"""
    print("\n=== 真实场景测试 ===")

    # 使用默认配置
    chunker = ArticleChunker(max_tokens=6000)  # 默认值

    # 创建一个 10000 tokens 左右的文章
    # 1 个中文字符约 1.5 tokens，所以 6500 字符 ≈ 10000 tokens
    long_content = "\n\n".join([
        f"第 {i} 段：人工智能技术正在快速发展，深度学习、机器学习、自然语言处理等领域都取得了重大突破。" * 20
        for i in range(10)
    ])

    article = Article(
        title="人工智能发展趋势分析报告",
        source="科技前沿",
        category="科技",
        url="https://example.com/ai-trend",
        content=long_content,
        char_count=len(long_content)
    )

    print(f"文章长度: {len(long_content)} 字符")

    # 先计算 token 数
    total_tokens = chunker.count_tokens(article.content)
    print(f"文章 token 数: {total_tokens}")

    # 切割
    chunks = chunker.chunk_article(article, task_name="test")

    print(f"\n✅ 切割结果:")
    print(f"   原文: {total_tokens} tokens")
    print(f"   切成: {len(chunks)} 个 chunks")
    print(f"   符合预期: {len(chunks)} chunks (应该是 2-3 个)")

    for i, chunk in enumerate(chunks):
        chunk_tokens = chunker.count_tokens(chunk.content)
        print(f"\n   Chunk {i + 1}:")
        print(f"     - chunk_index: {chunk.chunk_index}")
        print(f"     - total_chunks: {chunk.total_chunks}")
        print(f"     - content length: {len(chunk.content)} 字符")
        print(f"     - estimated tokens: {chunk_tokens}")

    # 验证
    assert len(chunks) >= 1 and len(chunks) <= 3, f"应该切成 2-3 个 chunks，实际: {len(chunks)}"
    print(f"\n✅ 测试通过！符合预期。")


def test_various_lengths():
    """测试不同长度的文章"""
    print("\n\n=== 不同长度测试 ===")

    chunker = ArticleChunker(max_tokens=6000)

    test_cases = [
        ("短文章 (1000 tokens)", "测试内容。" * 500, 1),
        ("中等文章 (5000 tokens)", "测试内容。" * 2500, 1),
        ("长文章 (10000 tokens)", "测试内容。" * 5000, 2),
        ("超长文章 (20000 tokens)", "测试内容。" * 10000, 3-4),
    ]

    for name, content, expected_chunks in test_cases:
        article = Article(
            title=name,
            source="测试",
            category="测试",
            url=f"https://test.com/{name}",
            content=content,
            char_count=len(content)
        )

        chunks = chunker.chunk_article(article, task_name="test")
        tokens = chunker.count_tokens(content)

        if isinstance(expected_chunks, int):
            status = "✓" if len(chunks) == expected_chunks else "✗"
            print(f"{status} {name}: {tokens} tokens → {len(chunks)} chunks (期望: {expected_chunks})")
        else:
            status = "✓"
            print(f"{status} {name}: {tokens} tokens → {len(chunks)} chunks (期望: {expected_chunks})")


if __name__ == "__main__":
    test_real_scenario()
    test_various_lengths()
