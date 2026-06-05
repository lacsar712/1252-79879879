# -*- coding: utf-8 -*-
"""
API Key 管理路由
"""
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from datetime import datetime

from database import get_db
from models import APIKey, APIKeyCallLog, User
from schemas import (
    APIKeyCreate, APIKeyUpdate, APIKeyResponse, APIKeyCreateResponse,
    APIKeyRotateResponse, APIKeyListResponse,
    APIKeyCallLogResponse, APIKeyCallLogListResponse,
    APIKeyAccessScopeOption, APIKeyRatePeriodOption, APIKeyStatusOption
)
from auth import get_current_admin_user
from api_key_auth import (
    generate_api_key, generate_api_secret, hash_secret,
    get_risk_status, is_expired
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/api-keys", tags=["API Key 管理"])


def enrich_api_key_response(db: Session, api_key: APIKey, show_secret: bool = False) -> APIKeyResponse:
    """丰富 API Key 响应数据"""
    creator = db.query(User).filter(User.id == api_key.created_by).first()
    risk_status = get_risk_status(db, api_key)

    return APIKeyResponse(
        id=api_key.id,
        name=api_key.name,
        remark=api_key.remark,
        api_key=api_key.api_key,
        api_secret=api_key.api_secret if show_secret else None,
        is_enabled=api_key.is_enabled,
        expires_at=api_key.expires_at,
        access_scope=api_key.access_scope,
        rate_limit=api_key.rate_limit,
        rate_period=api_key.rate_period,
        allowed_ips=api_key.allowed_ips,
        created_by=api_key.created_by,
        created_by_name=creator.username if creator else None,
        last_used_at=api_key.last_used_at,
        call_count=api_key.call_count,
        risk_status=risk_status,
        created_at=api_key.created_at,
        updated_at=api_key.updated_at
    )


@router.get("", response_model=APIKeyListResponse)
def get_api_keys(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词（名称或 Key）"),
    is_enabled: Optional[bool] = Query(None, description="启用状态"),
    risk_status: Optional[str] = Query(None, description="风险状态"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """获取 API Key 列表（需要管理员权限）"""
    query = db.query(APIKey)

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                APIKey.name.like(search_pattern),
                APIKey.api_key.like(search_pattern),
                APIKey.remark.like(search_pattern)
            )
        )

    if is_enabled is not None:
        query = query.filter(APIKey.is_enabled == is_enabled)

    now = datetime.utcnow()
    if risk_status == "expired":
        query = query.filter(and_(APIKey.expires_at.isnot(None), APIKey.expires_at < now))
    elif risk_status == "expiring_soon":
        from datetime import timedelta
        seven_days_later = now + timedelta(days=7)
        query = query.filter(and_(APIKey.expires_at.isnot(None), APIKey.expires_at > now, APIKey.expires_at <= seven_days_later))
    elif risk_status == "disabled":
        query = query.filter(APIKey.is_enabled == False)
    elif risk_status == "inactive":
        query = query.filter(APIKey.last_used_at.is_(None))

    total = query.count()
    offset = (page - 1) * page_size
    api_keys = query.order_by(APIKey.created_at.desc()).offset(offset).limit(page_size).all()

    items = [enrich_api_key_response(db, ak) for ak in api_keys]

    return APIKeyListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=items
    )


@router.get("/{api_key_id}", response_model=APIKeyResponse)
def get_api_key(
    api_key_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """获取 API Key 详情（需要管理员权限）"""
    api_key = db.query(APIKey).filter(APIKey.id == api_key_id).first()
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API Key 不存在"
        )
    return enrich_api_key_response(db, api_key)


@router.post("", response_model=APIKeyCreateResponse, status_code=status.HTTP_201_CREATED)
def create_api_key(
    api_key_data: APIKeyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """创建 API Key（需要管理员权限，密钥只展示一次）"""
    api_key_str = generate_api_key()
    api_secret_str = generate_api_secret()
    hashed_secret = hash_secret(api_secret_str)

    db_api_key = APIKey(
        name=api_key_data.name,
        remark=api_key_data.remark,
        api_key=api_key_str,
        api_secret=hashed_secret,
        is_enabled=api_key_data.is_enabled,
        expires_at=api_key_data.expires_at,
        access_scope=api_key_data.access_scope,
        rate_limit=api_key_data.rate_limit,
        rate_period=api_key_data.rate_period,
        allowed_ips=api_key_data.allowed_ips,
        created_by=current_user.id
    )

    db.add(db_api_key)
    db.commit()
    db.refresh(db_api_key)

    logger.info(f"API Key 创建成功: {api_key_data.name} (by {current_user.username})")

    return APIKeyCreateResponse(
        id=db_api_key.id,
        api_key=api_key_str,
        api_secret=api_secret_str,
        message="API Key 创建成功，请妥善保存密钥，只显示一次"
    )


@router.put("/{api_key_id}", response_model=APIKeyResponse)
def update_api_key(
    api_key_id: int,
    api_key_update: APIKeyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """更新 API Key（需要管理员权限）"""
    api_key = db.query(APIKey).filter(APIKey.id == api_key_id).first()
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API Key 不存在"
        )

    update_data = api_key_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(api_key, field, value)

    db.commit()
    db.refresh(api_key)

    logger.info(f"API Key 更新成功: {api_key.name} (by {current_user.username})")
    return enrich_api_key_response(db, api_key)


@router.delete("/{api_key_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_api_key(
    api_key_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """删除 API Key（需要管理员权限）"""
    api_key = db.query(APIKey).filter(APIKey.id == api_key_id).first()
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API Key 不存在"
        )

    key_name = api_key.name
    db.query(APIKeyCallLog).filter(APIKeyCallLog.api_key_id == api_key_id).delete()
    db.delete(api_key)
    db.commit()

    logger.info(f"API Key 删除成功: {key_name} (by {current_user.username})")
    return None


@router.post("/{api_key_id}/toggle", response_model=APIKeyResponse)
def toggle_api_key(
    api_key_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """启用/禁用 API Key（需要管理员权限）"""
    api_key = db.query(APIKey).filter(APIKey.id == api_key_id).first()
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API Key 不存在"
        )

    api_key.is_enabled = not api_key.is_enabled
    db.commit()
    db.refresh(api_key)

    action = "启用" if api_key.is_enabled else "禁用"
    logger.info(f"API Key {action}成功: {api_key.name} (by {current_user.username})")
    return enrich_api_key_response(db, api_key)


@router.post("/{api_key_id}/rotate", response_model=APIKeyRotateResponse)
def rotate_api_key(
    api_key_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """轮换 API Key（需要管理员权限，新密钥只展示一次）"""
    api_key = db.query(APIKey).filter(APIKey.id == api_key_id).first()
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API Key 不存在"
        )

    new_api_secret = generate_api_secret()
    api_key.api_secret = hash_secret(new_api_secret)
    api_key.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(api_key)

    logger.info(f"API Key 轮换成功: {api_key.name} (by {current_user.username})")

    return APIKeyRotateResponse(
        id=api_key.id,
        api_key=api_key.api_key,
        api_secret=new_api_secret,
        message="API Key 轮换成功，请妥善保存新密钥，只显示一次"
    )


@router.get("/{api_key_id}/logs", response_model=APIKeyCallLogListResponse)
def get_api_key_logs(
    api_key_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="状态筛选: success/failed"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """获取 API Key 调用日志（需要管理员权限）"""
    api_key = db.query(APIKey).filter(APIKey.id == api_key_id).first()
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API Key 不存在"
        )

    query = db.query(APIKeyCallLog).filter(APIKeyCallLog.api_key_id == api_key_id)

    if status == "success":
        query = query.filter(APIKeyCallLog.status_code < 400)
    elif status == "failed":
        query = query.filter(APIKeyCallLog.status_code >= 400)

    if start_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(APIKeyCallLog.created_at >= start_dt)
        except ValueError:
            pass

    if end_date:
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            end_dt = end_dt.replace(hour=23, minute=59, second=59)
            query = query.filter(APIKeyCallLog.created_at <= end_dt)
        except ValueError:
            pass

    total = query.count()
    offset = (page - 1) * page_size
    logs = query.order_by(APIKeyCallLog.created_at.desc()).offset(offset).limit(page_size).all()

    return APIKeyCallLogListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=logs
    )


@router.get("/scopes/list", response_model=List[APIKeyAccessScopeOption])
def get_access_scopes(
    current_user: User = Depends(get_current_admin_user)
):
    """获取访问范围选项列表"""
    return [
        {"value": "books:read", "label": "只读图书查询"},
        {"value": "books:full", "label": "图书完整访问"},
        {"value": "*", "label": "全部权限"}
    ]


@router.get("/rate-periods/list", response_model=List[APIKeyRatePeriodOption])
def get_rate_periods(
    current_user: User = Depends(get_current_admin_user)
):
    """获取频率周期选项列表"""
    return [
        {"value": "second", "label": "每秒"},
        {"value": "minute", "label": "每分钟"},
        {"value": "hour", "label": "每小时"},
        {"value": "day", "label": "每天"}
    ]


@router.get("/statuses/list", response_model=List[APIKeyStatusOption])
def get_api_key_statuses(
    current_user: User = Depends(get_current_admin_user)
):
    """获取 API Key 状态选项列表"""
    return [
        {"value": "all", "label": "全部", "type": ""},
        {"value": "enabled", "label": "已启用", "type": "success"},
        {"value": "disabled", "label": "已禁用", "type": "danger"},
        {"value": "expired", "label": "已过期", "type": "warning"},
        {"value": "expiring_soon", "label": "即将过期", "type": "warning"},
        {"value": "inactive", "label": "未使用", "type": "info"}
    ]
