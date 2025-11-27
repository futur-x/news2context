"""
场景分析 Agent
使用 LLM 分析用户场景并理解信息需求
"""

from typing import Dict, Any, List, Optional
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage
from loguru import logger


class SceneAnalyzer:
    """场景分析 Agent"""
    
    # 系统提示词
    SYSTEM_PROMPT = """你是一个专业的新闻需求分析专家。
你的任务是理解用户的角色和场景，分析他们需要什么类型的新闻信息。

请根据用户提供的场景描述，分析以下内容：
1. 用户角色的核心关注点
2. 需要的新闻类型和分类
3. 关键词列表
4. 推荐的新闻源特征

请以 JSON 格式返回分析结果。"""
    
    # 分析提示词模板
    ANALYSIS_PROMPT = """场景描述：{scene}

请分析这个场景，并返回以下 JSON 格式的结果：
{{
    "role": "角色名称",
    "focus_areas": ["关注点1", "关注点2", ...],
    "news_categories": ["分类1", "分类2", ...],
    "keywords": ["关键词1", "关键词2", ...],
    "source_features": {{
        "preferred_domains": ["推荐的网站域名"],
        "preferred_categories": ["推荐的分类"],
        "avoid_categories": ["应避免的分类"]
    }}
}}

示例：
场景：我是一名律师
结果：
{{
    "role": "律师",
    "focus_areas": ["法律法规", "司法案例", "法律政策", "行业动态"],
    "news_categories": ["政务", "综合"],
    "keywords": ["法律", "法规", "司法", "案例", "法院", "检察", "律师", "法治"],
    "source_features": {{
        "preferred_domains": ["gov.cn", "court.gov.cn", "spp.gov.cn"],
        "preferred_categories": ["政务", "综合"],
        "avoid_categories": ["娱乐", "游戏"]
    }}
}}"""
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4",
        temperature: float = 0.7
    ):
        """
        初始化场景分析器
        
        Args:
            api_key: OpenAI API Key
            base_url: API Base URL
            model: 模型名称
            temperature: 温度参数
        """
        self.llm = ChatOpenAI(
            api_key=api_key,
            base_url=base_url,
            model=model,
            temperature=temperature
        )
        
        logger.info(f"场景分析器已初始化: {model}")
    
    async def analyze_scene(self, scene: str) -> Dict[str, Any]:
        """
        分析场景
        
        Args:
            scene: 场景描述
            
        Returns:
            分析结果字典
        """
        logger.info(f"开始分析场景: {scene}")
        
        try:
            # 构建消息
            messages = [
                SystemMessage(content=self.SYSTEM_PROMPT),
                HumanMessage(content=self.ANALYSIS_PROMPT.format(scene=scene))
            ]
            
            # 调用 LLM
            response = await self.llm.agenerate([messages])
            result_text = response.generations[0][0].text
            
            # 解析 JSON
            import json
            # 提取 JSON 部分（可能包含在 markdown 代码块中）
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0]
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0]
            
            result = json.loads(result_text.strip())
            
            logger.success(f"场景分析完成: {result.get('role', 'Unknown')}")
            logger.info(f"关注点: {result.get('focus_areas', [])}")
            logger.info(f"关键词: {result.get('keywords', [])}")
            
            return result
        
        except Exception as e:
            logger.error(f"场景分析失败: {str(e)}")
            # 返回默认结果
            return {
                "role": scene,
                "focus_areas": [],
                "news_categories": ["综合"],
                "keywords": [scene],
                "source_features": {
                    "preferred_domains": [],
                    "preferred_categories": ["综合"],
                    "avoid_categories": []
                }
            }
    
    def get_recommended_categories(self, analysis: Dict[str, Any]) -> List[str]:
        """
        获取推荐的新闻分类
        
        Args:
            analysis: 分析结果
            
        Returns:
            分类列表
        """
        return analysis.get('news_categories', ['综合'])
    
    def get_keywords(self, analysis: Dict[str, Any]) -> List[str]:
        """
        获取关键词列表
        
        Args:
            analysis: 分析结果
            
        Returns:
            关键词列表
        """
        return analysis.get('keywords', [])
    
    def should_include_source(
        self,
        source: Dict[str, Any],
        analysis: Dict[str, Any]
    ) -> bool:
        """
        判断是否应该包含某个新闻源
        
        Args:
            source: 新闻源信息
            analysis: 场景分析结果
            
        Returns:
            是否包含
        """
        source_features = analysis.get('source_features', {})
        
        # 检查是否在避免列表中
        avoid_categories = source_features.get('avoid_categories', [])
        if source.get('category') in avoid_categories:
            return False
        
        # 检查是否在推荐分类中
        preferred_categories = source_features.get('preferred_categories', [])
        if preferred_categories and source.get('category') in preferred_categories:
            return True
        
        # 检查域名
        preferred_domains = source_features.get('preferred_domains', [])
        source_domain = source.get('domain', '')
        if preferred_domains:
            return any(domain in source_domain for domain in preferred_domains)
        
        # 默认包含
        return True
