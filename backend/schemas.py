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
