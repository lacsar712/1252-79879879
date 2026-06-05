# -*- coding: utf-8 -*-
"""
用户收货地址路由
"""
import logging
import re
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import User, UserAddress
from schemas import (
    UserAddressCreate,
    UserAddressUpdate,
    UserAddressResponse,
    UserAddressListResponse,
    UserAddressDeleteResponse,
    UserAddressReassignDefaultRequest
)
from auth import get_current_active_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/addresses", tags=["用户地址"])


PHONE_PATTERN = re.compile(r'^1[3-9]\d{9}$')


def validate_phone(phone: str) -> bool:
    """验证手机号格式"""
    return bool(PHONE_PATTERN.match(phone))


def get_full_address(address: UserAddress) -> str:
    """获取完整地址字符串"""
    return f"{address.province}{address.city}{address.district}{address.detail_address}"


def reset_other_defaults(db: Session, user_id: int, exclude_id: int = None):
    """将用户其他地址的默认状态重置为False"""
    query = db.query(UserAddress).filter(
        UserAddress.user_id == user_id,
        UserAddress.is_default == True
    )
    if exclude_id:
        query = query.filter(UserAddress.id != exclude_id)
    query.update({UserAddress.is_default: False})


@router.get("", response_model=UserAddressListResponse)
def get_my_addresses(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取当前用户的所有地址列表"""
    addresses = db.query(UserAddress).filter(
        UserAddress.user_id == current_user.id
    ).order_by(
        UserAddress.is_default.desc(),
        UserAddress.updated_at.desc()
    ).all()

    result = []
    for addr in addresses:
        addr_response = UserAddressResponse.model_validate(addr)
        addr_response.full_address = get_full_address(addr)
        result.append(addr_response)

    return UserAddressListResponse(
        total=len(result),
        items=result
    )


@router.get("/default", response_model=UserAddressResponse)
def get_default_address(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取当前用户的默认地址"""
    default_address = db.query(UserAddress).filter(
        UserAddress.user_id == current_user.id,
        UserAddress.is_default == True
    ).first()

    if not default_address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到默认地址"
        )

    result = UserAddressResponse.model_validate(default_address)
    result.full_address = get_full_address(default_address)
    return result


@router.get("/{address_id}", response_model=UserAddressResponse)
def get_address(
    address_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取指定地址详情"""
    address = db.query(UserAddress).filter(
        UserAddress.id == address_id,
        UserAddress.user_id == current_user.id
    ).first()

    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="地址不存在或无权限访问"
        )

    result = UserAddressResponse.model_validate(address)
    result.full_address = get_full_address(address)
    return result


@router.post("", response_model=UserAddressResponse, status_code=status.HTTP_201_CREATED)
def create_address(
    address_data: UserAddressCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """创建新地址"""
    if not validate_phone(address_data.phone):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="手机号格式不正确，请输入有效的11位手机号"
        )

    if address_data.is_default:
        reset_other_defaults(db, current_user.id)

    new_address = UserAddress(
        user_id=current_user.id,
        contact_name=address_data.contact_name,
        phone=address_data.phone,
        province=address_data.province,
        city=address_data.city,
        district=address_data.district,
        detail_address=address_data.detail_address,
        address_tag=address_data.address_tag,
        is_default=address_data.is_default
    )

    db.add(new_address)
    db.commit()
    db.refresh(new_address)

    logger.info(f"用户 {current_user.username} 创建了新地址 ID: {new_address.id}")

    result = UserAddressResponse.model_validate(new_address)
    result.full_address = get_full_address(new_address)
    return result


@router.put("/{address_id}", response_model=UserAddressResponse)
def update_address(
    address_id: int,
    address_data: UserAddressUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新地址"""
    address = db.query(UserAddress).filter(
        UserAddress.id == address_id,
        UserAddress.user_id == current_user.id
    ).first()

    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="地址不存在或无权限访问"
        )

    if address_data.phone is not None and not validate_phone(address_data.phone):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="手机号格式不正确，请输入有效的11位手机号"
        )

    if address_data.is_default:
        reset_other_defaults(db, current_user.id, exclude_id=address_id)

    if address_data.contact_name is not None:
        address.contact_name = address_data.contact_name
    if address_data.phone is not None:
        address.phone = address_data.phone
    if address_data.province is not None:
        address.province = address_data.province
    if address_data.city is not None:
        address.city = address_data.city
    if address_data.district is not None:
        address.district = address_data.district
    if address_data.detail_address is not None:
        address.detail_address = address_data.detail_address
    if address_data.address_tag is not None:
        address.address_tag = address_data.address_tag
    if address_data.is_default is not None:
        address.is_default = address_data.is_default

    db.commit()
    db.refresh(address)

    logger.info(f"用户 {current_user.username} 更新了地址 ID: {address_id}")

    result = UserAddressResponse.model_validate(address)
    result.full_address = get_full_address(address)
    return result


@router.patch("/{address_id}/set-default", response_model=UserAddressResponse)
def set_default_address(
    address_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """设置指定地址为默认地址"""
    address = db.query(UserAddress).filter(
        UserAddress.id == address_id,
        UserAddress.user_id == current_user.id
    ).first()

    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="地址不存在或无权限访问"
        )

    reset_other_defaults(db, current_user.id, exclude_id=address_id)
    address.is_default = True
    db.commit()
    db.refresh(address)

    logger.info(f"用户 {current_user.username} 将地址 ID: {address_id} 设为默认")

    result = UserAddressResponse.model_validate(address)
    result.full_address = get_full_address(address)
    return result


@router.delete("/{address_id}", response_model=UserAddressDeleteResponse)
def delete_address(
    address_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """删除地址"""
    address = db.query(UserAddress).filter(
        UserAddress.id == address_id,
        UserAddress.user_id == current_user.id
    ).first()

    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="地址不存在或无权限访问"
        )

    was_default = address.is_default

    db.delete(address)
    db.commit()

    logger.info(f"用户 {current_user.username} 删除了地址 ID: {address_id}")

    remaining_addresses = db.query(UserAddress).filter(
        UserAddress.user_id == current_user.id
    ).all()

    need_reassign = was_default and len(remaining_addresses) > 0

    remaining_list = []
    if need_reassign:
        for addr in remaining_addresses:
            remaining_list.append({
                "id": addr.id,
                "contact_name": addr.contact_name,
                "phone": addr.phone,
                "full_address": get_full_address(addr)
            })

    return UserAddressDeleteResponse(
        message="删除成功",
        need_reassign_default=need_reassign,
        remaining_addresses=remaining_list if need_reassign else None
    )


@router.post("/reassign-default", response_model=UserAddressResponse)
def reassign_default_address(
    request: UserAddressReassignDefaultRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """重新指定默认地址（删除默认地址后使用）"""
    address = db.query(UserAddress).filter(
        UserAddress.id == request.new_default_address_id,
        UserAddress.user_id == current_user.id
    ).first()

    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="地址不存在或无权限访问"
        )

    reset_other_defaults(db, current_user.id, exclude_id=request.new_default_address_id)
    address.is_default = True
    db.commit()
    db.refresh(address)

    logger.info(f"用户 {current_user.username} 重新指定默认地址 ID: {request.new_default_address_id}")

    result = UserAddressResponse.model_validate(address)
    result.full_address = get_full_address(address)
    return result
