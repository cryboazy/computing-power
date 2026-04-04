# 清理无用代码、文档和空目录规范

## 1. 概述

本规范用于清理项目中无用的代码、文档和空目录，提高代码质量和项目可维护性。

## 2. 清理范围

### 2.1 无用代码

#### 2.1.1 未使用的导入

| 文件 | 无用导入 | 说明 |
|------|---------|------|
| `backend/app/admin.py` | `secrets` | 导入但未使用 |
| `backend/app/api_cached.py` | `case`, `literal_column` | 导入但未使用 |
| `backend/app/aggregator.py` | `case` | 导入但未使用 |

### 2.2 重复/遗留文档

#### 2.2.1 重复的 specs 目录

项目中存在两个规范目录：
- `.specs/` - 数据导出功能规范（已完成实现）
- `specs/` - 分析报告功能规范（已完成实现）

两个目录的内容均为已完成功能的规范文档，可根据需要保留或删除。

**建议**：保留 `.specs/` 目录作为规范目录，删除 `specs/` 目录（内容已合并或不再需要）。

### 2.3 空文件

| 文件 | 说明 |
|------|------|
| `backend/app/__init__.py` | 空文件，但作为 Python 包标识文件，**保留** |

## 3. 清理操作

### 3.1 删除未使用的导入

#### 3.1.1 backend/app/admin.py

删除第 2 行的 `secrets` 导入：
```python
# 删除前
import hashlib
import secrets
import json

# 删除后
import hashlib
import json
```

#### 3.1.2 backend/app/api_cached.py

修改第 4 行，删除 `case` 和 `literal_column`：
```python
# 删除前
from sqlalchemy import func, and_, or_, case, desc, literal_column

# 删除后
from sqlalchemy import func, and_, or_, desc
```

#### 3.1.3 backend/app/aggregator.py

修改第 4 行，删除 `case`：
```python
# 删除前
from sqlalchemy import func, and_, or_, case

# 删除后
from sqlalchemy import func, and_, or_
```

### 3.2 删除重复目录

删除 `specs/` 目录及其所有内容：
- `specs/spec.md`
- `specs/tasks.md`
- `specs/checklist.md`

## 4. 保留内容

以下内容经分析后确认需要保留：

| 内容 | 保留原因 |
|------|---------|
| `backend/app/__init__.py` | Python 包标识文件 |
| `.specs/` 目录 | 当前使用的规范目录 |
| 所有模型文件 | 均被引用使用 |
| 所有组件文件 | 均被引用使用 |

## 5. 风险评估

| 操作 | 风险等级 | 说明 |
|------|---------|------|
| 删除未使用导入 | 低 | 不影响功能 |
| 删除 specs 目录 | 低 | 规范文档，不影响代码运行 |

## 6. 验证方法

1. 删除未使用导入后，运行 Python 语法检查
2. 删除目录后，确认项目结构完整
3. 运行项目确保无报错
