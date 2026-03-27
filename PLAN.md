# GPU档次管理重构计划

## 一、现状分析

### 1.1 数据库情况
- ✅ 远程数据库 `gpu_card_info` 表有 `card_type` 字段（1-高端, 2-中端, 3-低端），但**不在字典表中**
- ✅ 本地存在 `LocalPurposeDict` 表（用途字典缓存）
- ❌ 本地**不存在** GPU 档次字典表
- **决定**：GPU 档次字典完全在**本地数据库**管理，不使用远程 `sys_dict_data` 表

### 1.2 后端代码问题
1. **重复代码**：GPU档次分类逻辑在 [api_cached.py](file:///e:\dev\computing-power\backend\app\api_cached.py) 中重复出现 4 次
2. **硬编码**：`card_type` 值（1, 2, 3）和档次名称均为硬编码
3. **缺乏配置**：无法动态调整档次分类规则
4. **维护困难**：修改需要改动多处代码

### 1.3 前端代码问题
1. **重复代码**：GPU档次图表配置在多个组件中重复
   - [CenterPanel.vue](file:///e:\dev\computing-power\frontend\src\components\CenterPanel.vue) (第 1139 行)
   - [MultiOrgUsageDialog.vue](file:///e:\dev\computing-power\frontend\src\components\MultiOrgUsageDialog.vue) (第 1055 行)
   - [DeviceDetailTab.vue](file:///e:\dev\computing-power\frontend\src\components\DeviceDetailTab.vue)

2. **硬编码**：档次名称和键名在前端多处硬编码
   ```javascript
   const tierNames = ['高端卡', '中端卡', '低端卡', '未知']
   const tierKeys = ['high', 'medium', 'low', 'unknown']
   ```

3. **缺乏统一管理**：前后端档次配置不同步，容易导致不一致

---

## 二、实施计划

### 步骤 1：检查远程数据库结构 ✅
**文件**：`backend/app/models.py`
- 确认 `GpuCardInfo` 表的 `card_type` 字段
- `card_type` 值（1, 2, 3）是固定值，从远程 GPU 卡信息中获取
- **无需修改**，远程只提供 GPU 卡的基础信息

### 步骤 2：创建本地数据库表

#### 2.1 新增模型
**文件**：`backend/app/local_models.py`

```python
class LocalGpuTierDict(LocalBase):
    """GPU档次字典表 - 完全本地管理"""
    __tablename__ = "cached_gpu_tier_dict"

    id = Column(BigInteger, primary_key=True)
    dict_type = Column(String(100), nullable=False)  # "gpu_tier"
    dict_label = Column(String(100), nullable=False)  # "高端卡", "中端卡", "低端卡"
    dict_value = Column(Integer, nullable=False)     # 1, 2, 3（对应 card_type）
    dict_sort = Column(Integer, default=0)
    status = Column(SmallInteger, default=1)
    remark = Column(String(500), default="")
    deleted = Column(SmallInteger, default=0)
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        Index('idx_cached_tier_type', 'dict_type'),
        Index('idx_cached_tier_value', 'dict_value'),
        Index('idx_cached_tier_label', 'dict_label'),
    )
```

**说明**：
- `dict_value` 对应远程 `gpu_card_info.card_type` 的值（1, 2, 3）
- `dict_label` 是可配置的显示名称（如"高端卡"、"中端卡"、"低端卡"）
- 完全本地管理，不从远程同步

#### 2.2 更新初始化脚本
**文件**：`backend/app/init_local_db.py`

```python
def init_local_gpu_tier_dict(db):
    """初始化 GPU 档次字典"""
    tier_dicts = [
        {"id": 1, "dict_label": "高端卡", "dict_value": 1, "dict_sort": 1, "remark": "GPU档次-高端卡"},
        {"id": 2, "dict_label": "中端卡", "dict_value": 2, "dict_sort": 2, "remark": "GPU档次-中端卡"},
        {"id": 3, "dict_label": "低端卡", "dict_value": 3, "dict_sort": 3, "remark": "GPU档次-低端卡"}
    ]

    for d in tier_dicts:
        existing = db.query(LocalGpuTierDict).filter(
            LocalGpuTierDict.dict_type == 'gpu_tier',
            LocalGpuTierDict.dict_value == d["dict_value"]
        ).first()
        if not existing:
            tier_dict = LocalGpuTierDict(
                id=d["id"],
                dict_type='gpu_tier',
                dict_label=d["dict_label"],
                dict_value=d["dict_value"],
                dict_sort=d["dict_sort"],
                status=1,
                remark=d["remark"],
                deleted=0
            )
            db.add(tier_dict)

    db.commit()
    print("本地GPU档次字典初始化完成")
```

**需更新文件**：
1. `backend/app/local_models.py` - 添加 `LocalGpuTierDict` 模型
2. `backend/app/init_local_db.py` - 添加初始化函数并调用

### 步骤 3：实现后端管理功能

#### 3.1 后端 API（admin.py）
**需添加的 API 端点**：

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | /admin/dict/gpu-tier | 获取所有档次 |
| POST | /admin/dict/gpu-tier | 创建档次 |
| GET | /admin/dict/gpu-tier/{id} | 获取单个档次 |
| PUT | /admin/dict/gpu-tier/{id} | 更新档次 |
| PATCH | /admin/dict/gpu-tier/{id}/status | 更新状态 |
| DELETE | /admin/dict/gpu-tier/{id} | 删除档次 |

**Pydantic 模型**：
```python
class GpuTierDictRequest(BaseModel):
    dict_label: str
    dict_value: int
    dict_sort: int = 0
    status: int = 1
    remark: str = ""

class GpuTierStatusRequest(BaseModel):
    status: int
```

**验证规则**：
- ✅ `dict_value` 必须唯一（对应 `card_type` 值）
- ✅ `dict_label` 必须唯一（显示名称）
- ✅ `dict_value` 建议在 1-10 范围内
- ✅ 至少保留一个启用的档次

#### 3.2 前端管理页面（AdminPanel.vue）
**新增 Tab 页**：GPU档次管理

**功能要求**：
- ✅ 表格展示档次列表
- ✅ 添加按钮：打开添加对话框
- ✅ 编辑按钮：打开编辑对话框
- ✅ 删除按钮：确认删除
- ✅ 状态切换：启用/禁用开关
- ✅ 表单验证：唯一性检查
- ✅ 批量选择：支持多选操作

**UI 组件示例**：
```vue
<el-tab-pane label="GPU档次管理" name="gpu-tier">
  <div class="tier-header">
    <el-button type="primary" @click="openAddTierDialog">
      添加档次
    </el-button>
    <el-button @click="batchDeleteTier" :disabled="selectedTiers.length === 0">
      批量删除
    </el-button>
  </div>

  <el-table :data="tierList" @selection-change="handleTierSelection">
    <el-table-column type="selection" width="55" />
    <el-table-column prop="dict_value" label="档次值" width="100">
      <template #default="scope">
        <el-tag type="info">{{ scope.row.dict_value }}</el-tag>
      </template>
    </el-table-column>
    <el-table-column prop="dict_label" label="档次名称" />
    <el-table-column prop="dict_sort" label="排序" width="100" />
    <el-table-column prop="status" label="状态" width="100">
      <template #default="scope">
        <el-switch v-model="scope.row.status" @change="updateTierStatus(scope.row)" />
      </template>
    </el-table-column>
    <el-table-column label="操作" width="200" fixed="right">
      <template #default="scope">
        <el-button size="small" @click="openEditTierDialog(scope.row)">编辑</el-button>
        <el-button size="small" type="danger" @click="deleteTier(scope.row.id)">删除</el-button>
      </template>
    </el-table-column>
  </el-table>

  <!-- 添加/编辑对话框 -->
  <el-dialog v-model="tierDialogVisible">
    <el-form :model="tierForm" :rules="tierRules" ref="tierFormRef">
      <el-form-item label="档次值" prop="dict_value">
        <el-input-number v-model="tierForm.dict_value" :min="1" :max="10" />
        <span class="form-tip">对应 GPU 卡的 card_type 值</span>
      </el-form-item>
      <el-form-item label="档次名称" prop="dict_label">
        <el-input v-model="tierForm.dict_label" placeholder="如：高端卡、中端卡" />
      </el-form-item>
      <el-form-item label="排序">
        <el-input-number v-model="tierForm.dict_sort" :min="0" />
      </el-form-item>
      <el-form-item label="备注">
        <el-input type="textarea" v-model="tierForm.remark" />
      </el-form-item>
    </el-form>
  </el-dialog>
</el-tab-pane>
```

### 步骤 4：重构后端现有代码

#### 4.1 创建公共工具模块
**新建文件**：`backend/app/gpu_tier_utils.py`

```python
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from app.local_models import LocalGpuTierDict

class GPUTierManager:
    """GPU档次管理器 - 完全本地管理"""

    DEFAULT_TIERS = {
        1: {"label": "高端卡", "key": "high"},
        2: {"label": "中端卡", "key": "medium"},
        3: {"label": "低端卡", "key": "low"}
    }

    def __init__(self, db: Session):
        self.db = db
        self._cache = None

    def _load_tiers(self) -> Dict[int, Dict]:
        """从数据库加载档次配置"""
        if self._cache is not None:
            return self._cache

        tiers = self.db.query(LocalGpuTierDict).filter(
            LocalGpuTierDict.dict_type == "gpu_tier",
            LocalGpuTierDict.status == 1,
            LocalGpuTierDict.deleted == 0
        ).order_by(LocalGpuTierDict.dict_sort).all()

        self._cache = {}
        for tier in tiers:
            self._cache[tier.dict_value] = {
                "label": tier.dict_label,
                "key": tier.dict_label,  # 使用 label 作为 key
                "id": tier.id
            }

        # 如果缓存为空，使用默认值
        if not self._cache:
            self._cache = self.DEFAULT_TIERS.copy()

        return self._cache

    def invalidate_cache(self):
        """清除缓存"""
        self._cache = None

    def get_tier_label(self, card_type: int) -> str:
        """根据 card_type 获取档次名称"""
        tiers = self._load_tiers()
        tier = tiers.get(card_type)
        if tier:
            return tier["label"]
        # 使用默认映射
        return self.DEFAULT_TIERS.get(card_type, {}).get("label", "未知")

    def get_tier_key(self, card_type: int) -> str:
        """根据 card_type 获取档次 key"""
        tiers = self._load_tiers()
        tier = tiers.get(card_type)
        if tier:
            return tier["key"]
        # 使用默认 key
        default = self.DEFAULT_TIERS.get(card_type, {})
        return default.get("key", "unknown")

    def get_all_tiers(self) -> List[Dict]:
        """获取所有启用的档次"""
        tiers = self._load_tiers()
        return [
            {"value": k, "label": v["label"], "name": v["label"]}
            for k, v in sorted(tiers.items())
        ]

    def get_tier_map(self) -> Dict[int, str]:
        """获取 card_type 到档次 key 的映射"""
        tiers = self._load_tiers()
        result = {}
        for card_type, tier_info in tiers.items():
            result[card_type] = tier_info["key"]

        # 补充默认值
        for card_type, default_info in self.DEFAULT_TIERS.items():
            if card_type not in result:
                result[card_type] = default_info["key"]

        return result

    def get_label_map(self) -> Dict[int, str]:
        """获取 card_type 到档次名称的映射"""
        tiers = self._load_tiers()
        result = {}
        for card_type, tier_info in tiers.items():
            result[card_type] = tier_info["label"]

        # 补充默认值
        for card_type, default_info in self.DEFAULT_TIERS.items():
            if card_type not in result:
                result[card_type] = default_info["label"]

        return result

    def calculate_tier_counts(self, gpu_infos: Dict, devices: List) -> Dict[str, int]:
        """计算各档次的GPU数量"""
        tier_counts = {
            "high": 0, "medium": 0, "low": 0, "unknown": 0
        }

        tier_key_map = self.get_tier_map()

        for device in devices:
            gpu_model = device.gpu_model or ""
            gpu_info = gpu_infos.get(gpu_model)
            gpu_count = device.gpu_count or 1

            if gpu_info:
                tier_key = tier_key_map.get(gpu_info.card_type)
                if tier_key and tier_key in tier_counts:
                    tier_counts[tier_key] += gpu_count
                else:
                    tier_counts["unknown"] += gpu_count
            else:
                tier_counts["unknown"] += gpu_count

        return tier_counts

    def format_tier_result(self, tier_counts: Dict) -> List[Dict]:
        """格式化档次统计结果"""
        label_map = self.get_label_map()

        # 构建结果
        result = []
        for card_type, label in sorted(label_map.items()):
            tier_key = self.get_tier_key(card_type)
            if tier_key in tier_counts:
                result.append({
                    "name": label,
                    "value": tier_counts[tier_key]
                })

        # 添加未知
        result.append({
            "name": "未知",
            "value": tier_counts.get("unknown", 0)
        })

        return result

    def format_tier_by_org_result(self, tier_counts: Dict, org_name: str) -> Dict:
        """格式化按组织统计的档次结果"""
        label_map = self.get_label_map()

        result = {
            "org_name": org_name
        }

        for card_type, label in sorted(label_map.items()):
            tier_key = self.get_tier_key(card_type)
            if tier_key in tier_counts:
                result[tier_key] = tier_counts[tier_key]

        result["unknown"] = tier_counts.get("unknown", 0)
        result["total"] = sum(tier_counts.values())

        return result
```

#### 4.2 重构 api_cached.py
**需重构的函数**（共 4 个）：

1. **get_gpu_tier_distribution** (约第 716 行)
2. **get_gpu_tier_by_org_distribution** (约第 757 行)
3. **get_local_gpu_tier** (约第 1162 行)
4. **get_central_gpu_tier** (约第 1358 行)

**重构示例**：

```python
# 重构前（硬编码）
for device in devices:
    gpu_model = device.gpu_model or ""
    gpu_info = gpu_infos.get(gpu_model)
    gpu_count = device.gpu_count or 1
    if gpu_info:
        if gpu_info.card_type == 1:
            tier_counts["high"] += gpu_count
        elif gpu_info.card_type == 2:
            tier_counts["medium"] += gpu_count
        elif gpu_info.card_type == 3:
            tier_counts["low"] += gpu_count
        else:
            tier_counts["unknown"] += gpu_count
    else:
        tier_counts["unknown"] += gpu_count

return [
    {"name": "高端卡", "value": tier_counts["high"]},
    {"name": "中端卡", "value": tier_counts["medium"]},
    {"name": "低端卡", "value": tier_counts["low"]},
    {"name": "未知", "value": tier_counts["unknown"]}
]
```

```python
# 重构后（可配置）
from app.gpu_tier_utils import GPUTierManager

tier_manager = GPUTierManager(local_db)

tier_counts = tier_manager.calculate_tier_counts(gpu_infos, devices)

return tier_manager.format_tier_result(tier_counts)
```

#### 4.3 移除缓存同步逻辑
**说明**：
- ❌ 不需要从远程同步 GPU 档次字典
- ✅ GPU 档次字典完全在本地管理和配置
- ✅ 本地初始化脚本负责创建默认档次

---

### 步骤 5：重构前端现有代码

#### 5.1 创建前端工具模块
**新建文件**：`frontend/src/utils/gpuTierUtils.js`

```javascript
// GPU档次工具函数

// 默认档次配置
export const DEFAULT_TIER_CONFIG = {
  1: { label: '高端卡', key: 'high' },
  2: { label: '中端卡', key: 'medium' },
  3: { label: '低端卡', key: 'low' }
}

// 默认档次键名
export const DEFAULT_TIER_KEYS = ['high', 'medium', 'low', 'unknown']

// 默认档次名称
export const DEFAULT_TIER_NAMES = ['高端卡', '中端卡', '低端卡', '未知']

// 档次颜色配置
export const TIER_COLORS = {
  high: '#f56c6c',      // 红色
  medium: '#e6a23c',    // 橙色
  low: '#67c23a',       // 绿色
  unknown: '#909399'    // 灰色
}

// 创建统一的状态对象
let tierConfig = { ...DEFAULT_TIER_CONFIG }
let tierKeys = [...DEFAULT_TIER_KEYS]
let tierNames = [...DEFAULT_TIER_NAMES]

// 更新档次配置
export function updateTierConfig(config) {
  if (!config || !Array.isArray(config)) {
    tierConfig = { ...DEFAULT_TIER_CONFIG }
    tierKeys = [...DEFAULT_TIER_KEYS]
    tierNames = [...DEFAULT_TIER_NAMES]
    return
  }

  tierConfig = {}
  tierKeys = []
  tierNames = []

  config.forEach(item => {
    tierConfig[item.value] = {
      label: item.label,
      key: item.label
    }
    tierKeys.push(item.label)
    tierNames.push(item.label)
  })

  tierKeys.push('unknown')
  tierNames.push('未知')
}

// 获取档次键名
export function getTierKeys() {
  return tierKeys
}

// 获取档次名称
export function getTierNames() {
  return tierNames
}

// 获取档次配置
export function getTierConfig() {
  return { ...tierConfig }
}

// 根据 card_type 获取档次键名
export function getTierKey(cardType) {
  const config = tierConfig[cardType]
  if (config) {
    return config.key
  }
  const defaultConfig = DEFAULT_TIER_CONFIG[cardType]
  return defaultConfig ? defaultConfig.key : 'unknown'
}

// 根据 card_type 获取档次名称
export function getTierLabel(cardType) {
  const config = tierConfig[cardType]
  if (config) {
    return config.label
  }
  const defaultConfig = DEFAULT_TIER_CONFIG[cardType]
  return defaultConfig ? defaultConfig.label : '未知'
}

// 格式化档次数据
export function formatTierData(data) {
  if (!data || !Array.isArray(data)) {
    return []
  }
  return data.map(item => ({
    name: item.name || getTierLabel(item.value),
    value: item.value || 0
  }))
}

// 提取档次统计结果
export function extractTierCounts(data, keys = null) {
  if (!data) {
    return null
  }

  const tierKeys = keys || getTierKeys()
  const result = {}

  tierKeys.forEach(key => {
    result[key] = 0
  })

  if (Array.isArray(data)) {
    data.forEach(item => {
      if (item.name && result.hasOwnProperty(item.name)) {
        result[item.name] = item.value || 0
      }
    })
  }

  return result
}

// 计算档次总数
export function calculateTierTotal(data) {
  if (!data || !Array.isArray(data)) {
    return 0
  }
  return data.reduce((sum, item) => sum + (item.value || 0), 0)
}
```

#### 5.2 创建统一的状态管理
**新建文件**：`frontend/src/store/gpuTierStore.js`

```javascript
// GPU档次状态管理
import { ref } from 'vue'
import axios from 'axios'

const tierList = ref([])
const isLoading = ref(false)
const error = ref(null)

// 加载档次列表
export async function loadTierList() {
  if (isLoading.value) return tierList.value

  isLoading.value = true
  error.value = null

  try {
    const response = await axios.get('/api/admin/dict/gpu-tier')
    tierList.value = response.data || []

    // 更新工具函数配置
    updateTierConfig(tierList.value)

    return tierList.value
  } catch (err) {
    error.value = err.message
    console.error('加载GPU档次列表失败:', err)
    return []
  } finally {
    isLoading.value = false
  }
}

// 获取档次列表
export function getTierList() {
  return tierList.value
}

// 获取档次配置供图表使用
export function getTierConfigForChart() {
  if (tierList.value.length === 0) {
    return {
      names: [...DEFAULT_TIER_NAMES],
      keys: [...DEFAULT_TIER_KEYS],
      colors: Object.values(TIER_COLORS)
    }
  }

  const names = tierList.value.map(t => t.dict_label)
  const keys = tierList.value.map(t => t.dict_label)
  names.push('未知')
  keys.push('unknown')

  return {
    names,
    keys,
    colors: Object.values(TIER_COLORS)
  }
}

export default {
  tierList,
  isLoading,
  error,
  loadTierList,
  getTierList,
  getTierConfigForChart
}
```

#### 5.3 重构 CenterPanel.vue
**文件**：`frontend/src/components/CenterPanel.vue`

**重构前** (第 1136-1140 行)：
```javascript
const gpuTierOption = computed(() => {
  const colors = getAllColors()
  const tierColors = [colors.chart3, colors.chart4, colors.chart5, colors.chart6]
  const tierNames = ['高端卡', '中端卡', '低端卡', '未知']  // 硬编码
  const tierKeys = ['high', 'medium', 'low', 'unknown']    // 硬编码
  // ...
})
```

**重构后**：
```javascript
import { getTierNames, getTierKeys, TIER_COLORS } from '@/utils/gpuTierUtils'
import { getTierConfigForChart } from '@/store/gpuTierStore'

const gpuTierOption = computed(() => {
  const colors = getAllColors()
  const tierColors = [colors.chart3, colors.chart4, colors.chart5, colors.chart6]
  const { names: tierNames, keys: tierKeys } = getTierConfigForChart()
  // ...
})
```

#### 5.4 重构 MultiOrgUsageDialog.vue
**文件**：`frontend/src/components/MultiOrgUsageDialog.vue`

**重构前** (第 1051-1056 行)：
```javascript
const gpuTierOption = computed(() => {
  const orgNames = gpuTierByOrgData.value.map(d => d.org_name)

  const colors = ['#f56c6c', '#e6a23c', '#67c23a', '#909399']  // 硬编码颜色
  const tierNames = ['高端卡', '中端卡', '低端卡', '未知']      // 硬编码
  const tierKeys = ['high', 'medium', 'low', 'unknown']        // 硬编码
  // ...
})
```

**重构后**：
```javascript
import { getTierNames, getTierKeys, TIER_COLORS } from '@/utils/gpuTierUtils'
import { getTierConfigForChart } from '@/store/gpuTierStore'

const gpuTierOption = computed(() => {
  const orgNames = gpuTierByOrgData.value.map(d => d.org_name)

  const { names: tierNames, keys: tierKeys } = getTierConfigForChart()
  const colors = Object.values(TIER_COLORS)
  // ...
})
```

#### 5.5 重构 DeviceDetailTab.vue
**需检查并重构 GPU 档次相关的显示逻辑**。

#### 5.6 更新 API 调用
**文件**：`frontend/src/api/index.js`

```javascript
export const adminApi = {
  // 现有用途字典 API...

  // GPU 档次字典 API
  getGpuTierDict: () => api.get('/admin/dict/gpu-tier'),
  createGpuTier: (data) => api.post('/admin/dict/gpu-tier', data),
  updateGpuTier: (id, data) => api.put(`/admin/dict/gpu-tier/${id}`, data),
  deleteGpuTier: (id) => api.delete(`/admin/dict/gpu-tier/${id}`),
  updateGpuTierStatus: (id, status) => api.patch(`/admin/dict/gpu-tier/${id}/status`, { status })
}
```

#### 5.7 在应用启动时加载档次配置
**文件**：`frontend/src/main.js` 或 App.vue`

```javascript
import { loadTierList } from '@/store/gpuTierStore'

// 在应用启动时加载档次配置
onMounted(async () => {
  await loadTierList()
})
```

---

## 三、文件清单

### 3.1 后端新建文件
1. `backend/app/gpu_tier_utils.py` - GPU档次管理工具类
2. `backend/tests/test_gpu_tier.py` - 单元测试文件

### 3.2 后端修改文件
1. `backend/app/local_models.py` - 添加 `LocalGpuTierDict` 模型
2. `backend/app/admin.py` - 添加 GPU 档次管理 API（6 个端点）
3. `backend/app/api_cached.py` - 重构 4 个 GPU 档次相关 API
4. `backend/app/init_local_db.py` - 添加初始化 GPU 档次字典的函数

### 3.3 前端新建文件
1. `frontend/src/utils/gpuTierUtils.js` - GPU档次工具函数
2. `frontend/src/store/gpuTierStore.js` - GPU档次状态管理
3. `frontend/src/api/index.js` - 添加 GPU 档次 API 调用

### 3.4 前端修改文件
1. `frontend/src/components/AdminPanel.vue` - 添加 GPU 档次管理页面
2. `frontend/src/components/CenterPanel.vue` - 重构 GPU 档次图表配置
3. `frontend/src/components/MultiOrgUsageDialog.vue` - 重构 GPU 档次图表配置
4. `frontend/src/components/DeviceDetailTab.vue` - 重构 GPU 档次显示
5. `frontend/src/App.vue` 或 `main.js` - 添加应用启动时加载档次配置

---

## 四、API 端点清单

### 4.1 后端管理 API（admin.py）

| 方法 | 端点 | 描述 | 请求体 |
|------|------|------|--------|
| GET | /admin/dict/gpu-tier | 获取所有档次 | - |
| POST | /admin/dict/gpu-tier | 创建档次 | {dict_label, dict_value, dict_sort, status, remark} |
| GET | /admin/dict/gpu-tier/{id} | 获取单个档次 | - |
| PUT | /admin/dict/gpu-tier/{id} | 更新档次 | {dict_label, dict_value, dict_sort, status, remark} |
| PATCH | /admin/dict/gpu-tier/{id}/status | 更新状态 | {status: 0\|1} |
| DELETE | /admin/dict/gpu-tier/{id} | 删除档次 | - |

### 4.2 后端数据 API（api_cached.py）- 重构

| 方法 | 端点 | 描述 | 重构后 |
|------|------|------|--------|
| GET | /distribution/gpu-tier | GPU档次分布 | 使用 GPUTierManager |
| GET | /distribution/gpu-tier-by-org | 按组织GPU档次分布 | 使用 GPUTierManager |
| GET | /local/gpu-tier | 本地GPU档次 | 使用 GPUTierManager |
| GET | /central/gpu-tier | 中心GPU档次 | 使用 GPUTierManager |

### 4.3 前端 API（index.js）

| 方法 | 函数 | 描述 |
|------|------|------|
| GET | getGpuTierDict | 获取档次列表 |
| POST | createGpuTier | 创建档次 |
| PUT | updateGpuTier | 更新档次 |
| DELETE | deleteGpuTier | 删除档次 |
| PATCH | updateGpuTierStatus | 更新状态 |

---

## 五、测试计划

### 5.1 后端单元测试
**测试文件**：`backend/tests/test_gpu_tier.py`

```python
import pytest
from app.gpu_tier_utils import GPUTierManager
from app.local_models import LocalGpuTierDict

def test_get_default_tiers(db_session):
    """测试默认档次"""
    manager = GPUTierManager(db_session)
    tiers = manager.get_all_tiers()
    assert len(tiers) >= 3
    assert any(t['value'] == 1 for t in tiers)

def test_calculate_tier_counts(db_session):
    """测试档次计数"""
    manager = GPUTierManager(db_session)

    class MockGPUInfo:
        def __init__(self, card_type):
            self.card_type = card_type

    class MockDevice:
        def __init__(self, gpu_model, gpu_count):
            self.gpu_model = gpu_model
            self.gpu_count = gpu_count

    gpu_infos = {
        'A100': MockGPUInfo(1),
        'V100': MockGPUInfo(2),
        'T4': MockGPUInfo(3)
    }

    devices = [
        MockDevice('A100', 4),
        MockDevice('V100', 2),
        MockDevice('T4', 8)
    ]

    counts = manager.calculate_tier_counts(gpu_infos, devices)
    assert counts['high'] == 4
    assert counts['medium'] == 2
    assert counts['low'] == 8

def test_format_tier_result(db_session):
    """测试结果格式化"""
    manager = GPUTierManager(db_session)
    counts = {"high": 10, "medium": 20, "low": 30, "unknown": 5}
    result = manager.format_tier_result(counts)
    assert len(result) == 4  # high, medium, low, unknown
    assert result[0]['name'] in ['高端卡', 'High']
```

### 5.2 前端单元测试
**测试文件**：`frontend/tests/unit/gpuTierUtils.spec.js`

```javascript
import { describe, it, expect } from 'vitest'
import {
  getTierNames,
  getTierKeys,
  getTierConfig,
  updateTierConfig,
  extractTierCounts
} from '@/utils/gpuTierUtils'

describe('GPU Tier Utils', () => {
  it('should return default tier names', () => {
    const names = getTierNames()
    expect(names).toContain('高端卡')
    expect(names).toContain('中端卡')
    expect(names).toContain('低端卡')
  })

  it('should update tier config dynamically', () => {
    updateTierConfig([
      { value: 1, label: '高级卡' },
      { value: 2, label: '中级卡' }
    ])

    const names = getTierNames()
    expect(names).toContain('高级卡')
    expect(names).toContain('中级卡')
  })

  it('should extract tier counts correctly', () => {
    const data = [
      { name: '高端卡', value: 10 },
      { name: '中端卡', value: 20 }
    ]

    const counts = extractTierCounts(data)
    expect(counts['高端卡']).toBe(10)
    expect(counts['中端卡']).toBe(20)
  })
})
```

### 5.3 API 测试
- 测试后端 CRUD 操作
- 测试前端 API 调用
- 测试唯一性验证
- 测试状态切换
- 测试软删除

### 5.4 集成测试
- 测试前后端数据同步
- 测试档次配置更新后图表刷新
- 测试重构后 API 响应格式兼容性

### 5.5 重构验证
- 确保所有后端 API 函数正常工作
- 确保所有前端组件正常工作
- 验证返回结果与重构前一致
- 性能测试：确认无性能下降

---

## 六、风险评估

### 6.1 中风险
- **数据一致性**：删除档次后历史数据展示问题
- **版本兼容性**：重构后 API 响应格式兼容性
- **前后端同步**：前端缓存与后端配置同步问题

### 6.2 低风险
- **性能影响**：缓存机制确保性能
- **回退困难**：需要保留原硬编码逻辑作为后备

### 6.3 缓解措施
- ✅ 后端缓存机制减少数据库查询
- ✅ 前端状态管理确保数据一致性
- ✅ 保留 DEFAULT_TIERS 作为后备方案
- ✅ 完善的单元测试覆盖
- ✅ 保持 API 响应格式完全兼容
- ✅ 应用启动时自动加载最新配置

---

## 七、时间估算

| 步骤 | 任务 | 时间 |
|------|------|------|
| 1 | 检查远程数据库结构 | 0.5 天 |
| 2 | 创建本地数据库表和模型 | 1 天 |
| 3 | 实现后端管理 API | 1 天 |
| 4 | 实现前端管理页面 | 1 天 |
| 5 | 重构后端 api_cached.py | 1 天 |
| 6 | 创建前端工具模块和状态管理 | 0.5 天 |
| 7 | 重构前端组件 | 1 天 |
| 8 | 测试与验证 | 1 天 |

**总计：7 天**

---

## 八、预期成果

### 8.1 代码质量提升
- ✅ 消除 100% 的 GPU 档次硬编码（后端）
- ✅ 消除 100% 的 GPU 档次硬编码（前端）
- ✅ 消除后端 4 处重复代码
- ✅ 消除前端 3 处重复代码
- ✅ 代码复用率提升 80%

### 8.2 功能增强
- ✅ 可配置的 GPU 档次管理
- ✅ 完整的 CRUD 操作
- ✅ 批量操作支持
- ✅ 前后端配置同步
- ✅ 动态图表更新

### 8.3 可维护性提升
- ✅ 单一职责：档次管理逻辑独立
- ✅ 可扩展性：易于添加新档次
- ✅ 可测试性：完整的单元测试覆盖
- ✅ 统一管理：前后端使用相同的配置源

### 8.4 用户体验提升
- ✅ 实时更新：管理界面修改后图表自动刷新
- ✅ 一致性：前后端档次名称完全一致
- ✅ 灵活性：可根据业务需求灵活调整档次

---

**计划制定完成，请确认后开始实施。**
