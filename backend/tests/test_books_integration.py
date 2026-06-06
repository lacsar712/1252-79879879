# -*- coding: utf-8 -*-
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient


class TestBooksIntegration:

    def test_get_books_default_returns_200(self, client: TestClient):
        response = client.get("/api/books")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "items" in data
        assert data["total"] == 12
        assert data["page"] == 1
        assert data["page_size"] == 10

    def test_get_books_pagination_first_page(self, client: TestClient):
        response = client.get("/api/books", params={"page": 1, "page_size": 3})
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 3
        assert len(data["items"]) == 3
        assert data["total"] == 12

    def test_get_books_pagination_second_page(self, client: TestClient):
        response1 = client.get("/api/books", params={"page": 1, "page_size": 3})
        response2 = client.get("/api/books", params={"page": 2, "page_size": 3})
        assert response1.status_code == 200
        assert response2.status_code == 200
        ids1 = {b["id"] for b in response1.json()["items"]}
        ids2 = {b["id"] for b in response2.json()["items"]}
        assert len(ids1 & ids2) == 0

    def test_get_books_pagination_boundary_last_page(self, client: TestClient):
        response = client.get("/api/books", params={"page": 2, "page_size": 10})
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert len(data["items"]) == 2
        assert data["total"] == 12

    def test_get_books_pagination_boundary_beyond_total(self, client: TestClient):
        response = client.get("/api/books", params={"page": 10, "page_size": 10})
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 0
        assert data["total"] == 12

    def test_get_books_pagination_boundary_page_one_minimum(self, client: TestClient):
        response = client.get("/api/books", params={"page": 1, "page_size": 1})
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1

    def test_get_books_pagination_boundary_page_size_max(self, client: TestClient):
        response = client.get("/api/books", params={"page": 1, "page_size": 100})
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 12

    def test_get_books_invalid_page_zero_returns_422(self, client: TestClient):
        response = client.get("/api/books", params={"page": 0, "page_size": 10})
        assert response.status_code == 422

    def test_get_books_invalid_page_negative_returns_422(self, client: TestClient):
        response = client.get("/api/books", params={"page": -1, "page_size": 10})
        assert response.status_code == 422

    def test_get_books_invalid_page_size_zero_returns_422(self, client: TestClient):
        response = client.get("/api/books", params={"page": 1, "page_size": 0})
        assert response.status_code == 422

    def test_get_books_invalid_page_size_negative_returns_422(self, client: TestClient):
        response = client.get("/api/books", params={"page": 1, "page_size": -5})
        assert response.status_code == 422

    def test_get_books_invalid_page_size_exceeds_max_returns_422(self, client: TestClient):
        response = client.get("/api/books", params={"page": 1, "page_size": 101})
        assert response.status_code == 422

    def test_get_books_invalid_page_type_string_returns_422(self, client: TestClient):
        response = client.get("/api/books", params={"page": "abc", "page_size": 10})
        assert response.status_code == 422

    def test_get_books_invalid_page_size_type_string_returns_422(self, client: TestClient):
        response = client.get("/api/books", params={"page": 1, "page_size": "xyz"})
        assert response.status_code == 422

    def test_get_books_search_by_title(self, client: TestClient):
        response = client.get("/api/books", params={"search": "Python"})
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        for book in data["items"]:
            assert "Python" in book["title"]

    def test_get_books_search_by_author(self, client: TestClient):
        response = client.get("/api/books", params={"search": "Eric Matthes"})
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["author"] == "Eric Matthes"

    def test_get_books_search_by_publisher(self, client: TestClient):
        response = client.get("/api/books", params={"search": "机械工业出版社", "page_size": 20})
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 4
        for book in data["items"]:
            assert book["publisher"] == "机械工业出版社"

    def test_get_books_search_no_results(self, client: TestClient):
        response = client.get("/api/books", params={"search": "不存在的图书关键词999"})
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["items"]) == 0

    def test_get_books_search_partial_match(self, client: TestClient):
        response = client.get("/api/books", params={"search": "设计", "page_size": 20})
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 2
        for book in data["items"]:
            haystack = f"{book['title']} {book['author']} {book.get('publisher', '')}"
            assert "设计" in haystack

    def test_get_books_category_filter_programming(self, client: TestClient):
        response = client.get("/api/books", params={"category": "编程技术", "page_size": 20})
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 4
        for book in data["items"]:
            assert book["category"] == "编程技术"

    def test_get_books_category_filter_database(self, client: TestClient):
        response = client.get("/api/books", params={"category": "数据库", "page_size": 20})
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        for book in data["items"]:
            assert book["category"] == "数据库"

    def test_get_books_category_filter_no_results(self, client: TestClient):
        response = client.get("/api/books", params={"category": "不存在分类"})
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["items"]) == 0

    def test_get_books_search_and_category_combined(self, client: TestClient):
        response = client.get("/api/books", params={"search": "Python", "category": "编程技术", "page_size": 20})
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        for book in data["items"]:
            assert book["category"] == "编程技术"
            assert "Python" in book["title"]

    def test_get_books_search_and_category_no_overlap(self, client: TestClient):
        response = client.get("/api/books", params={"search": "Python", "category": "数据库"})
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0

    def test_get_books_sort_by_price_asc(self, client: TestClient):
        response = client.get("/api/books", params={"sort_by": "price", "sort_order": "asc", "page_size": 20})
        assert response.status_code == 200
        data = response.json()
        prices = [b["price"] for b in data["items"]]
        assert prices == sorted(prices)
        assert prices[0] == 39.00
        assert prices[-1] == 139.00

    def test_get_books_sort_by_price_desc(self, client: TestClient):
        response = client.get("/api/books", params={"sort_by": "price", "sort_order": "desc", "page_size": 20})
        assert response.status_code == 200
        data = response.json()
        prices = [b["price"] for b in data["items"]]
        assert prices == sorted(prices, reverse=True)
        assert prices[0] == 139.00
        assert prices[-1] == 39.00

    def test_get_books_sort_by_price_case_insensitive_order(self, client: TestClient):
        response = client.get("/api/books", params={"sort_by": "price", "sort_order": "DESC", "page_size": 20})
        assert response.status_code == 200
        data = response.json()
        prices = [b["price"] for b in data["items"]]
        assert prices == sorted(prices, reverse=True)

    def test_get_books_sort_by_invalid_field_defaults_to_created_at(self, client: TestClient):
        response_default = client.get("/api/books", params={"page_size": 20})
        response_invalid = client.get("/api/books", params={"sort_by": "invalid_field", "page_size": 20})
        assert response_default.status_code == 200
        assert response_invalid.status_code == 200
        ids_default = [b["id"] for b in response_default.json()["items"]]
        ids_invalid = [b["id"] for b in response_invalid.json()["items"]]
        assert ids_default == ids_invalid

    def test_get_books_no_results_empty_items_structure(self, client: TestClient):
        response = client.get("/api/books", params={"search": "完全不存在的结果"})
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []
        assert data["page"] == 1
        assert data["page_size"] == 10

    def test_get_books_duplicate_category_consistency_multiple_calls(self, client: TestClient):
        for _ in range(5):
            response = client.get("/api/books", params={"category": "编程技术", "sort_by": "price", "sort_order": "asc", "page_size": 20})
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 4
            prices = [b["price"] for b in data["items"]]
            assert prices == sorted(prices)

    def test_get_books_duplicate_category_count_across_categories(self, client: TestClient):
        categories = ["编程技术", "计算机基础", "软件工程", "前端开发", "数据库"]
        expected = [4, 2, 2, 2, 2]
        for cat, exp_count in zip(categories, expected):
            response = client.get("/api/books", params={"category": cat, "page_size": 100})
            assert response.status_code == 200
            assert response.json()["total"] == exp_count, f"分类 {cat} 数量不匹配"

    def test_get_books_duplicate_category_idempotent_response(self, client: TestClient):
        r1 = client.get("/api/books", params={"category": "编程技术", "sort_by": "price", "sort_order": "asc", "page_size": 100})
        r2 = client.get("/api/books", params={"category": "编程技术", "sort_by": "price", "sort_order": "asc", "page_size": 100})
        assert r1.json() == r2.json()

    def test_get_books_response_item_structure(self, client: TestClient):
        response = client.get("/api/books", params={"page_size": 1})
        assert response.status_code == 200
        book = response.json()["items"][0]
        required_fields = {"id", "title", "author", "price", "stock", "category", "created_at", "updated_at"}
        assert required_fields.issubset(set(book.keys()))

    def test_get_books_default_sort_newest_first(self, client: TestClient):
        response = client.get("/api/books", params={"page_size": 20})
        assert response.status_code == 200
        data = response.json()
        created_ats = [b["created_at"] for b in data["items"]]
        assert created_ats == sorted(created_ats, reverse=True)
