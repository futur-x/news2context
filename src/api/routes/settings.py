"""
配置管理路由
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from src.utils.config import get_config

router = APIRouter()

# --- 模型定义 ---

class SystemSettings(BaseModel):
    """系统配置模型"""
    llm_provider: str
    llm_api_key: str
    llm_base_url: str
    llm_model: str
    weaviate_url: str
    weaviate_api_key: Optional[str] = None

class EngineSettings(BaseModel):
    """引擎配置模型"""
    tophub_api_key: str
    tophub_base_url: str

# --- 路由定义 ---

@router.get("/settings/system", response_model=SystemSettings)
async def get_system_settings():
    """获取系统配置"""
    config = get_config()
    return SystemSettings(
        llm_provider=config.get('llm.provider', 'openai'),
        llm_api_key=config.get('llm.api_key', ''),
        llm_base_url=config.get('llm.base_url', ''),
        llm_model=config.get('llm.model', ''),
        weaviate_url=config.get('weaviate.url', ''),
        weaviate_api_key=config.get('weaviate.api_key', '')
    )

@router.put("/settings/system")
async def update_system_settings(settings: SystemSettings):
    """更新系统配置"""
    config = get_config()
    
    # 更新 LLM 配置
    config.set('llm.provider', settings.llm_provider)
    config.set('llm.api_key', settings.llm_api_key)
    config.set('llm.base_url', settings.llm_base_url)
    config.set('llm.model', settings.llm_model)
    
    # 更新 Weaviate 配置
    config.set('weaviate.url', settings.weaviate_url)
    if settings.weaviate_api_key:
        config.set('weaviate.api_key', settings.weaviate_api_key)
        
    # 保存配置
    try:
        config.save()
        return {"success": True, "message": "系统配置已更新"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save config: {str(e)}")

@router.get("/settings/engines/tophub", response_model=EngineSettings)
async def get_tophub_settings():
    """获取 TopHub 引擎配置"""
    config = get_config()
    return EngineSettings(
        tophub_api_key=config.get('news_sources.engines.tophub.api_key', ''),
        tophub_base_url=config.get('news_sources.engines.tophub.base_url', '')
    )

@router.put("/settings/engines/tophub")
async def update_tophub_settings(settings: EngineSettings):
    """更新 TopHub 引擎配置"""
    config = get_config()
    
    config.set('news_sources.engines.tophub.api_key', settings.tophub_api_key)
    config.set('news_sources.engines.tophub.base_url', settings.tophub_base_url)
    
    try:
        config.save()
        return {"success": True, "message": "TopHub 配置已更新"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save config: {str(e)}")
