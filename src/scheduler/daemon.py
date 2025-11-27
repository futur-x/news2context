"""
守护进程入口
"""

import time
import signal
import sys
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger

from src.core.task_manager import TaskManager
from src.scheduler.jobs import run_collection_job
from src.utils.logger import setup_logger

class SchedulerDaemon:
    """调度器守护进程"""
    
    def __init__(self):
        setup_logger(level="INFO")
        self.scheduler = BlockingScheduler()
        self.task_manager = TaskManager()
        self.running = False

    def load_jobs(self):
        """加载所有任务"""
        logger.info("正在加载调度任务...")
        tasks = self.task_manager.list_tasks()
        
        for task in tasks:
            # 检查是否启用
            if not task.status.get('enabled', True):
                continue
                
            # 检查是否有调度配置
            schedule = task.schedule
            if not schedule or 'cron' not in schedule:
                continue
                
            cron_expr = schedule['cron']
            job_id = f"job_{task.name}"
            
            try:
                # 添加作业
                self.scheduler.add_job(
                    run_collection_job,
                    CronTrigger.from_crontab(cron_expr),
                    args=[task.name],
                    id=job_id,
                    replace_existing=True
                )
                logger.info(f"已添加任务: {task.name} (Cron: {cron_expr})")
            except Exception as e:
                logger.error(f"添加任务 {task.name} 失败: {str(e)}")

    def start(self):
        """启动守护进程"""
        self.running = True
        
        # 注册信号处理
        signal.signal(signal.SIGINT, self._handle_exit)
        signal.signal(signal.SIGTERM, self._handle_exit)
        
        logger.info("News2Context 守护进程启动")
        
        # 初始加载
        self.load_jobs()
        
        # 启动调度器
        try:
            self.scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            self._handle_exit(None, None)

    def _handle_exit(self, signum, frame):
        """处理退出信号"""
        if self.running:
            logger.info("正在停止守护进程...")
            self.running = False
            self.scheduler.shutdown(wait=False)
            sys.exit(0)

if __name__ == "__main__":
    daemon = SchedulerDaemon()
    daemon.start()
