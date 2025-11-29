"""
新闻源选择器 - LLM 智能推荐版本
基于 LLM 理解用户场景，智能推荐最合适的新闻源
"""

from typing import Dict, Any, List
from loguru import logger
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
import json


class SourceSelector:
    """新闻源选择器 - LLM 智能版"""
    
    def __init__(self, llm_config: Dict[str, Any]):
        """
        初始化新闻源选择器
        
        Args:
            llm_config: LLM 配置
        """
        self.llm = ChatOpenAI(
            api_key=llm_config.get('api_key'),
            base_url=llm_config.get('base_url'),
            model=llm_config.get('model'),
            temperature=0.3  # 较低温度，保证推荐稳定性
        )
        logger.info("LLM 智能新闻源选择器已初始化")
    
    async def select_sources(
        self,
        all_sources: List[Dict[str, Any]],
        scene_description: str,
        max_sources: int = 30
    ) -> List[Dict[str, Any]]:
        """
        使用 LLM 智能选择新闻源
        
        Args:
            all_sources: 所有可用新闻源
            scene_description: 用户场景描述
            max_sources: 最大新闻源数量
            
        Returns:
            选中的新闻源列表
        """
        logger.info(f"开始 LLM 智能选择新闻源（总数: {len(all_sources)}，目标: {max_sources}）")
        
        # 准备源列表摘要（避免 token 过多）
        sources_summary = self._prepare_sources_summary(all_sources)
        
        # 构建 Prompt
        system_prompt = """你是一个专业的新闻源推荐专家。你的任务是根据用户的场景需求，从提供的新闻源列表中智能推荐最合适的新闻源。

**推荐原则**：
1. **质量优先**：优先推荐权威、专业、高质量的新闻源
2. **相关性强**：必须与用户场景高度相关
3. **多样性**：覆盖不同角度和维度
4. **避免冗余**：不要推荐内容重复的源

**评估维度**：
- 权威性：官方、主流媒体优先
- 专业性：垂直领域专业媒体
- 时效性：能提供最新资讯
- 深度性：能提供深度分析

**输出格式**：
返回 JSON 数组，每个元素包含：
{
  "hashid": "源ID",
  "reason": "推荐理由（简短，20字内）",
  "priority": "高/中/低"
}

按优先级排序，只返回最合适的源，不要为了凑数而推荐不相关的源。"""

        user_prompt = f"""**用户场景**：
{scene_description}

**可用新闻源**（共 {len(all_sources)} 个）：
{sources_summary}

**要求**：
请从以上新闻源中推荐最合适的 {max_sources} 个（可以少于 {max_sources} 个，但必须保证质量）。

请直接返回 JSON 数组，不要有任何其他文字。"""

        try:
            # 调用 LLM
            logger.info("正在调用 LLM 进行智能推荐...")
            response = await self.llm.agenerate([[
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]])
            
            result_text = response.generations[0][0].text.strip()
            
            # 提取 JSON（处理可能的 markdown 代码块）
            if result_text.startswith('```'):
                # 移除代码块标记
                result_text = result_text.split('```')[1]
                if result_text.startswith('json'):
                    result_text = result_text[4:]
                result_text = result_text.strip()
            
            # 解析 JSON
            recommendations = json.loads(result_text)
            
            # 根据推荐结果筛选源
            selected_sources = []
            hashid_to_source = {s['id']: s for s in all_sources}
            
            for rec in recommendations:
                hashid = rec.get('hashid')
                if hashid in hashid_to_source:
                    source = hashid_to_source[hashid].copy()
                    # 确保 hashid 字段存在
                    if 'hashid' not in source:
                        source['hashid'] = source.get('id')
                    source['recommendation_reason'] = rec.get('reason', '')
                    source['priority'] = rec.get('priority', '中')
                    selected_sources.append(source)
            
            logger.success(f"LLM 推荐了 {len(selected_sources)} 个高质量新闻源")
            
            # 打印推荐结果
            self._print_recommendations(selected_sources)
            
            return selected_sources
            
        except Exception as e:
            logger.error(f"LLM 推荐失败: {str(e)}")
            logger.warning("降级使用传统关键词匹配方法")
            # 降级方案：使用简单的关键词匹配
            return self._fallback_selection(all_sources, scene_description, max_sources)
    
    def _prepare_sources_summary(self, sources: List[Dict[str, Any]]) -> str:
        """
        准备新闻源摘要（精简版，避免 token 过多）
        
        Args:
            sources: 所有新闻源
            
        Returns:
            格式化的源列表字符串
        """
        lines = []
        
        # 按分类分组
        by_category = {}
        for source in sources:
            cat = source.get('category', '其他')
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(source)
        
        # 生成摘要
        for category in sorted(by_category.keys()):
            lines.append(f"\n【{category}】")
            for source in by_category[category][:50]:  # 每个分类最多50个
                hashid = source.get('id', source.get('hashid', ''))
                name = source.get('name', '')
                display = source.get('display', '')
                
                if display:
                    lines.append(f"- {hashid}: {name} - {display}")
                else:
                    lines.append(f"- {hashid}: {name}")
        
        return '\n'.join(lines)
    
    def _print_recommendations(self, sources: List[Dict[str, Any]]) -> None:
        """打印推荐结果"""
        logger.info("\n" + "="*60)
        logger.info("📋 LLM 推荐的新闻源：")
        logger.info("="*60)
        
        for i, source in enumerate(sources, 1):
            priority = source.get('priority', '中')
            reason = source.get('recommendation_reason', '')
            name = source.get('name', '')
            category = source.get('category', '')
            
            priority_icon = {
                '高': '⭐⭐⭐',
                '中': '⭐⭐',
                '低': '⭐'
            }.get(priority, '⭐⭐')
            
            logger.info(f"{i}. {name} ({category}) {priority_icon}")
            if reason:
                logger.info(f"   理由: {reason}")
        
        logger.info("="*60 + "\n")
    
    def _fallback_selection(
        self,
        all_sources: List[Dict[str, Any]],
        scene_description: str,
        max_sources: int
    ) -> List[Dict[str, Any]]:
        """
        降级方案：简单的关键词匹配
        
        Args:
            all_sources: 所有源
            scene_description: 场景描述
            max_sources: 最大数量
            
        Returns:
            选中的源列表
        """
        logger.info("使用降级方案：关键词匹配")
        
        # 提取关键词（简单分词）
        keywords = scene_description.lower().split()
        
        # 评分
        scored = []
        for source in all_sources:
            score = 0
            name = source.get('name', '').lower()
            display = source.get('display', '').lower()
            category = source.get('category', '').lower()
            
            for keyword in keywords:
                if keyword in name or keyword in display or keyword in category:
                    score += 1
            
            if score > 0:
                scored.append((source, score))
        
        # 排序并选择
        scored.sort(key=lambda x: x[1], reverse=True)
        selected = [s[0] for s in scored[:max_sources]]
        
        logger.info(f"降级方案选择了 {len(selected)} 个源")
        return selected
    
    def format_sources_for_display(self, sources: List[Dict[str, Any]]) -> str:
        """
        格式化新闻源列表用于显示
        
        Args:
            sources: 新闻源列表
            
        Returns:
            格式化的字符串
        """
        lines = []
        lines.append(f"\n📋 已选择 {len(sources)} 个新闻源：\n")
        
        # 按分类分组
        by_category = {}
        for source in sources:
            category = source.get('category', '其他')
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(source)
        
        # 输出
        for category, category_sources in sorted(by_category.items()):
            lines.append(f"【{category}】")
            for source in category_sources:
                name = source['name']
                display = source.get('display', '')
                reason = source.get('recommendation_reason', '')
                
                if reason:
                    lines.append(f"  • {name} - {display} ({reason})")
                else:
                    lines.append(f"  • {name} - {display}")
            lines.append("")
        
        return "\n".join(lines)
    
    def sources_to_config_format(self, sources: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        将新闻源转换为任务配置格式
        
        Args:
            sources: 新闻源列表
            
        Returns:
            配置格式的新闻源列表
        """
        return [
            {
                'hashid': source.get('id', source.get('hashid', '')),
                'name': source['name'],
                'category': source.get('category', ''),
                'display': source.get('display', '')
            }
            for source in sources
        ]
