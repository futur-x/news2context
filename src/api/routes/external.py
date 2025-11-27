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

class ExternalQueryResponse(BaseModel):
    """外部查询响应"""
    success: bool = True
    task_name: str
    query: str
    results: List[dict]
    total: int

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
    collection_manager = CollectionManager(
        weaviate_url=config.get('weaviate.url'),
        api_key=config.get('weaviate.api_key')
    )
    
    try:
        results = collection_manager.hybrid_search(
            collection_name=task.collection_name,
            query=request.query,
            limit=request.limit,
            alpha=config.get('weaviate.search.hybrid_alpha', 0.5)
        )
        
        # 格式化结果
        formatted_results = []
        for item in results:
            formatted_results.append({
                "content": item.get("content"),
                "score": item.get("_additional", {}).get("score"),
                "article_titles": item.get("article_titles", []),
                "sources": item.get("sources", []),
                "categories": item.get("categories", [])
            })
        
        return ExternalQueryResponse(
            task_name=task_name,
            query=request.query,
            results=formatted_results,
            total=len(formatted_results)
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
