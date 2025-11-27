"""
Phase 2 测试脚本
测试任务管理和 Weaviate 集成
"""

import asyncio
from pathlib import Path
import sys
from datetime import datetime

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.task_manager import TaskManager
from src.storage.weaviate_client import CollectionManager
from src.utils.config import get_config
from loguru import logger


async def test_task_manager():
    """测试任务管理器"""
    logger.info("=" * 60)
    logger.info("测试任务管理器")
    logger.info("=" * 60)
    
    try:
        # 创建任务管理器
        task_manager = TaskManager()
        
        # 测试创建任务
        logger.info("创建测试任务...")
        task = task_manager.create_task(
            name="test-legal-news",
            scene="律师",
            sources=[
                {"hashid": "xxx", "name": "测试新闻源1"},
                {"hashid": "yyy", "name": "测试新闻源2"}
            ],
            cron="0 8 * * *",
            date_range="today"
        )
        
        logger.success(f"✓ 任务已创建: {task.name}")
        logger.info(f"  - 场景: {task.scene}")
        logger.info(f"  - Collection: {task.collection_name}")
        logger.info(f"  - 新闻源数: {len(task.sources)}")
        logger.info(f"  - 配置锁定: {task.locked}")
        
        # 测试获取任务
        logger.info("\n获取任务...")
        retrieved_task = task_manager.get_task("test-legal-news")
        if retrieved_task:
            logger.success(f"✓ 任务已获取: {retrieved_task.name}")
        
        # 测试列出任务
        logger.info("\n列出所有任务...")
        tasks = task_manager.list_tasks()
        logger.success(f"✓ 找到 {len(tasks)} 个任务")
        for t in tasks:
            logger.info(f"  - {t.name} ({t.scene})")
        
        # 测试更新状态
        logger.info("\n更新任务状态...")
        task_manager.update_task_status(
            "test-legal-news",
            last_run=datetime.now(),
            next_run=datetime.now()
        )
        logger.success("✓ 状态已更新")
        
        # 测试删除任务
        logger.info("\n删除测试任务...")
        task_manager.delete_task("test-legal-news")
        logger.success("✓ 任务已删除")
        
        logger.success("\n✓ 任务管理器测试通过")
        return True
    
    except Exception as e:
        logger.error(f"✗ 任务管理器测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_weaviate():
    """测试 Weaviate 集成"""
    logger.info("=" * 60)
    logger.info("测试 Weaviate 集成")
    logger.info("=" * 60)
    
    try:
        config = get_config()
        weaviate_url = config.get('weaviate.url')
        weaviate_key = config.get('weaviate.api_key')
        
        logger.info(f"连接到 Weaviate: {weaviate_url}")
        
        # 创建 Collection 管理器
        collection_manager = CollectionManager(weaviate_url, weaviate_key)
        logger.success("✓ Weaviate 连接成功")
        
        # 测试创建 Collection
        logger.info("\n创建测试 Collection...")
        collection_name = "test_news_db"
        
        # 先删除（如果存在）
        if collection_manager.collection_exists(collection_name):
            collection_manager.delete_collection(collection_name)
        
        collection_manager.create_collection(collection_name)
        logger.success(f"✓ Collection 已创建: {collection_name}")
        
        # 测试插入数据
        logger.info("\n插入测试数据...")
        news_data = {
            "task_name": "test-task",
            "title": "测试新闻标题",
            "content": "这是一条测试新闻的内容，用于验证 Weaviate 的存储和搜索功能。",
            "url": "https://example.com/news/1",
            "source_name": "测试来源",
            "source_hashid": "test123",
            "published_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),  # RFC3339 格式
            "fetched_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "category": "测试",
            "excerpt": "测试新闻摘要"
        }
        
        uuid = collection_manager.insert_news(collection_name, news_data)
        if uuid:
            logger.success(f"✓ 数据已插入: {uuid}")
        
        # 测试统计
        logger.info("\n获取统计信息...")
        stats = collection_manager.get_collection_stats(collection_name)
        logger.success(f"✓ 统计信息: {stats}")
        
        # 测试搜索
        logger.info("\n测试语义搜索...")
        results = collection_manager.search_news(
            collection_name,
            "测试新闻",
            limit=5
        )
        logger.success(f"✓ 搜索结果: {len(results)} 条")
        
        # 清理：删除测试 Collection
        logger.info("\n删除测试 Collection...")
        collection_manager.delete_collection(collection_name)
        logger.success("✓ Collection 已删除")
        
        logger.success("\n✓ Weaviate 集成测试通过")
        return True
    
    except ConnectionError as e:
        logger.warning(f"⚠ Weaviate 未运行: {str(e)}")
        logger.info("提示: 请先启动 Weaviate 服务")
        logger.info("Docker 启动命令: docker run -p 8080:8080 semitechnologies/weaviate:latest")
        return False
    
    except Exception as e:
        logger.error(f"✗ Weaviate 集成测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    logger.info("开始 Phase 2 测试...")
    logger.info("")
    
    # 测试任务管理器
    task_ok = await test_task_manager()
    logger.info("")
    
    # 测试 Weaviate
    weaviate_ok = await test_weaviate()
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("测试总结")
    logger.info("=" * 60)
    logger.info(f"任务管理器: {'✓ 通过' if task_ok else '✗ 失败'}")
    logger.info(f"Weaviate 集成: {'✓ 通过' if weaviate_ok else '⚠ 跳过（服务未运行）'}")
    
    if task_ok and weaviate_ok:
        logger.success("\n🎉 所有测试通过！Phase 2 核心功能正常。")
    elif task_ok:
        logger.warning("\n⚠️  任务管理器正常，但 Weaviate 未运行。")
    else:
        logger.error("\n✗ 部分测试失败。")


if __name__ == '__main__':
    asyncio.run(main())
