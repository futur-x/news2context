"""
快速验证：处理 0 篇文章时不会出现 division by zero 错误
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.utils.chunker import ArticleChunker


def test_zero_articles():
    """测试处理 0 篇文章的情况"""
    print("\n=== 测试：处理 0 篇文章 ===")

    chunker = ArticleChunker(max_tokens=6000)

    # 传入空列表
    articles = []

    try:
        chunks = chunker.chunk_articles(articles, task_name="test")

        print(f"✅ 测试通过！")
        print(f"   输入: {len(articles)} 篇文章")
        print(f"   输出: {len(chunks)} 个 chunks")
        print(f"   没有出现 division by zero 错误")

        return True

    except ZeroDivisionError as e:
        print(f"❌ 测试失败：出现 division by zero 错误")
        print(f"   错误信息: {e}")
        return False
    except Exception as e:
        print(f"❌ 测试失败：出现其他错误")
        print(f"   错误信息: {e}")
        return False


if __name__ == "__main__":
    success = test_zero_articles()
    sys.exit(0 if success else 1)
