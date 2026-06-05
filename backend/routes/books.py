# -*- coding: utf-8 -*-
"""
图书管理路由
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from database import get_db
from models import Book, User
from schemas import BookCreate, BookUpdate, BookResponse, BookListResponse
from auth import get_current_admin_user, get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/books", tags=["图书管理"])


@router.get("", response_model=BookListResponse)
def get_books(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词（书名或作者）"),
    category: Optional[str] = Query(None, description="分类筛选"),
    db: Session = Depends(get_db)
):
    """获取图书列表（支持分页和搜索）"""
    query = db.query(Book)
    
    # 搜索过滤
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Book.title.like(search_pattern),
                Book.author.like(search_pattern),
                Book.publisher.like(search_pattern)
            )
        )
    
    # 分类过滤
    if category:
        query = query.filter(Book.category == category)
    
    # 获取总数
    total = query.count()
    
    # 分页
    offset = (page - 1) * page_size
    books = query.order_by(Book.created_at.desc()).offset(offset).limit(page_size).all()
    
    return BookListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=books
    )


@router.get("/categories/list", response_model=list)
def get_categories(db: Session = Depends(get_db)):
    """获取所有分类"""
    categories = db.query(Book.category).distinct().filter(Book.category.isnot(None)).all()
    return [cat[0] for cat in categories if cat[0]]


@router.get("/{book_id}", response_model=BookResponse)
def get_book(book_id: int, db: Session = Depends(get_db)):
    """获取图书详情"""
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="图书不存在"
        )
    return book


@router.post("", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
def create_book(
    book: BookCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """创建图书（需要管理员权限）"""
    # 检查ISBN是否重复
    if book.isbn:
        existing_book = db.query(Book).filter(Book.isbn == book.isbn).first()
        if existing_book:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ISBN已存在"
            )
    
    db_book = Book(**book.model_dump())
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    
    logger.info(f"图书创建成功: {book.title} (by {current_user.username})")
    return db_book


@router.put("/{book_id}", response_model=BookResponse)
def update_book(
    book_id: int,
    book_update: BookUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """更新图书（需要管理员权限）"""
    db_book = db.query(Book).filter(Book.id == book_id).first()
    if not db_book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="图书不存在"
        )
    
    # 更新字段
    update_data = book_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_book, field, value)
    
    db.commit()
    db.refresh(db_book)
    
    logger.info(f"图书更新成功: {db_book.title} (by {current_user.username})")
    return db_book


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """删除图书（需要管理员权限）"""
    db_book = db.query(Book).filter(Book.id == book_id).first()
    if not db_book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="图书不存在"
        )
    
    book_title = db_book.title
    db.delete(db_book)
    db.commit()
    
    logger.info(f"图书删除成功: {book_title} (by {current_user.username})")
    return None
