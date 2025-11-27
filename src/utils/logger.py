"""
日志工具
"""

import sys
from loguru import logger

def setup_logger(level: str = "INFO"):
    """
    设置日志配置
    
    Args:
        level: 日志级别
    """
    logger.remove()
    
    # 控制台输出
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=level
    )
    
    # 文件输出
    logger.add(
        "logs/news2context_{time:YYYY-MM-DD}.log",
        rotation="00:00",
        retention="7 days",
        level="DEBUG",
        encoding="utf-8"
    )
    
    logger.info(f"日志系统已初始化 (Level: {level})")
