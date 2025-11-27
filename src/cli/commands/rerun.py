"""
重新运行已有任务的命令
"""

import click
import asyncio
from rich.console import Console
from rich.table import Table
from rich import print as rprint
from loguru import logger

from src.core.task_manager import TaskManager
from src.core.collector import NewsCollector


console = Console()


@click.command(name='rerun')
@click.pass_context
def cli(ctx):
    """列出并重新运行已有任务"""
    asyncio.run(run_rerun(ctx))


async def run_rerun(ctx):
    """重新运行任务的主逻辑"""
    
    # 1. 列出所有任务
    task_manager = TaskManager()
    task_configs = task_manager.list_tasks()  # 返回 TaskConfig 对象列表
    
    if not task_configs:
        rprint("[yellow]⚠️  没有找到任何任务[/yellow]")
        rprint("[dim]提示: 使用 'collect wizard' 创建新任务[/dim]")
        return
    
    # 2. 显示任务列表
    rprint("\n[bold cyan]📋 可用任务列表[/bold cyan]\n")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("序号", style="dim", width=6)
    table.add_column("任务名称", style="cyan")
    table.add_column("新闻源数量", justify="right")
    table.add_column("日期范围")
    table.add_column("上次运行")
    
    for idx, task_config in enumerate(task_configs, 1):
        # TaskConfig 对象可以直接访问属性
        task_name = task_config.name
        sources_count = len(task_config.sources)
        date_range = task_config.schedule.get('date_range', 'yesterday')
        last_run = task_config.status.get('last_run', '从未运行')
        
        table.add_row(
            str(idx),
            task_name,
            str(sources_count),
            date_range,
            str(last_run)
        )
    
    console.print(table)
    
    # 3. 选择任务
    rprint("\n[bold]请选择要重新运行的任务:[/bold]")
    choice = click.prompt(
        "输入序号",
        type=click.IntRange(1, len(task_configs)),
        default=1
    )
    
    selected_task_config = task_configs[choice - 1]
    selected_task_name = selected_task_config.name
    
    # 4. 确认信息
    rprint(f"\n[bold green]✓ 选择的任务: {selected_task_name}[/bold green]")
    rprint(f"  - 新闻源: {len(selected_task_config.sources)} 个")
    rprint(f"  - 日期范围: {selected_task_config.schedule.get('date_range', 'yesterday')}")
    
    # 5. 确认运行
    if not click.confirm("\n是否开始运行?", default=True):
        rprint("[yellow]已取消[/yellow]")
        return
    
    # 6. 运行采集
    rprint(f"\n[bold cyan]🚀 开始运行任务: {selected_task_name}[/bold cyan]\n")
    
    # 执行采集
    collector = NewsCollector()
    
    with console.status(f"[bold green]正在采集任务 {selected_task_name}...") as status:
        try:
            count = await collector.collect_task(selected_task_name)
            
            rprint(f"\n[bold green]✓ 任务完成![/bold green]")
            rprint(f"  - 成功入库: {count} 个 chunks")
            
        except Exception as e:
            rprint(f"\n[bold red]✗ 任务失败: {str(e)}[/bold red]")
            logger.error(f"任务执行失败: {str(e)}")
            import traceback
            traceback.print_exc()
