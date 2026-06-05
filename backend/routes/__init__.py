# -*- coding: utf-8 -*-
"""
路由模块
"""
from routes.auth import router as auth_router
from routes.books import router as books_router
from routes.promotions import router as promotions_router
from routes.feedbacks import router as feedbacks_router

__all__ = ["auth_router", "books_router", "promotions_router", "feedbacks_router"]
