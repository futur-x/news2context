"""
任务管理路由
"""

from fastapi import APIRouter, HTTPException
from src.api.models import TaskListResponse, TaskDetail, TaskSource, TaskStatus
from src.core.task_manager import TaskManager

router = APIRouter()

@router.get("/tasks", response_model=TaskListResponse)
async def list_tasks():
    """获取所有任务"""
    manager = TaskManager()
    tasks = manager.list_tasks()
    
    task_details = []
    for task in tasks:
        task_details.append(_convert_task_to_model(task))
        
    return TaskListResponse(
        tasks=task_details,
        total=len(task_details)
    )

@router.get("/tasks/{task_name}", response_model=TaskDetail)
async def get_task(task_name: str):
    """获取任务详情"""
    manager = TaskManager()
    task = manager.get_task(task_name)
    
    if not task:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_name}")
        
    return _convert_task_to_model(task)

def _convert_task_to_model(task) -> TaskDetail:
    """将内部 Task 对象转换为 API 模型"""
    sources = [
        TaskSource(
            name=s['name'],
            hashid=s['hashid'],
            category=s.get('category')
        ) for s in task.sources
    ]
    
    status = TaskStatus(
        enabled=task.status.get('enabled', True),
        last_run=task.status.get('last_run'),
        next_run=task.status.get('next_run'),
        total_runs=task.status.get('total_runs', 0),
        last_error=task.status.get('last_error')
    )
    
    return TaskDetail(
        name=task.name,
        scene=task.scene,
        collection=task.weaviate['collection'],
        sources=sources,
        status=status,
        created_at=task.created_at,
        locked=task.locked
    )
