# 清理无用代码、文档和空目录 - 任务清单

## 任务列表

### Task 1: 清理 admin.py 中未使用的导入
- **描述**: 删除 `backend/app/admin.py` 中未使用的 `secrets` 导入
- **文件**: `backend/app/admin.py`
- **操作**: 删除第 2 行 `import secrets`
- **验证**: Python 语法检查通过

### Task 2: 清理 api_cached.py 中未使用的导入
- **描述**: 删除 `backend/app/api_cached.py` 中未使用的 `case` 和 `literal_column` 导入
- **文件**: `backend/app/api_cached.py`
- **操作**: 修改第 4 行，删除 `case` 和 `literal_column`
- **验证**: Python 语法检查通过

### Task 3: 清理 aggregator.py 中未使用的导入
- **描述**: 删除 `backend/app/aggregator.py` 中未使用的 `case` 导入
- **文件**: `backend/app/aggregator.py`
- **操作**: 修改第 4 行，删除 `case`
- **验证**: Python 语法检查通过

### Task 4: 删除重复的 specs 目录
- **描述**: 删除 `specs/` 目录及其所有内容
- **文件**: 
  - `specs/spec.md`
  - `specs/tasks.md`
  - `specs/checklist.md`
- **操作**: 删除整个 `specs/` 目录
- **验证**: 确认目录已删除，项目结构完整

### Task 5: 验证清理结果
- **描述**: 验证清理后项目正常运行
- **操作**:
  1. 检查 Python 语法
  2. 确认项目结构完整
  3. 确认无运行时错误
- **验收标准**: 项目正常启动，无报错
