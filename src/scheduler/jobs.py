"""
调度任务定义
"""

import asyncio
from datetime import datetime
from loguru import logger
from src.core.collector import NewsCollector
from src.core.task_manager import TaskManager

def run_collection_job(task_name: str):
    """
    采集任务包装器（供 APScheduler 调用）
    APScheduler 默认在线程池中运行同步函数，所以这里用 asyncio.run 包装异步调用
    """
    logger.info(f"调度器触发任务: {task_name}")

    # 获取任务管理器
    task_manager = TaskManager()
    task = task_manager.get_task(task_name)

    if not task:
        logger.error(f"任务不存在: {task_name}")
        return

    # 检查任务是否已在运行
    if task.status.get('running', False):
        logger.warning(f"任务 {task_name} 已在运行中，跳过本次调度")
        return

    async def run_with_status_tracking():
        """运行任务并跟踪状态"""
        try:
            # 1. 设置状态为运行中
            task_manager.update_task_status(task_name, {
                'running': True,
                'current_status': 'running',
                'progress': {
                    'total_sources': len(task.sources),
                    'processed_sources': 0,
                    'collected_articles': 0,
                    'start_time': datetime.now().isoformat(),
                    'status': 'collecting'
                }
            })
            logger.info(f"任务 {task_name} 开始执行（定时触发）")

            # 2. 执行采集
            collector = NewsCollector()
            count = await collector.collect_task(task_name)

            # 3. 更新状态为成功
            task_manager.update_task_status(task_name, {
                'running': False,
                'current_status': 'success',
                'last_run': datetime.now().isoformat(),
                'total_runs': task.status.get('total_runs', 0) + 1,
                'last_success_count': count,
                'last_error': None,
                'progress': None
            })
            logger.success(f"任务 {task_name} 执行完成，采集了 {count} 条/chunks")

        except Exception as e:
            # 更新状态为错误
            logger.error(f"任务执行失败 {task_name}: {str(e)}")
            task_manager.update_task_status(task_name, {
                'running': False,
                'current_status': 'error',
                'last_error': str(e),
                'progress': None
            })

    # 执行异步任务
    try:
        asyncio.run(run_with_status_tracking())
    except Exception as e:
        logger.error(f"任务执行异常 {task_name}: {str(e)}")
