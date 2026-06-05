# -*- coding: utf-8 -*-
"""
FastAPI 应用入口
"""
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from database import engine
from models import Base
from seed import init_db, seed_data
from routes.auth import router as auth_router
from routes.books import router as books_router
from routes.promotions import router as promotions_router
from routes.feedbacks import router as feedbacks_router
from routes.chapters import router as chapters_router
from routes.stock_takings import router as stock_takings_router
from routes.purchase_orders import router as purchase_orders_router

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化数据库
    logger.info("正在初始化数据库...")
    init_db()
    seed_data()
    logger.info("数据库初始化完成")
    yield
    # 关闭时的清理工作
    logger.info("应用关闭")


# 创建 FastAPI 应用
app = FastAPI(
    title="现代化在线书店 API",
    description="基于 FastAPI 构建的在线书店后端服务，提供用户认证和图书管理功能",
    version="1.0.0",
    lifespan=lifespan
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    logger.error(f"未捕获的异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "服务器内部错误，请稍后重试"}
    )


# 注册路由
app.include_router(auth_router)
app.include_router(books_router)
app.include_router(promotions_router)
app.include_router(feedbacks_router)
app.include_router(chapters_router)
app.include_router(stock_takings_router)
app.include_router(purchase_orders_router)

# 挂载静态文件
# 确保static目录存在
os.makedirs("static", exist_ok=True)
app.mount("/api/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    """根路由"""
    return {
        "message": "欢迎使用现代化在线书店 API",
        "docs": "/docs",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}
