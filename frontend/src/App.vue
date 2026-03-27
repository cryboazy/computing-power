<template>
  <div class="dashboard">
    <header class="dashboard-header">
      <div class="header-left">
        <el-button class="admin-btn" @click="showPasswordDialog" text>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="admin-icon">
            <circle cx="12" cy="12" r="3"></circle>
            <path
              d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z">
            </path>
          </svg>
        </el-button>
        <ThemeSwitcher />
      </div>
      <h1 class="header-title">智能算力监测平台</h1>
      <div class="header-right">
        <span class="time">{{ currentTime }}</span>
        <el-select v-model="globalNetworkFilter" class="network-select" size="small" placeholder="选择网络分类"
          :loading="networkLoading">
          <el-option label="全部网络" value="all" />
          <el-option v-for="network in networkList" :key="network.code" :label="network.name" :value="network.code" />
        </el-select>
        <el-select v-model="globalPurposeFilter" class="purpose-select" size="small" placeholder="设备用途"
          :loading="purposeLoading">
          <el-option label="全部用途" value="all" />
          <el-option v-for="purpose in purposeList" :key="purpose.dict_value" :label="purpose.dict_label"
            :value="String(purpose.dict_value)" />
        </el-select>
        <el-select v-model="timeType" class="time-type-select" size="small">
          <el-option v-for="type in TIME_TYPE_OPTIONS" :key="type.value" :label="type.label" :value="type.value" />
        </el-select>
        <el-select v-model="globalTimeRange" class="time-range-select" size="small">
          <el-option v-for="tab in TIME_RANGE_OPTIONS" :key="tab.value" :label="tab.label" :value="tab.value" />
        </el-select>
      </div>
    </header>

    <main class="dashboard-main">
      <aside v-show="leftPanelVisible" class="left-panel" :style="{ width: leftPanelWidth + 'px' }">
        <LeftPanel />
        <div class="panel-edge left">
          <button class="panel-toggle-btn left" @click="toggleLeftPanel" title="收起左侧面板">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="15 18 9 12 15 6"></polyline>
            </svg>
          </button>
          <div class="resize-handle left" @mousedown="startDragLeft"></div>
        </div>
      </aside>

      <aside v-if="!leftPanelVisible" class="panel-collapsed left">
        <button class="panel-toggle-btn expand" @click="toggleLeftPanel" title="展开左侧面板">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="9 18 15 12 9 6"></polyline>
          </svg>
        </button>
      </aside>

      <section class="center-panel">
        <CenterPanel />
      </section>

      <aside v-show="rightPanelVisible" class="right-panel" :style="{ width: rightPanelWidth + 'px' }">
        <div class="panel-edge right">
          <button class="panel-toggle-btn right" @click="toggleRightPanel" title="收起右侧面板">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="9 18 15 12 9 6"></polyline>
            </svg>
          </button>
          <div class="resize-handle right" @mousedown="startDragRight"></div>
        </div>
        <RightPanel />
      </aside>
      <aside v-if="!rightPanelVisible" class="panel-collapsed right">
        <button class="panel-toggle-btn expand" @click="toggleRightPanel" title="展开右侧面板">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="15 18 9 12 15 6"></polyline>
          </svg>
        </button>
      </aside>
    </main>

    <el-dialog v-model="expandVisible" width="90%" top="2vh" :close-on-click-modal="false" :close-on-press-escape="true"
      :show-close="false" class="expand-dialog" append-to-body :fullscreen="isExpandMaximized">
      <template #header>
        <div class="dialog-header">
          <div class="header-decoration">
            <span class="decoration-line"></span>
            <span class="decoration-dot"></span>
          </div>
          <h3 class="dialog-title">{{ expandTitle }}</h3>
          <div class="header-decoration right">
            <span class="decoration-dot"></span>
            <span class="decoration-line"></span>
          </div>
          <div class="window-controls">
            <button class="control-btn" @click="toggleExpandMaximize" :title="isExpandMaximized ? '还原' : '最大化'">
              <svg v-if="!isExpandMaximized" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
              </svg>
              <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M8 3v3a2 2 0 0 1-2 2H3m18 0h-3a2 2 0 0 1-2-2V3m0 18v-3a2 2 0 0 1 2-2h3M3 16h3a2 2 0 0 1 2 2v3">
                </path>
              </svg>
            </button>
            <button class="control-btn close-btn" @click="expandVisible = false" title="关闭">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
          </div>
        </div>
      </template>
      <MultiOrgUsageDialog :panel-type="expandPanelType" :sub-type="expandSubType"
        :time-range="expandData.timeRange || 'month'" :group-name="expandData.groupName || ''"
        :province-name="expandData.provinceName || ''" />
    </el-dialog>

    <el-dialog v-model="passwordDialogVisible" width="450px" :close-on-click-modal="false" class="password-dialog"
      :show-close="false">
      <template #header>
        <div class="dialog-header">
          <div class="header-decoration">
            <span class="decoration-line"></span>
            <span class="decoration-dot"></span>
          </div>
          <h3 class="dialog-title">后台管理验证</h3>
          <div class="header-decoration right">
            <span class="decoration-dot"></span>
            <span class="decoration-line"></span>
          </div>
          <button class="close-btn" @click="passwordDialogVisible = false">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
      </template>
      <div class="password-form">
        <el-input v-model="adminPassword" type="password" placeholder="请输入管理密码" show-password
          @keyup.enter="verifyPassword" />
        <el-button type="primary" @click="verifyPassword" :loading="passwordVerifying">
          验证
        </el-button>
      </div>
    </el-dialog>

    <el-dialog v-model="adminPanelVisible" width="800px" top="5vh" :close-on-click-modal="false" class="admin-dialog"
      :show-close="false">
      <template #header>
        <div class="dialog-header">
          <div class="header-decoration">
            <span class="decoration-line"></span>
            <span class="decoration-dot"></span>
          </div>
          <h3 class="dialog-title">后台管理</h3>
          <div class="header-decoration right">
            <span class="decoration-dot"></span>
            <span class="decoration-line"></span>
          </div>
          <button class="close-btn" @click="adminPanelVisible = false">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
      </template>
      <AdminPanel />
    </el-dialog>

    <OrgDetailDialog v-model:visible="orgDetailVisible" :org-id="currentOrgId" :initial-tab="currentOrgActiveTab"
      :time-range="globalTimeRange" :time-type="timeType" />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, provide, computed } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import LeftPanel from './components/LeftPanel.vue'
import CenterPanel from './components/CenterPanel.vue'
import RightPanel from './components/RightPanel.vue'
import MultiOrgUsageDialog from './components/MultiOrgUsageDialog.vue'
import ThemeSwitcher from './components/ThemeSwitcher.vue'
import AdminPanel from './components/AdminPanel.vue'
import OrgDetailDialog from './components/OrgDetailDialog.vue'
import { applyTheme, getStoredTheme } from './themes'
import { dashboardApi } from './api'

const currentTime = ref('')

const globalPageSize = ref(20)
const setGlobalPageSize = (size) => {
  globalPageSize.value = size
}

const expandVisible = ref(false)
const expandTitle = ref('')
const expandPanelType = ref('')
const expandSubType = ref('')
const expandData = ref({})
const isExpandMaximized = ref(false)

const toggleExpandMaximize = () => {
  isExpandMaximized.value = !isExpandMaximized.value
}

const passwordDialogVisible = ref(false)
const adminPanelVisible = ref(false)
const adminPassword = ref('')
const passwordVerifying = ref(false)

const orgDetailVisible = ref(false)
const currentOrgId = ref(null)
const currentOrgActiveTab = ref('devices')

const timeType = ref('work')
const TIME_TYPE_OPTIONS = [
  { value: 'work', label: '工作时间使用率' },
  { value: 'nonwork', label: '非工作时间使用率' },
  { value: 'all', label: '全天使用率' }
]

const globalTimeRange = ref('month')
const TIME_RANGE_OPTIONS = [
  { label: '近一个月', value: 'month' },
  { label: '近三个月', value: 'quarter' },
  { label: '近六个月', value: 'half_year' },
  { label: '近一年', value: 'year' }
]

const globalNetworkFilter = ref('all')
const networkList = ref([])
const networkLoading = ref(false)

const globalPurposeFilter = ref('all')
const purposeList = ref([])
const purposeLoading = ref(false)

const loadNetworkList = async () => {
  networkLoading.value = true
  try {
    const response = await dashboardApi.getNetworkList()
    networkList.value = response
  } catch (error) {
    console.error('[App] Failed to load network list:', error)
    ElMessage.error('加载网络分类失败')
  } finally {
    networkLoading.value = false
  }
}

const loadPurposeList = async () => {
  purposeLoading.value = true
  try {
    const response = await dashboardApi.getPurposeDict()
    purposeList.value = response
  } catch (error) {
    console.error('[App] Failed to load purpose list:', error)
    ElMessage.error('加载设备用途失败')
  } finally {
    purposeLoading.value = false
  }
}

const setTimeType = (type) => {
  timeType.value = type
}

provide('timeType', timeType)
provide('globalTimeRange', globalTimeRange)
provide('globalNetworkFilter', globalNetworkFilter)
provide('networkList', networkList)
provide('globalPurposeFilter', globalPurposeFilter)
provide('purposeList', purposeList)

let timer = null

const updateTime = () => {
  const now = new Date()
  currentTime.value = now.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

const showPanelExpand = (panelType, subType, title, data) => {
  expandPanelType.value = panelType
  expandSubType.value = subType
  expandTitle.value = title
  expandData.value = data
  expandVisible.value = true
}

const showOrgDetail = (orgId, activeTab = 'devices') => {
  currentOrgId.value = orgId
  currentOrgActiveTab.value = activeTab
  orgDetailVisible.value = true
}

const showPasswordDialog = () => {
  adminPassword.value = ''
  passwordDialogVisible.value = true
}

const verifyPassword = async () => {
  if (!adminPassword.value) {
    ElMessage.warning('请输入管理密码')
    return
  }

  passwordVerifying.value = true
  try {
    const response = await axios.post('/api/admin/verify-password', {
      password: adminPassword.value
    })

    if (response.data.success) {
      passwordDialogVisible.value = false
      adminPassword.value = ''
      adminPanelVisible.value = true
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '密码验证失败')
  } finally {
    passwordVerifying.value = false
  }
}

provide('showPanelExpand', showPanelExpand)
provide('showOrgDetail', showOrgDetail)
provide('globalPageSize', globalPageSize)
provide('setGlobalPageSize', setGlobalPageSize)

const usageThresholds = ref({
  high: 60.0,
  low: 30.0
})

const leftPanelVisible = ref(true)
const rightPanelVisible = ref(true)
const leftPanelWidth = ref(350)
const rightPanelWidth = ref(350)
const isDraggingLeft = ref(false)
const isDraggingRight = ref(false)

const MIN_PANEL_WIDTH = 200
const MAX_PANEL_WIDTH = 500

const toggleLeftPanel = () => {
  leftPanelVisible.value = !leftPanelVisible.value
}

const toggleRightPanel = () => {
  rightPanelVisible.value = !rightPanelVisible.value
}

const startDragLeft = (e) => {
  isDraggingLeft.value = true
  document.addEventListener('mousemove', onDragLeft)
  document.addEventListener('mouseup', endDragLeft)
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
}

const onDragLeft = (e) => {
  if (!isDraggingLeft.value) return
  const newWidth = e.clientX - 10
  if (newWidth >= MIN_PANEL_WIDTH && newWidth <= MAX_PANEL_WIDTH) {
    leftPanelWidth.value = newWidth
  }
}

const endDragLeft = () => {
  isDraggingLeft.value = false
  document.removeEventListener('mousemove', onDragLeft)
  document.removeEventListener('mouseup', endDragLeft)
  document.body.style.cursor = ''
  document.body.style.userSelect = ''
}

const startDragRight = (e) => {
  isDraggingRight.value = true
  document.addEventListener('mousemove', onDragRight)
  document.addEventListener('mouseup', endDragRight)
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
}

const onDragRight = (e) => {
  if (!isDraggingRight.value) return
  const newWidth = window.innerWidth - e.clientX - 10
  if (newWidth >= MIN_PANEL_WIDTH && newWidth <= MAX_PANEL_WIDTH) {
    rightPanelWidth.value = newWidth
  }
}

const endDragRight = () => {
  isDraggingRight.value = false
  document.removeEventListener('mousemove', onDragRight)
  document.removeEventListener('mouseup', endDragRight)
  document.body.style.cursor = ''
  document.body.style.userSelect = ''
}

const loadUsageThresholds = async () => {
  try {
    const response = await axios.get('/api/admin/config')
    usageThresholds.value = {
      high: response.data.high_usage_threshold || 60.0,
      low: response.data.low_usage_threshold || 30.0
    }
  } catch (error) {
    console.error('[App] Failed to load usage thresholds:', error)
  }
}

provide('usageThresholds', usageThresholds)

onMounted(() => {
  updateTime()
  timer = setInterval(updateTime, 1000)
  const storedTheme = getStoredTheme()
  applyTheme(storedTheme)
  loadUsageThresholds()
  loadNetworkList()
  loadPurposeList()
})

onUnmounted(() => {
  if (timer) {
    clearInterval(timer)
  }
})
</script>

<style lang="scss" scoped>
.dashboard {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: linear-gradient(135deg, var(--theme-bg-start) 0%, var(--theme-bg-middle) 50%, var(--theme-bg-end) 100%);
  overflow: hidden;
}

.dashboard-header {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  position: relative;
  background: linear-gradient(90deg,
      var(--theme-shadow) 0%,
      var(--theme-shadow-heavy) 50%,
      var(--theme-shadow) 100%);
  border-bottom: 1px solid var(--theme-border);

  .header-left {
    width: 200px;
    display: flex;
    align-items: center;
    gap: 12px;
    z-index: 1;
  }

  .header-right {
    width: 600px;
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: 15px;
    z-index: 1;
  }

  .time {
    font-size: 14px;
    color: var(--theme-text-secondary);
    white-space: nowrap;
    flex-shrink: 0;
  }

  .network-select {
    width: 100px;
    flex-shrink: 0;

    :deep(.el-input__wrapper) {
      background: var(--theme-shadow);
      border: 1px solid var(--theme-border);
      box-shadow: none;

      &:hover {
        border-color: var(--theme-primary);
      }
    }

    :deep(.el-input__inner) {
      color: var(--theme-text);
      font-size: 12px;
    }
  }

  .purpose-select {
    width: 100px;
    flex-shrink: 0;

    :deep(.el-input__wrapper) {
      background: var(--theme-shadow);
      border: 1px solid var(--theme-border);
      box-shadow: none;

      &:hover {
        border-color: var(--theme-primary);
      }
    }

    :deep(.el-input__inner) {
      color: var(--theme-text);
      font-size: 12px;
    }
  }

  .time-type-select {
    width: 120px;
    flex-shrink: 0;

    :deep(.el-input__wrapper) {
      background: var(--theme-shadow);
      border: 1px solid var(--theme-border);
      box-shadow: none;

      &:hover {
        border-color: var(--theme-primary);
      }
    }

    :deep(.el-input__inner) {
      color: var(--theme-text);
      font-size: 12px;
    }
  }

  .time-range-select {
    width: 100px;
    flex-shrink: 0;

    :deep(.el-input__wrapper) {
      background: var(--theme-shadow);
      border: 1px solid var(--theme-border);
      box-shadow: none;

      &:hover {
        border-color: var(--theme-primary);
      }
    }

    :deep(.el-input__inner) {
      color: var(--theme-text);
      font-size: 12px;
    }
  }

  .header-title {
    position: absolute;
    left: 50%;
    transform: translateX(-50%);
    font-size: 24px;
    font-weight: bold;
    background: linear-gradient(90deg, var(--theme-primary) 0%, var(--theme-secondary) 50%, var(--theme-primary) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    text-shadow: 0 0 20px var(--theme-glow);
    letter-spacing: 8px;
  }

  .admin-btn {
    padding: 8px;

    .admin-icon {
      width: 20px;
      height: 20px;
      color: var(--theme-text-secondary);
      transition: all 0.3s ease;
    }

    &:hover .admin-icon {
      color: var(--theme-primary);
      transform: rotate(45deg);
    }
  }
}

.dashboard-main {
  flex: 1;
  display: flex;
  padding: 10px;
  gap: 10px;
  overflow: hidden;

  .left-panel,
  .right-panel {
    flex-shrink: 0;
    display: flex;
    flex-direction: column;
    gap: 10px;
    position: relative;
    transition: width 0.3s ease;
  }

  .left-panel {
    width: v-bind('leftPanelWidth + "px"');
  }

  .right-panel {
    width: v-bind('rightPanelWidth + "px"');
  }

  .center-panel {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 10px;
    min-width: 0;
  }

  .panel-edge {
    position: absolute;
    top: 0;
    bottom: 0;
    width: 12px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 8px;
    z-index: 10;

    &.left {
      right: -11px;
    }

    &.right {
      left: -11px;
    }
  }

  .resize-handle {
    width: 10px;
    height: 40px;
    cursor: col-resize;
    background: var(--theme-border);
    border-radius: 3px;
    opacity: 0;
    transition: opacity 0.3s;

    &:hover {
      opacity: 1;
      background: var(--theme-primary);
    }
  }

  .left-panel:hover .panel-edge .resize-handle,
  .right-panel:hover .panel-edge .resize-handle {
    opacity: 0.5;
  }

  .panel-toggle-btn {
    width: 10px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--theme-shadow);
    border: 1px solid var(--theme-border);
    border-radius: 3px;
    cursor: pointer;
    transition: all 0.3s ease;
    padding: 0;

    svg {
      width: 8px;
      height: 8px;
      color: var(--theme-text-secondary);
      transition: color 0.3s ease;
    }

    &:hover {
      background: var(--theme-hover-bg);
      border-color: var(--theme-primary);

      svg {
        color: var(--theme-primary);
      }
    }

    &.expand {
      width: 30px;
      height: 60px;
      flex-shrink: 0;
    }
  }

  .panel-collapsed {
    flex-shrink: 0;
    width: 40px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding-top: 50px;

    &.left {
      order: -1;
    }
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
      var(--theme-hover-bg) 100%);
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
        transparent 100%);
  }

  .header-decoration {
    display: flex;
    align-items: center;
    gap: 8px;

    &.right {
      margin-right: 50px;

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

.password-form {
  display: flex;
  flex-direction: column;
  gap: 15px;
  padding: 20px;

  .el-button {
    width: 100%;
  }
}

:deep(.password-dialog),
:deep(.admin-dialog) {
  .el-dialog__header {
    padding: 0;
    margin: 0;
  }

  .el-dialog__body {
    padding: 0;
  }
}

:deep(.drilldown-dialog) {
  .el-dialog__body {
    padding: 0;
  }
}

.drilldown-tabs {
  width: 100%;

  .tab-header {
    display: flex;
    background: var(--theme-shadow);
    border-bottom: 1px solid var(--theme-border);

    .tab-item {
      padding: 12px 24px;
      cursor: pointer;
      transition: all 0.3s ease;
      color: var(--theme-text-secondary);
      font-size: 14px;
      font-weight: 500;
      border-bottom: 2px solid transparent;

      &:hover {
        color: var(--theme-primary);
        background: var(--theme-hover-bg);
      }

      &.active {
        color: var(--theme-primary);
        border-bottom-color: var(--theme-primary);
        background: var(--theme-hover-bg);
        box-shadow: 0 2px 8px var(--theme-glow);
      }
    }
  }

  .tab-content {
    padding: 20px;
  }
}
</style>
