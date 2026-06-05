# -*- coding: utf-8 -*-
"""
API Key 鉴权模块
"""
import logging
import time
import json
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from database import get_db
from models import APIKey, APIKeyCallLog

logger = logging.getLogger(__name__)

rate_limit_store: Dict[str, Dict] = {}


def generate_api_key() -> str:
    """生成 API Key"""
    prefix = "ak_"
    random_part = secrets.token_hex(16)
    return f"{prefix}{random_part}"


def generate_api_secret() -> str:
    """生成 API Secret"""
    return secrets.token_hex(32)


def hash_secret(secret: str) -> str:
    """哈希存储 Secret"""
    return hashlib.sha256(secret.encode()).hexdigest()


def get_client_ip(request: Request) -> str:
    """获取客户端 IP"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    return request.client.host if request.client else "unknown"


def is_ip_allowed(api_key: APIKey, client_ip: str) -> bool:
    """检查 IP 是否在允许列表中"""
    if not api_key.allowed_ips:
        return True
    allowed_ips = [ip.strip() for ip in api_key.allowed_ips.split(",")]
    return client_ip in allowed_ips


def check_rate_limit(api_key_id: int, rate_limit: int, rate_period: str) -> bool:
    """检查频率限制"""
    now = time.time()
    key = f"rate_limit_{api_key_id}"

    if rate_period == "second":
        window = 1
    elif rate_period == "hour":
        window = 3600
    elif rate_period == "day":
        window = 86400
    else:
        window = 60

    if key not in rate_limit_store:
        rate_limit_store[key] = {"count": 0, "start_time": now}

    store = rate_limit_store[key]

    if now - store["start_time"] > window:
        store["count"] = 0
        store["start_time"] = now

    if store["count"] >= rate_limit:
        return False

    store["count"] += 1
    return True


def is_expired(api_key: APIKey) -> bool:
    """检查是否过期"""
    if not api_key.expires_at:
        return False
    return datetime.utcnow() > api_key.expires_at


def has_access_scope(api_key: APIKey, required_scope: str) -> bool:
    """检查访问范围权限"""
    if not api_key.access_scope:
        return True
    scopes = [s.strip() for s in api_key.access_scope.split(",")]
    return required_scope in scopes or "*" in scopes


def get_api_key_from_header(request: Request) -> Optional[str]:
    """从请求头获取 API Key"""
    auth_header = request.headers.get("X-API-Key")
    if auth_header:
        return auth_header.strip()
    return None


def get_api_key_obj(
    api_key_str: str,
    db: Session = Depends(get_db)
) -> Optional[APIKey]:
    """根据 Key 字符串获取 API Key 对象"""
    api_key = db.query(APIKey).filter(APIKey.api_key == api_key_str).first()
    return api_key


async def authenticate_api_key(
    request: Request,
    db: Session = Depends(get_db),
    required_scope: str = "books:read"
) -> APIKey:
    """API Key 鉴权依赖"""
    api_key_str = get_api_key_from_header(request)
    if not api_key_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少 API Key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    api_key = get_api_key_obj(api_key_str, db)
    if not api_key:
        await log_api_call(db, None, api_key_str, request, 401, "无效的 API Key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的 API Key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    if not api_key.is_enabled:
        await log_api_call(db, api_key.id, api_key_str, request, 403, "API Key 已被禁用")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API Key 已被禁用"
        )

    if is_expired(api_key):
        await log_api_call(db, api_key.id, api_key_str, request, 403, "API Key 已过期")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API Key 已过期"
        )

    client_ip = get_client_ip(request)
    if not is_ip_allowed(api_key, client_ip):
        await log_api_call(db, api_key.id, api_key_str, request, 403, f"IP {client_ip} 不在允许列表中")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="IP 地址不在允许列表中"
        )

    if not has_access_scope(api_key, required_scope):
        await log_api_call(db, api_key.id, api_key_str, request, 403, f"缺少访问范围权限: {required_scope}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"缺少访问范围权限: {required_scope}"
        )

    if not check_rate_limit(api_key.id, api_key.rate_limit, api_key.rate_period):
        await log_api_call(db, api_key.id, api_key_str, request, 429, "调用频率超出限制")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="调用频率超出限制，请稍后重试"
        )

    api_key.last_used_at = datetime.utcnow()
    api_key.call_count += 1
    db.commit()

    return api_key


async def log_api_call(
    db: Session,
    api_key_id: Optional[int],
    api_key_str: str,
    request: Request,
    status_code: int,
    error_message: Optional[str] = None,
    response_time_ms: Optional[int] = None
):
    """记录 API 调用日志"""
    try:
        client_ip = get_client_ip(request)
        params = {}
        if request.query_params:
            params.update(dict(request.query_params))

        call_log = APIKeyCallLog(
            api_key_id=api_key_id if api_key_id else 0,
            api_key=api_key_str,
            endpoint=request.url.path,
            method=request.method,
            ip_address=client_ip,
            status_code=status_code,
            response_time_ms=response_time_ms,
            error_message=error_message,
            request_params=json.dumps(params, ensure_ascii=False) if params else None
        )
        db.add(call_log)
        db.commit()
    except Exception as e:
        logger.error(f"记录 API 调用日志失败: {e}")


def get_recent_failed_calls(db: Session, api_key_id: int, hours: int = 24) -> int:
    """获取最近失败调用次数"""
    since = datetime.utcnow() - timedelta(hours=hours)
    return db.query(APIKeyCallLog).filter(
        and_(
            APIKeyCallLog.api_key_id == api_key_id,
            APIKeyCallLog.status_code >= 400,
            APIKeyCallLog.created_at >= since
        )
    ).count()


def get_risk_status(db: Session, api_key: APIKey) -> Optional[str]:
    """获取风险状态"""
    if not api_key.is_enabled:
        return "disabled"

    if is_expired(api_key):
        return "expired"

    if api_key.expires_at and (api_key.expires_at - datetime.utcnow()).days <= 7:
        return "expiring_soon"

    failed_count = get_recent_failed_calls(db, api_key.id)
    if failed_count >= 10:
        return "high_risk"
    elif failed_count >= 5:
        return "medium_risk"

    if not api_key.last_used_at:
        return "inactive"

    return None


def cleanup_expired_rate_limits():
    """清理过期的频率限制记录"""
    now = time.time()
    expired_keys = []
    for key, store in rate_limit_store.items():
        if now - store["start_time"] > 86400:
            expired_keys.append(key)
    for key in expired_keys:
        del rate_limit_store[key]
