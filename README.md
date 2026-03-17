# 智能算力监测平台

一个基于 Vue 3 + FastAPI 的 GPU 使用情况监测平台，提供实时监控、数据可视化和统计分析功能。

## 项目结构

```
computing-power/
├── backend/                 # 后端服务 (FastAPI)
│   ├── app/
│   │   ├── config.py       # 配置管理
│   │   ├── database.py     # PostgreSQL 数据库连接
│   │   ├── local_database.py # SQLite 本地数据库
│   │   ├── api.py          # API 路由
│   │   └── ...
│   ├── data/               # 数据存储目录
│   ├── main.py             # 应用入口
│   ├── requirements.txt    # Python 依赖
│   └── Dockerfile          # 后端容器配置
├── frontend/               # 前端服务 (Vue 3)
│   ├── src/
│   │   ├── components/     # Vue 组件
│   │   ├── api/            # API 调用
│   │   └── ...
│   ├── package.json        # Node 依赖
│   ├── Dockerfile          # 前端容器配置
│   └── nginx.conf          # Nginx 配置
├── docker-compose.yml      # Docker 编排配置
├── .env.example            # 环境变量模板
├── start.sh                # 启动脚本 (Bash)
├── start.bat               # 启动脚本 (CMD)
└── start.ps1               # 启动脚本 (PowerShell)
```

## 技术栈

### 后端
- **FastAPI** - 高性能 Python Web 框架
- **SQLAlchemy** - ORM 数据库工具
- **PostgreSQL** - 远程数据库 (业务数据)
- **SQLite** - 本地数据库 (汇总数据)
- **APScheduler** - 定时任务调度

### 前端
- **Vue 3** - 渐进式 JavaScript 框架
- **Element Plus** - UI 组件库
- **ECharts** - 数据可视化图表
- **Vite** - 构建工具

## 快速开始

### 前置要求

- Python 3.12+
- Node.js 18+
- PostgreSQL 数据库
- Docker (可选，用于容器部署)

### 1. 配置环境变量

```bash
# Linux/Mac
cp .env.example .env

# Windows CMD
copy .env.example .env

# Windows PowerShell
Copy-Item .env.example .env
```

编辑 `.env` 文件，配置数据库连接信息：

```env
# 数据库配置
DB_HOST=your_database_host
DB_PORT=5432
DB_NAME=computing_power
DB_USER=your_username
DB_PASSWORD=your_password

# 业务配置
WORK_HOUR_START=9
WORK_HOUR_END=18
HIGH_USAGE_THRESHOLD=60.0
LOW_USAGE_THRESHOLD=30.0

# 服务端口
BACKEND_PORT=8001
FRONTEND_PORT=5173
```

### 2. 启动服务

#### 方式一：使用启动脚本 (推荐)

```bash
# Linux/Mac (Bash)
chmod +x start.sh
./start.sh dev        # 开发环境
./start.sh start      # Docker 容器部署
./start.sh stop       # 停止容器
./start.sh status     # 查看状态
./start.sh logs       # 查看日志

# Windows CMD
start.bat dev         # 开发环境
start.bat start       # Docker 容器部署
start.bat stop        # 停止容器

# Windows PowerShell
.\start.ps1 dev       # 开发环境
.\start.ps1 start     # Docker 容器部署
.\start.ps1 stop      # 停止容器
```

#### 方式二：手动启动

**后端服务：**

```bash
cd backend

# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# Linux/Mac
source .venv/bin/activate
# Windows
.venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 启动服务
python main.py
```

**前端服务：**

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build
```

#### 方式三：Docker 容器部署

```bash
# 构建并启动
docker-compose up -d --build

# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 3. 访问服务

- **前端界面**: http://localhost:5173
- **后端 API**: http://localhost:8001
- **API 文档**: http://localhost:8001/docs
- **健康检查**: http://localhost:8001/health

## 配置说明

### 数据库配置

项目使用双数据库架构：

| 数据库 | 用途 | 配置方式 |
|--------|------|----------|
| PostgreSQL | 远程业务数据 | 通过环境变量配置 |
| SQLite | 本地缓存数据 | 自动创建于 `backend/data/local.db` |

**缓存架构说明：**

- **静态数据缓存**：设备信息、组织结构、GPU卡信息、网络模块等静态数据缓存到本地SQLite数据库
- **汇总数据缓存**：GPU使用率汇总、组织统计等聚合数据存储在本地数据库
- **实时数据查询**：设备在线状态、实时监控数据等仍从远程PostgreSQL查询

**缓存同步策略：**

| 数据类型 | 同步间隔 | 说明 |
|----------|----------|------|
| GPU卡信息 | 24小时 | 静态数据，变化极少 |
| 网络模块 | 24小时 | 静态数据 |
| 组织结构 | 1小时 | 半静态数据 |
| 设备信息 | 30分钟 | 半静态数据 |
| 汇总数据 | 每日凌晨 | 聚合历史数据 |

### 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `DB_HOST` | `localhost` | PostgreSQL 主机地址 |
| `DB_PORT` | `5432` | PostgreSQL 端口 |
| `DB_NAME` | `computing_power` | 数据库名称 |
| `DB_USER` | `gaussdb` | 数据库用户名 |
| `DB_PASSWORD` | - | 数据库密码 (必填) |
| `WORK_HOUR_START` | `9` | 工作时段开始 |
| `WORK_HOUR_END` | `18` | 工作时段结束 |
| `HIGH_USAGE_THRESHOLD` | `60.0` | 高使用率阈值 (%) |
| `LOW_USAGE_THRESHOLD` | `30.0` | 低使用率阈值 (%) |
| `CACHE_SYNC_INTERVAL` | `3600` | 缓存同步间隔 (秒) |
| `BACKEND_PORT` | `8001` | 后端服务端口 |
| `FRONTEND_PORT` | `5173` | 前端服务端口 |

## Docker 部署

### 构建镜像

```bash
# 构建所有服务
docker-compose build

# 单独构建
docker-compose build backend
docker-compose build frontend
```

### 运行容器

```bash
# 后台运行
docker-compose up -d

# 前台运行 (可看到日志输出)
docker-compose up
```

### 数据持久化

容器使用 Docker Volume 持久化数据：

- `backend-data`: 后端数据目录 (`/app/data`)

## API 接口

### 主要接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | API 信息 |
| GET | `/health` | 健康检查 |
| GET | `/api/overview/stats` | 概览统计 |
| GET | `/api/trend/*` | 趋势数据 |
| GET | `/api/distribution/*` | 分布数据 |
| GET | `/api/ranking/*` | 排名数据 |
| GET | `/api/cache/status` | 缓存状态 |
| POST | `/api/cache/sync` | 手动同步缓存 |
| GET | `/api/admin/*` | 管理接口 |

### 缓存管理接口

**查看缓存状态：**
```
GET /api/cache/status
```

**手动触发缓存同步：**
```
POST /api/cache/sync?force=true
```

完整 API 文档请访问: http://localhost:8001/docs

## 开发指南

### 后端开发

```bash
cd backend

# 安装开发依赖
pip install -r requirements.txt

# 运行开发服务器 (热重载)
uvicorn main:app --reload --port 8001
```

### 前端开发

```bash
cd frontend

# 安装依赖
npm install

# 运行开发服务器
npm run dev

# 构建生产版本
npm run build

# 预览生产构建
npm run preview
```

## 故障排除

### 数据库连接失败

1. 检查 `.env` 文件中的数据库配置
2. 确认数据库服务正在运行
3. 验证网络连接和防火墙设置

### 容器启动失败

```bash
# 查看容器日志
docker-compose logs backend
docker-compose logs frontend

# 重新构建
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### 端口冲突

修改 `.env` 文件中的端口配置：

```env
BACKEND_PORT=8002
FRONTEND_PORT=5174
```

## 许可证

MIT License
