"""
聊天路由
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from src.core.task_manager import TaskManager
from src.storage.weaviate_client import CollectionManager
from src.utils.config import get_config
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

router = APIRouter()

class ChatMessage(BaseModel):
    """聊天消息"""
    role: str  # 'user' or 'assistant'
    content: str

class ChatRequest(BaseModel):
    """聊天请求"""
    task_name: str
    message: str
    history: Optional[List[ChatMessage]] = []

class ChatResponse(BaseModel):
    """聊天响应"""
    success: bool = True
    message: str
    sources: List[dict] = []

@router.post("/chat", response_model=ChatResponse)
async def chat_with_knowledge_base(request: ChatRequest):
    """
    与知识库聊天
    """
    # 验证任务是否存在
    task_manager = TaskManager()
    task = task_manager.get_task(request.task_name)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task not found: {request.task_name}")
    
    # 执行混合搜索获取相关内容
    config = get_config()
    collection_manager = CollectionManager(
        weaviate_url=config.get('weaviate.url'),
        api_key=config.get('weaviate.api_key')
    )
    
    try:
        # 搜索相关内容 - 使用 hybrid_search 方法
        search_config = config.get('weaviate.search', {})
        alpha = search_config.get('hybrid_alpha', 0.75)
        max_results = search_config.get('max_results', 5)
        
        results = collection_manager.hybrid_search(
            collection_name=task.collection_name,
            query=request.message,
            limit=max_results,
            alpha=alpha
        )
        
        # 构建上下文
        context_parts = []
        sources = []
        for idx, item in enumerate(results, 1):
            content = item.get("content", "")
            title = item.get("title", "")
            source = item.get("source_name", "")
            
            context_parts.append(f"[文档 {idx}]\n标题: {title}\n来源: {source}\n内容: {content}\n")
            sources.append({
                "content": content[:200] + "..." if len(content) > 200 else content,
                "score": item.get("_additional", {}).get("score"),
                "title": title,
                "source": source
            })
        
        context = "\n".join(context_parts)
        
        # 调用 LLM
        llm = ChatOpenAI(
            model=config.get('llm.model'),
            api_key=config.get('llm.api_key'),
            base_url=config.get('llm.base_url'),
            temperature=0.7
        )
        
        system_prompt = f"""你是一个专业的新闻分析助手。请基于以下新闻内容回答用户的问题。

新闻内容：
{context}

注意：
1. 请仅基于提供的新闻内容回答
2. 如果新闻内容中没有相关信息，请明确告知用户
3. 回答要简洁、准确、专业
4. 可以引用具体的新闻标题和来源"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=request.message)
        ]
        
        response = llm(messages)
        
        return ChatResponse(
            message=response.content,
            sources=sources
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")
