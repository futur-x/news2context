"""
新闻源管理路由
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from src.utils.config import get_config
from src.core.source_selector import SourceSelector
from src.engines.factory import EngineFactory
import asyncio

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

async def get_all_sources_from_engine() -> List[Dict[str, Any]]:
    """从 TopHub 引擎获取所有新闻源（与 CLI 一致）"""
    config = get_config()
    try:
        # 使用 EngineFactory 创建引擎（与 CLI 保持一致）
        engine = EngineFactory.create_engine(config.config)
        # 调用引擎的 get_all_sources 方法（会使用缓存）
        all_sources = await engine.get_all_sources()
        return all_sources
    except Exception as e:
        print(f"Error loading sources from engine: {e}")
        raise

# --- 路由定义 ---

@router.get("/sources", response_model=List[Source])
async def list_sources():
    """获取所有可用新闻源（从 TopHub API）"""
    try:
        sources = await get_all_sources_from_engine()
        return sources
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch sources: {str(e)}")

@router.post("/sources/recommend", response_model=RecommendResponse)
async def recommend_sources(request: RecommendRequest):
    """根据场景智能推荐新闻源（与 CLI 逻辑一致）"""
    config = get_config()
    llm_config = {
        'api_key': config.get('llm.api_key'),
        'base_url': config.get('llm.base_url'),
        'model': config.get('llm.model')
    }
    
    if not llm_config['api_key']:
        raise HTTPException(status_code=500, detail="LLM API key not configured")
        
    try:
        # 1. 获取所有源（与 CLI 一致）
        all_sources = await get_all_sources_from_engine()
        
        # 2. 使用 LLM 智能推荐（与 CLI 一致）
        selector = SourceSelector(llm_config)
        recommended = await selector.select_sources(
            all_sources=all_sources,
            scene_description=request.scene,
            max_sources=request.max_sources
        )
        
        return RecommendResponse(recommended_sources=recommended)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recommendation failed: {str(e)}")

