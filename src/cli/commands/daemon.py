"""
守护进程管理命令
"""

import click
import os
import sys
import subprocess
import signal
from rich.console import Console

console = Console()

PID_FILE = "data/daemon.pid"

@click.group(name='daemon')
def cli():
    """守护进程管理命令"""
    pass

@cli.command()
def start():
    """启动守护进程"""
    if _is_running():
        console.print("[yellow]守护进程已在运行[/yellow]")
        return

    # 确保日志目录存在
    os.makedirs("logs", exist_ok=True)
    
    # 启动后台进程
    try:
        with open("logs/daemon.out", "a") as stdout, open("logs/daemon.err", "a") as stderr:
            process = subprocess.Popen(
                [sys.executable, "-m", "src.scheduler.daemon"],
                stdout=stdout,
                stderr=stderr,
                cwd=os.getcwd(),
                start_new_session=True
            )
            
        # 保存 PID
        os.makedirs("data", exist_ok=True)
        with open(PID_FILE, "w") as f:
            f.write(str(process.pid))
            
        console.print(f"[green]守护进程已启动 (PID: {process.pid})[/green]")
        
    except Exception as e:
        console.print(f"[red]启动失败: {str(e)}[/red]")

@cli.command()
def stop():
    """停止守护进程"""
    if not _is_running():
        console.print("[yellow]守护进程未运行[/yellow]")
        return
        
    try:
        with open(PID_FILE, "r") as f:
            pid = int(f.read().strip())
            
        os.kill(pid, signal.SIGTERM)
        os.remove(PID_FILE)
        console.print(f"[green]守护进程已停止 (PID: {pid})[/green]")
        
    except ProcessLookupError:
        console.print("[yellow]进程不存在，清理 PID 文件[/yellow]")
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
    except Exception as e:
        console.print(f"[red]停止失败: {str(e)}[/red]")

@cli.command()
def status():
    """查看守护进程状态"""
    if _is_running():
        with open(PID_FILE, "r") as f:
            pid = f.read().strip()
        console.print(f"[green]守护进程正在运行 (PID: {pid})[/green]")
    else:
        console.print("[red]守护进程未运行[/red]")

@cli.command()
def logs():
    """查看守护进程日志"""
    # 简单实现：显示最后 20 行
    log_file = "logs/daemon.out" # 注意：实际日志可能在 loguru 生成的文件中
    # 这里我们查看 daemon.out 捕获的标准输出
    
    if not os.path.exists(log_file):
        console.print("[yellow]暂无日志[/yellow]")
        return
        
    try:
        # 使用 tail 命令
        subprocess.run(["tail", "-n", "20", log_file])
    except Exception as e:
        console.print(f"[red]读取日志失败: {str(e)}[/red]")

def _is_running():
    """检查是否运行中"""
    if not os.path.exists(PID_FILE):
        return False
        
    try:
        with open(PID_FILE, "r") as f:
            pid = int(f.read().strip())
        
        # 发送 0 信号检查进程是否存在
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, ValueError):
        return False
    except Exception:
        return False
