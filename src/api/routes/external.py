"""
外部访问 API 路由
供外部 AI 系统查询知识库
"""

from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
import secrets
import hashlib
from pathlib import Path
import yaml

from src.core.task_manager import TaskManager
from src.storage.weaviate_client import CollectionManager
from src.utils.config import get_config

router = APIRouter()

# Token 存储文件路径
TOKEN_FILE = Path(__file__).parent.parent.parent.parent / "config" / ".api_tokens.yaml"

# --- 模型定义 ---

class ExternalQueryRequest(BaseModel):
    """外部查询请求"""
    query: str = Field(..., description="查询问题")
    limit: int = Field(5, ge=1, le=20, description="返回结果数量")
    search_mode: str = Field("hybrid", description="搜索模式: hybrid, semantic, keyword")
    alpha: float = Field(0.5, ge=0.0, le=1.0, description="混合搜索权重 (0=纯关键词, 1=纯语义)")
    min_score: float = Field(0.0, ge=0.0, le=1.0, description="最低分数阈值 (低于此分数的结果不返回)")

class ExternalQueryResponse(BaseModel):
    """外部查询响应"""
    success: bool = True
    task_name: str
    query: str
    results: List[dict]
    total: int
    search_mode: str
    alpha: float

class TokenInfo(BaseModel):
    """Token 信息"""
    token_preview: str
    created_at: str
    last_used: Optional[str] = None

class GenerateTokenResponse(BaseModel):
    """生成 Token 响应"""
    success: bool = True
    token: str
    message: str

# --- Token 管理 ---

def _load_tokens() -> dict:
    """加载 Token 配置"""
    if not TOKEN_FILE.exists():
        return {"tokens": {}}
    
    with open(TOKEN_FILE, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {"tokens": {}}

def _save_tokens(data: dict):
    """保存 Token 配置"""
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(TOKEN_FILE, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True)

def _hash_token(token: str) -> str:
    """对 Token 进行哈希"""
    return hashlib.sha256(token.encode()).hexdigest()

def _verify_token(token: str) -> bool:
    """验证 Token"""
    token_data = _load_tokens()
    token_hash = _hash_token(token)
    return token_hash in token_data.get("tokens", {})

async def verify_api_token(authorization: Optional[str] = Header(None)):
    """验证 API Token 依赖"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    
    # 支持 "Bearer <token>" 格式
    if authorization.startswith("Bearer "):
        token = authorization[7:]
    else:
        token = authorization
    
    if not _verify_token(token):
        raise HTTPException(status_code=401, detail="Invalid API token")
    
    return token

# --- 路由定义 ---

@router.post("/external/{task_name}/query", response_model=ExternalQueryResponse)
async def query_knowledge_base(
    task_name: str,
    request: ExternalQueryRequest,
    token: str = Depends(verify_api_token)
):
    """
    外部 AI 查询知识库
    
    需要在 Header 中提供: Authorization: Bearer <token>
    """
    # 验证任务是否存在
    task_manager = TaskManager()
    task = task_manager.get_task(task_name)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_name}")
    
    # 执行混合搜索
    config = get_config()
    
    # 获取 Embedding API Key（优先使用 embedding.api_key，否则使用 llm.api_key）
    embedding_api_key = config.get('embedding.api_key') or config.get('llm.api_key')
    headers = {}
    if embedding_api_key:
        headers["X-OpenAI-Api-Key"] = embedding_api_key
    
    # 准备 embedding 配置
    embedding_config = {
        'model': config.get('embedding.model', 'text-embedding-3-small'),
        'base_url': config.get('embedding.base_url', 'https://litellm.futurx.cc'),
        'dimensions': config.get('embedding.dimensions', 1536)
    }
    
    collection_manager = CollectionManager(
        weaviate_url=config.get('weaviate.url'),
        api_key=config.get('weaviate.api_key'),
        additional_headers=headers,
        embedding_config=embedding_config
    )
    
    
    try:
        # 根据搜索模式设置 alpha
        if request.search_mode == 'semantic':
            alpha = 1.0  # 纯语义搜索
        elif request.search_mode == 'keyword':
            alpha = 0.0  # 纯关键词搜索
        else:  # hybrid
            alpha = request.alpha  # 使用用户指定的权重
        
        # 使用统一搜索接口（自动处理 NewsArticle 和 NewsChunk schema）
        results = collection_manager.unified_search(
            collection_name=task.collection_name,
            query=request.query,
            limit=request.limit
        )

        # 格式化结果
        formatted_results = []
        for item in results:
            # unified_search 返回的是 certainty
            certainty = item.get("_additional", {}).get("certainty", 0)

            # 转换 certainty 为 float
            try:
                score_float = float(certainty) if certainty is not None else 0.0
            except (ValueError, TypeError):
                score_float = 0.0

            # 过滤低分结果
            if score_float < request.min_score:
                continue

            formatted_results.append({
                "content": item.get("content"),  # 已经是拼接后的完整内容
                "score": score_float,
                "title": item.get("title"),
                "url": item.get("url"),
                "source_name": item.get("source_name"),
                "category": item.get("category"),
            })
        
        return ExternalQueryResponse(
            task_name=task_name,
            query=request.query,
            results=formatted_results,
            total=len(formatted_results),
            search_mode=request.search_mode,
            alpha=alpha
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

@router.post("/external/tokens", response_model=GenerateTokenResponse)
async def generate_api_token():
    """生成新的 API Token"""
    # 生成随机 Token
    token = f"n2kb_{secrets.token_urlsafe(32)}"
    token_hash = _hash_token(token)
    
    # 保存 Token
    token_data = _load_tokens()
    if "tokens" not in token_data:
        token_data["tokens"] = {}
    
    from datetime import datetime
    token_data["tokens"][token_hash] = {
        "created_at": datetime.now().isoformat(),
        "last_used": None
    }
    
    _save_tokens(token_data)
    
    return GenerateTokenResponse(
        token=token,
        message="Token generated successfully. Please save it securely - it won't be shown again."
    )

@router.get("/external/tokens", response_model=List[TokenInfo])
async def list_api_tokens():
    """列出所有 API Token (仅显示预览)"""
    token_data = _load_tokens()
    tokens = token_data.get("tokens", {})

    result = []
    for token_hash, info in tokens.items():
        result.append(TokenInfo(
            token_preview=f"{token_hash[:8]}...{token_hash[-8:]}",
            created_at=info.get("created_at"),
            last_used=info.get("last_used")
        ))

    return result

@router.delete("/external/tokens/{token_hash}")
async def delete_api_token(token_hash: str):
    """删除指定的 API Token"""
    token_data = _load_tokens()
    tokens = token_data.get("tokens", {})

    if token_hash not in tokens:
        raise HTTPException(status_code=404, detail="Token not found")

    del tokens[token_hash]
    token_data["tokens"] = tokens
    _save_tokens(token_data)

    return {"success": True, "message": "Token deleted successfully"}
