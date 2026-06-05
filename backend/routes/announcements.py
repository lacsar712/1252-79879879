# -*- coding: utf-8 -*-
"""
公告管理路由
"""
import logging
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from database import get_db
from models import Announcement, AnnouncementCloseRecord, User
from schemas import (
    AnnouncementCreate, AnnouncementUpdate, AnnouncementResponse,
    AnnouncementListResponse,
    AnnouncementDisplayPositionOption, AnnouncementDisplayTypeOption,
    AnnouncementTargetUserTypeOption, AnnouncementStatusOption
)
from auth import get_current_admin_user, get_current_active_user, get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/announcements", tags=["公告管理"])


ANNOUNCEMENT_STATUS_PENDING = "pending"
ANNOUNCEMENT_STATUS_ACTIVE = "active"
ANNOUNCEMENT_STATUS_ENDED = "ended"
ANNOUNCEMENT_STATUS_DISABLED = "disabled"

DISPLAY_POSITIONS = [
    {"value": "home", "label": "首页顶部"},
    {"value": "home_bottom", "label": "首页底部"},
    {"value": "book_list", "label": "图书列表页"},
    {"value": "book_detail", "label": "图书详情页"},
    {"value": "global", "label": "全站显示"},
]

DISPLAY_TYPES = [
    {"value": "banner", "label": "横幅"},
    {"value": "modal", "label": "弹窗"},
    {"value": "list", "label": "列表项"},
]

TARGET_USER_TYPES = [
    {"value": "all", "label": "所有用户"},
    {"value": "logged_in", "label": "已登录用户"},
    {"value": "guest", "label": "游客"},
    {"value": "admin", "label": "管理员"},
]

STATUS_OPTIONS = [
    {"value": "pending", "label": "未开始", "type": "info"},
    {"value": "active", "label": "进行中", "type": "success"},
    {"value": "ended", "label": "已结束", "type": "warning"},
    {"value": "disabled", "label": "已停用", "type": "danger"},
]


def get_announcement_status(announcement: Announcement) -> str:
    """获取公告状态"""
    if not announcement.is_enabled:
        return ANNOUNCEMENT_STATUS_DISABLED
    now = datetime.utcnow()
    if now < announcement.start_time:
        return ANNOUNCEMENT_STATUS_PENDING
    elif now > announcement.end_time:
        return ANNOUNCEMENT_STATUS_ENDED
    else:
        return ANNOUNCEMENT_STATUS_ACTIVE


def enrich_announcement_response(db: Session, announcement: Announcement) -> dict:
    """丰富公告响应数据"""
    result = announcement.__dict__.copy()
    result["status"] = get_announcement_status(announcement)
    
    creator = db.query(User).filter(User.id == announcement.created_by).first()
    if creator:
        result["created_by_name"] = creator.username
    
    return result


def check_target_user_match(announcement: Announcement, current_user: Optional[User]) -> bool:
    """检查公告目标用户类型是否匹配当前用户"""
    target_type = announcement.target_user_type
    
    if target_type == "all":
        return True
    elif target_type == "guest":
        return current_user is None
    elif target_type == "logged_in":
        return current_user is not None
    elif target_type == "admin":
        return current_user is not None and current_user.is_admin
    
    return True


def get_user_closed_announcement_ids(db: Session, user_id: Optional[int]) -> List[int]:
    """获取用户已关闭的公告ID列表"""
    if not user_id:
        return []
    
    closed_records = db.query(AnnouncementCloseRecord).filter(
        AnnouncementCloseRecord.user_id == user_id
    ).all()
    
    return [record.announcement_id for record in closed_records]


@router.get("/positions/list", response_model=List[AnnouncementDisplayPositionOption])
def get_display_positions():
    """获取公告展示位置选项"""
    return DISPLAY_POSITIONS


@router.get("/types/list", response_model=List[AnnouncementDisplayTypeOption])
def get_display_types():
    """获取公告展示类型选项"""
    return DISPLAY_TYPES


@router.get("/target-user-types/list", response_model=List[AnnouncementTargetUserTypeOption])
def get_target_user_types():
    """获取公告目标用户类型选项"""
    return TARGET_USER_TYPES


@router.get("/statuses/list", response_model=List[AnnouncementStatusOption])
def get_status_options():
    """获取公告状态选项"""
    return STATUS_OPTIONS


@router.get("/display", response_model=List[AnnouncementResponse])
def get_display_announcements(
    position: str = Query(..., description="展示位置: home/home_bottom/book_list/book_detail/global"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """获取当前页面需要展示的有效公告（前台接口）"""
    now = datetime.utcnow()
    
    query = db.query(Announcement).filter(
        Announcement.is_enabled == True,
        Announcement.start_time <= now,
        Announcement.end_time >= now,
        (Announcement.display_position == position) | (Announcement.display_position == "global")
    )
    
    all_announcements = query.order_by(
        desc(Announcement.is_pinned),
        desc(Announcement.priority),
        desc(Announcement.created_at)
    ).all()
    
    closed_ids = get_user_closed_announcement_ids(db, current_user.id if current_user else None)
    
    result = []
    for announcement in all_announcements:
        if announcement.id in closed_ids:
            continue
        
        if not check_target_user_match(announcement, current_user):
            continue
        
        announcement.view_count += 1
        db.flush()
        
        result.append(enrich_announcement_response(db, announcement))
    
    db.commit()
    return result


@router.post("/{announcement_id}/close", status_code=status.HTTP_204_NO_CONTENT)
def close_announcement(
    announcement_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """用户关闭公告（记录关闭状态，有效期内不再显示）"""
    announcement = db.query(Announcement).filter(Announcement.id == announcement_id).first()
    if not announcement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="公告不存在"
        )
    
    now = datetime.utcnow()
    if now > announcement.end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="公告已过期，无需关闭"
        )
    
    existing_record = db.query(AnnouncementCloseRecord).filter(
        AnnouncementCloseRecord.announcement_id == announcement_id,
        AnnouncementCloseRecord.user_id == current_user.id
    ).first()
    
    if existing_record:
        return None
    
    close_record = AnnouncementCloseRecord(
        announcement_id=announcement_id,
        user_id=current_user.id,
        closed_at=now
    )
    db.add(close_record)
    
    announcement.close_count += 1
    
    db.commit()
    
    logger.info(f"公告关闭成功: 公告ID={announcement_id}, 用户={current_user.username}")
    return None


@router.get("", response_model=AnnouncementListResponse)
def get_announcements(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="公告状态: pending/active/ended/disabled"),
    position: Optional[str] = Query(None, description="展示位置"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """获取公告列表（管理员接口）"""
    now = datetime.utcnow()
    query = db.query(Announcement)
    
    if status:
        if status == ANNOUNCEMENT_STATUS_PENDING:
            query = query.filter(Announcement.start_time > now, Announcement.is_enabled == True)
        elif status == ANNOUNCEMENT_STATUS_ACTIVE:
            query = query.filter(
                and_(
                    Announcement.start_time <= now,
                    Announcement.end_time >= now,
                    Announcement.is_enabled == True
                )
            )
        elif status == ANNOUNCEMENT_STATUS_ENDED:
            query = query.filter(Announcement.end_time < now, Announcement.is_enabled == True)
        elif status == ANNOUNCEMENT_STATUS_DISABLED:
            query = query.filter(Announcement.is_enabled == False)
    
    if position:
        query = query.filter(Announcement.display_position == position)
    
    if keyword:
        query = query.filter(
            (Announcement.title.like(f"%{keyword}%")) |
            (Announcement.content.like(f"%{keyword}%"))
        )
    
    total = query.count()
    offset = (page - 1) * page_size
    announcements = query.order_by(
        desc(Announcement.is_pinned),
        desc(Announcement.priority),
        desc(Announcement.created_at)
    ).offset(offset).limit(page_size).all()
    
    items = [enrich_announcement_response(db, a) for a in announcements]
    
    return AnnouncementListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=items
    )


@router.get("/{announcement_id}", response_model=AnnouncementResponse)
def get_announcement(
    announcement_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """获取公告详情（管理员接口）"""
    announcement = db.query(Announcement).filter(Announcement.id == announcement_id).first()
    if not announcement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="公告不存在"
        )
    
    return enrich_announcement_response(db, announcement)


@router.post("", response_model=AnnouncementResponse, status_code=status.HTTP_201_CREATED)
def create_announcement(
    announcement: AnnouncementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """创建公告（管理员接口）"""
    if announcement.end_time <= announcement.start_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="结束时间必须晚于开始时间"
        )
    
    valid_positions = [p["value"] for p in DISPLAY_POSITIONS]
    if announcement.display_position not in valid_positions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的展示位置，有效值为: {', '.join(valid_positions)}"
        )
    
    valid_types = [t["value"] for t in DISPLAY_TYPES]
    if announcement.display_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的展示类型，有效值为: {', '.join(valid_types)}"
        )
    
    valid_targets = [t["value"] for t in TARGET_USER_TYPES]
    if announcement.target_user_type not in valid_targets:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的目标用户类型，有效值为: {', '.join(valid_targets)}"
        )
    
    db_announcement = Announcement(
        title=announcement.title,
        content=announcement.content,
        display_position=announcement.display_position,
        display_type=announcement.display_type,
        start_time=announcement.start_time,
        end_time=announcement.end_time,
        is_pinned=announcement.is_pinned,
        priority=announcement.priority,
        target_user_type=announcement.target_user_type,
        is_enabled=announcement.is_enabled,
        created_by=current_user.id
    )
    db.add(db_announcement)
    db.commit()
    db.refresh(db_announcement)
    
    logger.info(f"公告创建成功: {announcement.title} (by {current_user.username})")
    return enrich_announcement_response(db, db_announcement)


@router.put("/{announcement_id}", response_model=AnnouncementResponse)
def update_announcement(
    announcement_id: int,
    announcement_update: AnnouncementUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """更新公告（管理员接口）"""
    db_announcement = db.query(Announcement).filter(Announcement.id == announcement_id).first()
    if not db_announcement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="公告不存在"
        )
    
    update_data = announcement_update.model_dump(exclude_unset=True)
    
    start_time = update_data.get("start_time", db_announcement.start_time)
    end_time = update_data.get("end_time", db_announcement.end_time)
    
    if "end_time" in update_data or "start_time" in update_data:
        if end_time <= start_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="结束时间必须晚于开始时间"
            )
    
    if "display_position" in update_data:
        valid_positions = [p["value"] for p in DISPLAY_POSITIONS]
        if update_data["display_position"] not in valid_positions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的展示位置，有效值为: {', '.join(valid_positions)}"
            )
    
    if "display_type" in update_data:
        valid_types = [t["value"] for t in DISPLAY_TYPES]
        if update_data["display_type"] not in valid_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的展示类型，有效值为: {', '.join(valid_types)}"
            )
    
    if "target_user_type" in update_data:
        valid_targets = [t["value"] for t in TARGET_USER_TYPES]
        if update_data["target_user_type"] not in valid_targets:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的目标用户类型，有效值为: {', '.join(valid_targets)}"
            )
    
    for field, value in update_data.items():
        setattr(db_announcement, field, value)
    
    db.commit()
    db.refresh(db_announcement)
    
    logger.info(f"公告更新成功: {db_announcement.title} (by {current_user.username})")
    return enrich_announcement_response(db, db_announcement)


@router.delete("/{announcement_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_announcement(
    announcement_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """删除公告（管理员接口）"""
    db_announcement = db.query(Announcement).filter(Announcement.id == announcement_id).first()
    if not db_announcement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="公告不存在"
        )
    
    db.query(AnnouncementCloseRecord).filter(
        AnnouncementCloseRecord.announcement_id == announcement_id
    ).delete()
    
    announcement_title = db_announcement.title
    db.delete(db_announcement)
    db.commit()
    
    logger.info(f"公告删除成功: {announcement_title} (by {current_user.username})")
    return None


@router.post("/{announcement_id}/toggle", response_model=AnnouncementResponse)
def toggle_announcement(
    announcement_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """切换公告启用/停用状态（管理员接口）"""
    db_announcement = db.query(Announcement).filter(Announcement.id == announcement_id).first()
    if not db_announcement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="公告不存在"
        )
    
    db_announcement.is_enabled = not db_announcement.is_enabled
    db.commit()
    db.refresh(db_announcement)
    
    logger.info(f"公告状态切换成功: {db_announcement.title} -> {db_announcement.is_enabled} (by {current_user.username})")
    return enrich_announcement_response(db, db_announcement)
