# 现代化在线书店

基于 FastAPI + Vue 3 的全栈在线书店项目，采用前后端分离架构设计。

## 🛠 技术栈

- **Frontend**: Vue 3 (Composition API) + TypeScript + Vite + Element Plus + Pinia + Axios
- **Backend**: FastAPI + SQLAlchemy + Pydantic + JWT
- **Database**: SQLite

## 🚀 启动指南 (How to Run)

### Docker 方式（推荐）

1. 确保 Docker Desktop 已启动
2. 在根目录执行：
   ```bash
   docker compose up -d --build
   ```
3. 等待容器启动完成...

### 本地开发方式

#### 后端
```bash
cd backend
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
```

#### 前端
```bash
cd frontend
npm install
npm run dev
```

## 🔗 服务地址 (Services)

- **Frontend**: http://localhost:3000
- **Backend Swagger**: http://localhost:8000/docs
- **Backend ReDoc**: http://localhost:8000/redoc

## 🧪 测试账号

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | admin | 123456 |
| 普通用户 | user | 123456 |

## 📦 项目结构

```
1252/
├── backend/                 # 后端服务
│   ├── routes/             # API 路由
│   │   ├── auth.py         # 认证路由
│   │   └── books.py        # 图书管理路由
│   ├── models.py           # 数据库模型
│   ├── schemas.py          # Pydantic 模式
│   ├── database.py         # 数据库配置
│   ├── auth.py             # JWT 认证
│   ├── seed.py             # 数据填充
│   ├── main.py             # 应用入口
│   ├── requirements.txt    # Python 依赖
│   └── Dockerfile
├── frontend/               # 前端应用
│   ├── src/
│   │   ├── api/           # API 服务
│   │   ├── layouts/       # 布局组件
│   │   ├── router/        # 路由配置
│   │   ├── stores/        # Pinia 状态管理
│   │   ├── styles/        # 全局样式
│   │   ├── types/         # TypeScript 类型
│   │   └── views/         # 页面组件
│   ├── package.json
│   ├── nginx.conf
│   └── Dockerfile
└── docker-compose.yml
```

## ✨ 功能特性

### 用户模块
- 用户注册（密码哈希加密存储）
- 用户登录（JWT 令牌认证）
- 路由守卫保护敏感页面

### 图书管理模块
- 分页展示图书列表
- 按书名/作者/出版社搜索
- 管理员可录入新图书
- 管理员可删除图书
- **出版社字段**：新增出版社信息管理

### UI/UX
- 现代化渐变设计
- Element Plus 组件库
- 响应式布局
- 骨架屏加载状态
- 流畅的页面过渡动画
