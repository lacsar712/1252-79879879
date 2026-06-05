# -*- coding: utf-8 -*-
"""
开放 API 路由（供第三方系统使用 API Key 调用）
"""
import logging
import time
from typing import Optional
from fastapi import APIRouter, Depends, Request, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from database import get_db
from models import APIKey, Book
from schemas import OpenAPIBookResponse, OpenAPIBookListResponse
from api_key_auth import authenticate_api_key, log_api_call

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/open", tags=["开放 API"])


@router.get("/books", response_model=OpenAPIBookListResponse)
async def get_open_books(
    request: Request,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词（书名、作者、出版社）"),
    category: Optional[str] = Query(None, description="分类筛选"),
    db: Session = Depends(get_db),
    api_key: APIKey = Depends(lambda req, db: authenticate_api_key(req, db, "books:read"))
):
    """只读图书查询接口（需要 API Key 鉴权）"""
    start_time = time.time()
    try:
        query = db.query(Book)

        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    Book.title.like(search_pattern),
                    Book.author.like(search_pattern),
                    Book.publisher.like(search_pattern)
                )
            )

        if category:
            query = query.filter(Book.category == category)

        total = query.count()
        offset = (page - 1) * page_size
        books = query.order_by(Book.created_at.desc()).offset(offset).limit(page_size).all()

        response_time_ms = int((time.time() - start_time) * 1000)
        await log_api_call(db, api_key.id, api_key.api_key, request, 200, None, response_time_ms)

        return OpenAPIBookListResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=books
        )
    except Exception as e:
        response_time_ms = int((time.time() - start_time) * 1000)
        await log_api_call(db, api_key.id, api_key.api_key, request, 500, str(e), response_time_ms)
        raise


@router.get("/books/{book_id}", response_model=OpenAPIBookResponse)
async def get_open_book(
    request: Request,
    book_id: int,
    db: Session = Depends(get_db),
    api_key: APIKey = Depends(lambda req, db: authenticate_api_key(req, db, "books:read"))
):
    """获取单本图书详情（需要 API Key 鉴权）"""
    start_time = time.time()
    try:
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            from fastapi import HTTPException
            response_time_ms = int((time.time() - start_time) * 1000)
            await log_api_call(db, api_key.id, api_key.api_key, request, 404, "图书不存在", response_time_ms)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="图书不存在"
            )

        response_time_ms = int((time.time() - start_time) * 1000)
        await log_api_call(db, api_key.id, api_key.api_key, request, 200, None, response_time_ms)

        return book
    except HTTPException:
        raise
    except Exception as e:
        response_time_ms = int((time.time() - start_time) * 1000)
        await log_api_call(db, api_key.id, api_key.api_key, request, 500, str(e), response_time_ms)
        raise


@router.get("/books/categories/list")
async def get_open_categories(
    request: Request,
    db: Session = Depends(get_db),
    api_key: APIKey = Depends(lambda req, db: authenticate_api_key(req, db, "books:read"))
):
    """获取所有分类（需要 API Key 鉴权）"""
    start_time = time.time()
    try:
        categories = db.query(Book.category).distinct().filter(Book.category.isnot(None)).all()
        result = [cat[0] for cat in categories if cat[0]]

        response_time_ms = int((time.time() - start_time) * 1000)
        await log_api_call(db, api_key.id, api_key.api_key, request, 200, None, response_time_ms)

        return result
    except Exception as e:
        response_time_ms = int((time.time() - start_time) * 1000)
        await log_api_call(db, api_key.id, api_key.api_key, request, 500, str(e), response_time_ms)
        raise
