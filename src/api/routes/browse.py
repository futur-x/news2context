"""
知识库浏览路由
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional

from src.core.task_manager import TaskManager
from src.storage.weaviate_client import CollectionManager
from src.utils.config import get_config

router = APIRouter()

class KnowledgeItem(BaseModel):
    """知识库条目"""
    id: Optional[str] = None
    title: str
    content: str
    source_name: str
    url: Optional[str] = None
    published_at: Optional[str] = None

class BrowseResponse(BaseModel):
    """浏览响应"""
    success: bool = True
    items: List[KnowledgeItem]
    total: int
    task_name: str

@router.get("/tasks/{task_name}/browse", response_model=BrowseResponse)
async def browse_knowledge_base(
    task_name: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    浏览知识库内容
    """
    # 验证任务是否存在
    task_manager = TaskManager()
    task = task_manager.get_task(task_name)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_name}")
    
    # 获取知识库内容
    config = get_config()
    
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
    
    try:
        collection_manager = CollectionManager(
            weaviate_url=config.get('weaviate.url'),
            api_key=config.get('weaviate.api_key'),
            additional_headers=headers,
            embedding_config=embedding_config
        )
    except Exception as e:
        # 如果连接失败，返回空列表而不是 500 错误
        print(f"Weaviate connection failed: {e}")
        return BrowseResponse(
            items=[],
            total=0,
            task_name=task_name,
            success=False
        )
    
    try:
        # 查询所有内容
        # 只查询 NewsChunk Schema 中实际存在的字段
        properties = [
            "content", 
            "article_titles",
            "sources",
            "article_urls",
            "created_at",
            "task_name",
            "categories"
        ]
        
        response = collection_manager.client.query.get(
            task.collection_name,
            properties
        ).with_limit(limit).with_offset(offset).do()
        
        items = []
        if 'data' in response and 'Get' in response['data']:
            collection_data = response['data']['Get'].get(task.collection_name, [])
            for item in collection_data:
                # 处理 Chunk Schema
                if 'article_titles' in item:
                    titles = item.get('article_titles', [])
                    sources = item.get('sources', [])
                    urls = item.get('article_urls', [])
                    
                    title = titles[0] if titles else "无标题"
                    if len(titles) > 1:
                        title = f"{title} 等 {len(titles)} 篇文章"
                        
                    source_name = ", ".join(sources[:3]) if sources else "未知来源"
                    url = urls[0] if urls else None
                    published_at = item.get('created_at')
                else:
                    # 处理 Article Schema
                    title = item.get('title', '无标题')
                    source_name = item.get('source_name', '未知来源')
                    url = item.get('url')
                    published_at = item.get('published_at')

                items.append(KnowledgeItem(
                    title=title,
                    content=item.get('content', ''),
                    source_name=source_name,
                    url=url,
                    published_at=published_at
                ))
        
        return BrowseResponse(
            items=items,
            total=len(items),
            task_name=task_name
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Browse failed: {str(e)}")
