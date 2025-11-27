"""
定时任务调度命令
"""

import click
import asyncio
from rich.console import Console
from rich.table import Table
from src.core.task_manager import TaskManager
from src.engines.factory import EngineFactory
from src.utils.config import get_config
from .collect import run_collection

console = Console()

@click.group(name='schedule')
def cli():
    """定时任务调度命令"""
    pass

@cli.command()
def list():
    """列出所有调度任务"""
    manager = TaskManager()
    tasks = manager.list_tasks()
    
    if not tasks:
        console.print("[yellow]暂无任务[/yellow]")
        return
        
    table = Table(title="调度列表")
    table.add_column("任务名称", style="cyan")
    table.add_column("Cron 表达式", style="green")
    table.add_column("下次运行", style="dim")
    table.add_column("状态", style="bold")
    
    for task in tasks:
        schedule = task.schedule or {}
        cron = schedule.get('cron', '未设置')
        status = "启用" if task.status['enabled'] else "禁用"
        status_style = "green" if task.status['enabled'] else "red"
        
        table.add_row(
            task.name,
            cron,
            str(task.status.get('next_run', '未知')),
            f"[{status_style}]{status}[/{status_style}]"
        )
    
    console.print(table)

@cli.command()
@click.argument('task_name')
def run(task_name):
    """手动运行任务"""
    manager = TaskManager()
    task = manager.get_task(task_name)
    
    if not task:
        console.print(f"[red]任务不存在: {task_name}[/red]")
        return
        
    # 不需要 engine 参数了，因为 run_collection 内部处理
    asyncio.run(run_collection(manager, task_name, None))

@cli.command()
@click.argument('task_name')
def enable(task_name):
    """启用任务调度"""
    manager = TaskManager()
    if manager.update_task_status(task_name, enabled=True):
        console.print(f"[green]任务已启用: {task_name}[/green]")
    else:
        console.print(f"[red]启用失败: {task_name}[/red]")

@cli.command()
@click.argument('task_name')
def disable(task_name):
    """禁用任务调度"""
    manager = TaskManager()
    if manager.update_task_status(task_name, enabled=False):
        console.print(f"[yellow]任务已禁用: {task_name}[/yellow]")
    else:
        console.print(f"[red]禁用失败: {task_name}[/red]")
