# -*- coding: utf-8 -*-
"""
活动专题管理路由
"""
import logging
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_

from database import get_db
from models import Promotion, PromotionBook, Book, User
from schemas import (
    PromotionCreate, PromotionUpdate, PromotionResponse,
    PromotionListResponse, PromotionBookResponse,
    PromotionStockDeductRequest
)
from auth import get_current_admin_user, get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/promotions", tags=["活动专题"])


PROMOTION_STATUS_PENDING = "pending"
PROMOTION_STATUS_ACTIVE = "active"
PROMOTION_STATUS_ENDED = "ended"


def get_promotion_status(start_time: datetime, end_time: datetime) -> str:
    """获取活动状态"""
    now = datetime.utcnow()
    if now < start_time:
        return PROMOTION_STATUS_PENDING
    elif now > end_time:
        return PROMOTION_STATUS_ENDED
    else:
        return PROMOTION_STATUS_ACTIVE


def get_remaining_seconds(start_time: datetime, end_time: datetime) -> Optional[int]:
    """获取剩余秒数（用于倒计时）"""
    now = datetime.utcnow()
    if now < start_time:
        return int((start_time - now).total_seconds())
    elif now < end_time:
        return int((end_time - now).total_seconds())
    return None


def enrich_promotion_response(promotion: Promotion) -> dict:
    """丰富活动响应数据，添加状态和倒计时"""
    result = promotion.__dict__.copy()
    result["status"] = get_promotion_status(promotion.start_time, promotion.end_time)
    result["remaining_seconds"] = get_remaining_seconds(promotion.start_time, promotion.end_time)
    return result


def enrich_promotion_book_response(db: Session, promotion_book: PromotionBook) -> dict:
    """丰富活动图书响应数据"""
    result = promotion_book.__dict__.copy()
    remaining_stock = promotion_book.promotion_stock - promotion_book.sold_stock
    result["remaining_stock"] = max(0, remaining_stock)
    
    book = db.query(Book).filter(Book.id == promotion_book.book_id).first()
    if book:
        result["original_price"] = book.price
        result["book"] = book
    return result


def check_book_conflict(
    db: Session,
    book_id: int,
    start_time: datetime,
    end_time: datetime,
    exclude_promotion_id: Optional[int] = None
) -> bool:
    """检查同一图书是否有活动时间冲突"""
    query = db.query(PromotionBook).join(Promotion).filter(
        PromotionBook.book_id == book_id,
        and_(
            Promotion.start_time < end_time,
            Promotion.end_time > start_time
        )
    )
    
    if exclude_promotion_id:
        query = query.filter(Promotion.id != exclude_promotion_id)
    
    conflict = query.first()
    return conflict is not None


def validate_promotion_books(
    db: Session,
    books_data: list,
    start_time: datetime,
    end_time: datetime,
    exclude_promotion_id: Optional[int] = None
):
    """校验活动图书数据"""
    book_ids = set()
    
    for book_data in books_data:
        book_id = book_data["book_id"]
        
        if book_id in book_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"图书 {book_id} 重复添加"
            )
        book_ids.add(book_id)
        
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"图书 {book_id} 不存在"
            )
        
        if book_data["promotion_price"] >= book.price:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"活动价不能高于或等于原价：{book.title}（活动价: {book_data['promotion_price']}, 原价: {book.price}）"
            )
        
        if book_data["promotion_stock"] > book.stock:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"活动库存不能超过图书总库存：{book.title}（活动库存: {book_data['promotion_stock']}, 总库存: {book.stock}）"
            )
        
        if check_book_conflict(db, book_id, start_time, end_time, exclude_promotion_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"图书活动时间冲突：{book.title} 在该时间段内已有活动"
            )


@router.get("", response_model=PromotionListResponse)
def get_promotions(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="活动状态：pending/active/ended"),
    is_displayed: Optional[bool] = Query(None, description="是否展示"),
    db: Session = Depends(get_db)
):
    """获取活动列表（支持分页和状态筛选）"""
    now = datetime.utcnow()
    query = db.query(Promotion)
    
    if is_displayed is not None:
        query = query.filter(Promotion.is_displayed == is_displayed)
    
    if status:
        if status == PROMOTION_STATUS_PENDING:
            query = query.filter(Promotion.start_time > now)
        elif status == PROMOTION_STATUS_ACTIVE:
            query = query.filter(
                and_(
                    Promotion.start_time <= now,
                    Promotion.end_time >= now
                )
            )
        elif status == PROMOTION_STATUS_ENDED:
            query = query.filter(Promotion.end_time < now)
    
    total = query.count()
    offset = (page - 1) * page_size
    promotions = query.order_by(Promotion.created_at.desc()).offset(offset).limit(page_size).all()
    
    items = []
    for promotion in promotions:
        promo_dict = enrich_promotion_response(promotion)
        promo_books = db.query(PromotionBook).filter(PromotionBook.promotion_id == promotion.id).all()
        promo_dict["books"] = [enrich_promotion_book_response(db, pb) for pb in promo_books]
        items.append(promo_dict)
    
    return PromotionListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=items
    )


@router.get("/{promotion_id}", response_model=PromotionResponse)
def get_promotion(promotion_id: int, db: Session = Depends(get_db)):
    """获取活动详情"""
    promotion = db.query(Promotion).filter(Promotion.id == promotion_id).first()
    if not promotion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="活动不存在"
        )
    
    promo_dict = enrich_promotion_response(promotion)
    promo_books = db.query(PromotionBook).filter(PromotionBook.promotion_id == promotion.id).all()
    promo_dict["books"] = [enrich_promotion_book_response(db, pb) for pb in promo_books]
    
    return promo_dict


@router.post("", response_model=PromotionResponse, status_code=status.HTTP_201_CREATED)
def create_promotion(
    promotion: PromotionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """创建活动（需要管理员权限）"""
    if promotion.end_time <= promotion.start_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="结束时间必须晚于开始时间"
        )
    
    books_data = [book.model_dump() for book in promotion.books]
    validate_promotion_books(db, books_data, promotion.start_time, promotion.end_time)
    
    db_promotion = Promotion(
        name=promotion.name,
        cover_image=promotion.cover_image,
        start_time=promotion.start_time,
        end_time=promotion.end_time,
        description=promotion.description,
        is_displayed=promotion.is_displayed
    )
    db.add(db_promotion)
    db.flush()
    
    for book_data in books_data:
        db_promo_book = PromotionBook(
            promotion_id=db_promotion.id,
            book_id=book_data["book_id"],
            promotion_price=book_data["promotion_price"],
            promotion_stock=book_data["promotion_stock"],
            purchase_limit=book_data.get("purchase_limit")
        )
        db.add(db_promo_book)
    
    db.commit()
    db.refresh(db_promotion)
    
    promo_dict = enrich_promotion_response(db_promotion)
    promo_books = db.query(PromotionBook).filter(PromotionBook.promotion_id == db_promotion.id).all()
    promo_dict["books"] = [enrich_promotion_book_response(db, pb) for pb in promo_books]
    
    logger.info(f"活动创建成功: {promotion.name} (by {current_user.username})")
    return promo_dict


@router.put("/{promotion_id}", response_model=PromotionResponse)
def update_promotion(
    promotion_id: int,
    promotion_update: PromotionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """更新活动（需要管理员权限）"""
    db_promotion = db.query(Promotion).filter(Promotion.id == promotion_id).first()
    if not db_promotion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="活动不存在"
        )
    
    update_data = promotion_update.model_dump(exclude_unset=True)
    
    start_time = update_data.get("start_time", db_promotion.start_time)
    end_time = update_data.get("end_time", db_promotion.end_time)
    
    if "end_time" in update_data and "start_time" in update_data:
        if end_time <= start_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="结束时间必须晚于开始时间"
            )
    
    if "books" in update_data:
        books_data = [book.model_dump() if hasattr(book, 'model_dump') else book for book in update_data["books"]]
        validate_promotion_books(db, books_data, start_time, end_time, promotion_id)
        
        db.query(PromotionBook).filter(PromotionBook.promotion_id == promotion_id).delete()
        
        for book_data in books_data:
            db_promo_book = PromotionBook(
                promotion_id=promotion_id,
                book_id=book_data["book_id"],
                promotion_price=book_data["promotion_price"],
                promotion_stock=book_data["promotion_stock"],
                purchase_limit=book_data.get("purchase_limit")
            )
            db.add(db_promo_book)
        
        del update_data["books"]
    
    for field, value in update_data.items():
        setattr(db_promotion, field, value)
    
    db.commit()
    db.refresh(db_promotion)
    
    promo_dict = enrich_promotion_response(db_promotion)
    promo_books = db.query(PromotionBook).filter(PromotionBook.promotion_id == db_promotion.id).all()
    promo_dict["books"] = [enrich_promotion_book_response(db, pb) for pb in promo_books]
    
    logger.info(f"活动更新成功: {db_promotion.name} (by {current_user.username})")
    return promo_dict


@router.delete("/{promotion_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_promotion(
    promotion_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """删除活动（需要管理员权限）"""
    db_promotion = db.query(Promotion).filter(Promotion.id == promotion_id).first()
    if not db_promotion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="活动不存在"
        )
    
    db.query(PromotionBook).filter(PromotionBook.promotion_id == promotion_id).delete()
    
    promotion_name = db_promotion.name
    db.delete(db_promotion)
    db.commit()
    
    logger.info(f"活动删除成功: {promotion_name} (by {current_user.username})")
    return None


@router.post("/{promotion_id}/deduct-stock", response_model=PromotionBookResponse)
def deduct_promotion_stock(
    promotion_id: int,
    request: PromotionStockDeductRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """扣减活动库存"""
    db_promotion = db.query(Promotion).filter(Promotion.id == promotion_id).first()
    if not db_promotion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="活动不存在"
        )
    
    promo_status = get_promotion_status(db_promotion.start_time, db_promotion.end_time)
    if promo_status != PROMOTION_STATUS_ACTIVE:
        status_text = {
            PROMOTION_STATUS_PENDING: "活动尚未开始",
            PROMOTION_STATUS_ENDED: "活动已结束"
        }
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=status_text.get(promo_status, "活动状态异常")
        )
    
    db_promo_book = db.query(PromotionBook).filter(
        PromotionBook.id == request.promotion_book_id,
        PromotionBook.promotion_id == promotion_id
    ).first()
    
    if not db_promo_book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="活动图书不存在"
        )
    
    remaining_stock = db_promo_book.promotion_stock - db_promo_book.sold_stock
    if remaining_stock < request.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"活动库存不足，剩余 {remaining_stock} 件"
        )
    
    if db_promo_book.purchase_limit and request.quantity > db_promo_book.purchase_limit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"超过限购数量，每单最多购买 {db_promo_book.purchase_limit} 件"
        )
    
    db_promo_book.sold_stock += request.quantity
    db.commit()
    db.refresh(db_promo_book)
    
    logger.info(f"活动库存扣减成功: 活动ID={promotion_id}, 图书ID={db_promo_book.book_id}, 数量={request.quantity} (by {current_user.username})")
    return enrich_promotion_book_response(db, db_promo_book)
