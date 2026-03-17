<template>
  <el-dialog
    v-model="dialogVisible"
    width="90%"
    top="2vh"
    :close-on-click-modal="false"
    :close-on-press-escape="true"
    :show-close="false"
    :fullscreen="isMaximized"
    class="org-detail-dialog"
    append-to-body
    @closed="handleClosed"
  >
    <template #header>
      <div class="dialog-header">
        <div class="header-decoration">
          <span class="decoration-line"></span>
          <span class="decoration-dot"></span>
        </div>
        <h3 class="dialog-title">{{ orgName || '组织机构详情' }}</h3>
        <div class="header-decoration right">
          <span class="decoration-dot"></span>
          <span class="decoration-line"></span>
        </div>
        <div class="window-controls">
          <button class="control-btn" @click="toggleMaximize" :title="isMaximized ? '还原' : '最大化'">
            <svg v-if="!isMaximized" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
            </svg>
            <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M8 3v3a2 2 0 0 1-2 2H3m18 0h-3a2 2 0 0 1-2-2V3m0 18v-3a2 2 0 0 1 2-2h3M3 16h3a2 2 0 0 1 2 2v3"></path>
            </svg>
          </button>
          <button class="control-btn close-btn" @click="dialogVisible = false" title="关闭">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
      </div>
    </template>
    
    <div class="dialog-content">
      <div v-if="loading" class="loading-container">
        <el-icon class="is-loading" :size="40"><Loading /></el-icon>
        <span>加载中...</span>
      </div>
      
      <div v-else-if="error" class="error-container">
        <el-icon :size="40" color="var(--theme-danger)"><Warning /></el-icon>
        <span>{{ error }}</span>
        <el-button type="primary" @click="fetchData">重试</el-button>
      </div>
      
      <div v-else class="org-detail-content">
        <div class="tab-nav">
          <div class="tab-items">
            <div 
              v-for="tab in tabs" 
              :key="tab.value"
              :class="['tab-item', { active: activeTab === tab.value }]"
              @click="activeTab = tab.value"
            >
              {{ tab.label }}
            </div>
          </div>
          <div v-if="activeTab === 'usage'" class="tab-controls">
            <div class="quick-select-buttons">
              <el-button 
                size="small" 
                :type="quickSelect === '1m' ? 'primary' : 'default'"
                @click="setQuickSelect('1m')"
              >近一个月</el-button>
              <el-button 
                size="small" 
                :type="quickSelect === '3m' ? 'primary' : 'default'"
                @click="setQuickSelect('3m')"
              >近三个月</el-button>
              <el-button 
                size="small" 
                :type="quickSelect === '6m' ? 'primary' : 'default'"
                @click="setQuickSelect('6m')"
              >近半年</el-button>
              <el-button 
                size="small" 
                :type="quickSelect === '1y' ? 'primary' : 'default'"
                @click="setQuickSelect('1y')"
              >近一年</el-button>
            </div>
            <div class="filter-group">
              <span class="filter-label">用途：</span>
              <el-select
                v-model="selectedPurpose"
                placeholder="全部用途"
                size="small"
                class="purpose-select"
              >
                <el-option
                  v-for="purpose in purposeList"
                  :key="purpose.value"
                  :label="purpose.label"
                  :value="purpose.value"
                />
              </el-select>
            </div>
            <div class="filter-group">
              <span class="filter-label">日期范围：</span>
              <el-date-picker
                v-model="dateRange"
                type="daterange"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                size="small"
                value-format="YYYY-MM-DD"
                @change="onDateRangeChange"
              />
            </div>
          </div>
        </div>
        
        <div class="tab-content">
          <DeviceDetailTab 
            v-if="activeTab === 'devices'"
            :org-detail="orgDetail"
            :org-id="orgId"
          />
          
          <UsageDetailTab 
            v-if="activeTab === 'usage'"
            :org-id="orgId"
            :date-range="dateRange"
            :purpose="selectedPurpose"
          />
        </div>
      </div>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref, watch, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading, Warning } from '@element-plus/icons-vue'
import { dashboardApi } from '../api'
import DeviceDetailTab from './OrgDetailTabs/DeviceDetailTab.vue'
import UsageDetailTab from './OrgDetailTabs/UsageDetailTab.vue'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  orgId: {
    type: [Number, String],
    default: null
  },
  initialTab: {
    type: String,
    default: 'devices'
  }
})

const emit = defineEmits(['update:visible'])

const dialogVisible = computed({
  get: () => props.visible,
  set: (val) => emit('update:visible', val)
})

const activeTab = ref(props.initialTab)
const isMaximized = ref(false)
const loading = ref(false)
const error = ref(null)
const orgDetail = ref(null)
const orgName = ref('')
const quickSelect = ref('3m')

const today = new Date()
const formatDate = (date) => {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

const getDateRange = (type) => {
  const now = new Date()
  let startDate
  switch (type) {
    case '1m':
      startDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)
      break
    case '3m':
      startDate = new Date(now.getTime() - 90 * 24 * 60 * 60 * 1000)
      break
    case '6m':
      startDate = new Date(now.getTime() - 180 * 24 * 60 * 60 * 1000)
      break
    case '1y':
      startDate = new Date(now.getTime() - 365 * 24 * 60 * 60 * 1000)
      break
    default:
      startDate = new Date(now.getTime() - 90 * 24 * 60 * 60 * 1000)
  }
  return [formatDate(startDate), formatDate(now)]
}

const dateRange = ref(getDateRange('3m'))
const selectedPurpose = ref(null)
const purposeList = ref([])

const fetchPurposeList = async () => {
  try {
    const data = await dashboardApi.getPurposeDict()
    const options = data || []
    purposeList.value = [{ value: null, label: '全部用途' }, ...options]
  } catch (error) {
    console.error('Failed to fetch purpose list:', error)
    purposeList.value = [
      { value: null, label: '全部用途' },
      { value: 1, label: '训练' },
      { value: 2, label: '研发' },
      { value: 3, label: '推理' }
    ]
  }
}

const onPurposeChange = () => {
}

onMounted(() => {
  fetchPurposeList()
})

const setQuickSelect = (type) => {
  quickSelect.value = type
  dateRange.value = getDateRange(type)
}

const onDateRangeChange = () => {
  quickSelect.value = null
}

const tabs = [
  { label: '设备详情', value: 'devices' },
  { label: '使用率详情', value: 'usage' }
]

const fetchData = async () => {
  console.log('[OrgDetailDialog] fetchData called with orgId:', props.orgId, 'type:', typeof props.orgId)
  if (!props.orgId) {
    error.value = '无效的组织机构ID'
    return
  }
  
  loading.value = true
  error.value = null
  
  try {
    console.log('[OrgDetailDialog] Calling API...')
    const data = await dashboardApi.getOrgDetail(props.orgId)
    console.log('[OrgDetailDialog] API response:', data)
    if (data.error) {
      console.log('[OrgDetailDialog] API returned error:', data.error)
      error.value = data.error
    } else {
      orgDetail.value = data
      orgName.value = data.org_name
      console.log('[OrgDetailDialog] Data loaded successfully')
    }
  } catch (err) {
    console.error('[OrgDetailDialog] Failed to fetch org detail:', err)
    console.error('[OrgDetailDialog] Error details:', err.response?.data || err.message)
    error.value = '数据加载失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

const toggleMaximize = () => {
  isMaximized.value = !isMaximized.value
}

const handleClosed = () => {
  activeTab.value = props.initialTab
  orgDetail.value = null
  orgName.value = ''
  error.value = null
}

watch(() => props.orgId, (newVal) => {
  if (newVal && dialogVisible.value) {
    fetchData()
  }
})

watch(() => props.visible, (newVal) => {
  if (newVal && props.orgId) {
    if (tabs.some(t => t.value === props.initialTab)) {
      activeTab.value = props.initialTab
    } else {
      activeTab.value = 'devices'
    }
    fetchData()
  }
})

watch(() => props.initialTab, (newVal) => {
  if (tabs.some(t => t.value === newVal)) {
    activeTab.value = newVal
  }
})
</script>

<style lang="scss" scoped>
.org-detail-dialog {
  :deep(.el-dialog__header) {
    padding: 0;
    margin: 0;
  }
  
  :deep(.el-dialog__body) {
    padding: 0;
    height: calc(90vh - 120px);
    min-height: 600px;
  }
}

.dialog-header {
  display: flex;
  align-items: center;
  padding: 18px 25px;
  background: linear-gradient(90deg, 
    var(--theme-hover-bg) 0%, 
    var(--theme-shadow) 20%,
    var(--theme-shadow) 80%,
    var(--theme-hover-bg) 100%
  );
  border-bottom: 1px solid var(--theme-border);
  position: relative;
  
  &::before {
    content: '';
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(90deg, 
      transparent 0%, 
      var(--theme-glow) 50%, 
      transparent 100%
    );
  }
  
  .header-decoration {
    display: flex;
    align-items: center;
    gap: 8px;
    
    &.right {
      margin-right: 80px;
      
      .decoration-line {
        background: linear-gradient(90deg, var(--theme-glow) 0%, transparent 100%);
      }
    }
    
    .decoration-line {
      width: 40px;
      height: 2px;
      background: linear-gradient(90deg, transparent 0%, var(--theme-glow) 100%);
    }
    
    .decoration-dot {
      width: 8px;
      height: 8px;
      background: var(--theme-primary);
      border-radius: 50%;
      box-shadow: 0 0 10px var(--theme-glow-heavy);
    }
  }
  
  .dialog-title {
    flex: 1;
    text-align: center;
    margin: 0 20px;
    font-size: 20px;
    font-weight: 600;
    background: linear-gradient(90deg, var(--theme-primary) 0%, var(--theme-secondary) 50%, var(--theme-primary) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: 4px;
    text-shadow: 0 0 30px var(--theme-glow);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  
  .window-controls {
    position: absolute;
    right: 20px;
    top: 50%;
    transform: translateY(-50%);
    display: flex;
    gap: 8px;
    
    .control-btn {
      width: 36px;
      height: 36px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: linear-gradient(135deg, var(--theme-hover-bg) 0%, var(--theme-shadow) 100%);
      border: 1px solid var(--theme-border-heavy);
      border-radius: 8px;
      cursor: pointer;
      transition: all 0.3s ease;
      
      svg {
        width: 16px;
        height: 16px;
        color: var(--theme-primary);
        transition: all 0.3s ease;
      }
      
      &:hover {
        background: linear-gradient(135deg, var(--theme-border-light) 0%, var(--theme-hover-bg) 100%);
        border-color: var(--theme-primary);
        box-shadow: 0 0 15px var(--theme-glow);
        transform: scale(1.05);
        
        svg {
          color: var(--theme-secondary);
        }
      }
      
      &:active {
        transform: scale(0.95);
      }
      
      &.close-btn {
        &:hover {
          border-color: var(--theme-danger);
          
          svg {
            color: var(--theme-danger);
          }
        }
      }
    }
  }
}

.dialog-content {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--theme-bg-start);
}

.loading-container,
.error-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  color: var(--theme-text-secondary);
  font-size: 14px;
}

.org-detail-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.tab-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--theme-shadow);
  border-bottom: 1px solid var(--theme-border);
  flex-shrink: 0;
  
  .tab-items {
    display: flex;
  }
  
  .tab-item {
    padding: 14px 32px;
    cursor: pointer;
    transition: all 0.3s ease;
    color: var(--theme-text-secondary);
    font-size: 14px;
    font-weight: 500;
    border-bottom: 2px solid transparent;
    position: relative;
    
    &:hover {
      color: var(--theme-primary);
      background: var(--theme-hover-bg);
    }
    
    &.active {
      color: var(--theme-primary);
      border-bottom-color: var(--theme-primary);
      background: var(--theme-hover-bg);
      box-shadow: 0 2px 8px var(--theme-glow);
      
      &::after {
        content: '';
        position: absolute;
        bottom: -2px;
        left: 0;
        right: 0;
        height: 2px;
        background: var(--theme-primary);
      }
    }
  }
  
  .tab-controls {
    display: flex;
    align-items: center;
    gap: 20px;
    padding-right: 20px;
    
    .quick-select-buttons {
      display: flex;
      gap: 8px;
    }
    
    .filter-group {
      display: flex;
      align-items: center;
      gap: 10px;
      
      .filter-label {
        font-size: 13px;
        color: var(--theme-text-secondary);
        white-space: nowrap;
      }
      
      .purpose-select {
        min-width: 100px;
      }
    }
  }
}

.tab-content {
  flex: 1;
  overflow: hidden;
  padding: 20px;
}
</style>
