"""
新闻采集命令
"""

import click
import asyncio
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.markdown import Markdown

from src.core.source_selector import SourceSelector
from src.core.task_manager import TaskManager
from src.engines.factory import EngineFactory
from src.utils.config import get_config

console = Console()

@click.group(name='collect')
def cli():
    """新闻采集命令"""
    pass

@cli.command()
@click.option('--scene', help='用户场景描述')
@click.pass_context
def wizard(ctx, scene):
    """交互式采集向导"""
    asyncio.run(run_wizard(ctx, scene))

async def run_wizard(ctx, scene):
    """运行采集向导"""
    config = get_config()
    
    # 1. 获取场景描述
    if not scene:
        console.print(Panel(
            "👋 欢迎使用 News2Context 智能采集向导！\n"
            "请描述您的使用场景，LLM 将为您智能推荐最合适的新闻源。", 
            title="News2Context Wizard"
        ))
        console.print("\n[dim]例如: 我是一名上市公司董事长，关心国家政策、国内外政治经济、科技发展[/dim]\n")
        scene = Prompt.ask("[bold cyan]请输入您的场景描述[/bold cyan]")
    
    if not scene.strip():
        console.print("[red]场景描述不能为空[/red]")
        return
    
    console.print(f"\n[green]✓ 场景描述已记录[/green]")
    
    # 2. 获取新闻源列表
    engine = EngineFactory.create_engine(config.config)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description="正在获取新闻源列表...", total=None)
        all_sources = await engine.get_all_sources()
    
    # 4. LLM 智能选择新闻源
    selector = SourceSelector(config.config['llm'])
    
    # 询问用户想要的新闻源数量
    max_sources = int(Prompt.ask("\n[bold cyan]请输入想要采集的新闻源数量[/bold cyan]", default="30"))
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description="正在调用 LLM 智能推荐新闻源...", total=None)
        # 直接传入场景描述，让 LLM 智能推荐
        selected_sources = await selector.select_sources(
            all_sources=all_sources,
            scene_description=scene,  # 直接使用用户输入的场景描述
            max_sources=max_sources
        )
    
    # 显示推荐结果
    console.print(selector.format_sources_for_display(selected_sources))
    
    if not Confirm.ask("\n是否创建采集任务？"):
        console.print("[yellow]操作已取消[/yellow]")
        return
    
    # 5. 选择日期范围
    console.print("\n[bold cyan]请选择采集的日期范围:[/bold cyan]")
    console.print("  [dim]注意: TopHub API 仅支持获取昨天及以前的数据[/dim]")
    console.print("  1. 最近1天")
    console.print("  2. 最近2天")
    console.print("  3. 最近3天")
    console.print("  4. 最近7天")
    
    date_choice = Prompt.ask("请选择", choices=["1", "2", "3", "4"], default="1")
    
    date_range_map = {
        "1": "last_1_days",
        "2": "last_2_days",
        "3": "last_3_days",
        "4": "last_7_days"
    }
    date_range = date_range_map[date_choice]
        
    # 6. 创建任务
    task_name = Prompt.ask("[bold cyan]请输入任务名称[/bold cyan]", default="news-task")
    
    task_manager = TaskManager()
    
    # 转换为配置格式
    config_sources = selector.sources_to_config_format(selected_sources)
    
    try:
        task_config = task_manager.create_task(
            name=task_name,
            scene=scene,
            sources=config_sources,
            cron="0 8 * * *",  # 默认每天早上8点执行
            date_range=date_range
        )
        console.print(f"\n[bold green]✓ 任务已创建: {task_name}[/bold green]")
        console.print(f"配置文件: {task_manager.schedules_dir}/{task_name}.yaml")
        console.print(f"数据库: {task_config.weaviate['collection']}")
        
    except Exception as e:
        console.print(f"\n[bold red]创建任务失败: {str(e)}[/bold red]")
        return

    # 7. 立即执行采集
    if Confirm.ask("\n是否立即执行一次采集？"):
        await run_collection(task_manager, task_name, engine)

async def run_collection(task_manager, task_name, engine):
    """执行采集任务"""
    from src.core.collector import NewsCollector
    
    console.print(f"\n[bold]开始执行任务: {task_name}[/bold]")
    
    collector = NewsCollector()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description=f"正在采集任务 {task_name}...", total=None)
        count = await collector.collect_task(task_name)
    
    console.print(f"\n[bold green]采集完成！共入库 {count} 条新闻[/bold green]")
