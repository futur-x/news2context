"""
基础架构测试脚本
验证配置系统和引擎工厂是否正常工作
"""

import asyncio
from pathlib import Path
import sys

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.utils.config import get_config
from src.engines.factory import EngineFactory
from loguru import logger


async def test_config():
    """测试配置系统"""
    logger.info("=" * 60)
    logger.info("测试配置系统")
    logger.info("=" * 60)
    
    try:
        config = get_config()
        
        # 测试配置读取
        logger.info(f"LLM Provider: {config.get('llm.provider')}")
        logger.info(f"LLM Model: {config.get('llm.model')}")
        logger.info(f"Active Engine: {config.get('news_sources.active_engine')}")
        logger.info(f"Weaviate URL: {config.get('weaviate.url')}")
        
        # 测试配置验证
        is_valid = config.validate()
        
        if is_valid:
            logger.success("✓ 配置系统测试通过")
        else:
            logger.warning("⚠ 配置验证失败，请检查 API Keys")
        
        return is_valid
    
    except Exception as e:
        logger.error(f"✗ 配置系统测试失败: {str(e)}")
        return False


async def test_engine():
    """测试引擎工厂"""
    logger.info("=" * 60)
    logger.info("测试引擎工厂")
    logger.info("=" * 60)
    
    try:
        config = get_config()
        
        # 创建引擎实例
        engine = EngineFactory.create_engine(config.config)
        logger.info(f"引擎类型: {engine.__class__.__name__}")
        logger.info(f"引擎名称: {engine.get_engine_name()}")
        
        # 测试获取分类
        categories = engine.get_categories()
        logger.info(f"支持的分类: {categories}")
        
        # 测试获取新闻源列表（仅获取前 5 个）
        logger.info("正在获取新闻源列表...")
        sources = await engine.get_all_sources()
        
        if sources:
            logger.success(f"✓ 成功获取 {len(sources)} 个新闻源")
            logger.info("前 5 个新闻源:")
            for source in sources[:5]:
                logger.info(f"  - {source['name']} ({source['category']})")
        else:
            logger.warning("⚠ 未获取到新闻源，请检查 API Key")
        
        logger.success("✓ 引擎工厂测试通过")
        return True
    
    except Exception as e:
        logger.error(f"✗ 引擎工厂测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    logger.info("开始基础架构测试...")
    logger.info("")
    
    # 测试配置系统
    config_ok = await test_config()
    logger.info("")
    
    # 测试引擎工厂
    if config_ok:
        engine_ok = await test_engine()
    else:
        logger.warning("跳过引擎测试（配置未通过验证）")
        engine_ok = False
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("测试总结")
    logger.info("=" * 60)
    logger.info(f"配置系统: {'✓ 通过' if config_ok else '✗ 失败'}")
    logger.info(f"引擎工厂: {'✓ 通过' if engine_ok else '✗ 失败'}")
    
    if config_ok and engine_ok:
        logger.success("\n🎉 所有测试通过！基础架构工作正常。")
    else:
        logger.warning("\n⚠️  部分测试失败，请检查配置。")


if __name__ == '__main__':
    asyncio.run(main())
