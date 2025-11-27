"""
配置管理命令
"""

import click
import yaml
from rich.console import Console
from rich.table import Table
from src.utils.config import get_config

console = Console()

@click.group(name='config')
def cli():
    """配置管理命令"""
    pass

@cli.command()
def show():
    """显示当前配置"""
    config = get_config()
    
    # 打印基本信息
    console.print("[bold]当前配置信息:[/bold]")
    
    # LLM 配置
    table = Table(title="LLM 配置")
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="green")
    
    llm_config = config.get('llm', {})
    for key, value in llm_config.items():
        if key == 'api_key':
            value = '******' if value else 'Not Set'
        table.add_row(str(key), str(value))
    
    console.print(table)
    
    # 引擎配置
    table = Table(title="引擎配置")
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="green")
    
    engine_config = config.get('news_sources', {})
    table.add_row("active_engine", str(engine_config.get('active_engine')))
    
    console.print(table)
    
    # Weaviate 配置
    table = Table(title="Weaviate 配置")
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="green")
    
    weaviate_config = config.get('weaviate', {})
    table.add_row("url", str(weaviate_config.get('url')))
    
    console.print(table)

@cli.command()
def validate():
    """验证配置有效性"""
    config = get_config()
    is_valid, errors = config.validate()
    
    if is_valid:
        console.print("[bold green]✓ 配置验证通过[/bold green]")
    else:
        console.print("[bold red]✗ 配置验证失败:[/bold red]")
        for error in errors:
            console.print(f"  - {error}")
