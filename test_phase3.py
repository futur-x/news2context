"""
Phase 3 测试脚本
测试 Agent 系统（场景分析 + 新闻源选择）
"""

import asyncio
from pathlib import Path
import sys

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.scene_analyzer import SceneAnalyzer
from src.core.source_selector import SourceSelector
from src.engines.factory import EngineFactory
from src.utils.config import get_config
from loguru import logger


async def test_scene_analyzer():
    """测试场景分析器"""
    logger.info("=" * 60)
    logger.info("测试场景分析器")
    logger.info("=" * 60)
    
    try:
        config = get_config()
        
        # 创建场景分析器
        analyzer = SceneAnalyzer(
            api_key=config.get('llm.api_key'),
            base_url=config.get('llm.base_url'),
            model=config.get('llm.model')
        )
        
        # 测试不同场景
        test_scenes = [
            "律师",
            "财经作者",
            "软件开发者"
        ]
        
        results = {}
        
        for scene in test_scenes:
            logger.info(f"\n分析场景: {scene}")
            analysis = await analyzer.analyze_scene(scene)
            results[scene] = analysis
            
            logger.success(f"✓ 场景分析完成")
            logger.info(f"  角色: {analysis.get('role')}")
            logger.info(f"  关注点: {analysis.get('focus_areas')}")
            logger.info(f"  推荐分类: {analysis.get('news_categories')}")
            logger.info(f"  关键词: {analysis.get('keywords')[:5]}...")  # 只显示前5个
        
        logger.success("\n✓ 场景分析器测试通过")
        return True, results
    
    except Exception as e:
        logger.error(f"✗ 场景分析器测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, {}


async def test_source_selector(scene_analysis: dict):
    """测试新闻源选择器"""
    logger.info("=" * 60)
    logger.info("测试新闻源选择器")
    logger.info("=" * 60)
    
    try:
        config = get_config()
        
        # 创建引擎获取所有新闻源
        logger.info("获取所有新闻源...")
        engine = EngineFactory.create_engine(config.config)
        all_sources = await engine.get_all_sources()
        logger.success(f"✓ 获取到 {len(all_sources)} 个新闻源")
        
        # 创建新闻源选择器
        selector = SourceSelector()
        
        # 测试每个场景的新闻源选择
        for scene, analysis in scene_analysis.items():
            logger.info(f"\n为场景 '{scene}' 选择新闻源...")
            
            selected_sources = selector.select_sources(
                all_sources,
                analysis,
                max_sources=15
            )
            
            logger.success(f"✓ 已选择 {len(selected_sources)} 个新闻源")
            
            # 显示选择的新闻源
            display_text = selector.format_sources_for_display(selected_sources)
            print(display_text)
        
        logger.success("\n✓ 新闻源选择器测试通过")
        return True
    
    except Exception as e:
        logger.error(f"✗ 新闻源选择器测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_end_to_end():
    """端到端测试：场景分析 → 新闻源选择"""
    logger.info("=" * 60)
    logger.info("端到端测试")
    logger.info("=" * 60)
    
    try:
        config = get_config()
        
        # 1. 场景分析
        logger.info("\n步骤 1: 场景分析")
        analyzer = SceneAnalyzer(
            api_key=config.get('llm.api_key'),
            base_url=config.get('llm.base_url'),
            model=config.get('llm.model')
        )
        
        scene = "我是一名投资分析师，关注科技和金融领域"
        logger.info(f"场景: {scene}")
        
        analysis = await analyzer.analyze_scene(scene)
        logger.success("✓ 场景分析完成")
        logger.info(f"  角色: {analysis.get('role')}")
        logger.info(f"  关键词: {analysis.get('keywords')}")
        
        # 2. 获取所有新闻源
        logger.info("\n步骤 2: 获取所有新闻源")
        engine = EngineFactory.create_engine(config.config)
        all_sources = await engine.get_all_sources()
        logger.success(f"✓ 获取到 {len(all_sources)} 个新闻源")
        
        # 3. 选择新闻源
        logger.info("\n步骤 3: 智能选择新闻源")
        selector = SourceSelector()
        selected_sources = selector.select_sources(
            all_sources,
            analysis,
            max_sources=20
        )
        
        logger.success(f"✓ 已选择 {len(selected_sources)} 个新闻源")
        
        # 4. 显示结果
        logger.info("\n步骤 4: 显示选择结果")
        display_text = selector.format_sources_for_display(selected_sources)
        print(display_text)
        
        # 5. 转换为配置格式
        config_sources = selector.sources_to_config_format(selected_sources)
        logger.info(f"\n配置格式示例（前3个）:")
        for source in config_sources[:3]:
            logger.info(f"  - {source}")
        
        logger.success("\n✓ 端到端测试通过")
        logger.success("🎉 Agent 系统可以正确分析场景并选择新闻源！")
        return True
    
    except Exception as e:
        logger.error(f"✗ 端到端测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    logger.info("开始 Phase 3 测试...")
    logger.info("")
    
    # 测试场景分析器
    analyzer_ok, scene_analysis = await test_scene_analyzer()
    logger.info("")
    
    # 测试新闻源选择器
    if analyzer_ok and scene_analysis:
        selector_ok = await test_source_selector(scene_analysis)
    else:
        logger.warning("跳过新闻源选择器测试（场景分析失败）")
        selector_ok = False
    
    logger.info("")
    
    # 端到端测试
    if analyzer_ok:
        e2e_ok = await test_end_to_end()
    else:
        logger.warning("跳过端到端测试（场景分析失败）")
        e2e_ok = False
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("测试总结")
    logger.info("=" * 60)
    logger.info(f"场景分析器: {'✓ 通过' if analyzer_ok else '✗ 失败'}")
    logger.info(f"新闻源选择器: {'✓ 通过' if selector_ok else '✗ 失败/跳过'}")
    logger.info(f"端到端测试: {'✓ 通过' if e2e_ok else '✗ 失败/跳过'}")
    
    if analyzer_ok and selector_ok and e2e_ok:
        logger.success("\n🎉 所有测试通过！Phase 3 Agent 系统正常工作。")
    else:
        logger.warning("\n⚠️  部分测试失败或跳过。")


if __name__ == '__main__':
    asyncio.run(main())
