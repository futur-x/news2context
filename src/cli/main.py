"""
News2Context CLI 主入口
"""

import click
from rich.console import Console
from rich.panel import Panel
from src.utils.config import get_config
from src.utils.logger import setup_logger
from .commands import collect, task, chat, schedule, daemon, config_cmd, rerun

# 初始化 Rich Console
console = Console()

@click.group()
@click.option('--debug/--no-debug', default=False, help='启用调试模式')
@click.version_option(version='2.0.0')
@click.pass_context
def cli(ctx, debug):
    """
    News2Context v2.0 - AI 驱动的新闻聚合系统
    
    支持功能：
    - 智能新闻采集 (collect)
    - 任务管理 (task)
    - 问答交互 (chat)
    - 定时调度 (schedule)
    - 配置管理 (config)
    """
    # 初始化上下文
    ctx.ensure_object(dict)
    ctx.obj['DEBUG'] = debug
    ctx.obj['CONSOLE'] = console
    
    # 设置日志
    setup_logger(level="DEBUG" if debug else "INFO")
    
    # 加载配置
    try:
        config = get_config()
        ctx.obj['CONFIG'] = config
    except Exception as e:
        console.print(f"[red]配置加载失败: {str(e)}[/red]")
        # 不退出，允许运行 config 命令修复配置

def main():
    """CLI 入口函数"""
    # 注册命令组
    cli.add_command(collect.cli)
    cli.add_command(task.cli)
    cli.add_command(chat.cli)
    cli.add_command(schedule.cli)
    cli.add_command(daemon.cli)
    cli.add_command(config_cmd.cli)
    cli.add_command(rerun.cli)
    
    # 打印欢迎信息
    console.print(Panel.fit(
        "[bold blue]News2Context v2.0[/bold blue]\n[dim]AI Driven News Aggregator[/dim]",
        border_style="blue"
    ))
    
    cli()

if __name__ == '__main__':
    main()
