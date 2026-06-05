# -*- coding: utf-8 -*-
"""
客服反馈路由
"""
import logging
import os
import uuid
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.orm import Session

from database import get_db
from models import User, Feedback, FeedbackAttachment, FeedbackReply, Book
from schemas import (
    FeedbackCreate,
    FeedbackResponse,
    FeedbackListResponse,
    FeedbackReplySubmit,
    FeedbackReplyResponse,
    FeedbackAttachmentResponse,
    FeedbackUploadResponse,
    FeedbackUpdate
)
from auth import get_current_active_user, get_current_admin_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/feedbacks", tags=["客服反馈"])

FEEDBACK_STATUS = ["pending", "processing", "replied", "closed"]
FEEDBACK_TYPES = ["product", "order", "account", "payment", "other"]

UPLOAD_DIR = "static/feedback_attachments"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/gif", "image/webp", "image/jpg"]
MAX_FILE_SIZE = 10 * 1024 * 1024


def get_status_text(status: str) -> str:
    status_map = {
        "pending": "待处理",
        "processing": "处理中",
        "replied": "已回复",
        "closed": "已关闭"
    }
    return status_map.get(status, status)


def get_type_text(type: str) -> str:
    type_map = {
        "product": "商品问题",
        "order": "订单问题",
        "account": "账户问题",
        "payment": "支付问题",
        "other": "其他问题"
    }
    return type_map.get(type, type)


def enrich_feedback_response(feedback: Feedback, db: Session, include_internal: bool = False) -> FeedbackResponse:
    attachments = db.query(FeedbackAttachment).filter(
        FeedbackAttachment.feedback_id == feedback.id
    ).all()

    reply_query = db.query(FeedbackReply).filter(FeedbackReply.feedback_id == feedback.id)
    if not include_internal:
        reply_query = reply_query.filter(FeedbackReply.is_internal == False)
    replies = reply_query.order_by(FeedbackReply.created_at.asc()).all()

    reply_responses = []
    for reply in replies:
        replier = db.query(User).filter(User.id == reply.replier_id).first()
        reply_resp = FeedbackReplyResponse(
            id=reply.id,
            feedback_id=reply.feedback_id,
            replier_id=reply.replier_id,
            replier_type=reply.replier_type,
            content=reply.content,
            is_internal=reply.is_internal,
            status_change=reply.status_change,
            replier_name=replier.username if replier else "未知用户",
            created_at=reply.created_at
        )
        reply_responses.append(reply_resp)

    user = db.query(User).filter(User.id == feedback.user_id).first()
    related_book = None
    if feedback.related_book_id:
        related_book = db.query(Book).filter(Book.id == feedback.related_book_id).first()

    return FeedbackResponse(
        id=feedback.id,
        user_id=feedback.user_id,
        type=feedback.type,
        title=feedback.title,
        description=feedback.description,
        contact_info=feedback.contact_info,
        related_order_id=feedback.related_order_id,
        related_book_id=feedback.related_book_id,
        status=feedback.status,
        username=user.username if user else None,
        related_book=related_book,
        attachments=[FeedbackAttachmentResponse.model_validate(a) for a in attachments],
        replies=reply_responses,
        created_at=feedback.created_at,
        updated_at=feedback.updated_at
    )


@router.post("/upload", response_model=FeedbackUploadResponse)
async def upload_attachment(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
):
    """上传反馈附件"""
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只支持上传图片文件 (JPG, PNG, GIF, WEBP)"
        )

    file_content = await file.read()
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件大小不能超过 10MB"
        )

    file_ext = os.path.splitext(file.filename)[1] if file.filename else ".jpg"
    unique_filename = f"{uuid.uuid4().hex}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    with open(file_path, "wb") as f:
        f.write(file_content)

    static_url = f"/api/static/feedback_attachments/{unique_filename}"

    logger.info(f"用户 {current_user.username} 上传反馈附件: {file.filename}")

    return FeedbackUploadResponse(
        file_name=file.filename or unique_filename,
        file_path=static_url,
        file_size=len(file_content),
        file_type=file.content_type or "image/jpeg"
    )


@router.post("", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
def create_feedback(
    feedback_data: FeedbackCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """用户提交反馈"""
    if feedback_data.type not in FEEDBACK_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的反馈类型，支持的类型: {', '.join(FEEDBACK_TYPES)}"
        )

    db_feedback = Feedback(
        user_id=current_user.id,
        type=feedback_data.type,
        title=feedback_data.title,
        description=feedback_data.description,
        contact_info=feedback_data.contact_info,
        related_order_id=feedback_data.related_order_id,
        related_book_id=feedback_data.related_book_id,
        status="pending"
    )
    db.add(db_feedback)
    db.flush()

    for att in feedback_data.attachments:
        db_attachment = FeedbackAttachment(
            feedback_id=db_feedback.id,
            file_name=att.file_name,
            file_path=att.file_path,
            file_size=att.file_size,
            file_type=att.file_type
        )
        db.add(db_attachment)

    db.commit()
    db.refresh(db_feedback)

    logger.info(f"用户 {current_user.username} 提交反馈 #{db_feedback.id}: {feedback_data.title}")

    return enrich_feedback_response(db_feedback, db)


@router.get("/my", response_model=FeedbackListResponse)
def get_my_feedbacks(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取我的反馈列表"""
    query = db.query(Feedback).filter(Feedback.user_id == current_user.id)

    if status:
        if status not in FEEDBACK_STATUS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的状态，支持的状态: {', '.join(FEEDBACK_STATUS)}"
            )
        query = query.filter(Feedback.status == status)

    if type:
        if type not in FEEDBACK_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的反馈类型，支持的类型: {', '.join(FEEDBACK_TYPES)}"
            )
        query = query.filter(Feedback.type == type)

    if start_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(Feedback.created_at >= start_dt)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="开始日期格式错误，请使用 YYYY-MM-DD 格式"
            )

    if end_date:
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            end_dt = end_dt.replace(hour=23, minute=59, second=59)
            query = query.filter(Feedback.created_at <= end_dt)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="结束日期格式错误，请使用 YYYY-MM-DD 格式"
            )

    total = query.count()
    feedbacks = query.order_by(Feedback.created_at.desc()) \
        .offset((page - 1) * page_size) \
        .limit(page_size) \
        .all()

    items = [enrich_feedback_response(f, db) for f in feedbacks]

    return FeedbackListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=items
    )


@router.get("/{feedback_id}", response_model=FeedbackResponse)
def get_feedback_detail(
    feedback_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取反馈详情"""
    feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="反馈不存在"
        )

    include_internal = current_user.is_admin
    if not current_user.is_admin and feedback.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权查看此反馈"
        )

    return enrich_feedback_response(feedback, db, include_internal=include_internal)


@router.post("/{feedback_id}/reply", response_model=FeedbackReplyResponse)
def reply_feedback(
    feedback_id: int,
    reply_data: FeedbackReplySubmit,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """用户追加回复"""
    feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="反馈不存在"
        )

    if feedback.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权回复此反馈"
        )

    if reply_data.is_internal:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="普通用户不能添加内部备注"
        )

    if reply_data.status_change:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="普通用户不能修改反馈状态"
        )

    if feedback.status == "closed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="反馈已关闭，不能继续回复"
        )

    db_reply = FeedbackReply(
        feedback_id=feedback_id,
        replier_id=current_user.id,
        replier_type="user",
        content=reply_data.content,
        is_internal=False
    )
    db.add(db_reply)

    if feedback.status == "replied":
        feedback.status = "processing"

    db.commit()
    db.refresh(db_reply)

    logger.info(f"用户 {current_user.username} 回复反馈 #{feedback_id}")

    replier_name = current_user.username
    return FeedbackReplyResponse(
        id=db_reply.id,
        feedback_id=db_reply.feedback_id,
        replier_id=db_reply.replier_id,
        replier_type=db_reply.replier_type,
        content=db_reply.content,
        is_internal=db_reply.is_internal,
        status_change=db_reply.status_change,
        replier_name=replier_name,
        created_at=db_reply.created_at
    )


@router.get("", response_model=FeedbackListResponse)
def get_all_feedbacks(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """客服获取所有反馈列表（管理员权限）"""
    query = db.query(Feedback)

    if status:
        if status not in FEEDBACK_STATUS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的状态，支持的状态: {', '.join(FEEDBACK_STATUS)}"
            )
        query = query.filter(Feedback.status == status)

    if type:
        if type not in FEEDBACK_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的反馈类型，支持的类型: {', '.join(FEEDBACK_TYPES)}"
            )
        query = query.filter(Feedback.type == type)

    if start_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(Feedback.created_at >= start_dt)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="开始日期格式错误，请使用 YYYY-MM-DD 格式"
            )

    if end_date:
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            end_dt = end_dt.replace(hour=23, minute=59, second=59)
            query = query.filter(Feedback.created_at <= end_dt)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="结束日期格式错误，请使用 YYYY-MM-DD 格式"
            )

    if keyword:
        query = query.filter(
            (Feedback.title.contains(keyword)) |
            (Feedback.description.contains(keyword)) |
            (Feedback.related_order_id.contains(keyword))
        )

    total = query.count()
    feedbacks = query.order_by(Feedback.created_at.desc()) \
        .offset((page - 1) * page_size) \
        .limit(page_size) \
        .all()

    items = [enrich_feedback_response(f, db, include_internal=True) for f in feedbacks]

    return FeedbackListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=items
    )


@router.post("/{feedback_id}/admin-reply", response_model=FeedbackReplyResponse)
def admin_reply_feedback(
    feedback_id: int,
    reply_data: FeedbackReplySubmit,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """客服回复反馈（管理员权限）"""
    feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="反馈不存在"
        )

    if reply_data.status_change and reply_data.status_change not in FEEDBACK_STATUS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的状态，支持的状态: {', '.join(FEEDBACK_STATUS)}"
        )

    db_reply = FeedbackReply(
        feedback_id=feedback_id,
        replier_id=current_user.id,
        replier_type="admin",
        content=reply_data.content,
        is_internal=reply_data.is_internal,
        status_change=reply_data.status_change
    )
    db.add(db_reply)

    if reply_data.status_change:
        feedback.status = reply_data.status_change
    elif not reply_data.is_internal and feedback.status == "pending":
        feedback.status = "replied"
    elif not reply_data.is_internal and feedback.status == "processing":
        feedback.status = "replied"

    db.commit()
    db.refresh(db_reply)

    log_msg = f"客服 {current_user.username} 回复反馈 #{feedback_id}"
    if reply_data.is_internal:
        log_msg += "（内部备注）"
    if reply_data.status_change:
        log_msg += f"，状态变更为: {reply_data.status_change}"
    logger.info(log_msg)

    return FeedbackReplyResponse(
        id=db_reply.id,
        feedback_id=db_reply.feedback_id,
        replier_id=db_reply.replier_id,
        replier_type=db_reply.replier_type,
        content=db_reply.content,
        is_internal=db_reply.is_internal,
        status_change=db_reply.status_change,
        replier_name=current_user.username,
        created_at=db_reply.created_at
    )


@router.put("/{feedback_id}/status", response_model=FeedbackResponse)
def update_feedback_status(
    feedback_id: int,
    update_data: FeedbackUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """修改反馈状态（管理员权限）"""
    feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="反馈不存在"
        )

    if update_data.status and update_data.status not in FEEDBACK_STATUS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的状态，支持的状态: {', '.join(FEEDBACK_STATUS)}"
        )

    old_status = feedback.status

    if update_data.status:
        feedback.status = update_data.status
    if update_data.title:
        feedback.title = update_data.title
    if update_data.description:
        feedback.description = update_data.description

    if update_data.status and old_status != update_data.status:
        db_reply = FeedbackReply(
            feedback_id=feedback_id,
            replier_id=current_user.id,
            replier_type="admin",
            content=f"客服将反馈状态从「{get_status_text(old_status)}」变更为「{get_status_text(update_data.status)}」",
            is_internal=False,
            status_change=update_data.status
        )
        db.add(db_reply)

    db.commit()
    db.refresh(feedback)

    logger.info(f"客服 {current_user.username} 修改反馈 #{feedback_id} 状态: {old_status} -> {update_data.status}")

    return enrich_feedback_response(feedback, db, include_internal=True)


@router.get("/types/list")
def get_feedback_types():
    """获取反馈类型列表"""
    return [
        {"value": "product", "label": "商品问题"},
        {"value": "order", "label": "订单问题"},
        {"value": "account", "label": "账户问题"},
        {"value": "payment", "label": "支付问题"},
        {"value": "other", "label": "其他问题"}
    ]


@router.get("/statuses/list")
def get_feedback_statuses():
    """获取反馈状态列表"""
    return [
        {"value": "pending", "label": "待处理"},
        {"value": "processing", "label": "处理中"},
        {"value": "replied", "label": "已回复"},
        {"value": "closed", "label": "已关闭"}
    ]
