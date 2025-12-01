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
    
    # 获取 Embedding API Key（优先使用 embedding.api_key，否则使用 llm.api_key）
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
    
    collection_manager = CollectionManager(
        weaviate_url=config.get('weaviate.url'),
        api_key=config.get('weaviate.api_key'),
        additional_headers=headers,
        embedding_config=embedding_config
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
    
    # 确定搜索参数
    alpha = 0.5
    if request.search_mode == 'semantic':
        alpha = 1.0
    elif request.search_mode == 'keyword':
        alpha = 0.0
        
    # 执行搜索
    for collection_name in collections_to_search:
        try:
            # 使用混合搜索以支持 NewsChunk schema 和搜索模式
            results = collection_manager.hybrid_search(
                collection_name=collection_name,
                query=request.query,
                limit=request.limit,
                alpha=alpha,
                similarity_threshold=0.0  # 尽可能返回结果
            )
            
            # 转换结果
            for item in results:
                # 处理 Chunk Schema 或 Article Schema
                if 'article_titles' in item: # 假设这是 Chunk Schema 的特征
                    titles = item.get('article_titles', [])
                    srcs = item.get('sources', [])
                    urls = item.get('article_urls', [])
                    
                    title = titles[0] if titles else "无标题"
                    if len(titles) > 1:
                        title = f"{title} 等 {len(titles)} 篇文章"
                    source_name = ", ".join(srcs[:2]) if srcs else "未知来源"
                    url = urls[0] if urls else None
                    published_at = item.get('created_at')
                    content = item.get('content') # Chunk Schema 的内容
                else: # 假设这是 Article Schema
                    title = item.get('title', '无标题')
                    source_name = item.get('source_name', '未知来源')
                    url = item.get('url')
                    published_at = item.get('published_at')
                    content = item.get('content') # Article Schema 的内容

                news_item = NewsItem(
                    id=item.get('_additional', {}).get('id'),
                    title=title,
                    content=content,
                    url=url,
                    source_name=source_name,
                    published_at=published_at,
                    score=item.get('_additional', {}).get('score'),  # 使用 score 而不是 certainty
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
