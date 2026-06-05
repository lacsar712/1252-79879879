# -*- coding: utf-8 -*-
"""
库存盘点路由
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime

from database import get_db
from models import StockTaking, StockTakingItem, Book, User
from schemas import (
    StockTakingCreate, StockTakingUpdate, StockTakingResponse, StockTakingListResponse,
    StockTakingBatchEntryRequest
)
from auth import get_current_admin_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/stock-takings", tags=["库存盘点"])


def generate_task_no(db: Session) -> str:
    """生成盘点任务编号"""
    prefix = "PD" + datetime.now().strftime("%Y%m%d")
    last_task = db.query(StockTaking).filter(
        StockTaking.task_no.like(f"{prefix}%")
    ).order_by(StockTaking.task_no.desc()).first()
    
    if last_task:
        seq = int(last_task.task_no[-4:]) + 1
    else:
        seq = 1
    
    return f"{prefix}{seq:04d}"


def enrich_stock_taking(db: Session, task: StockTaking) -> StockTakingResponse:
    """补充盘点任务的关联信息"""
    items = db.query(StockTakingItem).filter(
        StockTakingItem.stock_taking_id == task.id
    ).all()
    
    items_with_books = []
    for item in items:
        book = db.query(Book).filter(Book.id == item.book_id).first()
        item_data = {
            "id": item.id,
            "stock_taking_id": item.stock_taking_id,
            "book_id": item.book_id,
            "expected_stock": item.expected_stock,
            "actual_stock": item.actual_stock,
            "difference": item.difference,
            "book": book,
            "created_at": item.created_at,
            "updated_at": item.updated_at
        }
        items_with_books.append(item_data)
    
    creator = db.query(User).filter(User.id == task.created_by).first()
    confirmer = db.query(User).filter(User.id == task.confirmed_by).first() if task.confirmed_by else None
    
    total_books = len(items)
    completed_count = sum(1 for item in items if item.actual_stock is not None)
    difference_count = sum(1 for item in items if item.difference is not None and item.difference != 0)
    
    return StockTakingResponse(
        id=task.id,
        task_no=task.task_no,
        name=task.name,
        scope=task.scope,
        person_in_charge=task.person_in_charge,
        remark=task.remark,
        status=task.status,
        created_by=task.created_by,
        confirmed_by=task.confirmed_by,
        created_by_name=creator.username if creator else None,
        confirmed_by_name=confirmer.username if confirmer else None,
        items=items_with_books,
        total_books=total_books,
        completed_count=completed_count,
        difference_count=difference_count,
        created_at=task.created_at,
        updated_at=task.updated_at,
        confirmed_at=task.confirmed_at
    )


@router.get("", response_model=StockTakingListResponse)
def get_stock_takings(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="状态筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """获取盘点任务列表"""
    query = db.query(StockTaking)
    
    if status:
        query = query.filter(StockTaking.status == status)
    
    if keyword:
        search_pattern = f"%{keyword}%"
        from sqlalchemy import or_
        query = query.filter(
            or_(
                StockTaking.name.like(search_pattern),
                StockTaking.task_no.like(search_pattern),
                StockTaking.person_in_charge.like(search_pattern)
            )
        )
    
    total = query.count()
    offset = (page - 1) * page_size
    tasks = query.order_by(StockTaking.created_at.desc()).offset(offset).limit(page_size).all()
    
    enriched_tasks = [enrich_stock_taking(db, task) for task in tasks]
    
    return StockTakingListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=enriched_tasks
    )


@router.get("/history", response_model=StockTakingListResponse)
def get_stock_taking_history(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """获取历史盘点记录（仅已确认和已取消的）"""
    query = db.query(StockTaking).filter(
        StockTaking.status.in_(["confirmed", "cancelled"])
    )
    
    if keyword:
        search_pattern = f"%{keyword}%"
        from sqlalchemy import or_
        query = query.filter(
            or_(
                StockTaking.name.like(search_pattern),
                StockTaking.task_no.like(search_pattern)
            )
        )
    
    if start_date:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        query = query.filter(StockTaking.confirmed_at >= start)
    
    if end_date:
        end = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
        query = query.filter(StockTaking.confirmed_at <= end)
    
    total = query.count()
    offset = (page - 1) * page_size
    tasks = query.order_by(StockTaking.confirmed_at.desc()).offset(offset).limit(page_size).all()
    
    enriched_tasks = [enrich_stock_taking(db, task) for task in tasks]
    
    return StockTakingListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=enriched_tasks
    )


@router.get("/{task_id}", response_model=StockTakingResponse)
def get_stock_taking(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """获取盘点任务详情"""
    task = db.query(StockTaking).filter(StockTaking.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="盘点任务不存在"
        )
    
    return enrich_stock_taking(db, task)


@router.post("", response_model=StockTakingResponse, status_code=status.HTTP_201_CREATED)
def create_stock_taking(
    task_data: StockTakingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """创建盘点任务"""
    task_no = generate_task_no(db)
    
    task = StockTaking(
        task_no=task_no,
        name=task_data.name,
        scope=task_data.scope,
        person_in_charge=task_data.person_in_charge,
        remark=task_data.remark,
        status="draft",
        created_by=current_user.id
    )
    db.add(task)
    db.flush()
    
    for book_id in task_data.book_ids:
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"图书 ID {book_id} 不存在"
            )
        
        item = StockTakingItem(
            stock_taking_id=task.id,
            book_id=book_id,
            expected_stock=book.stock,
            actual_stock=None,
            difference=None
        )
        db.add(item)
    
    db.commit()
    db.refresh(task)
    
    logger.info(f"盘点任务创建成功: {task_no} (by {current_user.username})")
    return enrich_stock_taking(db, task)


@router.put("/{task_id}", response_model=StockTakingResponse)
def update_stock_taking(
    task_id: int,
    task_data: StockTakingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """更新盘点任务（仅草稿状态）"""
    task = db.query(StockTaking).filter(StockTaking.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="盘点任务不存在"
        )
    
    if task.status != "draft":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="仅草稿状态的盘点任务可修改"
        )
    
    if task_data.name is not None:
        task.name = task_data.name
    if task_data.scope is not None:
        task.scope = task_data.scope
    if task_data.person_in_charge is not None:
        task.person_in_charge = task_data.person_in_charge
    if task_data.remark is not None:
        task.remark = task_data.remark
    
    if task_data.book_ids is not None:
        db.query(StockTakingItem).filter(
            StockTakingItem.stock_taking_id == task.id
        ).delete()
        
        for book_id in task_data.book_ids:
            book = db.query(Book).filter(Book.id == book_id).first()
            if not book:
                db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"图书 ID {book_id} 不存在"
                )
            
            item = StockTakingItem(
                stock_taking_id=task.id,
                book_id=book_id,
                expected_stock=book.stock,
                actual_stock=None,
                difference=None
            )
            db.add(item)
    
    db.commit()
    db.refresh(task)
    
    logger.info(f"盘点任务更新成功: {task.task_no} (by {current_user.username})")
    return enrich_stock_taking(db, task)


@router.post("/{task_id}/start", response_model=StockTakingResponse)
def start_stock_taking(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """开始盘点"""
    task = db.query(StockTaking).filter(StockTaking.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="盘点任务不存在"
        )
    
    if task.status != "draft":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="仅草稿状态的盘点任务可开始"
        )
    
    task.status = "in_progress"
    db.commit()
    db.refresh(task)
    
    logger.info(f"盘点任务开始: {task.task_no} (by {current_user.username})")
    return enrich_stock_taking(db, task)


@router.post("/{task_id}/entry", response_model=StockTakingResponse)
def batch_entry_stock(
    task_id: int,
    entry_data: StockTakingBatchEntryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """批量录入实际库存"""
    task = db.query(StockTaking).filter(StockTaking.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="盘点任务不存在"
        )
    
    if task.status not in ["in_progress", "draft"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="仅草稿或盘点中的任务可录入数据"
        )
    
    items = db.query(StockTakingItem).filter(
        StockTakingItem.stock_taking_id == task.id
    ).all()
    item_map = {item.id: item for item in items}
    
    for entry in entry_data.items:
        item = item_map.get(entry.item_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"盘点明细 ID {entry.item_id} 不存在"
            )
        
        item.actual_stock = entry.actual_stock
        item.difference = entry.actual_stock - item.expected_stock
    
    db.commit()
    db.refresh(task)
    
    logger.info(f"盘点数据录入: {task.task_no} (by {current_user.username})")
    return enrich_stock_taking(db, task)


@router.post("/{task_id}/confirm", response_model=StockTakingResponse)
def confirm_stock_taking(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """确认盘点（批量修正库存，不可重复确认）"""
    task = db.query(StockTaking).filter(StockTaking.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="盘点任务不存在"
        )
    
    if task.status == "confirmed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该盘点任务已确认，不可重复确认"
        )
    
    if task.status != "in_progress":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="仅盘点中的任务可确认"
        )
    
    items = db.query(StockTakingItem).filter(
        StockTakingItem.stock_taking_id == task.id
    ).all()
    
    uncompleted = [item for item in items if item.actual_stock is None]
    if uncompleted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"还有 {len(uncompleted)} 本图书未完成盘点，请全部录入后再确认"
        )
    
    for item in items:
        if item.difference != 0:
            book = db.query(Book).filter(Book.id == item.book_id).first()
            if book:
                book.stock = item.actual_stock
    
    task.status = "confirmed"
    task.confirmed_by = current_user.id
    task.confirmed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(task)
    
    logger.info(f"盘点任务确认完成: {task.task_no} (by {current_user.username})")
    return enrich_stock_taking(db, task)


@router.post("/{task_id}/cancel", response_model=StockTakingResponse)
def cancel_stock_taking(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """取消盘点"""
    task = db.query(StockTaking).filter(StockTaking.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="盘点任务不存在"
        )
    
    if task.status == "confirmed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="已确认的盘点任务不可取消"
        )
    
    if task.status == "cancelled":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该盘点任务已取消"
        )
    
    task.status = "cancelled"
    task.confirmed_by = current_user.id
    task.confirmed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(task)
    
    logger.info(f"盘点任务取消: {task.task_no} (by {current_user.username})")
    return enrich_stock_taking(db, task)


@router.get("/scopes/list", response_model=list)
def get_scopes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """获取盘点范围选项"""
    return [
        {"value": "all", "label": "全库盘点"},
        {"value": "category", "label": "按分类盘点"},
        {"value": "low_stock", "label": "低库存盘点"},
        {"value": "custom", "label": "自定义范围"}
    ]
