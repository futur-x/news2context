"""
问答交互命令
"""

import click
import asyncio
from rich.console import Console
from rich.prompt import Prompt
from rich.markdown import Markdown
from rich.panel import Panel

from src.core.task_manager import TaskManager
from src.storage.weaviate_client import CollectionManager
from src.utils.config import get_config
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

console = Console()

@click.group(name='chat')
def cli():
    """问答交互命令"""
    pass

@cli.command()
@click.option('--task', 'task_name', help='指定任务名称')
def interactive(task_name):
    """开始交互式问答"""
    asyncio.run(run_chat(task_name))

async def run_chat(task_name):
    """运行问答循环"""
    config = get_config()
    task_manager = TaskManager()
    
    # 1. 选择任务
    if not task_name:
        tasks = task_manager.list_tasks()
        if not tasks:
            console.print("[yellow]暂无可用任务，请先使用 'collect' 命令创建任务。[/yellow]")
            return
            
        console.print("可用任务:")
        for i, t in enumerate(tasks, 1):
            console.print(f"{i}. {t.name} ({t.scene})")
            
        choice = Prompt.ask("请选择任务序号", choices=[str(i) for i in range(1, len(tasks) + 1)])
        task = tasks[int(choice) - 1]
        task_name = task.name
    else:
        task = task_manager.get_task(task_name)
        if not task:
            console.print(f"[red]任务不存在: {task_name}[/red]")
            return

    # 2. 初始化 Weaviate
    weaviate_url = config.get('weaviate.url')
    collection_manager = CollectionManager(weaviate_url)
    
    # 获取任务配置
    task_config = task_manager.get_task(task_name)
    if not task_config:
        console.print(f"[red]任务 {task_name} 不存在[/red]")
        return
    
    collection_name = task_config.weaviate['collection']
    
    # 3. 初始化 LLM
    llm_config = config.get('llm')
    llm = ChatOpenAI(
        model=llm_config.get('model', 'gpt-4'),
        temperature=llm_config.get('temperature', 0.7),
        openai_api_key=llm_config.get('api_key'),
        openai_api_base=llm_config.get('base_url')
    )
    
    # 4. 显示欢迎信息
    console.print(Panel.fit(
        f"[bold cyan]与任务 '{task_name}' 的知识库对话[/bold cyan]\n"
        f"[dim]输入 'exit' 或 'quit' 退出[/dim]",
        border_style="cyan"
    ))
    
    # 5. 对话循环
    while True:
        # 获取用户输入
        question = Prompt.ask("\n[bold green]你[/bold green]")
        
        if question.lower() in ['exit', 'quit', '退出']:
            console.print("[yellow]再见！[/yellow]")
            break
        
        # 使用混合搜索查询相关新闻
        search_config = config.get('weaviate.search', {})
        alpha = search_config.get('hybrid_alpha', 0.75)
        similarity_threshold = search_config.get('similarity_threshold', 0.7)
        max_results = search_config.get('max_results', 5)
        
        with console.status("[bold cyan]正在搜索相关新闻...[/bold cyan]"):
            # 使用混合搜索
            results = collection_manager.hybrid_search(
                collection_name=collection_name,
                query=question,
                alpha=alpha,
                limit=max_results,
                similarity_threshold=similarity_threshold
            )
        
        if not results:
            console.print("[yellow]未找到相关新闻。[/yellow]")
            continue
        
        # 构建上下文
        context_parts = []
        for i, result in enumerate(results, 1):
            score = float(result['_additional']['score'])
            content = result.get('content', '')
            sources = result.get('sources', [])
            article_count = result.get('article_count', 0)
            
            context_parts.append(
                f"[新闻片段 {i}] (相关度: {score:.2f}, 来源: {', '.join(sources[:2])}, 包含 {article_count} 篇文章)\n{content[:500]}..."
            )
        
        context = "\n\n".join(context_parts)
        
        # 调用 LLM 生成回答
        with console.status("[bold cyan]正在生成回答...[/bold cyan]"):
            messages = [
                SystemMessage(content=f"你是一个新闻助手。根据以下新闻内容回答用户问题。\n\n{context}"),
                HumanMessage(content=question)
            ]
            
            response = llm(messages)
        
        # 显示回答
        console.print(f"\n[bold blue]助手[/bold blue]:")
        console.print(Markdown(response.content))
        
        # 显示来源
        console.print(f"\n[dim]参考了 {len(results)} 个新闻片段[/dim]")
