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
    collection_manager = CollectionManager(
        weaviate_url=config.get('weaviate.url'),
        api_key=config.get('weaviate.api_key')
    )
    
    try:
        # 查询所有内容
        # 尝试查询 NewsChunk 字段
        properties = [
            "content", 
            "article_titles", "sources", "article_urls", "created_at",  # Chunk schema
            "title", "source_name", "url", "published_at"  # Article schema (fallback)
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
