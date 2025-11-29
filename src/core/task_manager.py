"""
任务管理器
负责任务的创建、读取、更新、删除（CRUD）
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger
import uuid


class TaskConfig:
    """任务配置类"""
    
    def __init__(self, data: Dict[str, Any]):
        self.name = data['name']
        self.scene = data['scene']
        self.created_at = data['created_at']
        self.locked = data.get('locked', True)
        self.sources = data['sources']
        self.schedule = data['schedule']
        self.weaviate = data['weaviate']
        self.engine = data['engine']
        self.status = data.get('status', {})
        self._data = data
    
    @property
    def collection_name(self) -> str:
        """获取 Weaviate Collection 名称"""
        return self.weaviate['collection']
    
    @property
    def is_enabled(self) -> bool:
        """任务是否启用"""
        return self.status.get('enabled', True)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self._data
    
    def __repr__(self):
        return f"TaskConfig(name={self.name}, scene={self.scene}, sources={len(self.sources)})"


class TaskManager:
    """任务管理器"""
    
    def __init__(self, schedules_dir: Optional[str] = None):
        """
        初始化任务管理器
        
        Args:
            schedules_dir: 任务配置目录，默认为 config/schedules
        """
        if schedules_dir is None:
            project_root = Path(__file__).parent.parent.parent
            schedules_dir = project_root / "config" / "schedules"
        
        self.schedules_dir = Path(schedules_dir)
        self.schedules_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"任务管理器已初始化: {self.schedules_dir}")
    
    def create_task(
        self,
        name: str,
        scene: str,
        sources: List[Dict[str, Any]],
        cron: str = "0 8 * * *",
        date_range: str = "today",
        engine_name: str = "tophub"
    ) -> TaskConfig:
        """
        创建新任务
        
        Args:
            name: 任务名称
            scene: 场景描述
            sources: 新闻源列表
            cron: Cron 表达式
            date_range: 日期范围（today, yesterday, last_7_days, custom）
            engine_name: 引擎名称
            
        Returns:
            任务配置对象
            
        Raises:
            ValueError: 任务已存在
        """
        # 检查任务是否已存在
        if self.task_exists(name):
            raise ValueError(f"任务 {name} 已存在")
        
        # 生成 Collection 名称
        collection_name = self._generate_collection_name(name)
        
        # 创建任务配置
        task_data = {
            'name': name,
            'scene': scene,
            'created_at': datetime.now().isoformat(),
            'locked': True,  # 配置锁定
            'sources': sources,
            'schedule': {
                'cron': cron,
                'date_range': date_range,
                'custom_range': {
                    'start': None,
                    'end': None
                }
            },
            'weaviate': {
                'collection': collection_name
            },
            'engine': {
                'name': engine_name
            },
            'status': {
                'enabled': True,
                'last_run': None,
                'next_run': None,
                'total_runs': 0,
                'last_error': None
            }
        }
        
        # 保存到文件
        self._save_task(name, task_data)
        
        logger.success(f"任务已创建: {name}")
        return TaskConfig(task_data)
    
    def get_task(self, name: str) -> Optional[TaskConfig]:
        """
        获取任务配置
        
        Args:
            name: 任务名称
            
        Returns:
            任务配置对象，不存在返回 None
        """
        task_file = self.schedules_dir / f"{name}.yaml"
        
        if not task_file.exists():
            return None
        
        with open(task_file, 'r', encoding='utf-8') as f:
            task_data = yaml.safe_load(f)
        
        return TaskConfig(task_data)
    
    def list_tasks(self) -> List[TaskConfig]:
        """
        列出所有任务
        
        Returns:
            任务配置列表
        """
        tasks = []
        
        for task_file in self.schedules_dir.glob("*.yaml"):
            try:
                with open(task_file, 'r', encoding='utf-8') as f:
                    task_data = yaml.safe_load(f)
                tasks.append(TaskConfig(task_data))
            except Exception as e:
                logger.error(f"加载任务配置失败 ({task_file}): {str(e)}")
        
        return tasks
    
    def delete_task(self, name: str) -> bool:
        """
        删除任务
        
        Args:
            name: 任务名称
            
        Returns:
            是否成功删除
        """
        task_file = self.schedules_dir / f"{name}.yaml"
        
        if not task_file.exists():
            logger.warning(f"任务不存在: {name}")
            return False
        
        task_file.unlink()
        logger.success(f"任务已删除: {name}")
        return True
    
    def update_task(self, name: str, updates: Dict[str, Any]) -> TaskConfig:
        """
        更新任务配置
        
        Args:
            name: 任务名称
            updates: 更新内容字典
            
        Returns:
            更新后的任务配置对象
            
        Raises:
            ValueError: 任务不存在
        """
        task = self.get_task(name)
        if not task:
            raise ValueError(f"任务 {name} 不存在")
            
        task_data = task.to_dict()
        
        # 更新支持的字段
        if 'scene' in updates:
            task_data['scene'] = updates['scene']
        if 'sources' in updates:
            task_data['sources'] = updates['sources']
        if 'schedule' in updates:
            # 深度合并 schedule
            if 'cron' in updates['schedule']:
                task_data['schedule']['cron'] = updates['schedule']['cron']
            if 'date_range' in updates['schedule']:
                task_data['schedule']['date_range'] = updates['schedule']['date_range']
        if 'status' in updates and 'enabled' in updates['status']:
             task_data['status']['enabled'] = updates['status']['enabled']
             
        # 保存更新
        self._save_task(name, task_data)
        logger.info(f"任务已更新: {name}")
        
        return TaskConfig(task_data)

    def update_task_status(
        self,
        name: str,
        status_updates: Dict[str, Any]
    ) -> bool:
        """
        更新任务状态（支持所有状态字段）
        
        Args:
            name: 任务名称
            status_updates: 状态更新字典
            
        Returns:
            是否更新成功
        """
        task = self.get_task(name)
        if not task:
            logger.error(f"任务 {name} 不存在")
            return False
            
        task_data = task.to_dict()
        
        # 更新状态字段
        for key, value in status_updates.items():
            task_data['status'][key] = value
            
        # 保存更新
        self._save_task(name, task_data)
        logger.info(f"任务状态已更新: {name}")
        return True
    
    def enable_task(self, name: str) -> bool:
        """启用任务"""
        return self._set_task_enabled(name, True)
    
    def disable_task(self, name: str) -> bool:
        """禁用任务"""
        return self._set_task_enabled(name, False)
    
    def _set_task_enabled(self, name: str, enabled: bool) -> bool:
        """设置任务启用状态"""
        task = self.get_task(name)
        
        if not task:
            return False
        
        task.status['enabled'] = enabled
        self._save_task(name, task.to_dict())
        
        status_text = "启用" if enabled else "禁用"
        logger.info(f"任务已{status_text}: {name}")
        return True
    
    def task_exists(self, name: str) -> bool:
        """检查任务是否存在"""
        task_file = self.schedules_dir / f"{name}.yaml"
        return task_file.exists()
    
    def _save_task(self, name: str, task_data: Dict[str, Any]):
        """保存任务配置到文件"""
        task_file = self.schedules_dir / f"{name}.yaml"
        
        with open(task_file, 'w', encoding='utf-8') as f:
            yaml.dump(task_data, f, allow_unicode=True, default_flow_style=False)
    
    def _generate_collection_name(self, task_name: str) -> str:
        """
        生成 Weaviate Collection 名称
        使用 UUID 确保唯一性和合规性 (Task_<uuid>)
        
        Args:
            task_name: 任务名称 (仅用于记录，不用于生成 ID)
            
        Returns:
            Collection 名称
        """
        # 生成唯一 ID
        unique_id = uuid.uuid4().hex
        return f"Task_{unique_id}"
