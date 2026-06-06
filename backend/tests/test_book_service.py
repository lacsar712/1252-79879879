# -*- coding: utf-8 -*-
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from sqlalchemy.orm import Session
from fastapi import HTTPException

from models import Book, User
from services.book_service import (
    apply_search_filter,
    apply_category_filter,
    apply_sorting,
    apply_pagination,
    build_query,
    get_books_list,
    validate_admin_permission,
    get_categories_list
)
from schemas import BookListResponse


class TestApplySearchFilter:

    def test_none_search_returns_unchanged_query(self, db_session: Session):
        base_query = db_session.query(Book)
        result = apply_search_filter(base_query, None)
        assert result is base_query

    def test_empty_string_search_returns_unchanged_query(self, seeded_db: Session):
        base_query = seeded_db.query(Book)
        result = apply_search_filter(base_query, "")
        assert result.count() == 12

    def test_search_by_title(self, seeded_db: Session):
        query = seeded_db.query(Book)
        result = apply_search_filter(query, "Python")
        assert result.count() == 3
        for book in result.all():
            assert "Python" in book.title

    def test_search_by_author(self, seeded_db: Session):
        query = seeded_db.query(Book)
        result = apply_search_filter(query, "Eric Matthes")
        assert result.count() == 1
        assert result.first().author == "Eric Matthes"

    def test_search_by_publisher(self, seeded_db: Session):
        query = seeded_db.query(Book)
        result = apply_search_filter(query, "机械工业出版社")
        count = result.count()
        assert count >= 4
        for book in result.all():
            assert book.publisher == "机械工业出版社"

    def test_search_no_results(self, seeded_db: Session):
        query = seeded_db.query(Book)
        result = apply_search_filter(query, "不存在的关键词xyz123")
        assert result.count() == 0

    def test_search_partial_match(self, seeded_db: Session):
        query = seeded_db.query(Book)
        result = apply_search_filter(query, "设计")
        count = result.count()
        assert count >= 2
        for book in result.all():
            haystack = f"{book.title} {book.author} {book.publisher or ''}"
            assert "设计" in haystack


class TestApplyCategoryFilter:

    def test_none_category_returns_unchanged_query(self, db_session: Session):
        base_query = db_session.query(Book)
        result = apply_category_filter(base_query, None)
        assert result is base_query

    def test_empty_string_category_returns_unchanged_query(self, seeded_db: Session):
        query = seeded_db.query(Book)
        result = apply_category_filter(query, "")
        assert result.count() == 12

    def test_category_programming(self, seeded_db: Session):
        query = seeded_db.query(Book)
        result = apply_category_filter(query, "编程技术")
        assert result.count() == 4
        for book in result.all():
            assert book.category == "编程技术"

    def test_category_frontend(self, seeded_db: Session):
        query = seeded_db.query(Book)
        result = apply_category_filter(query, "前端开发")
        assert result.count() == 2
        for book in result.all():
            assert book.category == "前端开发"

    def test_category_no_results(self, seeded_db: Session):
        query = seeded_db.query(Book)
        result = apply_category_filter(query, "不存在的分类")
        assert result.count() == 0

    def test_all_categories_count(self, seeded_db: Session):
        category_counts = {}
        for cat in ["编程技术", "计算机基础", "软件工程", "前端开发", "数据库"]:
            query = seeded_db.query(Book)
            result = apply_category_filter(query, cat)
            category_counts[cat] = result.count()
        assert category_counts["编程技术"] == 4
        assert category_counts["计算机基础"] == 2
        assert category_counts["软件工程"] == 2
        assert category_counts["前端开发"] == 2
        assert category_counts["数据库"] == 2
        assert sum(category_counts.values()) == 12


class TestApplySorting:

    def test_sort_by_price_asc(self, seeded_db: Session):
        query = seeded_db.query(Book)
        result = apply_sorting(query, "price", "asc")
        prices = [b.price for b in result.all()]
        assert prices == sorted(prices)

    def test_sort_by_price_desc(self, seeded_db: Session):
        query = seeded_db.query(Book)
        result = apply_sorting(query, "price", "desc")
        prices = [b.price for b in result.all()]
        assert prices == sorted(prices, reverse=True)

    def test_sort_by_price_case_insensitive_desc(self, seeded_db: Session):
        query = seeded_db.query(Book)
        result = apply_sorting(query, "price", "DESC")
        prices = [b.price for b in result.all()]
        assert prices == sorted(prices, reverse=True)

    def test_sort_by_price_invalid_order_defaults_asc(self, seeded_db: Session):
        query = seeded_db.query(Book)
        result = apply_sorting(query, "price", "invalid")
        prices = [b.price for b in result.all()]
        assert prices == sorted(prices)

    def test_default_sort_is_created_at_desc(self, seeded_db: Session):
        query = seeded_db.query(Book)
        result = apply_sorting(query, None, "asc")
        created_ats = [b.created_at for b in result.all()]
        assert created_ats == sorted(created_ats, reverse=True)

    def test_unknown_sort_field_falls_back_to_created_at(self, seeded_db: Session):
        query1 = seeded_db.query(Book)
        query2 = seeded_db.query(Book)
        result_default = apply_sorting(query1, None, "asc")
        result_other = apply_sorting(query2, "unknown", "asc")
        ids_default = [b.id for b in result_default.all()]
        ids_other = [b.id for b in result_other.all()]
        assert ids_default == ids_other


class TestApplyPagination:

    def test_first_page(self, seeded_db: Session):
        query = seeded_db.query(Book)
        books, total = apply_pagination(query, 1, 5)
        assert total == 12
        assert len(books) == 5

    def test_second_page_offset_correct(self, seeded_db: Session):
        query = seeded_db.query(Book)
        books1, _ = apply_pagination(query, 1, 5)
        books2, _ = apply_pagination(seeded_db.query(Book), 2, 5)
        ids1 = {b.id for b in books1}
        ids2 = {b.id for b in books2}
        assert len(ids1 & ids2) == 0
        assert len(books2) == 5

    def test_page_exceeding_total_returns_empty(self, seeded_db: Session):
        query = seeded_db.query(Book)
        books, total = apply_pagination(query, 100, 10)
        assert total == 12
        assert len(books) == 0

    def test_page_size_max(self, seeded_db: Session):
        query = seeded_db.query(Book)
        books, total = apply_pagination(query, 1, 100)
        assert total == 12
        assert len(books) == 12

    def test_empty_query(self, db_session: Session):
        query = db_session.query(Book)
        books, total = apply_pagination(query, 1, 10)
        assert total == 0
        assert len(books) == 0


class TestBuildQuery:

    def test_build_query_default(self, seeded_db: Session):
        query = build_query(seeded_db)
        assert query.count() == 12

    def test_build_query_with_search(self, seeded_db: Session):
        query = build_query(seeded_db, search="Python")
        assert query.count() == 3

    def test_build_query_with_category(self, seeded_db: Session):
        query = build_query(seeded_db, category="编程技术")
        assert query.count() == 4

    def test_build_query_with_search_and_category(self, seeded_db: Session):
        query = build_query(seeded_db, search="Python", category="编程技术")
        assert query.count() == 3

    def test_build_query_with_search_and_category_no_match(self, seeded_db: Session):
        query = build_query(seeded_db, search="Python", category="数据库")
        assert query.count() == 0

    def test_build_query_with_sort(self, seeded_db: Session):
        query = build_query(seeded_db, sort_by="price", sort_order="asc")
        prices = [b.price for b in query.all()]
        assert prices == sorted(prices)


class TestGetBooksList:

    def test_returns_book_list_response(self, seeded_db: Session):
        result = get_books_list(seeded_db, page=1, page_size=5)
        assert isinstance(result, BookListResponse)

    def test_default_pagination(self, seeded_db: Session):
        result = get_books_list(seeded_db, page=1, page_size=5)
        assert result.page == 1
        assert result.page_size == 5
        assert result.total == 12
        assert len(result.items) == 5

    def test_search_by_title(self, seeded_db: Session):
        result = get_books_list(seeded_db, page=1, page_size=20, search="Python")
        assert result.total == 3
        for b in result.items:
            assert "Python" in b.title

    def test_category_filter(self, seeded_db: Session):
        result = get_books_list(seeded_db, page=1, page_size=20, category="编程技术")
        assert result.total == 4
        for b in result.items:
            assert b.category == "编程技术"

    def test_sort_by_price_desc(self, seeded_db: Session):
        result = get_books_list(seeded_db, page=1, page_size=20, sort_by="price", sort_order="desc")
        prices = [b.price for b in result.items]
        assert prices == sorted(prices, reverse=True)

    def test_combined_filters(self, seeded_db: Session):
        result = get_books_list(
            seeded_db,
            page=1,
            page_size=20,
            search="Python",
            category="编程技术",
            sort_by="price",
            sort_order="asc"
        )
        assert result.total == 3
        for b in result.items:
            assert "Python" in b.title
            assert b.category == "编程技术"
        prices = [b.price for b in result.items]
        assert prices == sorted(prices)

    def test_empty_database(self, db_session: Session):
        result = get_books_list(db_session, page=1, page_size=10)
        assert result.total == 0
        assert len(result.items) == 0
        assert result.page == 1
        assert result.page_size == 10

    def test_response_schema_fields(self, seeded_db: Session):
        result = get_books_list(seeded_db, page=1, page_size=5)
        book = result.items[0]
        assert hasattr(book, "id")
        assert hasattr(book, "title")
        assert hasattr(book, "author")
        assert hasattr(book, "price")
        assert hasattr(book, "category")
        assert hasattr(book, "created_at")

    def test_idempotent_multiple_calls(self, seeded_db: Session):
        for _ in range(5):
            result = get_books_list(
                seeded_db,
                page=1,
                page_size=20,
                category="编程技术",
                sort_by="price",
                sort_order="asc"
            )
            assert result.total == 4
            prices = [b.price for b in result.items]
            assert prices == sorted(prices)


class TestValidateAdminPermission:

    def test_admin_user_passes(self):
        user = User(username="admin", is_admin=True)
        validate_admin_permission(user)

    def test_non_admin_raises_403(self):
        user = User(username="user", is_admin=False)
        with pytest.raises(HTTPException) as exc_info:
            validate_admin_permission(user)
        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "需要管理员权限"


class TestGetCategoriesList:

    def test_returns_all_categories(self, seeded_db: Session):
        categories = get_categories_list(seeded_db)
        assert isinstance(categories, list)
        assert len(categories) == 5
        assert "编程技术" in categories
        assert "计算机基础" in categories
        assert "软件工程" in categories
        assert "前端开发" in categories
        assert "数据库" in categories

    def test_empty_database_returns_empty_list(self, db_session: Session):
        categories = get_categories_list(db_session)
        assert categories == []

    def test_filters_none_and_empty(self, db_session: Session):
        db_session.add(Book(title="Test", author="Test", price=10.0, category=None))
        db_session.add(Book(title="Test2", author="Test2", price=10.0, category=""))
        db_session.add(Book(title="Test3", author="Test3", price=10.0, category="有效分类"))
        db_session.commit()
        categories = get_categories_list(db_session)
        assert categories == ["有效分类"]
        assert None not in categories
        assert "" not in categories
