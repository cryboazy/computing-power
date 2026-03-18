<template>
  <div class="admin-panel">
    <el-tabs v-model="activeTab" class="admin-tabs">
      <el-tab-pane label="系统配置" name="system">
        <div class="panel-section">
          <div class="section-content">
            <div class="config-item">
              <label>工作时段开始时间</label>
              <el-input-number v-model="config.work_hour_start" :min="0" :max="23" />
              <span class="unit">时</span>
            </div>
            <div class="config-item">
              <label>工作时段结束时间</label>
              <el-input-number v-model="config.work_hour_end" :min="0" :max="23" />
              <span class="unit">时</span>
            </div>
            <div class="config-item">
              <label>高使用率阈值</label>
              <el-input-number v-model="config.high_usage_threshold" :min="0" :max="100" :precision="1" />
              <span class="unit">%</span>
            </div>
            <div class="config-item">
              <label>低使用率阈值</label>
              <el-input-number v-model="config.low_usage_threshold" :min="0" :max="100" :precision="1" />
              <span class="unit">%</span>
            </div>
            <el-button type="primary" @click="saveConfig" :loading="configLoading">
              保存配置
            </el-button>
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="数据聚合" name="aggregation">
        <div class="panel-section">
          <div class="section-content">
            <div class="status-info">
              <div class="status-item">
                <span class="status-label">日汇总记录:</span>
                <span class="status-value">{{ aggregationStatus.daily_summary_count }}</span>
              </div>
              <div class="status-item">
                <span class="status-label">设备汇总记录:</span>
                <span class="status-value">{{ aggregationStatus.device_summary_count }}</span>
              </div>
              <div class="status-item">
                <span class="status-label">组织汇总记录:</span>
                <span class="status-value">{{ aggregationStatus.org_summary_count }}</span>
              </div>
              <div class="status-item">
                <span class="status-label">统计数据记录:</span>
                <span class="status-value">{{ aggregationStatus.statistics_count }}</span>
              </div>
              <div class="status-item">
                <span class="status-label">组织小时数据:</span>
                <span class="status-value">{{ aggregationStatus.org_hourly_count }}</span>
              </div>
              <div class="status-item">
                <span class="status-label">最近聚合时间:</span>
                <span class="status-value">{{ aggregationStatus.latest_aggregation_time || '无' }}</span>
              </div>
            </div>
            <div class="action-buttons">
              <div class="action-row">
                <el-radio-group v-model="aggregationMode" @change="resetRefreshDays">
                  <el-radio-button label="days">按天数</el-radio-button>
                  <el-radio-button label="dateRange">按时间段</el-radio-button>
                </el-radio-group>
              </div>
              <div class="action-row" v-if="aggregationMode === 'days'">
                <el-input-number v-model="refreshDays" :min="1" :max="365" />
                <span class="action-label">天</span>
                <el-button type="primary" @click="refreshAggregation" :loading="refreshLoading"
                  :disabled="refreshLoading">
                  刷新聚合数据
                </el-button>
              </div>
              <div class="action-row" v-else>
                <el-date-picker
                  v-model="dateRange"
                  type="daterange"
                  range-separator="至"
                  start-placeholder="开始日期"
                  end-placeholder="结束日期"
                  :picker-options="pickerOptions"
                  style="width: 240px"
                />
                <el-button type="primary" @click="refreshAggregationByDateRange" :loading="refreshLoading"
                  :disabled="refreshLoading || !dateRange || dateRange.length !== 2">
                  刷新聚合数据
                </el-button>
              </div>
              <div v-if="refreshProgress.show" class="progress-container">
                <div class="progress-header">
                  <span>进度: {{ refreshProgress.day }}/{{ refreshProgress.totalDays }} 天</span>
                  <span>{{ refreshProgress.percent }}%</span>
                </div>
                <el-progress :percentage="refreshProgress.percent" :stroke-width="12" :show-text="false" />
                <div class="progress-task">{{ refreshProgress.currentTask }}</div>
              </div>
              <div class="action-row">
                <el-button type="danger" @click="resetAggregation" :loading="resetLoading">
                  重置聚合数据
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="设备用途管理" name="purpose">
        <div class="panel-section">
          <div class="section-content">
            <div class="purpose-header">
              <el-button type="primary" @click="openAddPurposeDialog">
                添加设备用途
              </el-button>
            </div>
            <el-table :data="purposeList" style="width: 100%" border>
              <el-table-column prop="dict_value" label="值" width="100" />
              <el-table-column prop="dict_label" label="标签" />
              <el-table-column prop="dict_sort" label="排序" width="100" />
              <el-table-column prop="status" label="状态" width="100">
                <template #default="scope">
                  <el-switch v-model="scope.row.status" @change="updatePurposeStatus(scope.row)" :active-value="1"
                    :inactive-value="0" />
                </template>
              </el-table-column>
              <el-table-column label="操作" width="150" fixed="right">
                <template #default="scope">
                  <el-button size="small" @click="openEditPurposeDialog(scope.row)">
                    编辑
                  </el-button>
                  <el-button size="small" type="danger" @click="deletePurpose(scope.row.id)">
                    删除
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="密码管理" name="password">
        <div class="panel-section">
          <div class="section-content">
            <div class="password-form">
              <div class="form-item">
                <label>原密码</label>
                <el-input v-model="passwordForm.old_password" type="password" show-password placeholder="请输入原密码" />
              </div>
              <div class="form-item">
                <label>新密码</label>
                <el-input v-model="passwordForm.new_password" type="password" show-password
                  placeholder="请输入新密码(至少6位)" />
              </div>
              <div class="form-item">
                <label>确认新密码</label>
                <el-input v-model="passwordForm.confirm_password" type="password" show-password
                  placeholder="请再次输入新密码" />
              </div>
              <el-button type="primary" @click="changePassword" :loading="passwordLoading">
                修改密码
              </el-button>
            </div>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 添加/编辑设备用途对话框 -->
    <el-dialog v-model="purposeDialogVisible" width="500px" :show-close="false">
      <template #header>
        <div class="dialog-header">
          <div class="header-decoration">
            <span class="decoration-line"></span>
            <span class="decoration-dot"></span>
          </div>
          <h3 class="dialog-title">{{ purposeDialogTitle }}</h3>
          <div class="header-decoration right">
            <span class="decoration-dot"></span>
            <span class="decoration-line"></span>
          </div>
          <button class="close-btn" @click="purposeDialogVisible = false">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
      </template>
      <el-form :model="purposeForm" label-width="80px">
        <el-form-item label="标签">
          <el-input v-model="purposeForm.dict_label" placeholder="请输入设备用途标签" />
        </el-form-item>
        <el-form-item label="值">
          <el-input-number v-model="purposeForm.dict_value" :min="1" :max="999" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="purposeForm.dict_sort" :min="0" :max="999" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="purposeForm.status" :active-value="1" :inactive-value="0" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="purposeForm.remark" type="textarea" placeholder="请输入备注信息" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="purposeDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="savePurpose" :loading="purposeLoading">
            保存
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'

const activeTab = ref('system')

const config = ref({
  work_hour_start: 9,
  work_hour_end: 18,
  high_usage_threshold: 60.0,
  low_usage_threshold: 30.0
})

const aggregationStatus = ref({
  daily_summary_count: 0,
  device_summary_count: 0,
  org_summary_count: 0,
  statistics_count: 0,
  org_hourly_count: 0,
  latest_aggregation_time: null
})

const passwordForm = ref({
  old_password: '',
  new_password: '',
  confirm_password: ''
})

const refreshDays = ref(1)
const configLoading = ref(false)
const refreshLoading = ref(false)
const resetLoading = ref(false)
const passwordLoading = ref(false)
const refreshProgress = ref({
  show: false,
  percent: 0,
  currentTask: '',
  day: 0,
  totalDays: 0
})

// 时间段聚合相关
const aggregationMode = ref('days') // 'days' 或 'dateRange'
const dateRange = ref([])
const pickerOptions = ref({
  disabledDate(time) {
    return time.getTime() > Date.now()
  }
})

// 设备用途管理相关状态
const purposeList = ref([])
const purposeDialogVisible = ref(false)
const purposeDialogTitle = ref('添加设备用途')
const purposeForm = ref({
  id: null,
  dict_label: '',
  dict_value: 1,
  dict_sort: 0,
  status: 1,
  remark: ''
})
const purposeLoading = ref(false)

const loadConfig = async () => {
  try {
    const response = await axios.get('/api/admin/config')
    config.value = response.data
  } catch (error) {
    ElMessage.error('加载配置失败')
  }
}

const loadAggregationStatus = async () => {
  try {
    const response = await axios.get('/api/admin/aggregation/status')
    aggregationStatus.value = response.data
  } catch (error) {
    ElMessage.error('加载聚合状态失败')
  }
}

const loadPurposeList = async () => {
  try {
    const response = await axios.get('/api/dict/purpose')
    purposeList.value = response.data
  } catch (error) {
    ElMessage.error('加载设备用途失败')
  }
}

const saveConfig = async () => {
  configLoading.value = true
  try {
    await axios.put('/api/admin/config', config.value)
    ElMessage.success('配置保存成功')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '保存配置失败')
  } finally {
    configLoading.value = false
  }
}

const refreshAggregation = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要刷新最近 ${refreshDays.value} 天的聚合数据吗？`,
      '确认操作',
      { type: 'warning' }
    )

    refreshLoading.value = true
    refreshProgress.value = {
      show: true,
      percent: 0,
      currentTask: '正在初始化...',
      day: 0,
      totalDays: refreshDays.value
    }

    const eventSource = new EventSource(`/api/admin/aggregation/refresh?days=${refreshDays.value}`)

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data)

      if (data.type === 'start') {
        refreshProgress.value.totalDays = data.days
      } else if (data.type === 'day_start') {
        refreshProgress.value.day = data.day
        refreshProgress.value.currentTask = `处理 ${data.date}`
      } else if (data.type === 'progress') {
        refreshProgress.value.percent = data.progress
        refreshProgress.value.currentTask = data.current_task
      } else if (data.type === 'complete') {
        eventSource.close()
        refreshLoading.value = false
        refreshProgress.value.show = false
        ElMessage.success(data.message)
        loadAggregationStatus()
      } else if (data.type === 'error') {
        eventSource.close()
        refreshLoading.value = false
        refreshProgress.value.show = false
        ElMessage.error(data.message)
      }
    }

    eventSource.onerror = () => {
      eventSource.close()
      refreshLoading.value = false
      refreshProgress.value.show = false
      ElMessage.error('连接服务器失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('刷新失败')
    }
  }
}

const resetAggregation = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要重置所有聚合数据吗？此操作不可恢复！',
      '危险操作',
      { type: 'error', confirmButtonText: '确定重置', cancelButtonText: '取消' }
    )

    resetLoading.value = true
    const response = await axios.post('/api/admin/aggregation/reset')

    if (response.data.success) {
      ElMessage.success(response.data.message)
      loadAggregationStatus()
    } else {
      ElMessage.error(response.data.message)
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '重置失败')
    }
  } finally {
    resetLoading.value = false
  }
}

const resetRefreshDays = () => {
  // 切换模式时重置相关参数
  if (aggregationMode.value === 'days') {
    refreshDays.value = 1
  } else {
    dateRange.value = []
  }
}

const refreshAggregationByDateRange = async () => {
  if (!dateRange.value || dateRange.value.length !== 2) {
    ElMessage.warning('请选择有效的日期范围')
    return
  }

  try {
    const startDate = dateRange.value[0]
    const endDate = dateRange.value[1]
    const days = Math.ceil((endDate - startDate) / (1000 * 60 * 60 * 24)) + 1

    if (days > 365) {
      ElMessage.warning('日期范围不能超过365天')
      return
    }

    await ElMessageBox.confirm(
      `确定要刷新 ${startDate.getFullYear()}-${(startDate.getMonth() + 1).toString().padStart(2, '0')}-${startDate.getDate().toString().padStart(2, '0')} 至 ${endDate.getFullYear()}-${(endDate.getMonth() + 1).toString().padStart(2, '0')}-${endDate.getDate().toString().padStart(2, '0')} 的聚合数据吗？`,
      '确认操作',
      { type: 'warning' }
    )

    refreshLoading.value = true
    refreshProgress.value = {
      show: true,
      percent: 0,
      currentTask: '正在初始化...',
      day: 0,
      totalDays: days
    }

    // 计算日期范围内的所有日期
    const dates = []
    let currentDate = new Date(startDate)
    while (currentDate <= endDate) {
      dates.push(new Date(currentDate))
      currentDate.setDate(currentDate.getDate() + 1)
    }

    // 按顺序处理每个日期
    for (let i = 0; i < dates.length; i++) {
      const date = dates[i]
      const dateStr = date.toISOString().split('T')[0]
      
      // 调用后端API处理单个日期
      const eventSource = new EventSource(`/api/admin/aggregation/refresh?days=1&target_date_str=${dateStr}`)

      eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data)

        if (data.type === 'start') {
          refreshProgress.value.totalDays = dates.length
          refreshProgress.value.day = i + 1
        } else if (data.type === 'day_start') {
          refreshProgress.value.day = i + 1
          refreshProgress.value.currentTask = `处理 ${data.date}`
        } else if (data.type === 'progress') {
          // 计算总进度
          const totalSteps = dates.length * 5
          const currentStep = i * 5 + Math.ceil(data.progress / 20)
          const totalProgress = Math.round((currentStep / totalSteps) * 100)
          refreshProgress.value.percent = totalProgress
          refreshProgress.value.currentTask = data.current_task
        } else if (data.type === 'complete') {
          eventSource.close()
          
          // 如果是最后一个日期，完成整个过程
          if (i === dates.length - 1) {
            refreshLoading.value = false
            refreshProgress.value.show = false
            ElMessage.success(`成功刷新 ${dates.length} 天的聚合数据`)
            loadAggregationStatus()
          }
        } else if (data.type === 'error') {
          eventSource.close()
          refreshLoading.value = false
          refreshProgress.value.show = false
          ElMessage.error(data.message)
        }
      }

      eventSource.onerror = () => {
        eventSource.close()
        refreshLoading.value = false
        refreshProgress.value.show = false
        ElMessage.error('连接服务器失败')
      }

      // 等待当前日期处理完成
      await new Promise(resolve => {
        const checkInterval = setInterval(() => {
          if (!refreshLoading.value || i === dates.length - 1) {
            clearInterval(checkInterval)
            resolve()
          }
        }, 1000)
      })

      // 如果发生错误，停止处理
      if (!refreshLoading.value && i < dates.length - 1) {
        break
      }
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('刷新失败: ' + (error.message || '未知错误'))
    }
    refreshLoading.value = false
    refreshProgress.value.show = false
  }
}

const changePassword = async () => {
  if (!passwordForm.value.old_password) {
    ElMessage.warning('请输入原密码')
    return
  }
  if (!passwordForm.value.new_password || passwordForm.value.new_password.length < 6) {
    ElMessage.warning('新密码长度不能少于6位')
    return
  }
  if (passwordForm.value.new_password !== passwordForm.value.confirm_password) {
    ElMessage.warning('两次输入的新密码不一致')
    return
  }

  passwordLoading.value = true
  try {
    const response = await axios.post('/api/admin/change-password', {
      old_password: passwordForm.value.old_password,
      new_password: passwordForm.value.new_password
    })
    ElMessage.success(response.data.message)
    passwordForm.value = {
      old_password: '',
      new_password: '',
      confirm_password: ''
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '修改密码失败')
  } finally {
    passwordLoading.value = false
  }
}

// 设备用途管理相关方法
const openAddPurposeDialog = () => {
  purposeDialogTitle.value = '添加设备用途'
  purposeForm.value = {
    id: null,
    dict_label: '',
    dict_value: 1,
    dict_sort: 0,
    status: 1,
    remark: ''
  }
  purposeDialogVisible.value = true
}

const openEditPurposeDialog = (row) => {
  purposeDialogTitle.value = '编辑设备用途'
  purposeForm.value = {
    id: row.id,
    dict_label: row.dict_label,
    dict_value: row.dict_value,
    dict_sort: row.dict_sort,
    status: row.status,
    remark: row.remark || ''
  }
  purposeDialogVisible.value = true
}

const savePurpose = async () => {
  if (!purposeForm.value.dict_label) {
    ElMessage.warning('请输入设备用途标签')
    return
  }

  purposeLoading.value = true
  try {
    if (purposeForm.value.id) {
      // 编辑
      await axios.put(`/api/admin/dict/purpose/${purposeForm.value.id}`, purposeForm.value)
    } else {
      // 添加
      await axios.post('/api/admin/dict/purpose', purposeForm.value)
    }
    ElMessage.success('保存成功')
    purposeDialogVisible.value = false
    loadPurposeList()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '保存失败')
  } finally {
    purposeLoading.value = false
  }
}

const updatePurposeStatus = async (row) => {
  try {
    await axios.patch(`/api/admin/dict/purpose/${row.id}/status`, {
      status: row.status
    })
    ElMessage.success('状态更新成功')
  } catch (error) {
    ElMessage.error('状态更新失败')
    // 恢复原状态
    loadPurposeList()
  }
}

const deletePurpose = async (id) => {
  try {
    await ElMessageBox.confirm(
      '确定要删除这个设备用途吗？',
      '确认操作',
      { type: 'warning' }
    )

    await axios.delete(`/api/admin/dict/purpose/${id}`)
    ElMessage.success('删除成功')
    loadPurposeList()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

onMounted(() => {
  loadConfig()
  loadAggregationStatus()
  loadPurposeList()
})
</script>

<style lang="scss" scoped>
.admin-panel {
  padding: 20px;
  max-height: 70vh;
  overflow-y: auto;

  &::-webkit-scrollbar {
    width: 6px;
  }

  &::-webkit-scrollbar-thumb {
    background: var(--theme-border);
    border-radius: 3px;
  }

  &::-webkit-scrollbar-track {
    background: transparent;
  }
}

.admin-tabs {
  :deep(.el-tabs__header) {
    margin-bottom: 20px;

    .el-tabs__nav {
      background: var(--theme-panel-bg);
      border: 1px solid var(--theme-border);
      border-radius: 8px 8px 0 0;
      padding: 0 10px;
    }

    .el-tabs__item {
      padding: 12px 24px;
      font-size: 14px;
      color: var(--theme-text-secondary);

      &.is-active {
        color: var(--theme-primary);
        font-weight: 600;
      }
    }

    .el-tabs__active-bar {
      background: linear-gradient(90deg, var(--theme-primary) 0%, var(--theme-secondary) 100%);
      height: 3px;
    }
  }
}

.panel-section {
  background: var(--theme-panel-bg);
  border: 1px solid var(--theme-border);
  border-radius: 8px;
  margin-bottom: 20px;
  overflow: hidden;

  .section-content {
    padding: 20px;
  }
}

.config-item {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 15px;

  label {
    width: 140px;
    color: var(--theme-text);
    font-size: 14px;
  }

  .unit {
    color: var(--theme-text-secondary);
    font-size: 14px;
  }
}

.status-info {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-bottom: 20px;

  .status-item {
    display: flex;
    justify-content: space-between;
    padding: 10px 15px;
    background: var(--theme-hover-bg);
    border-radius: 6px;

    .status-label {
      color: var(--theme-text-secondary);
      font-size: 13px;
    }

    .status-value {
      color: var(--theme-primary);
      font-weight: 600;
      font-size: 14px;
    }
  }
}

.action-buttons {
  display: flex;
  flex-direction: column;
  gap: 15px;

  .action-row {
    display: flex;
    align-items: center;
    gap: 10px;

    .action-label {
      color: var(--theme-text-secondary);
      font-size: 14px;
    }
  }
}

.progress-container {
  background: var(--theme-hover-bg);
  border-radius: 8px;
  padding: 15px;
  margin-top: 5px;

  .progress-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 10px;
    font-size: 13px;
    color: var(--theme-text-secondary);
  }

  .progress-task {
    margin-top: 8px;
    font-size: 12px;
    color: var(--theme-primary);
    text-align: center;
  }

  :deep(.el-progress-bar__outer) {
    background-color: var(--theme-border);
  }

  :deep(.el-progress-bar__inner) {
    background: linear-gradient(90deg, var(--theme-primary) 0%, var(--theme-secondary) 100%);
  }
}

.password-form {
  .form-item {
    display: flex;
    align-items: center;
    gap: 15px;
    margin-bottom: 15px;

    label {
      width: 100px;
      color: var(--theme-text);
      font-size: 14px;
    }

    .el-input {
      flex: 1;
      max-width: 300px;
    }
  }
}

.purpose-header {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 15px;
}

:deep(.el-table) {
  background: var(--theme-panel-bg);
  border: 1px solid var(--theme-border);
  border-radius: 8px;
  overflow: hidden;

  .el-table__header-wrapper th {
    background: var(--theme-hover-bg);
    color: var(--theme-text);
    font-weight: 600;
    border-bottom: 1px solid var(--theme-border);
    text-align: center;
  }

  .el-table__body-wrapper tr {
    &:hover {
      background: var(--theme-hover-bg);
    }
  }

  .el-table__body-wrapper td {
    border-bottom: 1px solid var(--theme-border);
    text-align: center;
  }
}

:deep(.el-input-number) {
  width: 120px;
}

:deep(.el-button--primary) {
  background: linear-gradient(135deg, var(--theme-primary) 0%, var(--theme-secondary) 100%);
  border: none;

  &:hover {
    opacity: 0.9;
  }
}

:deep(.el-button--danger) {
  background: linear-gradient(135deg, #f56c6c 0%, #e6423e 100%);
  border: none;

  &:hover {
    opacity: 0.9;
  }
}

:deep(.el-dialog) {
  background: var(--theme-panel-bg);
  border-radius: 8px;

  .el-dialog__header {
    background: linear-gradient(90deg, var(--theme-hover-bg) 0%, var(--theme-shadow) 100%);
    border-bottom: 1px solid var(--theme-border);

    .el-dialog__title {
      color: var(--theme-primary);
      font-weight: 600;
    }
  }

  .el-dialog__body {
    padding: 20px;
  }

  .el-dialog__footer {
    border-top: 1px solid var(--theme-border);
    padding: 15px 20px;
  }
}

:deep(.el-form-item__label) {
  color: var(--theme-text);
  font-size: 14px;
}

:deep(.el-switch__core) {
  background-color: var(--theme-border);

  &:after {
    background-color: #fff;
  }

  &.is-active {
    background-color: var(--theme-primary);
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
  
  .close-btn {
    position: absolute;
    right: 20px;
    top: 50%;
    transform: translateY(-50%);
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
      width: 18px;
      height: 18px;
      color: var(--theme-primary);
      transition: all 0.3s ease;
    }
    
    &:hover {
      background: linear-gradient(135deg, var(--theme-border-light) 0%, var(--theme-hover-bg) 100%);
      border-color: var(--theme-primary);
      box-shadow: 0 0 15px var(--theme-glow);
      transform: translateY(-50%) scale(1.05);
      
      svg {
        color: var(--theme-secondary);
      }
    }
    
    &:active {
      transform: translateY(-50%) scale(0.95);
    }
  }
}

:deep(.el-dialog) {
  .el-dialog__header {
    padding: 0;
    margin: 0;
  }
  
  .el-dialog__body {
    padding: 30px 20px;
  }
  
  .el-form {
    margin-top: 10px;
  }
  
  .el-form-item {
    margin-bottom: 16px;
  }
}
</style>
