# -*- coding: utf-8 -*-
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc

from models import Book
from routes.books import get_books
from schemas import BookListResponse


class TestGetBooksUnit:

    def test_default_pagination_returns_first_page(self, seeded_db: Session):
        result = get_books(page=1, page_size=5, search=None, category=None, sort_by=None, sort_order="asc", db=seeded_db)
        assert isinstance(result, BookListResponse)
        assert result.page == 1
        assert result.page_size == 5
        assert result.total == 12
        assert len(result.items) == 5

    def test_second_page_returns_correct_offset(self, seeded_db: Session):
        result = get_books(page=2, page_size=5, search=None, category=None, sort_by=None, sort_order="asc", db=seeded_db)
        assert len(result.items) == 5
        assert result.page == 2
        all_ids_page1 = [b.id for b in get_books(page=1, page_size=5, search=None, category=None, sort_by=None, sort_order="asc", db=seeded_db).items]
        all_ids_page2 = [b.id for b in result.items]
        assert len(set(all_ids_page1) & set(all_ids_page2)) == 0

    def test_page_exceeding_total_returns_empty(self, seeded_db: Session):
        result = get_books(page=100, page_size=10, search=None, category=None, sort_by=None, sort_order="asc", db=seeded_db)
        assert len(result.items) == 0
        assert result.total == 12

    def test_page_size_max_boundary(self, seeded_db: Session):
        result = get_books(page=1, page_size=100, search=None, category=None, sort_by=None, sort_order="asc", db=seeded_db)
        assert len(result.items) == 12
        assert result.total == 12

    def test_search_by_title(self, seeded_db: Session):
        result = get_books(page=1, page_size=20, search="Python", category=None, sort_by=None, sort_order="asc", db=seeded_db)
        assert result.total == 3
        titles = [b.title for b in result.items]
        for t in titles:
            assert "Python" in t

    def test_search_by_author(self, seeded_db: Session):
        result = get_books(page=1, page_size=20, search="Eric Matthes", category=None, sort_by=None, sort_order="asc", db=seeded_db)
        assert result.total == 1
        assert result.items[0].author == "Eric Matthes"

    def test_search_by_publisher(self, seeded_db: Session):
        result = get_books(page=1, page_size=20, search="机械工业出版社", category=None, sort_by=None, sort_order="asc", db=seeded_db)
        publishers = [b.publisher for b in result.items]
        for p in publishers:
            assert p == "机械工业出版社"
        assert result.total >= 4

    def test_search_no_results(self, seeded_db: Session):
        result = get_books(page=1, page_size=10, search="不存在的关键词xyz123", category=None, sort_by=None, sort_order="asc", db=seeded_db)
        assert result.total == 0
        assert len(result.items) == 0

    def test_search_partial_match(self, seeded_db: Session):
        result = get_books(page=1, page_size=20, search="设计", category=None, sort_by=None, sort_order="asc", db=seeded_db)
        assert result.total >= 2
        for book in result.items:
            haystack = f"{book.title} {book.author} {book.publisher or ''}"
            assert "设计" in haystack

    def test_category_filter_returns_only_matching(self, seeded_db: Session):
        result = get_books(page=1, page_size=20, search=None, category="编程技术", sort_by=None, sort_order="asc", db=seeded_db)
        assert result.total == 4
        for book in result.items:
            assert book.category == "编程技术"

    def test_category_filter_frontend(self, seeded_db: Session):
        result = get_books(page=1, page_size=20, search=None, category="前端开发", sort_by=None, sort_order="asc", db=seeded_db)
        assert result.total == 2
        categories = {b.category for b in result.items}
        assert categories == {"前端开发"}

    def test_category_filter_no_results(self, seeded_db: Session):
        result = get_books(page=1, page_size=10, search=None, category="不存在的分类", sort_by=None, sort_order="asc", db=seeded_db)
        assert result.total == 0
        assert len(result.items) == 0

    def test_search_and_category_combined(self, seeded_db: Session):
        result = get_books(page=1, page_size=20, search="Python", category="编程技术", sort_by=None, sort_order="asc", db=seeded_db)
        assert result.total == 3
        for book in result.items:
            assert book.category == "编程技术"
            assert "Python" in book.title

    def test_search_and_category_no_combined_results(self, seeded_db: Session):
        result = get_books(page=1, page_size=20, search="Python", category="数据库", sort_by=None, sort_order="asc", db=seeded_db)
        assert result.total == 0

    def test_sort_by_price_ascending(self, seeded_db: Session):
        result = get_books(page=1, page_size=20, search=None, category=None, sort_by="price", sort_order="asc", db=seeded_db)
        prices = [b.price for b in result.items]
        assert prices == sorted(prices)
        assert prices[0] == 39.00
        assert prices[-1] == 139.00

    def test_sort_by_price_descending(self, seeded_db: Session):
        result = get_books(page=1, page_size=20, search=None, category=None, sort_by="price", sort_order="desc", db=seeded_db)
        prices = [b.price for b in result.items]
        assert prices == sorted(prices, reverse=True)
        assert prices[0] == 139.00
        assert prices[-1] == 39.00

    def test_sort_by_price_ignores_invalid_order_defaults_asc(self, seeded_db: Session):
        result = get_books(page=1, page_size=20, search=None, category=None, sort_by="price", sort_order="invalid", db=seeded_db)
        prices = [b.price for b in result.items]
        assert prices == sorted(prices)

    def test_default_sort_is_by_created_at_desc(self, seeded_db: Session):
        result = get_books(page=1, page_size=20, search=None, category=None, sort_by=None, sort_order="asc", db=seeded_db)
        created_ats = [b.created_at for b in result.items]
        assert created_ats == sorted(created_ats, reverse=True)

    def test_sort_by_other_field_falls_back_to_created_at(self, seeded_db: Session):
        result_default = get_books(page=1, page_size=20, search=None, category=None, sort_by=None, sort_order="asc", db=seeded_db)
        result_other = get_books(page=1, page_size=20, search=None, category=None, sort_by="unknown", sort_order="asc", db=seeded_db)
        ids_default = [b.id for b in result_default.items]
        ids_other = [b.id for b in result_other.items]
        assert ids_default == ids_other

    def test_duplicate_category_returns_consistent_results(self, seeded_db: Session):
        for _ in range(5):
            result = get_books(page=1, page_size=20, search=None, category="编程技术", sort_by="price", sort_order="asc", db=seeded_db)
            assert result.total == 4
            prices = [b.price for b in result.items]
            assert prices == sorted(prices)

    def test_duplicate_category_count_stability(self, seeded_db: Session):
        category_counts = {}
        for cat in ["编程技术", "计算机基础", "软件工程", "前端开发", "数据库"]:
            result = get_books(page=1, page_size=100, search=None, category=cat, sort_by=None, sort_order="asc", db=seeded_db)
            category_counts[cat] = result.total
        assert category_counts["编程技术"] == 4
        assert category_counts["计算机基础"] == 2
        assert category_counts["软件工程"] == 2
        assert category_counts["前端开发"] == 2
        assert category_counts["数据库"] == 2
        assert sum(category_counts.values()) == 12

    def test_duplicate_category_idempotency(self, seeded_db: Session):
        result1 = get_books(page=1, page_size=100, search=None, category="编程技术", sort_by="price", sort_order="asc", db=seeded_db)
        result2 = get_books(page=1, page_size=100, search=None, category="编程技术", sort_by="price", sort_order="asc", db=seeded_db)
        ids1 = [b.id for b in result1.items]
        ids2 = [b.id for b in result2.items]
        assert ids1 == ids2

    def test_empty_database_returns_zero(self, db_session: Session):
        result = get_books(page=1, page_size=10, search=None, category=None, sort_by=None, sort_order="asc", db=db_session)
        assert result.total == 0
        assert len(result.items) == 0

    def test_response_schema_fields(self, seeded_db: Session):
        result = get_books(page=1, page_size=5, search=None, category=None, sort_by=None, sort_order="asc", db=seeded_db)
        book = result.items[0]
        assert hasattr(book, "id")
        assert hasattr(book, "title")
        assert hasattr(book, "author")
        assert hasattr(book, "price")
        assert hasattr(book, "category")
        assert hasattr(book, "created_at")
