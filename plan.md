# 聚合数据刷新超时问题解决方案

## 问题分析

### 当前架构

系统使用 SSE (Server-Sent Events) 实现聚合数据刷新的进度跟踪：

- 前端通过 `EventSource` 连接后端 `/api/admin/aggregation/refresh` 接口
- 后端使用 `StreamingResponse` 流式返回进度事件
- 聚合操作在生成器中同步执行

### 问题根因

1. **SSE 连接超时**
   - 当数据量巨大时，单个聚合步骤（如 `aggregate_device_hourly_stats`）可能执行数分钟
   - 期间没有向客户端发送任何数据，导致连接超时
   - 浏览器默认超时、Nginx 代理超时（默认60秒）、负载均衡器超时
2. **同步阻塞**
   - 聚合操作是同步执行的，在 `generate_progress()` 中直接调用 `aggregator.aggregate_xxx()`
   - 这些方法执行时间长，期间无法发送心跳或进度更新
3. **缺乏任务持久化**
   - 任务状态仅存在于内存中
   - 连接中断后无法恢复任务
   - 无法查看历史任务执行情况

## 解决方案

采用 **后台任务队列 + 任务状态持久化** 方案：

### 核心设计

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   前端      │────>│  创建任务API  │────>│  任务队列   │
└─────────────┘     └──────────────┘     └─────────────┘
       │                                        │
       │ 轮询任务状态                            │ 后台线程执行
       v                                        v
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  进度显示   │<────│  任务状态API  │<────│  更新进度   │
└─────────────┘     └──────────────┘     └─────────────┘
```

### 实施步骤

#### 1. 创建任务模型 (LocalAggregationTask)

新增字段：

- `task_id`: 任务唯一标识
- `task_type`: 任务类型 (refresh/reset)
- `status`: 状态 (pending/running/completed/failed/cancelled)
- `progress`: 当前进度百分比
- `current_step`: 当前步骤描述
- `total_steps`: 总步骤数
- `processed_days`: 已处理天数
- `total_days`: 总天数
- `target_dates`: 目标日期列表 (JSON)
- `error_message`: 错误信息
- `start_time`: 开始时间
- `end_time`: 结束时间
- `created_by`: 创建者

#### 2. 后端 API 改造

**新增接口：**

- `POST /api/admin/aggregation/tasks` - 创建刷新任务
- `GET /api/admin/aggregation/tasks/{task_id}` - 查询任务状态
- `GET /api/admin/aggregation/tasks` - 查询任务列表
- `POST /api/admin/aggregation/tasks/{task_id}/cancel` - 取消任务

**移除接口：**

- `GET /api/admin/aggregation/refresh` (SSE方式) - 保留但标记为废弃

#### 3. 后台任务执行器

创建 `backend/app/task_executor.py`：

- 使用 `threading.Thread` 在后台执行聚合任务
- 定期更新任务进度到数据库
- 支持任务取消
- 异常处理和错误记录

#### 4. 前端改造

修改 `AdminPanel.vue`：

- 创建任务后获取 task\_id
- 使用 `setInterval` 轮询任务状态（每2秒）
- 显示任务进度和状态
- 支持取消正在运行的任务
- 显示最近任务列表

#### 5. 数据库迁移

创建新的任务表迁移脚本

### 详细设计

#### 任务状态流转

```
pending -> running -> completed
        |         |
        |         v
        |       failed
        |
        v
      cancelled
```

#### 进度更新策略

每个聚合步骤完成后更新进度：

- 每天有6个聚合步骤
- 每完成一个步骤，更新 `current_step` 和 `progress`
- 前端轮询获取最新进度

#### 并发控制

- 同时只允许一个刷新任务运行
- 如果有正在运行的任务，新任务返回错误提示
- 支持取消当前任务后创建新任务

### 文件变更清单

| 文件                                       | 变更类型 | 说明                         |
| ---------------------------------------- | ---- | -------------------------- |
| `backend/app/local_models.py`            | 修改   | 添加 LocalAggregationTask 模型 |
| `backend/app/admin.py`                   | 修改   | 添加任务管理API，改造刷新接口           |
| `backend/app/task_executor.py`           | 新增   | 后台任务执行器                    |
| `frontend/src/components/AdminPanel.vue` | 修改   | 改用轮询方式获取进度                 |

### 优势

1. **可靠性**：任务状态持久化，不受连接中断影响
2. **可恢复**：支持查看历史任务，可重新执行失败任务
3. **可控性**：支持取消正在运行的任务
4. **可扩展**：未来可扩展为分布式任务队列（如 Celery）
5. **用户体验**：前端可以关闭页面后重新查看任务状态

### 风险与缓解

| 风险      | 缓解措施                       |
| ------- | -------------------------- |
| 后台线程崩溃  | 添加异常捕获，更新任务状态为 failed      |
| 数据库连接泄漏 | 使用 context manager 管理数据库会话 |
| 并发冲突    | 使用锁机制确保同时只有一个任务运行          |
| 内存占用    | 任务完成后及时清理资源                |

## 实施计划

1. **Phase 1**: 数据模型和迁移
   - 添加 LocalAggregationTask 模型
   - 创建数据库表
   - 更新数据库初始化代码
2. **Phase 2**: 后端核心功能
   - 实现任务执行器
   - 添加任务管理 API
3. **Phase 3**: 前端适配
   - 改造 AdminPanel.vue
   - 添加任务列表显示
4. **Phase 4**: 测试和优化
   - 功能测试
   - 性能测试
   - 错误处理完善

