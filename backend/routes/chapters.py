# -*- coding: utf-8 -*-
"""
试读章节管理路由
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from database import get_db
from models import BookChapter, Book, User
from schemas import (
    BookChapterCreate, BookChapterUpdate, BookChapterResponse,
    BookChapterListResponse, BookChapterPublicResponse, BookChapterPublicListResponse
)
from auth import get_current_admin_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chapters", tags=["试读章节管理"])


@router.get("/public/{book_id}", response_model=BookChapterPublicListResponse)
def get_public_chapters(
    book_id: int,
    db: Session = Depends(get_db)
):
    """获取图书的公开试读章节列表（用户端）"""
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="图书不存在"
        )
    
    chapters = db.query(BookChapter).filter(
        BookChapter.book_id == book_id,
        BookChapter.is_public == True
    ).order_by(BookChapter.sort_order.asc(), BookChapter.created_at.asc()).all()
    
    return BookChapterPublicListResponse(
        total=len(chapters),
        items=chapters
    )


@router.get("/public/{book_id}/{chapter_id}", response_model=BookChapterPublicResponse)
def get_public_chapter_detail(
    book_id: int,
    chapter_id: int,
    db: Session = Depends(get_db)
):
    """获取公开章节详情（用户端）"""
    chapter = db.query(BookChapter).filter(
        BookChapter.id == chapter_id,
        BookChapter.book_id == book_id,
        BookChapter.is_public == True
    ).first()
    
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="章节不存在或未公开"
        )
    
    return chapter


@router.get("/admin/{book_id}", response_model=BookChapterListResponse)
def get_admin_chapters(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """获取图书的所有章节列表（管理端，包含隐藏章节）"""
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="图书不存在"
        )
    
    chapters = db.query(BookChapter).filter(
        BookChapter.book_id == book_id
    ).order_by(BookChapter.sort_order.asc(), BookChapter.created_at.asc()).all()
    
    return BookChapterListResponse(
        total=len(chapters),
        items=chapters
    )


@router.get("/admin/{book_id}/{chapter_id}", response_model=BookChapterResponse)
def get_admin_chapter_detail(
    book_id: int,
    chapter_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """获取章节详情（管理端）"""
    chapter = db.query(BookChapter).filter(
        BookChapter.id == chapter_id,
        BookChapter.book_id == book_id
    ).first()
    
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="章节不存在"
        )
    
    return chapter


@router.post("", response_model=BookChapterResponse, status_code=status.HTTP_201_CREATED)
def create_chapter(
    chapter: BookChapterCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """创建章节（需要管理员权限）"""
    book = db.query(Book).filter(Book.id == chapter.book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="图书不存在"
        )
    
    db_chapter = BookChapter(**chapter.model_dump())
    db.add(db_chapter)
    db.commit()
    db.refresh(db_chapter)
    
    logger.info(f"章节创建成功: {chapter.title} (图书ID: {chapter.book_id}, by {current_user.username})")
    return db_chapter


@router.put("/{chapter_id}", response_model=BookChapterResponse)
def update_chapter(
    chapter_id: int,
    chapter_update: BookChapterUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """更新章节（需要管理员权限）"""
    db_chapter = db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
    if not db_chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="章节不存在"
        )
    
    update_data = chapter_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_chapter, field, value)
    
    db.commit()
    db.refresh(db_chapter)
    
    logger.info(f"章节更新成功: {db_chapter.title} (by {current_user.username})")
    return db_chapter


@router.patch("/{chapter_id}/toggle-public", response_model=BookChapterResponse)
def toggle_chapter_public(
    chapter_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """切换章节公开/隐藏状态（需要管理员权限）"""
    db_chapter = db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
    if not db_chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="章节不存在"
        )
    
    db_chapter.is_public = not db_chapter.is_public
    db.commit()
    db.refresh(db_chapter)
    
    status_text = "公开" if db_chapter.is_public else "隐藏"
    logger.info(f"章节{status_text}成功: {db_chapter.title} (by {current_user.username})")
    return db_chapter


@router.patch("/{chapter_id}/sort", response_model=BookChapterResponse)
def update_chapter_sort(
    chapter_id: int,
    sort_order: int = Query(..., ge=0, description="排序值"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """更新章节排序（需要管理员权限）"""
    db_chapter = db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
    if not db_chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="章节不存在"
        )
    
    db_chapter.sort_order = sort_order
    db.commit()
    db.refresh(db_chapter)
    
    logger.info(f"章节排序更新成功: {db_chapter.title} -> {sort_order} (by {current_user.username})")
    return db_chapter


@router.delete("/{chapter_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chapter(
    chapter_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """删除章节（需要管理员权限）"""
    db_chapter = db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
    if not db_chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="章节不存在"
        )
    
    chapter_title = db_chapter.title
    db.delete(db_chapter)
    db.commit()
    
    logger.info(f"章节删除成功: {chapter_title} (by {current_user.username})")
    return None


@router.get("/preview/{chapter_id}", response_model=BookChapterResponse)
def preview_chapter(
    chapter_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """预览章节内容（管理端，无论是否公开都可查看）"""
    chapter = db.query(BookChapter).filter(BookChapter.id == chapter_id).first()
    
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="章节不存在"
        )
    
    return chapter
