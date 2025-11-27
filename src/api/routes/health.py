"""
健康检查路由
"""

from fastapi import APIRouter
from src.api.models import HealthResponse
from src.utils.config import get_config
from src.storage.weaviate_client import CollectionManager

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """系统健康检查"""
    config = get_config()
    components = {
        "api": "running",
        "weaviate": "unknown"
    }
    
    # 检查 Weaviate 连接
    try:
        client = CollectionManager(
            weaviate_url=config.get('weaviate.url'),
            api_key=config.get('weaviate.api_key')
        )
        # 简单调用一个轻量级方法检查连接
        if client.client.is_ready():
            components["weaviate"] = "connected"
        else:
            components["weaviate"] = "disconnected"
    except Exception as e:
        components["weaviate"] = f"error: {str(e)}"
    
    status = "healthy" if components["weaviate"] == "connected" else "degraded"
    
    return HealthResponse(
        status=status,
        components=components
    )
