"""
API 数据模型定义
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

# --- 基础响应模型 ---

class BaseResponse(BaseModel):
    """基础响应"""
    success: bool = True
    message: str = "Success"

class ErrorResponse(BaseResponse):
    """错误响应"""
    success: bool = False
    error_code: str
    details: Optional[Dict[str, Any]] = None

# --- 任务相关模型 ---

class TaskSource(BaseModel):
    """新闻源模型"""
    name: str
    hashid: str
    category: Optional[str] = None

class TaskStatus(BaseModel):
    """任务状态模型"""
    enabled: bool
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    total_runs: int = 0
    last_error: Optional[str] = None

class TaskDetail(BaseModel):
    """任务详情模型"""
    name: str
    scene: str
    collection: str
    sources: List[TaskSource]
    status: TaskStatus
    created_at: datetime
    locked: bool

class TaskListResponse(BaseResponse):
    """任务列表响应"""
    tasks: List[TaskDetail]
    total: int

class CreateTaskRequest(BaseModel):
    """创建任务请求"""
    name: str = Field(..., description="任务名称 (英文)")
    scene: str = Field(..., description="场景描述")
    sources: List[TaskSource] = Field(..., description="新闻源列表")
    cron: str = Field("0 8 * * *", description="Cron 表达式")
    date_range: str = Field("today", description="日期范围")
    engine_name: str = Field("tophub", description="引擎名称")

class UpdateTaskRequest(BaseModel):
    """更新任务请求"""
    scene: Optional[str] = None
    sources: Optional[List[TaskSource]] = None
    schedule: Optional[Dict[str, Any]] = None
    status: Optional[Dict[str, bool]] = None

# --- 查询相关模型 ---

class SearchRequest(BaseModel):
    """搜索请求"""
    query: str = Field(..., description="查询关键词或问题")
    task_name: Optional[str] = Field(None, description="指定任务名称，不指定则搜索所有")
    limit: int = Field(10, ge=1, le=50, description="返回数量限制")
    date_from: Optional[str] = Field(None, description="开始日期 (YYYY-MM-DD)")
    date_to: Optional[str] = Field(None, description="结束日期 (YYYY-MM-DD)")
    search_mode: str = Field("hybrid", description="搜索模式: hybrid, semantic, keyword")

class NewsItem(BaseModel):
    """新闻条目模型"""
    id: Optional[str] = None
    title: str
    content: Optional[str] = None
    url: str
    source_name: str
    published_at: Optional[str] = None
    score: Optional[float] = None  # 相似度分数
    task_name: Optional[str] = None

class SearchResponse(BaseResponse):
    """搜索响应"""
    results: List[NewsItem]
    total: int
    query: str

# --- 系统相关模型 ---

class SystemStats(BaseModel):
    """系统统计信息"""
    total_tasks: int
    weaviate_status: str
    version: str = "2.0.0"

class HealthResponse(BaseResponse):
    """健康检查响应"""
    status: str
    components: Dict[str, str]
