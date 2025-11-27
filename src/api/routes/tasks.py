"""
任务管理路由
"""

from fastapi import APIRouter, HTTPException
from src.api.models import TaskListResponse, TaskDetail, TaskSource, TaskStatus, CreateTaskRequest, UpdateTaskRequest
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

@router.post("/tasks", response_model=TaskDetail)
async def create_task(request: CreateTaskRequest):
    """创建新任务"""
    manager = TaskManager()
    try:
        # 转换 sources 模型为字典
        sources_dict = [s.dict() for s in request.sources]
        
        task = manager.create_task(
            name=request.name,
            scene=request.scene,
            sources=sources_dict,
            cron=request.cron,
            date_range=request.date_range,
            engine_name=request.engine_name
        )
        return _convert_task_to_model(task)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/tasks/{task_name}", response_model=TaskDetail)
async def update_task(task_name: str, request: UpdateTaskRequest):
    """更新任务"""
    manager = TaskManager()
    try:
        updates = request.dict(exclude_unset=True)
        # 如果包含 sources，需要转换为字典
        if 'sources' in updates:
            updates['sources'] = [s.dict() for s in request.sources]
            
        task = manager.update_task(task_name, updates)
        return _convert_task_to_model(task)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/tasks/{task_name}")
async def delete_task(task_name: str):
    """删除任务"""
    manager = TaskManager()
    success = manager.delete_task(task_name)
    if not success:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_name}")
    return {"success": True, "message": f"Task {task_name} deleted"}

@router.post("/tasks/{task_name}/run")
async def run_task(task_name: str):
    """手动触发任务运行"""
    # 这里只是简单触发，实际上可能需要异步处理或调用 Collector
    # 为了演示，我们暂时只检查任务是否存在
    manager = TaskManager()
    task = manager.get_task(task_name)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_name}")
    
    # TODO: 集成 Celery 或异步任务队列来真正运行任务
    # 目前仅返回成功响应
    return {"success": True, "message": f"Task {task_name} triggered (Async execution not yet implemented)"}

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
