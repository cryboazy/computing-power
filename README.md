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
│   │   ├── local_models.py  # SQLite 数据模型
│   │   ├── api_cached.py   # API 路由 (缓存版)
│   │   ├── admin.py        # 管理后台 API
│   │   ├── aggregator.py   # 数据聚合服务
│   │   ├── cache_sync.py   # 缓存同步服务
│   │   ├── models.py       # PostgreSQL 数据模型
│   │   ├── org_constants.py # 组织代码常量
│   │   └── ...
│   ├── data/               # 数据存储目录
│   ├── sql/                # SQL 脚本
│   │   ├── sys_dict_data.sql
│   │   └── system_config.sql
│   ├── main.py             # 应用入口
│   ├── requirements.txt    # Python 依赖
│   └── Dockerfile          # 后端容器配置
├── frontend/               # 前端服务 (Vue 3)
│   ├── src/
│   │   ├── components/    # Vue 组件
│   │   │   ├── OrgDetailTabs/  # 组织详情标签页
│   │   │   │   ├── DeviceDetailTab.vue
│   │   │   │   └── UsageDetailTab.vue
│   │   │   └── ...
│   │   ├── api/           # API 调用
│   │   ├── assets/        # 静态资源 (中国地图JSON)
│   │   ├── composables/    # 组合式函数
│   │   ├── styles/         # 全局样式
│   │   └── themes/        # 主题配置
│   ├── public/             # 静态资源
│   ├── package.json       # Node 依赖
│   ├── Dockerfile         # 前端容器配置
│   ├── nginx.conf         # Nginx 配置
│   └── vite.config.js     # Vite 配置
├── docker/                 # Docker 配置
│   └── daemon.json        # Docker 镜像加速配置
├── docker-compose.yml      # Docker 编排配置
├── .env.example            # 环境变量模板
└── .gitignore             # Git 忽略文件
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
- Docker (可选，用于容器部署)

**注意**: 如果使用 Docker 部署，PostgreSQL 数据库会自动创建，无需额外安装。

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

### 2. 配置 Docker 镜像加速 (可选)

如果使用 Docker 部署，可以配置镜像加速以提高拉取速度：

```bash
# Linux/Mac
sudo mkdir -p /etc/docker
sudo cp docker/daemon.json /etc/docker/daemon.json
sudo systemctl restart docker

# Windows
# 将 docker/daemon.json 内容复制到 Docker Desktop 的配置中
# Settings -> Docker Engine
```

### 3. 启动服务

#### 方式一：手动启动 (开发环境)

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

# 初始化本地数据库
python -m app.init_local_db

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

#### 方式二：Docker 容器部署 (生产环境)

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

### 4. 访问服务

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

**数据库初始化：**

首次运行需要初始化数据库表和配置：

```bash
# 初始化本地 SQLite 数据库
cd backend
python -m app.init_local_db

# 创建远程 PostgreSQL 数据库表（可选，如果表不存在）
python create_dict_table.py
python create_system_config.py
```

**数据库表结构：**

PostgreSQL 远程数据库包含以下主要表：
- `sys_dict_data` - 字典数据表（设备用途等）
- `system_config` - 系统配置表
- 其他业务数据表（设备、GPU卡、组织等）

SQLite 本地数据库包含以下表：
- `local_system_config` - 本地系统配置
- `local_daily_gpu_usage_summary` - GPU使用率日汇总
- `local_daily_device_summary` - 设备使用率日汇总
- `local_org_gpu_usage_summary` - 组织GPU使用率汇总
- `local_statistics_data` - 统计数据缓存

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
| GET | `/api/admin/config` | 获取系统配置 |
| POST | `/api/admin/config` | 更新系统配置 |
| GET | `/api/admin/aggregation/status` | 数据聚合状态 |
| POST | `/api/admin/aggregation/trigger` | 触发数据聚合 |
| GET | `/api/admin/aggregation/daily` | 日汇总数据统计 |
| GET | `/api/admin/aggregation/device` | 设备汇总数据统计 |

### 系统配置接口

**获取系统配置：**
```
GET /api/admin/config
```

**更新系统配置：**
```
POST /api/admin/config
Content-Type: application/json

{
  "work_hour_start": 9,
  "work_hour_end": 18,
  "high_usage_threshold": 60.0,
  "low_usage_threshold": 30.0
}
```

### 数据聚合接口

**查看聚合状态：**
```
GET /api/admin/aggregation/status
```

**手动触发聚合：**
```
POST /api/admin/aggregation/trigger
```

**查看日汇总统计：**
```
GET /api/admin/aggregation/daily?days=30
```

**查看设备汇总统计：**
```
GET /api/admin/aggregation/device?days=30
```

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

## 系统功能

### 核心功能

- **实时监控**: 实时展示 GPU 设备使用率、显存使用情况等关键指标
- **数据可视化**: 通过图表展示资源趋势、使用率趋势、使用率预警等
- **统计分析**: 提供全国、地方厅局、部机关等多维度的统计分析
- **排名展示**: 展示各地区/组织 GPU 使用率排名
- **组织详情**: 支持查看组织机构的详细使用情况，包括设备详情和使用详情
- **设备详情**: 支持查看单个设备的详细使用情况，支持自定义时间范围查询
- **系统配置**: 支持配置工作时段、使用率阈值等系统参数
- **数据聚合**: 自动聚合历史数据，支持手动触发聚合
- **缓存管理**: 智能缓存静态数据和汇总数据，提升查询性能
- **GPU档次管理**: 可配置的 GPU 档次分类管理，支持高端卡、中端卡、低端卡等分类，支持动态调整档次配置

### 前端组件

| 组件 | 说明 | 功能 |
|------|------|------|
| `LeftPanel.vue` | 左侧面板 | 展示资源趋势、使用率趋势、使用率预警 |
| `CenterPanel.vue` | 中央面板 | 展示概览统计、全国/地方/部机关分布图表 |
| `RightPanel.vue` | 右侧面板 | 展示全国及各分组使用率排名 |
| `AdminPanel.vue` | 管理面板 | 系统配置和数据聚合管理 |
| `OrgDetailDialog.vue` | 组织详情弹窗 | 展示组织机构的详细使用情况 |
| `DeviceUsageDetailDialog.vue` | 设备详情弹窗 | 展示单个设备的详细使用情况 |
| `ThemeSwitcher.vue` | 主题切换器 | 支持明暗主题切换 |
| `PanelExpandContent.vue` | 面板展开内容 | 展示面板展开后的详细内容 |
| `DeviceDetailTab.vue` | 设备详情标签 | 组织详情中的设备列表标签页 |
| `UsageDetailTab.vue` | 使用详情标签 | 组织详情中的使用情况标签页 |

### 组织代码常量

系统使用以下组织代码常量（定义于 `backend/app/org_constants.py`）：

| 常量 | 值 | 说明 |
|------|-----|------|
| `ORG_CODE_CHINA` | `CHINA` | 全国组织代码 |
| `ORG_CODE_LOCAL` | `LOCAL` | 地方厅局组织代码 |
| `ORG_CODE_MINISTRY` | `MINISTRY` | 部机关组织代码 |

### 数据分析维度

- **时间维度**: 支持按月、季度、半年、年等时间范围查看趋势
- **组织维度**: 支持全国、地方厅局、部机关等多维度分析
- **设备维度**: 支持按设备、GPU卡等粒度查看使用情况
- **使用率维度**: 支持高使用率、低使用率等预警分析

## 数据管理工具

### 数据聚合脚本

项目提供了多个数据聚合工具脚本：

| 脚本 | 说明 | 使用场景 |
|------|------|----------|
| `aggregate_week_data.py` | 聚合最近7天的数据 | 日常数据更新 |
| `run_agg_data.py` | 聚合指定天数的数据 | 快速聚合最近数据 |
| `reset_aggregation.py` | 清空并重新生成所有聚合数据 | 数据修复或首次初始化 |

**使用示例：**

```bash
# 聚合最近7天的数据
python aggregate_week_data.py

# 聚合最近3天的数据
python run_agg_data.py

# 清空并重新生成所有聚合数据（谨慎使用）
python reset_aggregation.py
```

### 数据库管理脚本

| 脚本 | 说明 |
|------|------|
| `create_dict_table.py` | 创建字典数据表并初始化设备用途字典 |
| `create_system_config.py` | 创建系统配置表 |
| `init_local_db.py` | 初始化本地 SQLite 数据库 |

**使用示例：**

```bash
# 创建远程数据库表
python create_dict_table.py
python create_system_config.py

# 初始化本地数据库
python -m app.init_local_db
```

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

## 安全注意事项

### 默认管理员账户

系统内置默认管理员账户，**首次部署后请立即修改密码**：

| 账户 | 默认密码 | 说明 |
|------|----------|------|
| `admin` | `admin123` | 管理员账户 |

### 生产环境安全建议

1. **修改默认密码**: 首次登录后立即修改管理员密码
2. **限制 CORS**: 在 `backend/main.py` 中将 `allow_origins` 设置为具体域名
3. **使用 HTTPS**: 生产环境必须使用 HTTPS
4. **保护环境变量**: 确保 `.env` 文件不被提交到版本控制
5. **数据库安全**: 使用强密码，限制数据库访问 IP

### 密码策略

- 最小长度：6 位
- 建议包含：大小写字母、数字、特殊字符

## 许可证

MIT License

## 更新日志

详见 [CHANGELOG.md](CHANGELOG.md)
