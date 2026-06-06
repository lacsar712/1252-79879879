# -*- coding: utf-8 -*-
import os
import sys
from datetime import datetime, timedelta
from typing import Generator, List

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi.middleware.cors import CORSMiddleware

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Base, Book
from database import get_db
from routes.books import router as books_router


def create_test_app() -> FastAPI:
    app = FastAPI(title="Test Bookstore API")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(books_router)
    return app


def create_test_books(db: Session) -> List[Book]:
    now = datetime.utcnow()
    books = [
        Book(
            id=1,
            title="Python编程：从入门到实践",
            author="Eric Matthes",
            publisher="人民邮电出版社",
            isbn="9787115428021",
            price=89.00,
            stock=50,
            description="Python入门书籍",
            cover_image="/static/images/python.png",
            category="编程技术",
            created_at=now - timedelta(hours=12)
        ),
        Book(
            id=2,
            title="JavaScript高级程序设计",
            author="Nicholas C. Zakas",
            publisher="人民邮电出版社",
            isbn="9787115545382",
            price=129.00,
            stock=35,
            description="JavaScript经典之作",
            cover_image="/static/images/js.png",
            category="编程技术",
            created_at=now - timedelta(hours=10)
        ),
        Book(
            id=3,
            title="深入理解计算机系统",
            author="Randal E. Bryant",
            publisher="机械工业出版社",
            isbn="9787111544933",
            price=139.00,
            stock=20,
            description="计算机系统组成原理",
            cover_image="/static/images/csapp.png",
            category="计算机基础",
            created_at=now - timedelta(hours=8)
        ),
        Book(
            id=4,
            title="算法导论",
            author="Thomas H. Cormen",
            publisher="机械工业出版社",
            isbn="9787111407014",
            price=128.00,
            stock=25,
            description="算法权威教材",
            cover_image="/static/images/algorithm.png",
            category="计算机基础",
            created_at=now - timedelta(hours=6)
        ),
        Book(
            id=5,
            title="代码整洁之道",
            author="Robert C. Martin",
            publisher="人民邮电出版社",
            isbn="9787115216875",
            price=59.00,
            stock=40,
            description="软件工程经典",
            cover_image="/static/images/clean_code.png",
            category="软件工程",
            created_at=now - timedelta(hours=4)
        ),
        Book(
            id=6,
            title="设计模式：可复用面向对象软件的基础",
            author="Erich Gamma",
            publisher="机械工业出版社",
            isbn="9787111618336",
            price=79.00,
            stock=30,
            description="23种设计模式",
            cover_image="/static/images/design_patterns.png",
            category="软件工程",
            created_at=now - timedelta(hours=2)
        ),
        Book(
            id=7,
            title="Vue.js设计与实现",
            author="霍春阳",
            publisher="人民邮电出版社",
            isbn="9787115583867",
            price=89.00,
            stock=45,
            description="Vue.js 3原理",
            cover_image="/static/images/vue.png",
            category="前端开发",
            created_at=now - timedelta(minutes=90)
        ),
        Book(
            id=8,
            title="React进阶实战",
            author="徐超",
            publisher="电子工业出版社",
            isbn="9787121350628",
            price=79.00,
            stock=28,
            description="React开发进阶",
            cover_image="/static/images/react.png",
            category="前端开发",
            created_at=now - timedelta(minutes=60)
        ),
        Book(
            id=9,
            title="MySQL必知必会",
            author="Ben Forta",
            publisher="人民邮电出版社",
            isbn="9787115313980",
            price=39.00,
            stock=60,
            description="MySQL入门经典",
            cover_image="/static/images/mysql.png",
            category="数据库",
            created_at=now - timedelta(minutes=30)
        ),
        Book(
            id=10,
            title="Redis设计与实现",
            author="黄健宏",
            publisher="机械工业出版社",
            isbn="9787111464747",
            price=79.00,
            stock=35,
            description="Redis内部原理",
            cover_image="/static/images/redis.png",
            category="数据库",
            created_at=now - timedelta(minutes=15)
        ),
        Book(
            id=11,
            title="Python数据分析实战",
            author="Python",
            publisher="Python出版社",
            isbn="9787000000011",
            price=99.00,
            stock=100,
            description="Python数据分析",
            cover_image="/static/images/python_data.png",
            category="编程技术",
            created_at=now - timedelta(minutes=10)
        ),
        Book(
            id=12,
            title="Python数据科学手册",
            author="Python Author",
            publisher="人民邮电出版社",
            isbn="9787000000012",
            price=109.00,
            stock=80,
            description="Python数据科学",
            cover_image="/static/images/python_sci.png",
            category="编程技术",
            created_at=now - timedelta(minutes=5)
        ),
    ]
    db.add_all(books)
    db.commit()
    return books


@pytest.fixture(scope="function")
def db_session(tmp_path) -> Generator[Session, None, None]:
    db_file = tmp_path / "test_books.db"
    engine = create_engine(
        f"sqlite:///{db_file}",
        connect_args={"check_same_thread": False}
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()
        if db_file.exists():
            db_file.unlink()


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    test_app = create_test_app()

    def override_get_db() -> Generator[Session, None, None]:
        try:
            yield db_session
        finally:
            pass

    test_app.dependency_overrides[get_db] = override_get_db
    create_test_books(db_session)
    with TestClient(test_app) as c:
        yield c
    test_app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def seeded_db(db_session: Session) -> Session:
    create_test_books(db_session)
    return db_session
