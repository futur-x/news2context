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
        response = collection_manager.client.query.get(
            task.collection_name,
            ["title", "content", "source_name", "url", "published_at"]
        ).with_limit(limit).with_offset(offset).do()
        
        items = []
        if 'data' in response and 'Get' in response['data']:
            collection_data = response['data']['Get'].get(task.collection_name, [])
            for item in collection_data:
                items.append(KnowledgeItem(
                    title=item.get('title', ''),
                    content=item.get('content', ''),
                    source_name=item.get('source_name', ''),
                    url=item.get('url'),
                    published_at=item.get('published_at')
                ))
        
        return BrowseResponse(
            items=items,
            total=len(items),
            task_name=task_name
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Browse failed: {str(e)}")
