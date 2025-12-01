"""检查 Weaviate 中的数据"""
import asyncio
from src.storage.weaviate_client import CollectionManager
from src.utils.config import get_config

async def main():
    config = get_config()
    cm = CollectionManager(
        weaviate_url=config.get('weaviate.url'),
        api_key=config.get('weaviate.api_key')
    )
    
    collection_name = "Ceo_2_db"
    
    # 获取所有数据的统计
    print(f"\n=== Collection: {collection_name} ===\n")
    
    # 按分类统计
    categories = {}
    sources = {}
    
    # 获取一些样本数据
    results = cm.search_news(collection_name, "政策", limit=10)
    
    print(f"搜索'政策'找到 {len(results)} 条结果:\n")
    for i, item in enumerate(results, 1):
        print(f"{i}. [{item.get('category')}] {item.get('title')}")
        print(f"   来源: {item.get('source_name')}")
        print(f"   内容预览: {item.get('content', '')[:100]}...")
        print()
    
    # 搜索国家相关
    results2 = cm.search_news(collection_name, "国家 政府", limit=10)
    print(f"\n搜索'国家 政府'找到 {len(results2)} 条结果:\n")
    for i, item in enumerate(results2, 1):
        print(f"{i}. [{item.get('category')}] {item.get('title')}")
        print(f"   来源: {item.get('source_name')}")
        print()

if __name__ == "__main__":
    asyncio.run(main())
