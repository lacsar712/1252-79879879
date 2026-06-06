# 现代化在线书店

基于 FastAPI + Vue 3 的全栈在线书店项目，采用前后端分离架构设计。

## 🛠 技术栈

- **Frontend**: Vue 3 (Composition API) + TypeScript + Vite + Element Plus + Pinia + Axios
- **Backend**: FastAPI + SQLAlchemy + Pydantic + JWT
- **Database**: SQLite

## 🚀 启动指南 (How to Run)

### Docker 方式（推荐，一键启动）

1. 确保 Docker Desktop 已启动
2. 在项目根目录执行：
   ```bash
   docker compose up -d --build
   ```
3. 等待容器启动完成（约 1-2 分钟）
4. 访问以下服务地址即可使用

### 本地开发方式

#### 1. 配置环境变量

项目已提供 `.env.example` 作为参考，直接复制即可使用默认配置：

```bash
# 根目录（可选，Docker 方式使用）
copy .env.example .env

# 后端
cd backend
copy .env.example .env
cd ..

# 前端
cd frontend
copy .env.example .env
cd ..
```

#### 2. 启动后端

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

#### 3. 启动前端（新终端）

```bash
cd frontend
npm install
npm run dev
```

## 🔗 服务地址 (Services)

| 服务 | 地址 | 说明 |
|------|------|------|
| **前端应用** | http://localhost:3000 | 书店主页 |
| **后端 Swagger 文档** | http://localhost:8000/docs 或 http://localhost:3000/docs | API 交互文档 |
| **后端 ReDoc 文档** | http://localhost:8000/redoc 或 http://localhost:3000/redoc | API 参考文档 |
| **静态图片** | http://localhost:8000/api/static/images/ 或 http://localhost:3000/api/static/images/ | 图书封面等静态资源 |
| **健康检查** | http://localhost:8000/health | 后端服务健康状态 |

> Docker 方式下，前端端口 3000 已通过 Nginx 代理 `/api`、`/docs`、`/redoc` 到后端，因此所有服务均可通过 `localhost:3000` 访问。

## 🔧 环境变量配置

### 后端环境变量（backend/.env）

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `BACKEND_HOST` | `0.0.0.0` | 后端监听地址 |
| `BACKEND_PORT` | `8000` | 后端监听端口 |
| `DATABASE_URL` | `sqlite:///./data/bookstore.db` | SQLite 数据库路径 |
| `SECRET_KEY` | `bookstore-secret-key-2024-very-secure` | JWT 签名密钥 |
| `CORS_ORIGINS` | `http://localhost:3000,http://127.0.0.1:3000` | 允许的跨域源，逗号分隔，设为 `*` 允许所有 |

### 前端环境变量（frontend/.env）

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `VITE_API_BASE_URL` | `/api` | API 请求基础路径 |
| `VITE_API_PROXY_TARGET` | `http://localhost:8000` | Vite 开发代理目标（本地开发时后端地址） |
| `FRONTEND_HOST` | `0.0.0.0` | Vite 开发服务器监听地址 |
| `FRONTEND_PORT` | `3000` | Vite 开发服务器监听端口 |

## 📁 数据持久化

- **SQLite 数据库**: 本地开发时存储在 `backend/data/bookstore.db`，Docker 方式通过 volume 持久化
- **静态图片**: 存储在 `backend/static/images/`，Docker 方式通过 bind mount 挂载
- 所有环境文件（`.env`）已在 `.gitignore` 中排除，不会被提交

## 🧪 测试账号

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | admin | 123456 |
| 普通用户 | user | 123456 |

## 📦 项目结构

```
1252/
├── .env.example            # 根目录环境变量示例
├── docker-compose.yml      # Docker Compose 配置
├── backend/                 # 后端服务
│   ├── .env.example        # 后端环境变量示例
│   ├── data/               # SQLite 数据库目录（自动创建）
│   ├── routes/             # API 路由
│   ├── services/           # 业务逻辑服务
│   ├── static/images/      # 静态图片资源
│   ├── models.py           # 数据库模型
│   ├── schemas.py          # Pydantic 模式
│   ├── database.py         # 数据库配置（含 dotenv 加载）
│   ├── auth.py             # JWT 认证（含 dotenv 加载）
│   ├── seed.py             # 数据填充
│   ├── main.py             # FastAPI 应用入口（CORS 基于环境变量）
│   ├── requirements.txt    # Python 依赖（含 python-dotenv）
│   └── Dockerfile
├── frontend/               # 前端应用
│   ├── .env                # 前端环境变量
│   ├── .env.example        # 前端环境变量示例
│   ├── src/
│   │   ├── api/           # API 服务
│   │   ├── utils/request.ts # Axios 请求封装（baseURL 来自 env）
│   │   ├── vite-env.d.ts   # Vite 环境变量类型定义
│   │   └── ...
│   ├── vite.config.ts      # Vite 配置（代理基于环境变量）
│   ├── nginx.conf          # Nginx 配置（含 API/文档代理）
│   ├── package.json
│   └── Dockerfile
└── README.md
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
