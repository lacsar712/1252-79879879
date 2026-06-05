# -*- coding: utf-8 -*-
"""
Pydantic 数据模式定义
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


# ========== 用户相关 Schema ==========
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=100)


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[int] = None


# ========== 图书相关 Schema ==========
class BookBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    author: str = Field(..., min_length=1, max_length=100)
    publisher: Optional[str] = Field(None, max_length=100)
    isbn: Optional[str] = Field(None, max_length=20)
    price: float = Field(..., gt=0)
    stock: int = Field(default=0, ge=0)
    description: Optional[str] = None
    cover_image: Optional[str] = None
    category: Optional[str] = None


class BookCreate(BookBase):
    pass


class BookUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    author: Optional[str] = Field(None, min_length=1, max_length=100)
    publisher: Optional[str] = Field(None, max_length=100)
    isbn: Optional[str] = Field(None, max_length=20)
    price: Optional[float] = Field(None, gt=0)
    stock: Optional[int] = Field(None, ge=0)
    description: Optional[str] = None
    cover_image: Optional[str] = None
    category: Optional[str] = None


class BookResponse(BookBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BookListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[BookResponse]


# ========== 活动相关 Schema ==========
class PromotionBookBase(BaseModel):
    book_id: int = Field(..., gt=0)
    promotion_price: float = Field(..., gt=0)
    promotion_stock: int = Field(default=0, ge=0)
    purchase_limit: Optional[int] = Field(None, ge=1)


class PromotionBookCreate(PromotionBookBase):
    pass


class PromotionBookUpdate(BaseModel):
    book_id: Optional[int] = Field(None, gt=0)
    promotion_price: Optional[float] = Field(None, gt=0)
    promotion_stock: Optional[int] = Field(None, ge=0)
    purchase_limit: Optional[int] = Field(None, ge=1)


class PromotionBookResponse(PromotionBookBase):
    id: int
    promotion_id: int
    sold_stock: int
    remaining_stock: Optional[int] = None
    original_price: Optional[float] = None
    book: Optional[BookResponse] = None

    class Config:
        from_attributes = True


class PromotionBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    cover_image: Optional[str] = None
    start_time: datetime
    end_time: datetime
    description: Optional[str] = None
    is_displayed: bool = True


class PromotionCreate(PromotionBase):
    books: List[PromotionBookCreate] = Field(default_factory=list)


class PromotionUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    cover_image: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    description: Optional[str] = None
    is_displayed: Optional[bool] = None
    books: Optional[List[PromotionBookCreate]] = None


class PromotionResponse(PromotionBase):
    id: int
    status: Optional[str] = None
    remaining_seconds: Optional[int] = None
    books: List[PromotionBookResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PromotionListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[PromotionResponse]


class PromotionStockDeductRequest(BaseModel):
    promotion_book_id: int = Field(..., gt=0)
    quantity: int = Field(..., ge=1)


# ========== 客服反馈相关 Schema ==========
class FeedbackAttachmentBase(BaseModel):
    file_name: str
    file_path: str
    file_size: Optional[int] = None
    file_type: Optional[str] = None


class FeedbackAttachmentCreate(FeedbackAttachmentBase):
    pass


class FeedbackAttachmentResponse(FeedbackAttachmentBase):
    id: int
    feedback_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class FeedbackReplyBase(BaseModel):
    content: str = Field(..., min_length=1)


class FeedbackReplyCreate(FeedbackReplyBase):
    is_internal: bool = False
    status_change: Optional[str] = None


class FeedbackReplyResponse(FeedbackReplyBase):
    id: int
    feedback_id: int
    replier_id: int
    replier_type: str
    is_internal: bool
    status_change: Optional[str] = None
    replier_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class FeedbackBase(BaseModel):
    type: str = Field(..., min_length=1, max_length=50)
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    contact_info: Optional[str] = Field(None, max_length=200)
    related_order_id: Optional[str] = Field(None, max_length=100)
    related_book_id: Optional[int] = None


class FeedbackCreate(FeedbackBase):
    attachments: List[FeedbackAttachmentCreate] = Field(default_factory=list)


class FeedbackUpdate(BaseModel):
    status: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None


class FeedbackResponse(FeedbackBase):
    id: int
    user_id: int
    status: str
    username: Optional[str] = None
    related_book: Optional[BookResponse] = None
    attachments: List[FeedbackAttachmentResponse] = Field(default_factory=list)
    replies: List[FeedbackReplyResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FeedbackListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[FeedbackResponse]


class FeedbackReplySubmit(BaseModel):
    content: str = Field(..., min_length=1)
    is_internal: bool = False
    status_change: Optional[str] = None


class FeedbackUploadResponse(BaseModel):
    file_name: str
    file_path: str
    file_size: int
    file_type: str


# ========== 试读章节相关 Schema ==========
class BookChapterBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    sort_order: int = Field(default=0, ge=0)
    is_public: bool = True


class BookChapterCreate(BookChapterBase):
    book_id: int = Field(..., gt=0)


class BookChapterUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = None
    sort_order: Optional[int] = Field(None, ge=0)
    is_public: Optional[bool] = None


class BookChapterResponse(BookChapterBase):
    id: int
    book_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BookChapterPublicResponse(BaseModel):
    id: int
    book_id: int
    title: str
    content: str
    sort_order: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BookChapterListResponse(BaseModel):
    total: int
    items: List[BookChapterResponse]


class BookChapterPublicListResponse(BaseModel):
    total: int
    items: List[BookChapterPublicResponse]


# ========== 库存盘点相关 Schema ==========
class StockTakingItemBase(BaseModel):
    book_id: int = Field(..., gt=0)


class StockTakingItemCreate(StockTakingItemBase):
    pass


class StockTakingItemUpdate(BaseModel):
    item_id: int = Field(..., gt=0)
    actual_stock: int = Field(..., ge=0)


class StockTakingItemResponse(StockTakingItemBase):
    id: int
    stock_taking_id: int
    expected_stock: int
    actual_stock: Optional[int] = None
    difference: Optional[int] = None
    book: Optional[BookResponse] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StockTakingBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    scope: str = Field(..., min_length=1, max_length=100)
    person_in_charge: Optional[str] = Field(None, max_length=100)
    remark: Optional[str] = None


class StockTakingCreate(StockTakingBase):
    book_ids: List[int] = Field(..., min_length=1)


class StockTakingUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    scope: Optional[str] = Field(None, min_length=1, max_length=100)
    person_in_charge: Optional[str] = Field(None, max_length=100)
    remark: Optional[str] = None
    book_ids: Optional[List[int]] = Field(None, min_length=1)


class StockTakingResponse(StockTakingBase):
    id: int
    task_no: str
    status: str
    created_by: int
    confirmed_by: Optional[int] = None
    created_by_name: Optional[str] = None
    confirmed_by_name: Optional[str] = None
    items: List[StockTakingItemResponse] = Field(default_factory=list)
    total_books: int = 0
    completed_count: int = 0
    difference_count: int = 0
    created_at: datetime
    updated_at: datetime
    confirmed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class StockTakingListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[StockTakingResponse]


class StockTakingBatchEntryRequest(BaseModel):
    items: List[StockTakingItemUpdate] = Field(..., min_length=1)


class StockTakingConfirmRequest(BaseModel):
    pass


# ========== 供应商相关 Schema ==========
class SupplierBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    contact_person: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = Field(None, max_length=500)
    remark: Optional[str] = None


class SupplierCreate(SupplierBase):
    pass


class SupplierUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    contact_person: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = Field(None, max_length=500)
    remark: Optional[str] = None


class SupplierResponse(SupplierBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SupplierListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[SupplierResponse]


# ========== 采购单明细相关 Schema ==========
class PurchaseOrderItemBase(BaseModel):
    book_id: int = Field(..., gt=0)
    quantity: int = Field(..., ge=1)
    unit_price: float = Field(..., gt=0)
    expected_arrival_time: Optional[datetime] = None


class PurchaseOrderItemCreate(PurchaseOrderItemBase):
    pass


class PurchaseOrderItemUpdate(BaseModel):
    book_id: Optional[int] = Field(None, gt=0)
    quantity: Optional[int] = Field(None, ge=1)
    unit_price: Optional[float] = Field(None, gt=0)
    expected_arrival_time: Optional[datetime] = None


class PurchaseOrderItemResponse(PurchaseOrderItemBase):
    id: int
    purchase_order_id: int
    received_quantity: int
    book: Optional[BookResponse] = None
    subtotal: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ========== 采购单相关 Schema ==========
class PurchaseOrderBase(BaseModel):
    supplier_id: int = Field(..., gt=0)
    purchase_date: datetime
    remark: Optional[str] = None


class PurchaseOrderCreate(PurchaseOrderBase):
    items: List[PurchaseOrderItemCreate] = Field(..., min_length=1)


class PurchaseOrderUpdate(BaseModel):
    supplier_id: Optional[int] = Field(None, gt=0)
    purchase_date: Optional[datetime] = None
    remark: Optional[str] = None
    items: Optional[List[PurchaseOrderItemCreate]] = Field(None, min_length=1)


class PurchaseOrderResponse(PurchaseOrderBase):
    id: int
    order_no: str
    total_amount: float
    status: str
    created_by: int
    confirmed_by: Optional[int] = None
    created_by_name: Optional[str] = None
    confirmed_by_name: Optional[str] = None
    supplier: Optional[SupplierResponse] = None
    items: List[PurchaseOrderItemResponse] = Field(default_factory=list)
    stock_impact: Optional[List[dict]] = None
    created_at: datetime
    updated_at: datetime
    confirmed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PurchaseOrderListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[PurchaseOrderResponse]


class PurchaseOrderConfirmRequest(BaseModel):
    pass


class PurchaseOrderStatusOption(BaseModel):
    value: str
    label: str
    type: str


# ========== 用户地址相关 Schema ==========
class UserAddressBase(BaseModel):
    contact_name: str = Field(..., min_length=1, max_length=50)
    phone: str = Field(..., min_length=11, max_length=20)
    province: str = Field(..., min_length=1, max_length=50)
    city: str = Field(..., min_length=1, max_length=50)
    district: str = Field(..., min_length=1, max_length=50)
    detail_address: str = Field(..., min_length=1, max_length=500)
    address_tag: Optional[str] = Field(None, max_length=20)
    is_default: bool = False


class UserAddressCreate(UserAddressBase):
    pass


class UserAddressUpdate(BaseModel):
    contact_name: Optional[str] = Field(None, min_length=1, max_length=50)
    phone: Optional[str] = Field(None, min_length=11, max_length=20)
    province: Optional[str] = Field(None, min_length=1, max_length=50)
    city: Optional[str] = Field(None, min_length=1, max_length=50)
    district: Optional[str] = Field(None, min_length=1, max_length=50)
    detail_address: Optional[str] = Field(None, min_length=1, max_length=500)
    address_tag: Optional[str] = Field(None, max_length=20)
    is_default: Optional[bool] = None


class UserAddressSetDefaultRequest(BaseModel):
    pass


class UserAddressDeleteResponse(BaseModel):
    message: str
    need_reassign_default: bool = False
    remaining_addresses: Optional[List[dict]] = None


class UserAddressReassignDefaultRequest(BaseModel):
    new_default_address_id: int = Field(..., gt=0)


class UserAddressResponse(UserAddressBase):
    id: int
    user_id: int
    full_address: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserAddressListResponse(BaseModel):
    total: int
    items: List[UserAddressResponse]


class BookCompareData(BaseModel):
    id: int
    title: str
    author: str
    publisher: Optional[str]
    category: Optional[str]
    price: float
    stock: int
    description: Optional[str]
    cover_image: Optional[str]
    isbn: Optional[str]
    rating: Optional[float]
    review_count: int
    tags: List[str]
    is_valid: bool
    invalid_reason: Optional[str] = None


class BookCompareRequest(BaseModel):
    book_ids: List[int] = Field(..., min_length=1, max_length=4)


class BookCompareResponse(BaseModel):
    items: List[BookCompareData]
    invalid_ids: List[int]


# ========== API Key 相关 Schema ==========
class APIKeyBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    remark: Optional[str] = Field(None, max_length=500)
    is_enabled: bool = True
    expires_at: Optional[datetime] = None
    access_scope: str = Field("books:read", max_length=200)
    rate_limit: int = Field(100, ge=1, le=10000)
    rate_period: str = Field("minute", max_length=20)
    allowed_ips: Optional[str] = Field(None, max_length=500)


class APIKeyCreate(APIKeyBase):
    pass


class APIKeyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    remark: Optional[str] = Field(None, max_length=500)
    is_enabled: Optional[bool] = None
    expires_at: Optional[datetime] = None
    access_scope: Optional[str] = Field(None, max_length=200)
    rate_limit: Optional[int] = Field(None, ge=1, le=10000)
    rate_period: Optional[str] = Field(None, max_length=20)
    allowed_ips: Optional[str] = Field(None, max_length=500)


class APIKeyResponse(APIKeyBase):
    id: int
    api_key: str
    api_secret: Optional[str] = None
    created_by: int
    created_by_name: Optional[str] = None
    last_used_at: Optional[datetime] = None
    call_count: int = 0
    risk_status: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class APIKeyCreateResponse(BaseModel):
    id: int
    api_key: str
    api_secret: str
    message: str


class APIKeyRotateResponse(BaseModel):
    id: int
    api_key: str
    api_secret: str
    message: str


class APIKeyListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[APIKeyResponse]


class APIKeyCallLogResponse(BaseModel):
    id: int
    api_key_id: int
    api_key: str
    endpoint: str
    method: str
    ip_address: Optional[str]
    status_code: int
    response_time_ms: Optional[int]
    error_message: Optional[str]
    request_params: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class APIKeyCallLogListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[APIKeyCallLogResponse]


class APIKeyAccessScopeOption(BaseModel):
    value: str
    label: str


class APIKeyRatePeriodOption(BaseModel):
    value: str
    label: str


class APIKeyStatusOption(BaseModel):
    value: str
    label: str
    type: str


class OpenAPIBookResponse(BaseModel):
    id: int
    title: str
    author: str
    publisher: Optional[str]
    isbn: Optional[str]
    price: float
    stock: int
    description: Optional[str]
    cover_image: Optional[str]
    category: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class OpenAPIBookListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[OpenAPIBookResponse]


# ========== 公告相关 Schema ==========
class AnnouncementBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    display_position: str = Field(..., max_length=50)
    display_type: str = Field("banner", max_length=20)
    start_time: datetime
    end_time: datetime
    is_pinned: bool = False
    priority: int = Field(0, ge=0, le=100)
    target_user_type: str = Field("all", max_length=20)
    is_enabled: bool = True


class AnnouncementCreate(AnnouncementBase):
    pass


class AnnouncementUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = None
    display_position: Optional[str] = Field(None, max_length=50)
    display_type: Optional[str] = Field(None, max_length=20)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    is_pinned: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=0, le=100)
    target_user_type: Optional[str] = Field(None, max_length=20)
    is_enabled: Optional[bool] = None


class AnnouncementResponse(AnnouncementBase):
    id: int
    created_by: int
    created_by_name: Optional[str] = None
    view_count: int
    close_count: int
    status: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AnnouncementListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[AnnouncementResponse]


class AnnouncementCloseRequest(BaseModel):
    pass


class AnnouncementDisplayPositionOption(BaseModel):
    value: str
    label: str


class AnnouncementDisplayTypeOption(BaseModel):
    value: str
    label: str


class AnnouncementTargetUserTypeOption(BaseModel):
    value: str
    label: str


class AnnouncementStatusOption(BaseModel):
    value: str
    label: str
    type: str
