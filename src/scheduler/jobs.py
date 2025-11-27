"""
调度任务定义
"""

import asyncio
from loguru import logger
from src.core.collector import NewsCollector

def run_collection_job(task_name: str):
    """
    采集任务包装器（供 APScheduler 调用）
    APScheduler 默认在线程池中运行同步函数，所以这里用 asyncio.run 包装异步调用
    """
    logger.info(f"调度器触发任务: {task_name}")
    try:
        collector = NewsCollector()
        asyncio.run(collector.collect_task(task_name))
    except Exception as e:
        logger.error(f"任务执行失败 {task_name}: {str(e)}")
