"""
单元测试：验证智能切割功能
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.utils.chunker import ArticleChunker
from src.utils.markdown_parser import Article
from datetime import datetime


def test_short_article():
    """测试短文章（不需要切割）"""
    print("\n=== 测试 1: 短文章（不切割）===")

    chunker = ArticleChunker(max_tokens=6000)

    # 创建一个短文章（约 100 字）
    article = Article(
        title="短文章测试",
        source="测试源",
        category="测试",
        url="https://test.com/short",
        content="这是一篇短文章。" * 20,  # 约 100 字
        char_count=100
    )

    chunks = chunker.chunk_article(article, task_name="test_task")

    assert len(chunks) == 1, f"短文章应该只有 1 个 chunk，实际: {len(chunks)}"
    assert chunks[0].chunk_index == 0, "chunk_index 应该是 0"
    assert chunks[0].total_chunks == 1, "total_chunks 应该是 1"
    assert chunks[0].title == "短文章测试"
    assert chunks[0].url == "https://test.com/short"

    print(f"✅ 短文章测试通过: {len(chunks)} chunk")
    print(f"   Article ID: {chunks[0].article_id}")
    print(f"   Content length: {len(chunks[0].content)} 字符")


def test_long_article():
    """测试长文章（需要切割）"""
    print("\n=== 测试 2: 长文章（需要切割）===")

    chunker = ArticleChunker(max_tokens=500)  # 设置小的限制便于测试

    # 创建一个长文章（模拟超长内容）
    long_content = "\n\n".join([
        f"这是第 {i} 段内容。" + ("人工智能技术正在快速发展，深度学习、机器学习、自然语言处理等领域都取得了重大突破。" * 10)
        for i in range(20)
    ])

    article = Article(
        title="人工智能的未来发展趋势",
        source="科技日报",
        category="科技",
        url="https://test.com/long-ai-article",
        content=long_content,
        char_count=len(long_content)
    )

    chunks = chunker.chunk_article(article, task_name="test_task")

    print(f"✅ 长文章切割结果:")
    print(f"   原文长度: {len(long_content)} 字符")
    print(f"   切割成: {len(chunks)} 个 chunks")

    assert len(chunks) > 1, f"长文章应该被切割成多个 chunks，实际: {len(chunks)}"

    # 验证所有 chunks 的 article_id 相同
    article_ids = [chunk.article_id for chunk in chunks]
    assert len(set(article_ids)) == 1, "所有 chunks 的 article_id 应该相同"

    # 验证 chunk_index 连续
    for i, chunk in enumerate(chunks):
        assert chunk.chunk_index == i, f"第 {i} 个 chunk 的 index 应该是 {i}，实际: {chunk.chunk_index}"
        assert chunk.total_chunks == len(chunks), f"total_chunks 应该是 {len(chunks)}，实际: {chunk.total_chunks}"
        assert chunk.title == "人工智能的未来发展趋势", "所有 chunks 应该有相同的标题"
        assert chunk.url == "https://test.com/long-ai-article", "所有 chunks 应该有相同的 URL"

        # 验证每个 chunk 都包含索引信息
        if i == 0:
            assert "【第 1/" in chunk.content, "第一个 chunk 应该包含【第 1/X 部分】"

        print(f"   Chunk {i + 1}/{len(chunks)}: {len(chunk.content)} 字符")

    print(f"   共享 Article ID: {chunks[0].article_id}")


def test_article_id_consistency():
    """测试相同 URL 的文章有相同的 article_id"""
    print("\n=== 测试 3: Article ID 一致性 ===")

    chunker = ArticleChunker(max_tokens=6000)

    url = "https://test.com/same-url"

    # 创建两篇 URL 相同的文章
    article1 = Article(
        title="文章1",
        source="源1",
        category="分类1",
        url=url,
        content="内容1",
        char_count=10
    )

    article2 = Article(
        title="文章2",
        source="源2",
        category="分类2",
        url=url,
        content="内容2",
        char_count=10
    )

    chunks1 = chunker.chunk_article(article1, task_name="test_task")
    chunks2 = chunker.chunk_article(article2, task_name="test_task")

    assert chunks1[0].article_id == chunks2[0].article_id, \
        "相同 URL 的文章应该有相同的 article_id"

    print(f"✅ Article ID 一致性测试通过")
    print(f"   URL: {url}")
    print(f"   Article ID: {chunks1[0].article_id}")


def test_chunk_content_format():
    """测试 chunk 内容格式"""
    print("\n=== 测试 4: Chunk 内容格式 ===")

    chunker = ArticleChunker(max_tokens=500)  # 小限制，确保切割

    long_content = "\n\n".join([
        f"段落 {i}：" + ("这是测试内容。" * 30)
        for i in range(10)
    ])

    article = Article(
        title="格式测试文章",
        source="测试源",
        category="测试分类",
        url="https://test.com/format",
        content=long_content,
        char_count=len(long_content)
    )

    chunks = chunker.chunk_article(article, task_name="test_task")

    print(f"切割成 {len(chunks)} 个 chunks")

    for i, chunk in enumerate(chunks):
        content = chunk.content

        # 验证包含标题
        assert "格式测试文章" in content, f"Chunk {i} 应该包含文章标题"

        # 验证包含来源和分类
        assert "测试源" in content, f"Chunk {i} 应该包含来源"
        assert "测试分类" in content, f"Chunk {i} 应该包含分类"

        # 验证包含链接
        assert "https://test.com/format" in content, f"Chunk {i} 应该包含链接"

        # 验证包含索引信息（除了单 chunk 的情况）
        if len(chunks) > 1:
            assert f"【第 {i + 1}/{len(chunks)} 部分】" in content, \
                f"Chunk {i} 应该包含【第 {i+1}/{len(chunks)} 部分】标记"

        print(f"   Chunk {i + 1} 格式验证通过 ✓")

    # 注意：Article 类没有 published_at 字段，所以 chunk 内容不会包含发布时间

    print(f"✅ 内容格式测试通过")


def test_token_counting():
    """测试 token 计数"""
    print("\n=== 测试 5: Token 计数 ===")

    chunker = ArticleChunker(max_tokens=6000)

    # 测试不同长度的文本
    test_cases = [
        ("短文本", "你好世界" * 10, "应该很少"),
        ("中文本", "人工智能技术" * 100, "应该适中"),
        ("长文本", "深度学习和机器学习是现代AI的核心技术。" * 500, "应该较多"),
    ]

    for name, text, expected in test_cases:
        token_count = chunker.count_tokens(text)
        print(f"   {name}: {len(text)} 字符 → {token_count} tokens ({expected})")
        assert token_count > 0, f"{name} 的 token 数应该大于 0"

    print(f"✅ Token 计数测试通过")


def test_batch_chunking():
    """测试批量切割"""
    print("\n=== 测试 6: 批量切割 ===")

    chunker = ArticleChunker(max_tokens=500)

    articles = [
        Article(
            title=f"文章 {i}",
            source="批量测试源",
            category="测试",
            url=f"https://test.com/batch-{i}",
            content="测试内容。" * (50 * i),  # 不同长度
            char_count=50 * i
        )
        for i in range(1, 6)  # 5 篇文章
    ]

    all_chunks = chunker.chunk_articles(articles, task_name="batch_test")

    print(f"✅ 批量切割结果:")
    print(f"   原始文章: {len(articles)} 篇")
    print(f"   生成 chunks: {len(all_chunks)} 个")
    print(f"   平均每篇: {len(all_chunks) / len(articles):.1f} chunks")

    assert len(all_chunks) >= len(articles), "chunks 数量应该 >= 文章数量"

    # 验证每篇文章的 chunks 有正确的 article_id
    for article in articles:
        article_id = chunker.generate_article_id(article.url)
        article_chunks = [c for c in all_chunks if c.article_id == article_id]
        print(f"   文章 '{article.title}': {len(article_chunks)} chunks")
        assert len(article_chunks) > 0, f"文章 {article.title} 应该有至少 1 个 chunk"


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("开始运行智能切割单元测试")
    print("=" * 60)

    try:
        test_short_article()
        test_long_article()
        test_article_id_consistency()
        test_chunk_content_format()
        test_token_counting()
        test_batch_chunking()

        print("\n" + "=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)

        return True

    except AssertionError as e:
        print("\n" + "=" * 60)
        print(f"❌ 测试失败: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ 测试出错: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
