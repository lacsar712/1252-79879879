# -*- coding: utf-8 -*-
"""
路由模块
"""
from routes.auth import router as auth_router
from routes.books import router as books_router
from routes.promotions import router as promotions_router
from routes.feedbacks import router as feedbacks_router
from routes.chapters import router as chapters_router
from routes.stock_takings import router as stock_takings_router

__all__ = ["auth_router", "books_router", "promotions_router", "feedbacks_router", "chapters_router", "stock_takings_router"]
