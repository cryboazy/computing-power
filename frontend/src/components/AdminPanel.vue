<template>
  <div class="admin-panel">
    <div class="panel-section">
      <div class="section-header">
        <span class="section-icon">⚙️</span>
        <span class="section-title">系统配置</span>
      </div>
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

    <div class="panel-section">
      <div class="section-header">
        <span class="section-icon">📊</span>
        <span class="section-title">数据聚合</span>
      </div>
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
            <el-input-number v-model="refreshDays" :min="1" :max="365" />
            <span class="action-label">天</span>
            <el-button type="primary" @click="refreshAggregation" :loading="refreshLoading" :disabled="refreshLoading">
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

    <div class="panel-section">
      <div class="section-header">
        <span class="section-icon">🔐</span>
        <span class="section-title">密码管理</span>
      </div>
      <div class="section-content">
        <div class="password-form">
          <div class="form-item">
            <label>原密码</label>
            <el-input v-model="passwordForm.old_password" type="password" show-password placeholder="请输入原密码" />
          </div>
          <div class="form-item">
            <label>新密码</label>
            <el-input v-model="passwordForm.new_password" type="password" show-password placeholder="请输入新密码(至少6位)" />
          </div>
          <div class="form-item">
            <label>确认新密码</label>
            <el-input v-model="passwordForm.confirm_password" type="password" show-password placeholder="请再次输入新密码" />
          </div>
          <el-button type="primary" @click="changePassword" :loading="passwordLoading">
            修改密码
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'

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

onMounted(() => {
  loadConfig()
  loadAggregationStatus()
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

.panel-section {
  background: var(--theme-panel-bg);
  border: 1px solid var(--theme-border);
  border-radius: 8px;
  margin-bottom: 20px;
  overflow: hidden;
  
  .section-header {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 15px 20px;
    background: linear-gradient(90deg, var(--theme-hover-bg) 0%, var(--theme-shadow) 100%);
    border-bottom: 1px solid var(--theme-border);
    
    .section-icon {
      font-size: 18px;
    }
    
    .section-title {
      font-size: 16px;
      font-weight: 600;
      color: var(--theme-primary);
    }
  }
  
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
</style>
