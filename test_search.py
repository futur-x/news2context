
import sys
import os

# 添加项目根目录到 path
sys.path.append(os.getcwd())

from src.storage.weaviate_client import CollectionManager
from src.utils.config import get_config

def test_search():
    config = get_config()
    collection_manager = CollectionManager(
        weaviate_url=config.get('weaviate.url'),
        api_key=config.get('weaviate.api_key')
    )
    
    collection_name = "News_jj2_db"
    query = "航班"
    
    print(f"Testing search on collection: {collection_name}")
    print(f"Query: {query}")
    
    try:
        # Test hybrid search
        print("\n--- Hybrid Search (alpha=0.5) ---")
        results = collection_manager.hybrid_search(
            collection_name=collection_name,
            query=query,
            limit=5,
            alpha=0.5,
            similarity_threshold=0.0
        )
        print(f"Found {len(results)} results")
        for item in results:
            print(f"- Title: {item.get('article_titles', ['No Title'])[0]}")
            print(f"  Score: {item.get('_additional', {}).get('score')}")
            
        # Test hybrid search with keyword only
        print("\n--- Keyword Search (alpha=0.0) ---")
        results = collection_manager.hybrid_search(
            collection_name=collection_name,
            query=query,
            limit=5,
            alpha=0.0,
            similarity_threshold=0.0
        )
        print(f"Found {len(results)} results")
        for item in results:
            print(f"- Title: {item.get('article_titles', ['No Title'])[0]}")
            print(f"  Score: {item.get('_additional', {}).get('score')}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_search()
