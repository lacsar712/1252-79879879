# -*- coding: utf-8 -*-
"""
数据库初始化脚本 - 填充演示数据
"""
import logging
from sqlalchemy.orm import Session
from database import engine, SessionLocal
from models import Base, User, Book, Promotion, PromotionBook
from datetime import datetime, timedelta
from auth import get_password_hash

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_db():
    """初始化数据库表"""
    Base.metadata.create_all(bind=engine)
    logger.info("数据库表创建成功")


def seed_data():
    """填充演示数据"""
    db = SessionLocal()
    try:
        # 检查是否已有数据
        if db.query(User).count() > 0:
            logger.info("数据库已有数据，跳过初始化")
            return

        # 创建管理员用户
        admin = User(
            username="admin",
            email="admin@bookstore.com",
            hashed_password=get_password_hash("123456"),
            is_admin=True,
            is_active=True
        )
        db.add(admin)

        # 创建普通用户
        user = User(
            username="user",
            email="user@bookstore.com",
            hashed_password=get_password_hash("123456"),
            is_admin=False,
            is_active=True
        )
        db.add(user)

        # 创建示例图书
        # 使用本地静态图片路径，通过 /api/static/images/ 访问
        books = [
            Book(
                title="Python编程：从入门到实践",
                author="Eric Matthes",
                publisher="人民邮电出版社",
                isbn="9787115428028",
                price=89.00,
                stock=50,
                description="一本Python入门经典书籍，适合编程初学者学习Python的基础知识和项目实践。",
                cover_image="/api/static/images/python_crash_course.png",
                category="编程技术"
            ),
            Book(
                title="JavaScript高级程序设计",
                author="Nicholas C. Zakas",
                publisher="人民邮电出版社",
                isbn="9787115545381",
                price=129.00,
                stock=35,
                description="JavaScript领域的经典之作，全面深入地介绍了JavaScript语言的核心概念和高级特性。",
                cover_image="/api/static/images/s33703494.jpg",
                category="编程技术"
            ),
            Book(
                title="深入理解计算机系统",
                author="Randal E. Bryant",
                publisher="机械工业出版社",
                isbn="9787111544937",
                price=139.00,
                stock=20,
                description="从程序员的视角讲解计算机系统的组成与运作原理，是计算机专业学生的必读书目。",
                cover_image="/api/static/images/s29195878.jpg",
                category="计算机基础"
            ),
            Book(
                title="算法导论",
                author="Thomas H. Cormen",
                publisher="机械工业出版社",
                isbn="9787111407010",
                price=128.00,
                stock=25,
                description="全面介绍了现代计算机算法的各种概念和技术，是算法学习的权威教材。",
                cover_image="/api/static/images/s25648004.jpg",
                category="计算机基础"
            ),
            Book(
                title="代码整洁之道",
                author="Robert C. Martin",
                publisher="人民邮电出版社",
                isbn="9787115216878",
                price=59.00,
                stock=40,
                description="软件工程领域的经典著作，讲述如何写出整洁、可维护的高质量代码。",
                cover_image="/api/static/images/s4103991.jpg",
                category="软件工程"
            ),
            Book(
                title="设计模式：可复用面向对象软件的基础",
                author="Erich Gamma",
                publisher="机械工业出版社",
                isbn="9787111618331",
                price=79.00,
                stock=30,
                description="GOF四人组的经典之作，系统讲解23种设计模式，是软件设计的必读书籍。",
                cover_image="/api/static/images/design_patterns.png",
                category="软件工程"
            ),
            Book(
                title="Vue.js设计与实现",
                author="霍春阳",
                publisher="人民邮电出版社",
                isbn="9787115583864",
                price=89.00,
                stock=45,
                description="深入解析Vue.js 3的设计原理与实现细节，帮助开发者理解框架内部机制。",
                cover_image="/api/static/images/vue_design.png",
                category="前端开发"
            ),
            Book(
                title="React进阶实战",
                author="徐超",
                publisher="电子工业出版社",
                isbn="9787121350627",
                price=79.00,
                stock=28,
                description="React开发的进阶指南，涵盖Hooks、性能优化、状态管理等核心主题。",
                cover_image="/api/static/images/react_advanced.png",
                category="前端开发"
            ),
            Book(
                title="MySQL必知必会",
                author="Ben Forta",
                publisher="人民邮电出版社",
                isbn="9787115313980",
                price=39.00,
                stock=60,
                description="MySQL入门经典，以简洁明了的方式介绍SQL语言和MySQL数据库的使用。",
                cover_image="/api/static/images/mysql_must_know.png",
                category="数据库"
            ),
            Book(
                title="Redis设计与实现",
                author="黄健宏",
                publisher="机械工业出版社",
                isbn="9787111464747",
                price=79.00,
                stock=35,
                description="深入剖析Redis内部实现原理，是理解Redis设计思想的权威书籍。",
                cover_image="/api/static/images/s27297117.jpg",
                category="数据库"
            ),
            Book(
                title="活着",
                author="余华",
                publisher="作家出版社",
                isbn="9787506365437",
                price=45.00,
                stock=80,
                description="余华的代表作，讲述一个人历经世间沧桑和磨难的故事，文字朴实而震撼人心。",
                cover_image="/api/static/images/s29053580.jpg",
                category="文学小说"
            ),
            Book(
                title="三体",
                author="刘慈欣",
                publisher="重庆出版社",
                isbn="9787536692930",
                price=68.00,
                stock=55,
                description="中国科幻文学里程碑之作，雨果奖获奖作品，展现宇宙文明的宏大叙事。",
                cover_image="/api/static/images/s28357056.jpg",
                category="科幻小说"
            )
        ]
        
        for book in books:
            db.add(book)
        
        db.flush()
        
        now = datetime.utcnow()
        promotions = [
            Promotion(
                name="暑期读书狂欢节",
                cover_image="/api/static/images/s28357056.jpg",
                start_time=now - timedelta(days=1),
                end_time=now + timedelta(days=30),
                description="炎炎夏日，书香相伴！精选图书低至5折，限时抢购，不容错过！",
                is_displayed=True
            ),
            Promotion(
                name="编程技术进阶周",
                cover_image="/api/static/images/vue_design.png",
                start_time=now + timedelta(days=7),
                end_time=now + timedelta(days=14),
                description="提升编程技能，精选编程技术图书，助力你的技术成长之路！",
                is_displayed=True
            ),
            Promotion(
                name="文学经典特卖会",
                cover_image="/api/static/images/s29053580.jpg",
                start_time=now - timedelta(days=60),
                end_time=now - timedelta(days=30),
                description="品味文学经典，感受文字魅力。已结束的经典活动回顾。",
                is_displayed=False
            )
        ]
        
        for promotion in promotions:
            db.add(promotion)
        
        db.flush()
        
        promotion_books_data = [
            {"promotion_idx": 0, "book_idx": 0, "price": 49.00, "stock": 30, "limit": 2},
            {"promotion_idx": 0, "book_idx": 5, "price": 45.00, "stock": 20, "limit": 1},
            {"promotion_idx": 0, "book_idx": 8, "price": 19.90, "stock": 50, "limit": 3},
            {"promotion_idx": 0, "book_idx": 10, "price": 29.00, "stock": 40, "limit": 2},
            {"promotion_idx": 1, "book_idx": 1, "price": 79.00, "stock": 15, "limit": 1},
            {"promotion_idx": 1, "book_idx": 6, "price": 59.00, "stock": 25, "limit": 2},
            {"promotion_idx": 1, "book_idx": 7, "price": 49.00, "stock": 20, "limit": 2},
            {"promotion_idx": 1, "book_idx": 2, "price": 89.00, "stock": 10, "limit": 1},
            {"promotion_idx": 2, "book_idx": 10, "price": 25.00, "stock": 50, "limit": 3},
            {"promotion_idx": 2, "book_idx": 11, "price": 39.00, "stock": 30, "limit": 2},
        ]
        
        for pb_data in promotion_books_data:
            promotion = promotions[pb_data["promotion_idx"]]
            book = books[pb_data["book_idx"]]
            db.add(PromotionBook(
                promotion_id=promotion.id,
                book_id=book.id,
                promotion_price=pb_data["price"],
                promotion_stock=pb_data["stock"],
                sold_stock=0,
                purchase_limit=pb_data["limit"]
            ))
        
        db.commit()
        logger.info("演示数据填充成功")
        logger.info(f"  - 创建用户: admin (密码: 123456, 管理员)")
        logger.info(f"  - 创建用户: user (密码: 123456, 普通用户)")
        logger.info(f"  - 创建图书: {len(books)} 本")
        logger.info(f"  - 创建活动: {len(promotions)} 个")
        logger.info(f"  - 创建活动图书关联: {len(promotion_books_data)} 条")
        
    except Exception as e:
        logger.error(f"数据填充失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
    seed_data()
