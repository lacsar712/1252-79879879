# -*- coding: utf-8 -*-
"""
图书服务层
提供图书查询的搜索、筛选、排序、分页等核心业务逻辑
"""
import logging
from typing import Optional, Tuple, List

from sqlalchemy.orm import Session, Query
from sqlalchemy import or_

from models import Book, User
from schemas import BookListResponse

logger = logging.getLogger(__name__)


def apply_search_filter(query: Query, search: Optional[str]) -> Query:
    """
    应用搜索过滤条件
    在书名、作者、出版社字段上进行模糊匹配

    Args:
        query: SQLAlchemy Query 对象
        search: 搜索关键词

    Returns:
        应用了搜索条件后的 Query 对象
    """
    if not search:
        return query

    search_pattern = f"%{search}%"
    query = query.filter(
        or_(
            Book.title.like(search_pattern),
            Book.author.like(search_pattern),
            Book.publisher.like(search_pattern)
        )
    )
    return query


def apply_category_filter(query: Query, category: Optional[str]) -> Query:
    """
    应用分类过滤条件

    Args:
        query: SQLAlchemy Query 对象
        category: 图书分类名称

    Returns:
        应用了分类条件后的 Query 对象
    """
    if not category:
        return query

    query = query.filter(Book.category == category)
    return query


def apply_sorting(query: Query, sort_by: Optional[str], sort_order: str) -> Query:
    """
    应用排序条件

    Args:
        query: SQLAlchemy Query 对象
        sort_by: 排序字段，目前支持 "price"，其他值默认按创建时间排序
        sort_order: 排序方向，"desc" 为降序，其他值（包括无效值）默认为升序

    Returns:
        应用了排序条件后的 Query 对象
    """
    if sort_by == "price":
        if sort_order.lower() == "desc":
            query = query.order_by(Book.price.desc())
        else:
            query = query.order_by(Book.price.asc())
    else:
        query = query.order_by(Book.created_at.desc())

    return query


def apply_pagination(query: Query, page: int, page_size: int) -> Tuple[List[Book], int]:
    """
    应用分页并返回结果列表和总数

    Args:
        query: SQLAlchemy Query 对象
        page: 页码（从1开始）
        page_size: 每页数量

    Returns:
        (分页后的图书列表, 符合条件的总记录数)
    """
    total = query.count()
    offset = (page - 1) * page_size
    books = query.offset(offset).limit(page_size).all()
    return books, total


def build_query(
    db: Session,
    search: Optional[str] = None,
    category: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_order: str = "asc"
) -> Query:
    """
    构建完整的图书查询 Query（不含分页）

    按顺序组合：搜索过滤 -> 分类过滤 -> 排序

    Args:
        db: 数据库会话
        search: 搜索关键词
        category: 分类筛选
        sort_by: 排序字段
        sort_order: 排序方向

    Returns:
        已应用所有过滤和排序条件的 Query 对象
    """
    query = db.query(Book)
    query = apply_search_filter(query, search)
    query = apply_category_filter(query, category)
    query = apply_sorting(query, sort_by, sort_order)
    return query


def get_books_list(
    db: Session,
    page: int = 1,
    page_size: int = 10,
    search: Optional[str] = None,
    category: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_order: str = "asc"
) -> BookListResponse:
    """
    获取图书列表（核心查询服务）

    整合搜索、分类筛选、排序、分页逻辑，返回标准化的分页响应。

    Args:
        db: 数据库会话
        page: 页码，从1开始
        page_size: 每页数量，1-100
        search: 搜索关键词（书名、作者、出版社模糊匹配）
        category: 分类筛选
        sort_by: 排序字段，"price" 或默认按创建时间
        sort_order: 排序方向，"asc" 或 "desc"

    Returns:
        BookListResponse 包含 total、page、page_size、items
    """
    query = build_query(db, search, category, sort_by, sort_order)
    books, total = apply_pagination(query, page, page_size)

    return BookListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=books
    )


def validate_admin_permission(current_user: User) -> None:
    """
    校验管理员权限

    Args:
        current_user: 当前登录用户

    Raises:
        HTTPException: 当用户不是管理员时抛出 403 异常
    """
    from fastapi import HTTPException, status

    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )


def get_categories_list(db: Session) -> List[str]:
    """
    获取所有图书分类列表

    Args:
        db: 数据库会话

    Returns:
        去重后的分类名称列表（不含 None 和空字符串）
    """
    categories = db.query(Book.category).distinct().filter(Book.category.isnot(None)).all()
    return [cat[0] for cat in categories if cat[0]]
