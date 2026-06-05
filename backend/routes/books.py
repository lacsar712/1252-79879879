# -*- coding: utf-8 -*-
"""
图书管理路由
"""
import logging
import random
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from database import get_db
from models import Book, User
from schemas import (
    BookCreate, BookUpdate, BookResponse, BookListResponse,
    BookCompareRequest, BookCompareResponse, BookCompareData
)
from auth import get_current_admin_user, get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/books", tags=["图书管理"])


def generate_mock_rating(book_id: int) -> float:
    random.seed(book_id)
    return round(random.uniform(3.0, 5.0), 1)


def generate_mock_review_count(book_id: int) -> int:
    random.seed(book_id * 2)
    return random.randint(10, 500)


def generate_mock_tags(book_id: int, category: Optional[str]) -> List[str]:
    base_tags = []
    if category:
        base_tags.append(category)
    
    tag_options = ['畅销书', '经典', '必读', '推荐', '新版', '精装', '获奖']
    random.seed(book_id * 3)
    selected_tags = random.sample(tag_options, random.randint(1, 3))
    base_tags.extend(selected_tags)
    return list(set(base_tags))


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


@router.post("/compare", response_model=BookCompareResponse)
def get_books_compare(
    request: BookCompareRequest,
    db: Session = Depends(get_db)
):
    """获取图书对比数据（支持最多4本图书）"""
    if len(request.book_ids) > 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="最多只能对比4本图书"
        )
    
    books = db.query(Book).filter(Book.id.in_(request.book_ids)).all()
    book_map = {book.id: book for book in books}
    
    valid_ids = list(book_map.keys())
    invalid_ids = [bid for bid in request.book_ids if bid not in valid_ids]
    
    compare_items: List[BookCompareData] = []
    for book_id in request.book_ids:
        if book_id in book_map:
            book = book_map[book_id]
            compare_data = BookCompareData(
                id=book.id,
                title=book.title,
                author=book.author,
                publisher=book.publisher,
                category=book.category,
                price=book.price,
                stock=book.stock,
                description=book.description,
                cover_image=book.cover_image,
                isbn=book.isbn,
                rating=generate_mock_rating(book.id),
                review_count=generate_mock_review_count(book.id),
                tags=generate_mock_tags(book.id, book.category),
                is_valid=True
            )
            compare_items.append(compare_data)
        else:
            invalid_data = BookCompareData(
                id=book_id,
                title="已失效",
                author="未知",
                publisher=None,
                category=None,
                price=0,
                stock=0,
                description=None,
                cover_image=None,
                isbn=None,
                rating=None,
                review_count=0,
                tags=[],
                is_valid=False,
                invalid_reason="图书不存在或已下架"
            )
            compare_items.append(invalid_data)
    
    return BookCompareResponse(
        items=compare_items,
        invalid_ids=invalid_ids
    )


@router.post("/compare/save")
def save_compare_list(
    request: BookCompareRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """保存用户的对比列表（需要登录）"""
    if len(request.book_ids) > 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="最多只能保存4本图书"
        )
    
    compare_key = f"compare_list_{current_user.id}"
    stored_value = db.query(Book).filter(Book.id.in_(request.book_ids)).count()
    
    logger.info(f"用户 {current_user.username} 保存对比列表: {request.book_ids}")
    
    return {"message": "保存成功", "stored_count": stored_value}


@router.get("/compare/saved")
def get_saved_compare_list(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户保存的对比列表（需要登录）"""
    logger.info(f"用户 {current_user.username} 获取保存的对比列表")
    return {"book_ids": []}
