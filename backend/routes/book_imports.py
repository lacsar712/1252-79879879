# -*- coding: utf-8 -*-
"""
图书导入路由
"""
import logging
import csv
import io
import uuid
import os
from typing import Optional, List, Dict, Tuple
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.orm import Session
from collections import defaultdict

from database import get_db
from models import Book, User, BookImportRecord, BookImportItem
from schemas import (
    BookImportUploadResponse,
    BookImportPreviewRequest,
    BookImportPreviewResponse,
    BookImportPreviewRow,
    BookImportFieldMapping,
    BookImportConfirmRequest,
    BookImportProgressResponse,
    BookImportResultResponse,
    BookImportRecordResponse,
    BookImportRecordDetailResponse,
    BookImportRecordListResponse,
    BookImportItemResponse,
    BookResponse
)
from auth import get_current_admin_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/books/import", tags=["图书导入"])

UPLOAD_DIR = "temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

BOOK_FIELDS = {
    "title": {"label": "书名", "required": True, "type": "string", "max_length": 200},
    "author": {"label": "作者", "required": True, "type": "string", "max_length": 100},
    "publisher": {"label": "出版社", "required": False, "type": "string", "max_length": 100},
    "isbn": {"label": "ISBN", "required": False, "type": "string", "max_length": 20},
    "price": {"label": "价格", "required": True, "type": "float", "min_value": 0},
    "stock": {"label": "库存", "required": False, "type": "integer", "min_value": 0},
    "description": {"label": "描述", "required": False, "type": "text"},
    "cover_image": {"label": "封面图片", "required": False, "type": "string", "max_length": 500},
    "category": {"label": "分类", "required": False, "type": "string", "max_length": 50},
}

uploaded_files: Dict[str, Dict] = {}


def generate_import_no() -> str:
    """生成导入单号"""
    return f"IMP{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6].upper()}"


def parse_csv_content(content: str) -> Tuple[List[str], List[List[str]]]:
    """解析CSV内容"""
    reader = csv.reader(io.StringIO(content))
    rows = list(reader)
    if not rows:
        return [], []
    columns = [col.strip() for col in rows[0]]
    data_rows = rows[1:]
    return columns, data_rows


def validate_isbn(isbn: str, db: Session, existing_isbns: set) -> List[str]:
    """校验ISBN"""
    errors = []
    if not isbn:
        return errors
    isbn_clean = isbn.strip().replace("-", "")
    if len(isbn_clean) not in (10, 13):
        errors.append(f"ISBN格式不正确，应为10或13位数字")
    if isbn_clean in existing_isbns:
        errors.append(f"ISBN已存在于当前导入文件中")
    existing_book = db.query(Book).filter(Book.isbn == isbn_clean).first()
    if existing_book:
        errors.append(f"ISBN已存在于数据库中")
    return errors


def validate_book_data(row_data: Dict, db: Session, existing_isbns: set, categories: set, publishers: set) -> Tuple[List[str], List[str]]:
    """校验单行图书数据"""
    errors = []
    warnings = []

    for field_name, field_config in BOOK_FIELDS.items():
        value = row_data.get(field_name)
        
        if field_config["required"] and (value is None or str(value).strip() == ""):
            errors.append(f"{field_config['label']}不能为空")
            continue

        if value is None or str(value).strip() == "":
            continue

        value_str = str(value).strip()

        if field_config["type"] == "string" and "max_length" in field_config:
            if len(value_str) > field_config["max_length"]:
                errors.append(f"{field_config['label']}长度不能超过{field_config['max_length']}字符")

        if field_config["type"] == "float":
            try:
                float_val = float(value_str)
                if "min_value" in field_config and float_val <= field_config["min_value"]:
                    errors.append(f"{field_config['label']}必须大于{field_config['min_value']}")
            except (ValueError, TypeError):
                errors.append(f"{field_config['label']}格式不正确，应为数字")

        if field_config["type"] == "integer":
            try:
                int_val = int(float(value_str))
                if "min_value" in field_config and int_val < field_config["min_value"]:
                    errors.append(f"{field_config['label']}不能小于{field_config['min_value']}")
            except (ValueError, TypeError):
                errors.append(f"{field_config['label']}格式不正确，应为整数")

        if field_name == "isbn":
            isbn_errors = validate_isbn(value_str, db, existing_isbns)
            errors.extend(isbn_errors)

        if field_name == "category" and value_str not in categories:
            warnings.append(f"分类「{value_str}」为新分类，导入时将自动创建")

        if field_name == "publisher" and value_str not in publishers:
            warnings.append(f"出版社「{value_str}」为新出版社，导入时将自动创建")

    return errors, warnings


def map_row_to_book_data(row: List[str], columns: List[str], field_mappings: List[BookImportFieldMapping]) -> Dict:
    """将CSV行映射到图书字段"""
    mapping_dict = {m.csv_column: m.target_field for m in field_mappings if m.target_field}
    book_data = {}
    
    for col_idx, col_name in enumerate(columns):
        target_field = mapping_dict.get(col_name)
        if target_field and col_idx < len(row):
            value = row[col_idx].strip() if row[col_idx] else None
            book_data[target_field] = value
    
    return book_data


@router.post("/upload", response_model=BookImportUploadResponse)
async def upload_csv_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_admin_user)
):
    """上传CSV文件"""
    if not file.filename or not file.filename.lower().endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请上传CSV格式的文件"
        )

    content = await file.read()
    try:
        content_str = content.decode('utf-8-sig')
    except UnicodeDecodeError:
        try:
            content_str = content.decode('gbk')
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="文件编码不正确，请使用UTF-8或GBK编码"
            )

    columns, data_rows = parse_csv_content(content_str)
    
    if not columns:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV文件内容为空"
        )

    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}.csv")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content_str)

    uploaded_files[file_id] = {
        "file_name": file.filename,
        "file_size": len(content),
        "file_path": file_path,
        "columns": columns,
        "data_rows": data_rows,
        "created_by": current_user.id,
        "created_at": datetime.now()
    }

    logger.info(f"文件上传成功: {file.filename} (by {current_user.username})")

    return BookImportUploadResponse(
        file_id=file_id,
        file_name=file.filename,
        file_size=len(content),
        columns=columns,
        total_rows=len(data_rows)
    )


@router.post("/preview", response_model=BookImportPreviewResponse)
def preview_import_data(
    request: BookImportPreviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """预览导入数据并进行校验"""
    file_info = uploaded_files.get(request.file_id)
    if not file_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文件不存在或已过期，请重新上传"
        )

    columns = file_info["columns"]
    data_rows = file_info["data_rows"]

    categories = set()
    publishers = set()
    existing_books = db.query(Book).all()
    for book in existing_books:
        if book.category:
            categories.add(book.category)
        if book.publisher:
            publishers.add(book.publisher)

    existing_isbns = set()
    preview_rows: List[BookImportPreviewRow] = []
    error_count = 0
    warning_count = 0

    for row_idx, row in enumerate(data_rows[:100]):
        row_number = row_idx + 1
        book_data = map_row_to_book_data(row, columns, request.field_mappings)
        
        isbn = book_data.get("isbn", "").strip()
        if isbn:
            isbn = isbn.replace("-", "")
        
        errors, warnings = validate_book_data(book_data, db, existing_isbns, categories, publishers)
        
        if isbn:
            existing_isbns.add(isbn)

        has_errors = len(errors) > 0
        if has_errors:
            error_count += 1
        if len(warnings) > 0:
            warning_count += 1

        preview_row = BookImportPreviewRow(
            row_number=row_number,
            title=book_data.get("title"),
            author=book_data.get("author"),
            publisher=book_data.get("publisher"),
            isbn=isbn if isbn else book_data.get("isbn"),
            price=float(book_data["price"]) if book_data.get("price") and book_data["price"].strip() else None,
            stock=int(float(book_data["stock"])) if book_data.get("stock") and book_data["stock"].strip() else None,
            description=book_data.get("description"),
            cover_image=book_data.get("cover_image"),
            category=book_data.get("category"),
            errors=errors,
            warnings=warnings,
            is_skipped=False
        )
        preview_rows.append(preview_row)

    return BookImportPreviewResponse(
        file_id=request.file_id,
        file_name=file_info["file_name"],
        total_rows=len(data_rows),
        columns=columns,
        field_mappings=request.field_mappings,
        preview_rows=preview_rows,
        has_errors=error_count > 0,
        error_count=error_count,
        warning_count=warning_count
    )


@router.post("/confirm", response_model=BookImportProgressResponse)
def confirm_import(
    request: BookImportConfirmRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """确认导入"""
    file_info = uploaded_files.get(request.file_id)
    if not file_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文件不存在或已过期，请重新上传"
        )

    columns = file_info["columns"]
    data_rows = file_info["data_rows"]

    import_no = generate_import_no()
    
    import_record = BookImportRecord(
        import_no=import_no,
        file_name=file_info["file_name"],
        file_size=file_info["file_size"],
        total_rows=len(data_rows),
        status="processing",
        created_by=current_user.id,
        created_at=datetime.now()
    )
    db.add(import_record)
    db.flush()

    categories = set()
    publishers = set()
    existing_books = db.query(Book).all()
    existing_isbns_db = set()
    for book in existing_books:
        if book.category:
            categories.add(book.category)
        if book.publisher:
            publishers.add(book.publisher)
        if book.isbn:
            existing_isbns_db.add(book.isbn.replace("-", ""))

    skipped_rows_set = set(request.skipped_rows)
    row_updates_dict = {u.row_number: u for u in request.row_updates}

    success_count = 0
    failed_count = 0
    skipped_count = 0
    existing_isbns_file = set()
    error_messages = []

    for row_idx, row in enumerate(data_rows):
        row_number = row_idx + 1
        book_data = map_row_to_book_data(row, columns, request.field_mappings)

        if row_number in row_updates_dict:
            update = row_updates_dict[row_number]
            update_dict = update.model_dump(exclude_unset=True)
            for key, value in update_dict.items():
                if key != "row_number" and key != "is_skipped":
                    book_data[key] = value
            if update.is_skipped is not None:
                if update.is_skipped:
                    skipped_rows_set.add(row_number)
                else:
                    skipped_rows_set.discard(row_number)

        import_item = BookImportItem(
            import_record_id=import_record.id,
            row_number=row_number,
            title=book_data.get("title"),
            author=book_data.get("author"),
            publisher=book_data.get("publisher"),
            isbn=book_data.get("isbn"),
            price=float(book_data["price"]) if book_data.get("price") and str(book_data["price"]).strip() else None,
            stock=int(float(book_data["stock"])) if book_data.get("stock") and str(book_data["stock"]).strip() else 0,
            description=book_data.get("description"),
            cover_image=book_data.get("cover_image"),
            category=book_data.get("category"),
            status="pending"
        )

        if row_number in skipped_rows_set:
            import_item.status = "skipped"
            skipped_count += 1
            db.add(import_item)
            continue

        errors, warnings = validate_book_data(book_data, db, existing_isbns_file, categories, publishers)

        isbn = book_data.get("isbn", "").strip()
        if isbn:
            isbn_clean = isbn.replace("-", "")
            book_data["isbn"] = isbn_clean
            import_item.isbn = isbn_clean
            existing_isbns_file.add(isbn_clean)

        if errors:
            import_item.status = "failed"
            import_item.error_message = "; ".join(errors)
            failed_count += 1
            error_messages.append(f"第{row_number}行: {'; '.join(errors)}")
            db.add(import_item)
            continue

        try:
            db_book = Book(
                title=book_data.get("title", ""),
                author=book_data.get("author", ""),
                publisher=book_data.get("publisher"),
                isbn=book_data.get("isbn"),
                price=float(book_data.get("price", 0)),
                stock=int(float(book_data.get("stock", 0))) if book_data.get("stock") else 0,
                description=book_data.get("description"),
                cover_image=book_data.get("cover_image"),
                category=book_data.get("category")
            )
            db.add(db_book)
            db.flush()

            import_item.status = "success"
            import_item.book_id = db_book.id
            success_count += 1

            if book_data.get("category"):
                categories.add(book_data["category"])
            if book_data.get("publisher"):
                publishers.add(book_data["publisher"])

        except Exception as e:
            import_item.status = "failed"
            import_item.error_message = str(e)
            failed_count += 1
            error_messages.append(f"第{row_number}行: {str(e)}")

        db.add(import_item)

    import_record.success_count = success_count
    import_record.failed_count = failed_count
    import_record.skipped_count = skipped_count
    import_record.status = "completed"
    import_record.completed_at = datetime.now()
    import_record.error_summary = "\n".join(error_messages[:10]) if error_messages else None

    db.commit()
    db.refresh(import_record)

    if request.file_id in uploaded_files:
        file_path = uploaded_files[request.file_id]["file_path"]
        if os.path.exists(file_path):
            os.remove(file_path)
        del uploaded_files[request.file_id]

    logger.info(f"导入完成: {import_no} - 成功{success_count}条, 失败{failed_count}条, 跳过{skipped_count}条 (by {current_user.username})")

    return BookImportProgressResponse(
        import_record_id=import_record.id,
        import_no=import_no,
        status=import_record.status,
        total_rows=import_record.total_rows,
        processed_rows=success_count + failed_count + skipped_count,
        success_count=success_count,
        failed_count=failed_count,
        skipped_count=skipped_count,
        progress_percent=100.0
    )


@router.get("/progress/{import_record_id}", response_model=BookImportProgressResponse)
def get_import_progress(
    import_record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """获取导入进度"""
    import_record = db.query(BookImportRecord).filter(BookImportRecord.id == import_record_id).first()
    if not import_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="导入记录不存在"
        )

    processed = import_record.success_count + import_record.failed_count + import_record.skipped_count
    progress = (processed / import_record.total_rows * 100) if import_record.total_rows > 0 else 0

    return BookImportProgressResponse(
        import_record_id=import_record.id,
        import_no=import_record.import_no,
        status=import_record.status,
        total_rows=import_record.total_rows,
        processed_rows=processed,
        success_count=import_record.success_count,
        failed_count=import_record.failed_count,
        skipped_count=import_record.skipped_count,
        progress_percent=round(progress, 2)
    )


@router.get("/records", response_model=BookImportRecordListResponse)
def get_import_records(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="状态筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索（文件名/导入单号）"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """获取导入记录列表"""
    query = db.query(BookImportRecord)

    if status:
        query = query.filter(BookImportRecord.status == status)

    if keyword:
        search_pattern = f"%{keyword}%"
        query = query.filter(
            (BookImportRecord.file_name.like(search_pattern)) |
            (BookImportRecord.import_no.like(search_pattern))
        )

    total = query.count()
    offset = (page - 1) * page_size
    records = query.order_by(BookImportRecord.created_at.desc()).offset(offset).limit(page_size).all()

    user_ids = [r.created_by for r in records]
    users = db.query(User).filter(User.id.in_(user_ids)).all()
    user_map = {u.id: u.username for u in users}

    record_responses = []
    for record in records:
        resp = BookImportRecordResponse.model_validate(record)
        resp.created_by_name = user_map.get(record.created_by)
        record_responses.append(resp)

    return BookImportRecordListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=record_responses
    )


@router.get("/records/{import_record_id}", response_model=BookImportRecordDetailResponse)
def get_import_record_detail(
    import_record_id: int,
    status_filter: Optional[str] = Query(None, description="明细状态筛选"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """获取导入记录详情"""
    import_record = db.query(BookImportRecord).filter(BookImportRecord.id == import_record_id).first()
    if not import_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="导入记录不存在"
        )

    items_query = db.query(BookImportItem).filter(BookImportItem.import_record_id == import_record_id)
    if status_filter:
        items_query = items_query.filter(BookImportItem.status == status_filter)
    items = items_query.order_by(BookImportItem.row_number).all()

    book_ids = [item.book_id for item in items if item.book_id]
    books = db.query(Book).filter(Book.id.in_(book_ids)).all()
    book_map = {b.id: BookResponse.model_validate(b) for b in books}

    user = db.query(User).filter(User.id == import_record.created_by).first()

    item_responses = []
    for item in items:
        resp = BookImportItemResponse.model_validate(item)
        if item.book_id and item.book_id in book_map:
            resp.book = book_map[item.book_id]
        item_responses.append(resp)

    detail_resp = BookImportRecordDetailResponse.model_validate(import_record)
    detail_resp.created_by_name = user.username if user else None
    detail_resp.items = item_responses

    return detail_resp


@router.get("/fields", response_model=list)
def get_import_fields(
    current_user: User = Depends(get_current_admin_user)
):
    """获取可导入的字段列表"""
    fields = []
    for field_name, field_config in BOOK_FIELDS.items():
        fields.append({
            "field": field_name,
            "label": field_config["label"],
            "required": field_config["required"],
            "type": field_config["type"]
        })
    return fields
