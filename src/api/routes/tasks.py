"""
任务管理路由
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime
from src.api.models import TaskDetail, TaskListResponse, CreateTaskRequest, UpdateTaskRequest, TaskSource, TaskStatus
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
        print(f"[DEBUG] Updating task {task_name} with updates: {updates}")
        # 如果包含 sources，需要转换为字典
        if 'sources' in updates:
            updates['sources'] = [s.dict() for s in request.sources]
            print(f"[DEBUG] Converted sources count: {len(updates['sources'])}")
            
        task = manager.update_task(task_name, updates)
        print(f"[DEBUG] Task updated successfully, new sources count: {len(task.sources)}")
        return _convert_task_to_model(task)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print(f"[ERROR] Update task failed: {str(e)}")
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
    manager = TaskManager()
    task = manager.get_task(task_name)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_name}")
    
    # 检查任务是否已在运行
    if task.status.get('running', False):
        return {"success": False, "message": f"Task {task_name} is already running"}
    
    # 启动异步任务
    import asyncio
    from src.core.collector import NewsCollector
    
    async def run_collection_task():
        """后台运行采集任务"""
        try:
            # 更新状态为运行中
            manager.update_task_status(task_name, {
                'running': True,
                'current_status': 'running',
                'progress': {
                    'total_sources': len(task.sources),
                    'processed_sources': 0,
                    'collected_articles': 0,
                    'start_time': datetime.now().isoformat()
                }
            })
            
            # 执行采集
            collector = NewsCollector()
            count = await collector.collect_task(task_name)
            
            # 更新状态为成功
            manager.update_task_status(task_name, {
                'running': False,
                'current_status': 'success',
                'last_run': datetime.now().isoformat(),
                'total_runs': task.status.get('total_runs', 0) + 1,
                'last_success_count': count,
                'last_error': None,
                'progress': None
            })
            
        except Exception as e:
            # 更新状态为错误
            manager.update_task_status(task_name, {
                'running': False,
                'current_status': 'error',
                'last_error': str(e),
                'progress': None
            })
    
    # 在后台运行任务
    asyncio.create_task(run_collection_task())
    
    return {"success": True, "message": f"Task {task_name} started"}

@router.get("/tasks/{task_name}/status")
async def get_task_status(task_name: str):
    """获取任务实时状态（用于轮询）"""
    manager = TaskManager()
    task = manager.get_task(task_name)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_name}")
    
    return {
        "running": task.status.get('running', False),
        "current_status": task.status.get('current_status', 'idle'),
        "progress": task.status.get('progress'),
        "last_error": task.status.get('last_error')
    }

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
        running=task.status.get('running', False),
        current_status=task.status.get('current_status', 'idle'),
        progress=task.status.get('progress'),
        last_run=task.status.get('last_run'),
        next_run=task.status.get('next_run'),
        total_runs=task.status.get('total_runs', 0),
        last_error=task.status.get('last_error'),
        last_success_count=task.status.get('last_success_count', 0)
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
