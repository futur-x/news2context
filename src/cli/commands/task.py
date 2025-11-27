"""
任务管理命令
"""

import click
from rich.console import Console
from rich.table import Table
from rich.prompt import Confirm
from src.core.task_manager import TaskManager

console = Console()

@click.group(name='task')
def cli():
    """任务管理命令"""
    pass

@cli.command()
def list():
    """列出所有任务"""
    manager = TaskManager()
    tasks = manager.list_tasks()
    
    if not tasks:
        console.print("[yellow]暂无任务[/yellow]")
        return
        
    table = Table(title="任务列表")
    table.add_column("名称", style="cyan")
    table.add_column("场景", style="green")
    table.add_column("新闻源数", justify="right")
    table.add_column("上次运行", style="dim")
    table.add_column("总运行次数", justify="right")
    table.add_column("状态", style="bold")
    
    for task in tasks:
        status = "启用" if task.status['enabled'] else "禁用"
        status_style = "green" if task.status['enabled'] else "red"
        
        table.add_row(
            task.name,
            task.scene,
            str(len(task.sources)),
            str(task.status.get('last_run', '从未')),
            str(task.status.get('total_runs', 0)),
            f"[{status_style}]{status}[/{status_style}]"
        )
    
    console.print(table)

@cli.command()
@click.argument('task_name')
def show(task_name):
    """显示任务详情"""
    manager = TaskManager()
    task = manager.get_task(task_name)
    
    if not task:
        console.print(f"[red]任务不存在: {task_name}[/red]")
        return
        
    console.print(f"[bold cyan]任务详情: {task.name}[/bold cyan]")
    console.print(f"场景: {task.scene}")
    console.print(f"Collection: {task.weaviate['collection']}")
    console.print(f"创建时间: {task.created_at}")
    
    # 新闻源列表
    table = Table(title="新闻源列表")
    table.add_column("名称", style="cyan")
    table.add_column("分类", style="green")
    table.add_column("HashID", style="dim")
    
    for source in task.sources:
        table.add_row(
            source['name'],
            source.get('category', '未知'),
            source['hashid']
        )
    
    console.print(table)

@cli.command()
@click.argument('task_name')
def delete(task_name):
    """删除任务"""
    manager = TaskManager()
    task = manager.get_task(task_name)
    
    if not task:
        console.print(f"[red]任务不存在: {task_name}[/red]")
        return
        
    if Confirm.ask(f"确定要删除任务 '{task_name}' 及其所有数据吗？此操作不可恢复！"):
        if manager.delete_task(task_name):
            console.print(f"[green]任务已删除: {task_name}[/green]")
        else:
            console.print(f"[red]删除任务失败[/red]")
