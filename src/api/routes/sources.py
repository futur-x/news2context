"""
新闻源管理路由
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from src.utils.config import get_config
from src.core.source_selector import SourceSelector
import yaml
import os

router = APIRouter()

# --- 模型定义 ---

class Source(BaseModel):
    name: str
    hashid: str
    url: Optional[str] = None
    category: str

class RecommendRequest(BaseModel):
    scene: str
    max_sources: int = 10

class RecommendResponse(BaseModel):
    recommended_sources: List[Dict[str, Any]]

# --- 辅助函数 ---

def get_all_sources() -> List[Dict[str, Any]]:
    """从配置文件加载所有新闻源"""
    config = get_config()
    # 这里我们直接读取 config/news_sources.yaml，因为 ConfigManager 可能没有加载它
    # 或者我们可以通过 ConfigManager 获取如果它已经被合并
    # 让我们尝试直接读取文件以确保获取完整列表
    
    try:
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        config_path = os.path.join(project_root, 'config', 'news_sources.yaml')
        
        with open(config_path, 'r', encoding='utf-8') as f:
            source_config = yaml.safe_load(f)
            
        all_sources = []
        for category in source_config.get('categories', []):
            cat_name = category['name']
            for source in category.get('sources', []):
                source['category'] = cat_name
                all_sources.append(source)
                
        return all_sources
    except Exception as e:
        print(f"Error loading sources: {e}")
        return []

# --- 路由定义 ---

@router.get("/sources", response_model=List[Source])
async def list_sources():
    """获取所有可用新闻源"""
    return get_all_sources()

@router.post("/sources/recommend", response_model=RecommendResponse)
async def recommend_sources(request: RecommendRequest):
    """根据场景智能推荐新闻源"""
    config = get_config()
    llm_config = {
        'api_key': config.get('llm.api_key'),
        'base_url': config.get('llm.base_url'),
        'model': config.get('llm.model')
    }
    
    if not llm_config['api_key']:
        raise HTTPException(status_code=500, detail="LLM API key not configured")
        
    selector = SourceSelector(llm_config)
    all_sources = get_all_sources()
    
    try:
        recommended = await selector.select_sources(
            all_sources=all_sources,
            scene_description=request.scene,
            max_sources=request.max_sources
        )
        return RecommendResponse(recommended_sources=recommended)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recommendation failed: {str(e)}")
