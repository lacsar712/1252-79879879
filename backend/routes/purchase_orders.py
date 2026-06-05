# -*- coding: utf-8 -*-
"""
采购入库路由
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime

from database import get_db
from models import (
    Supplier, PurchaseOrder, PurchaseOrderItem, 
    Book, User, StockChange
)
from schemas import (
    SupplierCreate, SupplierUpdate, SupplierResponse, SupplierListResponse,
    PurchaseOrderCreate, PurchaseOrderUpdate, PurchaseOrderResponse,
    PurchaseOrderListResponse, PurchaseOrderItemCreate,
    PurchaseOrderStatusOption
)
from auth import get_current_admin_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/purchase-orders", tags=["采购入库"])


def generate_order_no(db: Session) -> str:
    """生成采购单编号"""
    prefix = "PO" + datetime.now().strftime("%Y%m%d")
    last_order = db.query(PurchaseOrder).filter(
        PurchaseOrder.order_no.like(f"{prefix}%")
    ).order_by(PurchaseOrder.order_no.desc()).first()
    
    if last_order:
        seq = int(last_order.order_no[-4:]) + 1
    else:
        seq = 1
    
    return f"{prefix}{seq:04d}"


def calculate_total_amount(items: list) -> float:
    """计算采购单总金额"""
    return sum(item.quantity * item.unit_price for item in items)


def enrich_purchase_order(db: Session, order: PurchaseOrder) -> PurchaseOrderResponse:
    """补充采购单的关联信息"""
    items = db.query(PurchaseOrderItem).filter(
        PurchaseOrderItem.purchase_order_id == order.id
    ).all()
    
    items_with_books = []
    for item in items:
        book = db.query(Book).filter(Book.id == item.book_id).first()
        subtotal = item.quantity * item.unit_price
        item_data = {
            "id": item.id,
            "purchase_order_id": item.purchase_order_id,
            "book_id": item.book_id,
            "quantity": item.quantity,
            "unit_price": item.unit_price,
            "expected_arrival_time": item.expected_arrival_time,
            "received_quantity": item.received_quantity,
            "book": book,
            "subtotal": subtotal,
            "created_at": item.created_at,
            "updated_at": item.updated_at
        }
        items_with_books.append(item_data)
    
    supplier = db.query(Supplier).filter(Supplier.id == order.supplier_id).first()
    creator = db.query(User).filter(User.id == order.created_by).first()
    confirmer = db.query(User).filter(User.id == order.confirmed_by).first() if order.confirmed_by else None
    
    stock_impact = None
    if order.status == "received":
        stock_impact = []
        for item in items:
            book = db.query(Book).filter(Book.id == item.book_id).first()
            stock_impact.append({
                "book_id": item.book_id,
                "book_title": book.title if book else "未知图书",
                "added_quantity": item.quantity,
                "unit_cost": item.unit_price,
                "total_cost": item.quantity * item.unit_price
            })
    
    return PurchaseOrderResponse(
        id=order.id,
        order_no=order.order_no,
        supplier_id=order.supplier_id,
        purchase_date=order.purchase_date,
        total_amount=order.total_amount,
        remark=order.remark,
        status=order.status,
        created_by=order.created_by,
        confirmed_by=order.confirmed_by,
        created_by_name=creator.username if creator else None,
        confirmed_by_name=confirmer.username if confirmer else None,
        supplier=supplier,
        items=items_with_books,
        stock_impact=stock_impact,
        created_at=order.created_at,
        updated_at=order.updated_at,
        confirmed_at=order.confirmed_at
    )


# ==================== 供应商管理接口 ====================

@router.get("/suppliers", response_model=SupplierListResponse)
def get_suppliers(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """获取供应商列表"""
    query = db.query(Supplier)
    
    if keyword:
        search_pattern = f"%{keyword}%"
        from sqlalchemy import or_
        query = query.filter(
            or_(
                Supplier.name.like(search_pattern),
                Supplier.contact_person.like(search_pattern),
                Supplier.phone.like(search_pattern)
            )
        )
    
    total = query.count()
    offset = (page - 1) * page_size
    suppliers = query.order_by(Supplier.created_at.desc()).offset(offset).limit(page_size).all()
    
    return SupplierListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=suppliers
    )


@router.get("/suppliers/all", response_model=list)
def get_all_suppliers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """获取所有供应商（用于下拉选择）"""
    suppliers = db.query(Supplier).order_by(Supplier.name.asc()).all()
    return [{"id": s.id, "name": s.name, "contact_person": s.contact_person, "phone": s.phone} for s in suppliers]


@router.get("/suppliers/{supplier_id}", response_model=SupplierResponse)
def get_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """获取供应商详情"""
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="供应商不存在"
        )
    return supplier


@router.post("/suppliers", response_model=SupplierResponse, status_code=status.HTTP_201_CREATED)
def create_supplier(
    supplier_data: SupplierCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """创建供应商"""
    existing = db.query(Supplier).filter(Supplier.name == supplier_data.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="供应商名称已存在"
        )
    
    supplier = Supplier(
        name=supplier_data.name,
        contact_person=supplier_data.contact_person,
        phone=supplier_data.phone,
        email=supplier_data.email,
        address=supplier_data.address,
        remark=supplier_data.remark
    )
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    
    logger.info(f"供应商创建成功: {supplier.name} (by {current_user.username})")
    return supplier


@router.put("/suppliers/{supplier_id}", response_model=SupplierResponse)
def update_supplier(
    supplier_id: int,
    supplier_data: SupplierUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """更新供应商"""
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="供应商不存在"
        )
    
    if supplier_data.name is not None and supplier_data.name != supplier.name:
        existing = db.query(Supplier).filter(Supplier.name == supplier_data.name).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="供应商名称已存在"
            )
        supplier.name = supplier_data.name
    
    if supplier_data.contact_person is not None:
        supplier.contact_person = supplier_data.contact_person
    if supplier_data.phone is not None:
        supplier.phone = supplier_data.phone
    if supplier_data.email is not None:
        supplier.email = supplier_data.email
    if supplier_data.address is not None:
        supplier.address = supplier_data.address
    if supplier_data.remark is not None:
        supplier.remark = supplier_data.remark
    
    db.commit()
    db.refresh(supplier)
    
    logger.info(f"供应商更新成功: {supplier.name} (by {current_user.username})")
    return supplier


@router.delete("/suppliers/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """删除供应商"""
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="供应商不存在"
        )
    
    has_orders = db.query(PurchaseOrder).filter(PurchaseOrder.supplier_id == supplier_id).first()
    if has_orders:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该供应商有关联采购单，无法删除"
        )
    
    db.delete(supplier)
    db.commit()
    
    logger.info(f"供应商删除成功: {supplier.name} (by {current_user.username})")


# ==================== 采购单管理接口 ====================

@router.get("", response_model=PurchaseOrderListResponse)
def get_purchase_orders(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="状态筛选"),
    supplier_id: Optional[int] = Query(None, description="供应商筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """获取采购单列表"""
    query = db.query(PurchaseOrder)
    
    if status:
        query = query.filter(PurchaseOrder.status == status)
    
    if supplier_id:
        query = query.filter(PurchaseOrder.supplier_id == supplier_id)
    
    if keyword:
        search_pattern = f"%{keyword}%"
        from sqlalchemy import or_
        query = query.filter(
            or_(
                PurchaseOrder.order_no.like(search_pattern),
                PurchaseOrder.remark.like(search_pattern)
            )
        )
    
    if start_date:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        query = query.filter(PurchaseOrder.purchase_date >= start)
    
    if end_date:
        end = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
        query = query.filter(PurchaseOrder.purchase_date <= end)
    
    total = query.count()
    offset = (page - 1) * page_size
    orders = query.order_by(PurchaseOrder.created_at.desc()).offset(offset).limit(page_size).all()
    
    enriched_orders = [enrich_purchase_order(db, order) for order in orders]
    
    return PurchaseOrderListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=enriched_orders
    )


@router.get("/{order_id}", response_model=PurchaseOrderResponse)
def get_purchase_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """获取采购单详情"""
    order = db.query(PurchaseOrder).filter(PurchaseOrder.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="采购单不存在"
        )
    
    return enrich_purchase_order(db, order)


@router.post("", response_model=PurchaseOrderResponse, status_code=status.HTTP_201_CREATED)
def create_purchase_order(
    order_data: PurchaseOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """创建采购单（草稿状态）"""
    supplier = db.query(Supplier).filter(Supplier.id == order_data.supplier_id).first()
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="供应商不存在"
        )
    
    order_no = generate_order_no(db)
    total_amount = calculate_total_amount(order_data.items)
    
    order = PurchaseOrder(
        order_no=order_no,
        supplier_id=order_data.supplier_id,
        purchase_date=order_data.purchase_date,
        total_amount=total_amount,
        remark=order_data.remark,
        status="draft",
        created_by=current_user.id
    )
    db.add(order)
    db.flush()
    
    for item_data in order_data.items:
        book = db.query(Book).filter(Book.id == item_data.book_id).first()
        if not book:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"图书 ID {item_data.book_id} 不存在"
            )
        
        item = PurchaseOrderItem(
            purchase_order_id=order.id,
            book_id=item_data.book_id,
            quantity=item_data.quantity,
            unit_price=item_data.unit_price,
            expected_arrival_time=item_data.expected_arrival_time,
            received_quantity=0
        )
        db.add(item)
    
    db.commit()
    db.refresh(order)
    
    logger.info(f"采购单创建成功: {order_no} (by {current_user.username})")
    return enrich_purchase_order(db, order)


@router.put("/{order_id}", response_model=PurchaseOrderResponse)
def update_purchase_order(
    order_id: int,
    order_data: PurchaseOrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """更新采购单（仅草稿和待入库状态）"""
    order = db.query(PurchaseOrder).filter(PurchaseOrder.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="采购单不存在"
        )
    
    if order.status not in ["draft", "pending"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="仅草稿或待入库状态的采购单可修改"
        )
    
    if order_data.supplier_id is not None:
        supplier = db.query(Supplier).filter(Supplier.id == order_data.supplier_id).first()
        if not supplier:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="供应商不存在"
            )
        order.supplier_id = order_data.supplier_id
    
    if order_data.purchase_date is not None:
        order.purchase_date = order_data.purchase_date
    
    if order_data.remark is not None:
        order.remark = order_data.remark
    
    if order_data.items is not None:
        db.query(PurchaseOrderItem).filter(
            PurchaseOrderItem.purchase_order_id == order.id
        ).delete()
        
        total_amount = calculate_total_amount(order_data.items)
        order.total_amount = total_amount
        
        for item_data in order_data.items:
            book = db.query(Book).filter(Book.id == item_data.book_id).first()
            if not book:
                db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"图书 ID {item_data.book_id} 不存在"
                )
            
            item = PurchaseOrderItem(
                purchase_order_id=order.id,
                book_id=item_data.book_id,
                quantity=item_data.quantity,
                unit_price=item_data.unit_price,
                expected_arrival_time=item_data.expected_arrival_time,
                received_quantity=0
            )
            db.add(item)
    
    db.commit()
    db.refresh(order)
    
    logger.info(f"采购单更新成功: {order.order_no} (by {current_user.username})")
    return enrich_purchase_order(db, order)


@router.post("/{order_id}/submit", response_model=PurchaseOrderResponse)
def submit_purchase_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """提交采购单（草稿 → 待入库）"""
    order = db.query(PurchaseOrder).filter(PurchaseOrder.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="采购单不存在"
        )
    
    if order.status != "draft":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="仅草稿状态的采购单可提交"
        )
    
    items = db.query(PurchaseOrderItem).filter(
        PurchaseOrderItem.purchase_order_id == order.id
    ).all()
    
    if not items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="采购单没有明细项，无法提交"
        )
    
    order.status = "pending"
    db.commit()
    db.refresh(order)
    
    logger.info(f"采购单提交成功: {order.order_no} (by {current_user.username})")
    return enrich_purchase_order(db, order)


@router.post("/{order_id}/confirm", response_model=PurchaseOrderResponse)
def confirm_purchase_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """确认入库（待入库 → 已入库），增加库存、记录成本并生成库存变动记录"""
    order = db.query(PurchaseOrder).filter(PurchaseOrder.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="采购单不存在"
        )
    
    if order.status == "received":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该采购单已确认入库，不可重复确认"
        )
    
    if order.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="仅待入库状态的采购单可确认入库"
        )
    
    items = db.query(PurchaseOrderItem).filter(
        PurchaseOrderItem.purchase_order_id == order.id
    ).all()
    
    if not items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="采购单没有明细项，无法确认入库"
        )
    
    for item in items:
        book = db.query(Book).filter(Book.id == item.book_id).first()
        if not book:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"图书 ID {item.book_id} 不存在"
            )
        
        before_stock = book.stock
        after_stock = book.stock + item.quantity
        
        stock_change = StockChange(
            book_id=item.book_id,
            change_type="purchase_in",
            change_quantity=item.quantity,
            before_stock=before_stock,
            after_stock=after_stock,
            related_order_id=order.id,
            related_order_no=order.order_no,
            related_order_type="purchase_order",
            unit_cost=item.unit_price,
            total_cost=item.quantity * item.unit_price,
            remark=f"采购单 {order.order_no} 入库",
            created_by=current_user.id
        )
        db.add(stock_change)
        
        book.stock = after_stock
        item.received_quantity = item.quantity
    
    order.status = "received"
    order.confirmed_by = current_user.id
    order.confirmed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(order)
    
    logger.info(f"采购单确认入库成功: {order.order_no} (by {current_user.username})")
    return enrich_purchase_order(db, order)


@router.post("/{order_id}/cancel", response_model=PurchaseOrderResponse)
def cancel_purchase_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """取消采购单"""
    order = db.query(PurchaseOrder).filter(PurchaseOrder.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="采购单不存在"
        )
    
    if order.status == "received":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="已入库的采购单不可取消"
        )
    
    if order.status == "cancelled":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该采购单已取消"
        )
    
    order.status = "cancelled"
    order.confirmed_by = current_user.id
    order.confirmed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(order)
    
    logger.info(f"采购单取消: {order.order_no} (by {current_user.username})")
    return enrich_purchase_order(db, order)


@router.get("/statuses/list", response_model=list)
def get_purchase_order_statuses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """获取采购单状态选项"""
    return [
        PurchaseOrderStatusOption(value="draft", label="草稿", type="info"),
        PurchaseOrderStatusOption(value="pending", label="待入库", type="warning"),
        PurchaseOrderStatusOption(value="received", label="已入库", type="success"),
        PurchaseOrderStatusOption(value="cancelled", label="已取消", type="danger")
    ]


@router.get("/{order_id}/stock-changes", response_model=list)
def get_purchase_order_stock_changes(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """获取采购单关联的库存变动记录"""
    order = db.query(PurchaseOrder).filter(PurchaseOrder.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="采购单不存在"
        )
    
    changes = db.query(StockChange).filter(
        StockChange.related_order_id == order_id,
        StockChange.related_order_type == "purchase_order"
    ).all()
    
    result = []
    for change in changes:
        book = db.query(Book).filter(Book.id == change.book_id).first()
        result.append({
            "id": change.id,
            "book_id": change.book_id,
            "book_title": book.title if book else "未知图书",
            "change_type": change.change_type,
            "change_quantity": change.change_quantity,
            "before_stock": change.before_stock,
            "after_stock": change.after_stock,
            "unit_cost": change.unit_cost,
            "total_cost": change.total_cost,
            "remark": change.remark,
            "created_at": change.created_at
        })
    
    return result
