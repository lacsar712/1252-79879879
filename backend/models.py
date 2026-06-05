# -*- coding: utf-8 -*-
"""
数据库模型定义
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class User(Base):
    """用户模型"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Book(Base):
    """图书模型"""
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(200), nullable=False, index=True)
    author = Column(String(100), nullable=False, index=True)
    publisher = Column(String(100), nullable=True)
    isbn = Column(String(20), unique=True, nullable=True)
    price = Column(Float, nullable=False)
    stock = Column(Integer, default=0)
    description = Column(Text, nullable=True)
    cover_image = Column(String(500), nullable=True)
    category = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Promotion(Base):
    """活动专题模型"""
    __tablename__ = "promotions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(200), nullable=False, index=True)
    cover_image = Column(String(500), nullable=True)
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_displayed = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PromotionBook(Base):
    """活动图书关联模型"""
    __tablename__ = "promotion_books"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    promotion_id = Column(Integer, nullable=False, index=True)
    book_id = Column(Integer, nullable=False, index=True)
    promotion_price = Column(Float, nullable=False)
    promotion_stock = Column(Integer, nullable=False, default=0)
    sold_stock = Column(Integer, nullable=False, default=0)
    purchase_limit = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Feedback(Base):
    """客服反馈主表"""
    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    type = Column(String(50), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    contact_info = Column(String(200), nullable=True)
    related_order_id = Column(String(100), nullable=True, index=True)
    related_book_id = Column(Integer, nullable=True, index=True)
    status = Column(String(50), nullable=False, default="pending", index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class FeedbackAttachment(Base):
    """反馈附件表"""
    __tablename__ = "feedback_attachments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    feedback_id = Column(Integer, nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=True)
    file_type = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class FeedbackReply(Base):
    """反馈回复记录表"""
    __tablename__ = "feedback_replies"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    feedback_id = Column(Integer, nullable=False, index=True)
    replier_id = Column(Integer, nullable=False, index=True)
    replier_type = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    is_internal = Column(Boolean, default=False, index=True)
    status_change = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class BookChapter(Base):
    """试读章节模型"""
    __tablename__ = "book_chapters"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    book_id = Column(Integer, nullable=False, index=True)
    title = Column(String(200), nullable=False, index=True)
    content = Column(Text, nullable=False)
    sort_order = Column(Integer, default=0, index=True)
    is_public = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class StockTaking(Base):
    """库存盘点任务模型"""
    __tablename__ = "stock_takings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    task_no = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False, index=True)
    scope = Column(String(100), nullable=False)
    person_in_charge = Column(String(100), nullable=True)
    remark = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="draft", index=True)
    created_by = Column(Integer, nullable=False, index=True)
    confirmed_by = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    confirmed_at = Column(DateTime, nullable=True)


class StockTakingItem(Base):
    """库存盘点明细模型"""
    __tablename__ = "stock_taking_items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    stock_taking_id = Column(Integer, nullable=False, index=True)
    book_id = Column(Integer, nullable=False, index=True)
    expected_stock = Column(Integer, nullable=False, default=0)
    actual_stock = Column(Integer, nullable=True)
    difference = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Supplier(Base):
    """供应商模型"""
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(200), nullable=False, index=True)
    contact_person = Column(String(100), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(100), nullable=True)
    address = Column(String(500), nullable=True)
    remark = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PurchaseOrder(Base):
    """采购单主表模型"""
    __tablename__ = "purchase_orders"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_no = Column(String(50), unique=True, index=True, nullable=False)
    supplier_id = Column(Integer, nullable=False, index=True)
    purchase_date = Column(DateTime, nullable=False, index=True)
    total_amount = Column(Float, nullable=False, default=0)
    remark = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="draft", index=True)
    created_by = Column(Integer, nullable=False, index=True)
    confirmed_by = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    confirmed_at = Column(DateTime, nullable=True)


class PurchaseOrderItem(Base):
    """采购单明细表模型"""
    __tablename__ = "purchase_order_items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    purchase_order_id = Column(Integer, nullable=False, index=True)
    book_id = Column(Integer, nullable=False, index=True)
    quantity = Column(Integer, nullable=False, default=0)
    unit_price = Column(Float, nullable=False, default=0)
    expected_arrival_time = Column(DateTime, nullable=True)
    received_quantity = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class StockChange(Base):
    """库存变动记录表模型"""
    __tablename__ = "stock_changes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    book_id = Column(Integer, nullable=False, index=True)
    change_type = Column(String(50), nullable=False, index=True)
    change_quantity = Column(Integer, nullable=False, default=0)
    before_stock = Column(Integer, nullable=False, default=0)
    after_stock = Column(Integer, nullable=False, default=0)
    related_order_id = Column(Integer, nullable=True, index=True)
    related_order_no = Column(String(50), nullable=True, index=True)
    related_order_type = Column(String(50), nullable=True, index=True)
    unit_cost = Column(Float, nullable=True)
    total_cost = Column(Float, nullable=True)
    remark = Column(Text, nullable=True)
    created_by = Column(Integer, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class UserAddress(Base):
    """用户收货地址模型"""
    __tablename__ = "user_addresses"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    contact_name = Column(String(50), nullable=False)
    phone = Column(String(20), nullable=False, index=True)
    province = Column(String(50), nullable=False)
    city = Column(String(50), nullable=False)
    district = Column(String(50), nullable=False)
    detail_address = Column(String(500), nullable=False)
    address_tag = Column(String(20), nullable=True)
    is_default = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class APIKey(Base):
    """API Key 模型"""
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False, index=True)
    remark = Column(String(500), nullable=True)
    api_key = Column(String(64), unique=True, index=True, nullable=False)
    api_secret = Column(String(64), nullable=False)
    is_enabled = Column(Boolean, default=True, index=True)
    expires_at = Column(DateTime, nullable=True, index=True)
    access_scope = Column(String(200), default="books:read", index=True)
    rate_limit = Column(Integer, default=100, nullable=False)
    rate_period = Column(String(20), default="minute", nullable=False)
    allowed_ips = Column(String(500), nullable=True)
    created_by = Column(Integer, nullable=False, index=True)
    last_used_at = Column(DateTime, nullable=True)
    call_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class APIKeyCallLog(Base):
    """API Key 调用日志模型"""
    __tablename__ = "api_key_call_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    api_key_id = Column(Integer, nullable=False, index=True)
    api_key = Column(String(64), nullable=False, index=True)
    endpoint = Column(String(200), nullable=False, index=True)
    method = Column(String(10), nullable=False)
    ip_address = Column(String(50), nullable=True, index=True)
    status_code = Column(Integer, nullable=False, index=True)
    response_time_ms = Column(Integer, nullable=True)
    error_message = Column(String(1000), nullable=True)
    request_params = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class Announcement(Base):
    """公告模型"""
    __tablename__ = "announcements"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(200), nullable=False, index=True)
    content = Column(Text, nullable=False)
    display_position = Column(String(50), nullable=False, index=True)
    display_type = Column(String(20), nullable=False, default="banner")
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=False, index=True)
    is_pinned = Column(Boolean, default=False, index=True)
    priority = Column(Integer, default=0, index=True)
    target_user_type = Column(String(20), nullable=False, default="all")
    is_enabled = Column(Boolean, default=True, index=True)
    created_by = Column(Integer, nullable=False, index=True)
    view_count = Column(Integer, default=0)
    close_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AnnouncementCloseRecord(Base):
    """公告关闭记录模型"""
    __tablename__ = "announcement_close_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    announcement_id = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    closed_at = Column(DateTime, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
