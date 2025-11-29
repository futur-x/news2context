"""
FastAPI 应用入口
"""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from src.utils.logger import setup_logger
from src.api.routes import health, tasks, query, settings, external, chat, browse, sources

def create_app() -> FastAPI:
    """创建并配置 FastAPI 应用"""
    # 初始化日志
    setup_logger()
    
    app = FastAPI(
        title="News2Context API",
        description="AI 驱动的新闻聚合系统 API",
        version="2.0.0"
    )
    
    # 配置 CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 允许所有来源，生产环境应限制
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 注册路由
    app.include_router(health.router, prefix="/api", tags=["System"])
    app.include_router(tasks.router, prefix="/api", tags=["Tasks"])
    app.include_router(query.router, prefix="/api", tags=["Query"])
    app.include_router(settings.router, prefix="/api", tags=["Settings"])
    app.include_router(external.router, prefix="/api", tags=["External"])
    app.include_router(chat.router, prefix="/api", tags=["Chat"])
    app.include_router(browse.router, prefix="/api", tags=["Browse"])
    app.include_router(sources.router, prefix="/api", tags=["Sources"])
    
    return app

app = create_app()

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    body = await request.body()
    logger.error(f"Validation Error: {exc.errors()}")
    logger.error(f"Request Body: {body.decode()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": body.decode()},
    )



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.app:app", host="0.0.0.0", port=8043, reload=True)
