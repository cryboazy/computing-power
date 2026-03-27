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
            <div class="scheduled-config">
              <div class="scheduled-config-header">
                <span class="config-title">定时更新配置</span>
                <el-switch v-model="config.auto_aggregation_enabled" @change="saveConfig" />
              </div>
              <div class="scheduled-config-body" v-if="config.auto_aggregation_enabled">
                <div class="scheduled-time">
                  <span class="time-label">每天执行时间:</span>
                  <el-input-number v-model="config.auto_aggregation_hour" :min="0" :max="23" @change="saveConfig" />
                  <span class="time-separator">:</span>
                  <el-input-number v-model="config.auto_aggregation_minute" :min="0" :max="59" @change="saveConfig" />
                  <span class="time-hint">(时:分)</span>
                </div>
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
                <el-button v-if="refreshLoading" type="warning" size="small" @click="cancelCurrentTask" style="margin-top: 10px;">
                  取消任务
                </el-button>
              </div>
              <div v-if="recentTasks.length > 0" class="recent-tasks">
                <div class="recent-tasks-header">最近任务</div>
                <div v-for="task in recentTasks" :key="task.task_id" class="recent-task-item">
                  <div class="task-info">
                    <span class="task-status" :class="task.status">{{ getStatusText(task.status) }}</span>
                    <span class="task-time">{{ formatTaskTime(task.create_time) }}</span>
                  </div>
                  <div class="task-detail">
                    <span>{{ task.total_days }}天</span>
                    <span v-if="task.status === 'completed'">{{ task.progress }}%</span>
                    <span v-else-if="task.status === 'failed'" class="error-text">{{ task.error_message }}</span>
                  </div>
                </div>
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

      <el-tab-pane label="GPU档次管理" name="gpu-tier">
        <div class="panel-section">
          <div class="section-content">
            <div class="tier-header">
              <el-button type="primary" @click="openAddTierDialog">
                添加档次
              </el-button>
              <el-button @click="batchDeleteTier" :disabled="selectedTiers.length === 0">
                批量删除
              </el-button>
            </div>
            <el-table :data="tierList" style="width: 100%" border @selection-change="handleTierSelection">
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
                  <el-switch v-model="scope.row.status" @change="updateTierStatus(scope.row)" :active-value="1"
                    :inactive-value="0" />
                </template>
              </el-table-column>
              <el-table-column label="操作" width="200" fixed="right">
                <template #default="scope">
                  <el-button size="small" @click="openEditTierDialog(scope.row)">
                    编辑
                  </el-button>
                  <el-button size="small" type="danger" @click="deleteTier(scope.row.id)">
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

      <el-tab-pane label="数据库状态" name="database">
        <div class="panel-section">
          <div class="section-content">
            <div class="database-header">
              <el-button type="primary" @click="refreshDatabaseStatus" :loading="dbStatusLoading">
                刷新状态
              </el-button>
              <el-button @click="testDatabaseConnection" :loading="dbTestLoading">
                测试连接
              </el-button>
            </div>
            
            <div class="database-section">
              <div class="section-title">
                <span class="title-icon main-db"></span>
                主数据库 (远程)
                <el-tag :type="dbStatus.main_database?.status === 'connected' ? 'success' : 'danger'" size="small">
                  {{ dbStatus.main_database?.status === 'connected' ? '已连接' : '未连接' }}
                </el-tag>
              </div>
              <div class="db-info-grid" v-if="dbStatus.main_database">
                <div class="db-info-item">
                  <span class="info-label">主机地址</span>
                  <span class="info-value">{{ dbStatus.main_database.host || '-' }}</span>
                </div>
                <div class="db-info-item">
                  <span class="info-label">端口</span>
                  <span class="info-value">{{ dbStatus.main_database.port || '-' }}</span>
                </div>
                <div class="db-info-item">
                  <span class="info-label">数据库名</span>
                  <span class="info-value">{{ dbStatus.main_database.database || '-' }}</span>
                </div>
                <div class="db-info-item" v-if="dbStatus.main_database.connection_pool">
                  <span class="info-label">连接池状态</span>
                  <span class="info-value">
                    {{ dbStatus.main_database.connection_pool.checked_out }}/{{ dbStatus.main_database.connection_pool.size }} 使用中
                    <span class="pool-detail">(溢出: {{ dbStatus.main_database.connection_pool.overflow }})</span>
                  </span>
                </div>
                <div class="db-info-item full-width" v-if="dbStatus.main_database.error">
                  <span class="info-label error">错误信息</span>
                  <span class="info-value error">{{ dbStatus.main_database.error }}</span>
                </div>
              </div>
            </div>

            <div class="database-section">
              <div class="section-title">
                <span class="title-icon local-db"></span>
                本地缓存数据库 (SQLite)
                <el-tag :type="dbStatus.local_database?.status === 'connected' ? 'success' : 'danger'" size="small">
                  {{ dbStatus.local_database?.status === 'connected' ? '已连接' : '未连接' }}
                </el-tag>
              </div>
              <div class="db-info-grid" v-if="dbStatus.local_database">
                <div class="db-info-item">
                  <span class="info-label">文件路径</span>
                  <span class="info-value path">{{ dbStatus.local_database.path || '-' }}</span>
                </div>
                <div class="db-info-item">
                  <span class="info-label">文件大小</span>
                  <span class="info-value">{{ dbStatus.local_database.size_human || '0 Bytes' }}</span>
                </div>
                <div class="db-info-item" v-if="dbStatus.local_database.sqlite_info">
                  <span class="info-label">日志模式</span>
                  <span class="info-value">{{ dbStatus.local_database.sqlite_info.journal_mode }}</span>
                </div>
                <div class="db-info-item" v-if="dbStatus.local_database.sqlite_info">
                  <span class="info-label">同步模式</span>
                  <span class="info-value">{{ dbStatus.local_database.sqlite_info.synchronous }}</span>
                </div>
                <div class="db-info-item full-width" v-if="dbStatus.local_database.error">
                  <span class="info-label error">错误信息</span>
                  <span class="info-value error">{{ dbStatus.local_database.error }}</span>
                </div>
              </div>
              
              <div class="tables-section" v-if="dbStatus.local_database?.tables">
                <div class="tables-title">数据表统计</div>
                <div class="tables-grid">
                  <div class="table-item" v-for="(table, tableName) in dbStatus.local_database.tables" :key="tableName">
                    <span class="table-name">{{ table.display_name }}</span>
                    <span class="table-count">{{ formatNumber(table.count) }} 条</span>
                  </div>
                </div>
              </div>
            </div>

            <div class="database-section" v-if="dbStatus.cache_status && dbStatus.cache_status.length > 0">
              <div class="section-title">
                <span class="title-icon cache"></span>
                缓存同步状态
              </div>
              <el-table :data="dbStatus.cache_status" style="width: 100%" border size="small">
                <el-table-column prop="cache_name" label="缓存名称" width="150" />
                <el-table-column prop="record_count" label="记录数" width="100">
                  <template #default="scope">
                    {{ formatNumber(scope.row.record_count) }}
                  </template>
                </el-table-column>
                <el-table-column prop="last_sync_time" label="最后同步时间">
                  <template #default="scope">
                    {{ scope.row.last_sync_time ? formatDateTime(scope.row.last_sync_time) : '-' }}
                  </template>
                </el-table-column>
                <el-table-column prop="status" label="状态" width="100">
                  <template #default="scope">
                    <el-tag :type="scope.row.status === 'success' ? 'success' : 'danger'" size="small">
                      {{ scope.row.status === 'success' ? '成功' : '失败' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="error_message" label="错误信息">
                  <template #default="scope">
                    <span v-if="scope.row.error_message" class="error-text">{{ scope.row.error_message }}</span>
                    <span v-else>-</span>
                  </template>
                </el-table-column>
              </el-table>
            </div>

            <div class="database-section" v-if="connectionTest.main_database || connectionTest.local_database">
              <div class="section-title">
                <span class="title-icon test"></span>
                连接测试结果
              </div>
              <div class="test-results">
                <div class="test-item" v-if="connectionTest.main_database">
                  <span class="test-label">主数据库</span>
                  <el-tag :type="connectionTest.main_database.success ? 'success' : 'danger'" size="small">
                    {{ connectionTest.main_database.success ? '连接成功' : '连接失败' }}
                  </el-tag>
                  <span v-if="connectionTest.main_database.latency_ms" class="latency">
                    延迟: {{ connectionTest.main_database.latency_ms }} ms
                  </span>
                  <span v-if="connectionTest.main_database.error" class="error-text">
                    {{ connectionTest.main_database.error }}
                  </span>
                </div>
                <div class="test-item" v-if="connectionTest.local_database">
                  <span class="test-label">本地数据库</span>
                  <el-tag :type="connectionTest.local_database.success ? 'success' : 'danger'" size="small">
                    {{ connectionTest.local_database.success ? '连接成功' : '连接失败' }}
                  </el-tag>
                  <span v-if="connectionTest.local_database.latency_ms" class="latency">
                    延迟: {{ connectionTest.local_database.latency_ms }} ms
                  </span>
                  <span v-if="connectionTest.local_database.error" class="error-text">
                    {{ connectionTest.local_database.error }}
                  </span>
                </div>
              </div>
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

    <el-dialog v-model="tierDialogVisible" width="500px" :show-close="false">
      <template #header>
        <div class="dialog-header">
          <div class="header-decoration">
            <span class="decoration-line"></span>
            <span class="decoration-dot"></span>
          </div>
          <h3 class="dialog-title">{{ tierDialogTitle }}</h3>
          <div class="header-decoration right">
            <span class="decoration-dot"></span>
            <span class="decoration-line"></span>
          </div>
          <button class="close-btn" @click="tierDialogVisible = false">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
      </template>
      <el-form :model="tierForm" label-width="80px">
        <el-form-item label="档次值">
          <el-input-number v-model="tierForm.dict_value" :min="1" :max="10" />
          <span class="form-tip">对应 GPU 卡的 card_type 值</span>
        </el-form-item>
        <el-form-item label="档次名称">
          <el-input v-model="tierForm.dict_label" placeholder="如：高端卡、中端卡" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="tierForm.dict_sort" :min="0" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="tierForm.status" :active-value="1" :inactive-value="0" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="tierForm.remark" type="textarea" placeholder="请输入备注信息" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="tierDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveTier" :loading="tierLoading">
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
  low_usage_threshold: 30.0,
  auto_aggregation_enabled: true,
  auto_aggregation_hour: 1,
  auto_aggregation_minute: 0
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
const currentTaskId = ref(null)
const pollInterval = ref(null)
const recentTasks = ref([])

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

// GPU 档次管理相关状态
const tierList = ref([])
const tierDialogVisible = ref(false)
const tierDialogTitle = ref('添加档次')
const tierForm = ref({
  id: null,
  dict_value: 1,
  dict_label: '',
  dict_sort: 0,
  status: 1,
  remark: ''
})
const tierLoading = ref(false)
const selectedTiers = ref([])

const dbStatus = ref({
  main_database: null,
  local_database: null,
  cache_status: []
})
const dbStatusLoading = ref(false)
const dbTestLoading = ref(false)
const connectionTest = ref({
  main_database: null,
  local_database: null
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
      currentTask: '正在创建任务...',
      day: 0,
      totalDays: refreshDays.value
    }

    const response = await axios.post('/api/admin/aggregation/tasks', {
      days: refreshDays.value
    })

    if (response.data.success) {
      currentTaskId.value = response.data.task_id
      startPolling()
    } else {
      refreshLoading.value = false
      refreshProgress.value.show = false
      ElMessage.error(response.data.message || '创建任务失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      refreshLoading.value = false
      refreshProgress.value.show = false
      ElMessage.error(error.response?.data?.detail || '刷新失败')
    }
  }
}

const startPolling = () => {
  if (pollInterval.value) {
    clearInterval(pollInterval.value)
  }
  
  pollInterval.value = setInterval(async () => {
    if (!currentTaskId.value) {
      clearInterval(pollInterval.value)
      return
    }
    
    try {
      const response = await axios.get(`/api/admin/aggregation/tasks/${currentTaskId.value}`)
      const task = response.data
      
      refreshProgress.value.percent = task.progress
      refreshProgress.value.currentTask = task.current_step || ''
      refreshProgress.value.day = task.processed_days
      refreshProgress.value.totalDays = task.total_days
      
      if (task.status === 'completed') {
        clearInterval(pollInterval.value)
        pollInterval.value = null
        refreshLoading.value = false
        refreshProgress.value.show = false
        currentTaskId.value = null
        ElMessage.success('聚合数据刷新完成')
        loadAggregationStatus()
        loadRecentTasks()
      } else if (task.status === 'failed') {
        clearInterval(pollInterval.value)
        pollInterval.value = null
        refreshLoading.value = false
        refreshProgress.value.show = false
        currentTaskId.value = null
        ElMessage.error(`刷新失败: ${task.error_message || '未知错误'}`)
        loadRecentTasks()
      } else if (task.status === 'cancelled') {
        clearInterval(pollInterval.value)
        pollInterval.value = null
        refreshLoading.value = false
        refreshProgress.value.show = false
        currentTaskId.value = null
        ElMessage.warning('任务已取消')
        loadRecentTasks()
      }
    } catch (error) {
      console.error('轮询任务状态失败:', error)
    }
  }, 2000)
}

const cancelCurrentTask = async () => {
  if (!currentTaskId.value) return
  
  try {
    await axios.post(`/api/admin/aggregation/tasks/${currentTaskId.value}/cancel`)
    if (pollInterval.value) {
      clearInterval(pollInterval.value)
      pollInterval.value = null
    }
    refreshLoading.value = false
    refreshProgress.value.show = false
    currentTaskId.value = null
    ElMessage.success('任务已取消')
    loadRecentTasks()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '取消任务失败')
  }
}

const loadRecentTasks = async () => {
  try {
    const response = await axios.get('/api/admin/aggregation/tasks?limit=5')
    recentTasks.value = response.data.tasks
  } catch (error) {
    console.error('加载任务列表失败:', error)
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
      currentTask: '正在创建任务...',
      day: 0,
      totalDays: days
    }

    const startDateStr = `${startDate.getFullYear()}-${(startDate.getMonth() + 1).toString().padStart(2, '0')}-${startDate.getDate().toString().padStart(2, '0')}`
    const endDateStr = `${endDate.getFullYear()}-${(endDate.getMonth() + 1).toString().padStart(2, '0')}-${endDate.getDate().toString().padStart(2, '0')}`

    const response = await axios.post('/api/admin/aggregation/tasks', {
      start_date: startDateStr,
      end_date: endDateStr
    })

    if (response.data.success) {
      currentTaskId.value = response.data.task_id
      startPolling()
    } else {
      refreshLoading.value = false
      refreshProgress.value.show = false
      ElMessage.error(response.data.message || '创建任务失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      refreshLoading.value = false
      refreshProgress.value.show = false
      ElMessage.error(error.response?.data?.detail || '刷新失败')
    }
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

// GPU 档次管理函数
const loadTierList = async () => {
  try {
    const response = await axios.get('/api/admin/dict/gpu-tier')
    tierList.value = response.data || []
  } catch (error) {
    console.error('加载GPU档次列表失败:', error)
  }
}

const openAddTierDialog = () => {
  tierDialogTitle.value = '添加档次'
  tierForm.value = {
    id: null,
    dict_value: 1,
    dict_label: '',
    dict_sort: 0,
    status: 1,
    remark: ''
  }
  tierDialogVisible.value = true
}

const openEditTierDialog = (row) => {
  tierDialogTitle.value = '编辑档次'
  tierForm.value = {
    id: row.id,
    dict_value: row.dict_value,
    dict_label: row.dict_label,
    dict_sort: row.dict_sort,
    status: row.status,
    remark: row.remark || ''
  }
  tierDialogVisible.value = true
}

const saveTier = async () => {
  if (!tierForm.value.dict_label) {
    ElMessage.warning('请输入档次名称')
    return
  }

  tierLoading.value = true
  try {
    if (tierForm.value.id) {
      await axios.put(`/api/admin/dict/gpu-tier/${tierForm.value.id}`, tierForm.value)
    } else {
      await axios.post('/api/admin/dict/gpu-tier', tierForm.value)
    }
    ElMessage.success('保存成功')
    tierDialogVisible.value = false
    loadTierList()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '保存失败')
  } finally {
    tierLoading.value = false
  }
}

const updateTierStatus = async (row) => {
  try {
    await axios.patch(`/api/admin/dict/gpu-tier/${row.id}/status`, {
      status: row.status
    })
    ElMessage.success('状态更新成功')
  } catch (error) {
    ElMessage.error('状态更新失败')
    loadTierList()
  }
}

const deleteTier = async (id) => {
  try {
    await ElMessageBox.confirm(
      '确定要删除这个档次吗？',
      '确认操作',
      { type: 'warning' }
    )

    await axios.delete(`/api/admin/dict/gpu-tier/${id}`)
    ElMessage.success('删除成功')
    loadTierList()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleTierSelection = (selection) => {
  selectedTiers.value = selection
}

const batchDeleteTier = async () => {
  if (selectedTiers.value.length === 0) {
    ElMessage.warning('请选择要删除的档次')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedTiers.value.length} 个档次吗？`,
      '确认操作',
      { type: 'warning' }
    )

    for (const tier of selectedTiers.value) {
      await axios.delete(`/api/admin/dict/gpu-tier/${tier.id}`)
    }

    ElMessage.success('批量删除成功')
    selectedTiers.value = []
    loadTierList()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量删除失败')
    }
  }
}

const refreshDatabaseStatus = async () => {
  dbStatusLoading.value = true
  try {
    const response = await axios.get('/api/admin/database/status')
    dbStatus.value = response.data
  } catch (error) {
    ElMessage.error('获取数据库状态失败')
  } finally {
    dbStatusLoading.value = false
  }
}

const testDatabaseConnection = async () => {
  dbTestLoading.value = true
  connectionTest.value = {
    main_database: null,
    local_database: null
  }
  try {
    const response = await axios.get('/api/admin/database/test-connection')
    connectionTest.value = response.data
    if (response.data.main_database?.success && response.data.local_database?.success) {
      ElMessage.success('所有数据库连接正常')
    } else if (!response.data.main_database?.success || !response.data.local_database?.success) {
      ElMessage.warning('部分数据库连接异常，请查看详情')
    }
  } catch (error) {
    ElMessage.error('测试连接失败')
  } finally {
    dbTestLoading.value = false
  }
}

const formatNumber = (num) => {
  if (num === null || num === undefined) return '0'
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

const formatDateTime = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}-${date.getDate().toString().padStart(2, '0')} ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}:${date.getSeconds().toString().padStart(2, '0')}`
}

onMounted(() => {
  loadConfig()
  loadAggregationStatus()
  loadPurposeList()
  loadTierList()
  loadRecentTasks()
  checkRunningTask()
  refreshDatabaseStatus()
})

const checkRunningTask = async () => {
  try {
    const response = await axios.get('/api/admin/aggregation/status')
    if (response.data.running_task_id) {
      currentTaskId.value = response.data.running_task_id
      refreshLoading.value = true
      refreshProgress.value.show = true
      startPolling()
    }
  } catch (error) {
    console.error('检查运行中任务失败:', error)
  }
}

const getStatusText = (status) => {
  const statusMap = {
    'pending': '等待中',
    'running': '运行中',
    'completed': '已完成',
    'failed': '失败',
    'cancelled': '已取消'
  }
  return statusMap[status] || status
}

const formatTaskTime = (timeStr) => {
  if (!timeStr) return ''
  const date = new Date(timeStr)
  return `${date.getMonth() + 1}/${date.getDate()} ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
}
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

.scheduled-config {
  background: var(--theme-hover-bg);
  border-radius: 8px;
  padding: 15px;
  margin-bottom: 20px;
  border: 1px solid var(--theme-border);

  .scheduled-config-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;

    .config-title {
      font-size: 14px;
      font-weight: 600;
      color: var(--theme-text);
    }
  }

  .scheduled-config-body {
    padding-top: 10px;
    border-top: 1px solid var(--theme-border);

    .scheduled-time {
      display: flex;
      align-items: center;
      gap: 10px;

      .time-label {
        font-size: 13px;
        color: var(--theme-text-secondary);
      }

      .time-separator {
        font-size: 16px;
        font-weight: 600;
        color: var(--theme-text);
      }

      .time-hint {
        font-size: 12px;
        color: var(--theme-text-secondary);
        margin-left: 5px;
      }
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

.recent-tasks {
  background: var(--theme-hover-bg);
  border-radius: 8px;
  padding: 15px;
  margin-top: 10px;

  .recent-tasks-header {
    font-size: 13px;
    color: var(--theme-text-secondary);
    margin-bottom: 10px;
    font-weight: 500;
  }

  .recent-task-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 0;
    border-bottom: 1px solid var(--theme-border);

    &:last-child {
      border-bottom: none;
    }

    .task-info {
      display: flex;
      align-items: center;
      gap: 10px;

      .task-status {
        font-size: 12px;
        padding: 2px 8px;
        border-radius: 4px;

        &.completed {
          background: rgba(103, 194, 58, 0.2);
          color: #67c23a;
        }

        &.running {
          background: rgba(64, 158, 255, 0.2);
          color: #409eff;
        }

        &.failed {
          background: rgba(245, 108, 108, 0.2);
          color: #f56c6c;
        }

        &.cancelled {
          background: rgba(144, 147, 153, 0.2);
          color: #909399;
        }

        &.pending {
          background: rgba(230, 162, 60, 0.2);
          color: #e6a23c;
        }
      }

      .task-time {
        font-size: 12px;
        color: var(--theme-text-secondary);
      }
    }

    .task-detail {
      font-size: 12px;
      color: var(--theme-text-secondary);

      .error-text {
        color: #f56c6c;
        margin-left: 8px;
      }
    }
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

.database-header {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.database-section {
  background: var(--theme-hover-bg);
  border-radius: 8px;
  padding: 15px;
  margin-bottom: 15px;

  .section-title {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 15px;
    font-weight: 600;
    color: var(--theme-text);
    margin-bottom: 15px;
    padding-bottom: 10px;
    border-bottom: 1px solid var(--theme-border);

    .title-icon {
      width: 12px;
      height: 12px;
      border-radius: 50%;

      &.main-db {
        background: linear-gradient(135deg, #409eff 0%, #67c23a 100%);
        box-shadow: 0 0 8px rgba(64, 158, 255, 0.5);
      }

      &.local-db {
        background: linear-gradient(135deg, #e6a23c 0%, #f56c6c 100%);
        box-shadow: 0 0 8px rgba(230, 162, 60, 0.5);
      }

      &.cache {
        background: linear-gradient(135deg, #909399 0%, #c0c4cc 100%);
        box-shadow: 0 0 8px rgba(144, 147, 153, 0.5);
      }

      &.test {
        background: linear-gradient(135deg, var(--theme-primary) 0%, var(--theme-secondary) 100%);
        box-shadow: 0 0 8px var(--theme-glow);
      }
    }
  }
}

.db-info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;

  .db-info-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 12px;
    background: var(--theme-panel-bg);
    border-radius: 6px;
    border: 1px solid var(--theme-border);

    &.full-width {
      grid-column: 1 / -1;
    }

    .info-label {
      color: var(--theme-text-secondary);
      font-size: 13px;

      &.error {
        color: #f56c6c;
      }
    }

    .info-value {
      color: var(--theme-text);
      font-size: 13px;
      font-weight: 500;

      &.path {
        font-family: monospace;
        font-size: 11px;
        word-break: break-all;
        max-width: 200px;
        text-align: right;
      }

      &.error {
        color: #f56c6c;
        font-size: 12px;
      }

      .pool-detail {
        color: var(--theme-text-secondary);
        font-size: 11px;
        margin-left: 5px;
      }
    }
  }
}

.tables-section {
  margin-top: 15px;

  .tables-title {
    font-size: 13px;
    color: var(--theme-text-secondary);
    margin-bottom: 10px;
    font-weight: 500;
  }

  .tables-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;

    .table-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 8px 12px;
      background: var(--theme-panel-bg);
      border-radius: 6px;
      border: 1px solid var(--theme-border);

      .table-name {
        color: var(--theme-text-secondary);
        font-size: 12px;
      }

      .table-count {
        color: var(--theme-primary);
        font-size: 12px;
        font-weight: 600;
      }
    }
  }
}

.test-results {
  display: flex;
  flex-direction: column;
  gap: 10px;

  .test-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 15px;
    background: var(--theme-panel-bg);
    border-radius: 6px;
    border: 1px solid var(--theme-border);

    .test-label {
      color: var(--theme-text);
      font-size: 13px;
      font-weight: 500;
      min-width: 80px;
    }

    .latency {
      color: var(--theme-text-secondary);
      font-size: 12px;
      margin-left: 10px;
    }

    .error-text {
      color: #f56c6c;
      font-size: 12px;
      margin-left: 10px;
    }
  }
}

.error-text {
  color: #f56c6c;
}
</style>
