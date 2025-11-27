"""
查询路由
"""

from fastapi import APIRouter, HTTPException
from src.api.models import SearchRequest, SearchResponse, NewsItem
from src.core.task_manager import TaskManager
from src.storage.weaviate_client import CollectionManager
from src.utils.config import get_config

router = APIRouter()

@router.post("/query", response_model=SearchResponse)
async def search_news(request: SearchRequest):
    """语义搜索新闻"""
    config = get_config()
    task_manager = TaskManager()
    collection_manager = CollectionManager(
        weaviate_url=config.get('weaviate.url'),
        api_key=config.get('weaviate.api_key')
    )
    
    all_results = []
    
    # 确定要搜索的 Collection
    collections_to_search = []
    
    if request.task_name:
        task = task_manager.get_task(request.task_name)
        if not task:
            raise HTTPException(status_code=404, detail=f"Task not found: {request.task_name}")
        collections_to_search.append(task.weaviate['collection'])
    else:
        # 搜索所有任务
        tasks = task_manager.list_tasks()
        collections_to_search = [t.weaviate['collection'] for t in tasks]
    
    # 执行搜索
    for collection_name in collections_to_search:
        try:
            results = collection_manager.search_news(
                collection_name=collection_name,
                query=request.query,
                limit=request.limit
            )
            
            # 转换结果
            for item in results:
                news_item = NewsItem(
                    id=item.get('_additional', {}).get('id'),
                    title=item.get('title'),
                    content=item.get('content'),
                    url=item.get('url'),
                    source_name=item.get('source_name'),
                    published_at=item.get('published_at'),
                    score=item.get('_additional', {}).get('certainty'),
                    task_name=item.get('task_name')
                )
                all_results.append(news_item)
                
        except Exception as e:
            # 记录错误但继续搜索其他 Collection
            print(f"Error searching collection {collection_name}: {e}")
            continue
    
    # 对所有结果按分数排序
    all_results.sort(key=lambda x: x.score if x.score else 0, reverse=True)
    
    # 截取 Top N
    final_results = all_results[:request.limit]
    
    return SearchResponse(
        results=final_results,
        total=len(final_results),
        query=request.query
    )
