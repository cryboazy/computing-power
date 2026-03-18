<template>
  <div class="device-detail-tab">
    <div class="stats-cards">
      <div class="stat-card">
        <div class="stat-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect>
            <line x1="8" y1="21" x2="16" y2="21"></line>
            <line x1="12" y1="17" x2="12" y2="21"></line>
          </svg>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ orgDetail?.total_devices || 0 }}</div>
          <div class="stat-label">设备总数</div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="4" y="4" width="16" height="16" rx="2" ry="2"></rect>
            <rect x="9" y="9" width="6" height="6"></rect>
            <line x1="9" y1="1" x2="9" y2="4"></line>
            <line x1="15" y1="1" x2="15" y2="4"></line>
            <line x1="9" y1="20" x2="9" y2="23"></line>
            <line x1="15" y1="20" x2="15" y2="23"></line>
            <line x1="20" y1="9" x2="23" y2="9"></line>
            <line x1="20" y1="14" x2="23" y2="14"></line>
            <line x1="1" y1="9" x2="4" y2="9"></line>
            <line x1="1" y1="14" x2="4" y2="14"></line>
          </svg>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ orgDetail?.total_memory_gb || 0 }} <span class="unit">GB</span></div>
          <div class="stat-label">显存总量</div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"></path>
          </svg>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ orgDetail?.total_compute_tflops || 0 }} <span class="unit">TFLOPS</span></div>
          <div class="stat-label">总算力</div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M22 12h-4l-3 9L9 3l-3 9H2"></path>
          </svg>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ orgDetail?.avg_usage_rate || 0 }} <span class="unit">%</span></div>
          <div class="stat-label">平均使用率</div>
        </div>
      </div>
    </div>
    
    <div v-if="distributionLoading" class="distribution-loading">
      <el-icon class="is-loading" :size="24"><Loading /></el-icon>
      <span>加载中...</span>
    </div>
    
    <div v-else class="charts-grid-standalone">
      <div class="chart-card">
        <div class="chart-wrapper">
          <v-chart :option="gpuTierPieOption" autoresize />
        </div>
      </div>
      
      <div class="chart-card">
        <div class="chart-wrapper">
          <v-chart :option="networkPieOption" autoresize />
        </div>
      </div>
      
      <div class="chart-card">
        <div class="chart-wrapper">
          <v-chart :option="purposePieOption" autoresize />
        </div>
      </div>
    </div>
    
    <div class="device-table-container">
      <div class="table-header">
        <h4>设备列表</h4>
        <div class="table-controls">
          <el-input
            v-model="searchQuery"
            placeholder="搜索设备..."
            prefix-icon="Search"
            size="small"
            style="width: 200px"
            clearable
          />
          <el-button type="primary" size="small" @click="exportData">
            <el-icon><Download /></el-icon>
            导出
          </el-button>
        </div>
      </div>
      
      <el-table
        :data="filteredDevices"
        stripe
        border
        v-loading="tableLoading"
        style="width: 100%"
        :default-sort="{ prop: 'name', order: 'ascending' }"
        @row-click="handleDeviceClick"
      >
        <el-table-column
          type="index"
          label="序号"
          width="60"
          align="center"
        />
        <el-table-column
          prop="name"
          label="设备名称"
          min-width="120"
          sortable
          show-overflow-tooltip
        />
        <el-table-column
          prop="gpu_model"
          label="GPU型号"
          min-width="120"
          sortable
          show-overflow-tooltip
        />
        <el-table-column
          prop="gpu_count"
          label="GPU数量"
          width="110"
          sortable
          align="center"
        />
        <el-table-column
          prop="memory_gb"
          label="显存(GB)"
          width="110"
          sortable
          align="center"
        />
        <el-table-column
          prop="compute_tflops"
          label="总算力"
          width="110"
          sortable
          align="center"
        />
        <el-table-column
          prop="cpu_cores"
          label="CPU核数"
          width="110"
          sortable
          align="center"
        />
        <el-table-column
          prop="memory_size"
          label="内存(GB)"
          width="110"
          sortable
          align="center"
        />
        <el-table-column
          prop="disk_size"
          label="存储(GB)"
          width="110"
          sortable
          align="center"
        />
        <el-table-column
          prop="usage_rate"
          label="最近使用率(%)"
          width="140"
          sortable
          align="center"
        >
          <template #default="{ row }">
            <el-progress 
              :percentage="Math.min(100, Math.round(row.usage_rate))" 
              :color="getUsageColor(row.usage_rate)"
              :stroke-width="8"
            />
          </template>
        </el-table-column>
        <el-table-column
          prop="net_module_name"
          label="运行网络"
          width="120"
          sortable
          align="center"
          show-overflow-tooltip
        >
          <template #default="{ row }">
            <el-tag :color="getNetworkTagColor()" :style="{ color: getNetworkTextColor() }" size="small" effect="dark">
              {{ row.net_module_name || '-' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column
          prop="purpose"
          label="用途"
          width="80"
          sortable
          align="center"
        >
          <template #default="{ row }">
            <el-tag :style="getPurposeTagStyle(row.purpose)" size="small">
              {{ getPurposeText(row.purpose) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column
          prop="is_online"
          label="状态"
          width="80"
          align="center"
        >
          <template #default="{ row }">
            <el-tag :style="getOnlineStatusStyle(row.is_online)" size="small">
              {{ getOnlineStatusText(row.is_online) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column
          prop="updated_at"
          label="更新时间"
          width="160"
          align="center"
        >
          <template #default="{ row }">
            {{ formatDateTime(row.updated_at) }}
          </template>
        </el-table-column>
      </el-table>
      
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="filteredDevices.length"
          layout="total, sizes, prev, pager, next, jumper"
          size="small"
          :pager-count="5"
        />
      </div>
    </div>
    
    <DeviceUsageDetailDialog
      v-model="deviceUsageDialogVisible"
      :device-id="selectedDeviceId"
      :device-name="selectedDeviceName"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Download, Search, Loading } from '@element-plus/icons-vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { PieChart, BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import { dashboardApi } from '../../api'
import { useTheme } from '../../composables/useTheme'
import DeviceUsageDetailDialog from '../DeviceUsageDetailDialog.vue'

use([
  CanvasRenderer,
  PieChart,
  BarChart,
  GridComponent,
  TooltipComponent,
  LegendComponent
])

const { getAllColors } = useTheme()

const props = defineProps({
  orgDetail: {
    type: Object,
    default: null
  },
  orgId: {
    type: [Number, String],
    default: null
  }
})

const searchQuery = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const tableLoading = ref(false)
const distributionLoading = ref(false)
const distributionData = ref(null)
const purposeDict = ref([])

const deviceUsageDialogVisible = ref(false)
const selectedDeviceId = ref(null)
const selectedDeviceName = ref('')

const allDevices = computed(() => props.orgDetail?.devices || [])

const filteredDevices = computed(() => {
  if (!searchQuery.value) {
    return allDevices.value
  }
  const query = searchQuery.value.toLowerCase()
  return allDevices.value.filter(device => 
    device.name?.toLowerCase().includes(query) ||
    device.gpu_model?.toLowerCase().includes(query) ||
    device.code?.toLowerCase().includes(query)
  )
})

const paginatedDevices = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredDevices.value.slice(start, end)
})

const getUsageColor = (usage) => {
  const colors = getAllColors()
  if (usage >= 80) return colors.danger
  if (usage >= 50) return colors.warning
  return colors.success
}

const getOnlineStatusStyle = (isOnline) => {
  const colors = getAllColors()
  if (isOnline === 1) {
    return { backgroundColor: colors.success + '20', borderColor: colors.success, color: colors.success }
  } else if (isOnline === 0) {
    return { backgroundColor: colors.danger + '20', borderColor: colors.danger, color: colors.danger }
  } else {
    return { backgroundColor: colors.warning + '20', borderColor: colors.warning, color: colors.warning }
  }
}

const getOnlineStatusText = (isOnline) => {
  if (isOnline === 1) return '在线'
  if (isOnline === 0) return '离线'
  return '异常'
}

const getPurposeText = (purpose) => {
  const item = purposeDict.value.find(p => p.value === purpose)
  return item?.label || '-'
}

const getPurposeTagStyle = (purpose) => {
  const colors = getAllColors()
  const chartColors = [colors.primary, colors.warning, colors.success, colors.chart1, colors.chart2, colors.chart3, colors.chart4]
  const index = purposeDict.value.findIndex(p => p.value === purpose)
  const color = index >= 0 ? chartColors[index % chartColors.length] : colors.info
  return { backgroundColor: color + '20', borderColor: color, color: color }
}

const getNetworkTagColor = () => {
  const colors = getAllColors()
  return colors.primary
}

const getNetworkTextColor = () => {
  const colors = getAllColors()
  return colors.textLight || '#ffffff'
}

const formatDateTime = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  if (isNaN(date.getTime())) return '-'
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  const seconds = String(date.getSeconds()).padStart(2, '0')
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
}

const handleDeviceClick = (row) => {
  selectedDeviceId.value = row.id
  selectedDeviceName.value = row.name
  deviceUsageDialogVisible.value = true
}

const exportData = () => {
  if (!allDevices.value.length) {
    ElMessage.warning('没有可导出的数据')
    return
  }
  
  tableLoading.value = true
  
  setTimeout(() => {
    try {
      const headers = ['序号', '设备名称', 'GPU型号', 'GPU数量', '显存(GB)', '总算力', 'CPU核数', '内存(GB)', '存储(GB)', '使用率(%)', '运行网络', '用途', '状态', '更新时间']
      const rows = allDevices.value.map((device, index) => [
        index + 1,
        device.name || '',
        device.gpu_model || '',
        device.gpu_count || 0,
        device.memory_gb || 0,
        device.compute_tflops || 0,
        device.cpu_cores || 0,
        device.memory_size || 0,
        device.disk_size || 0,
        device.usage_rate || 0,
        device.net_module_name || '-',
        getPurposeText(device.purpose),
        device.is_online === 1 ? '在线' : device.is_online === 0 ? '离线' : '异常',
        formatDateTime(device.updated_at)
      ])
      
      const csvContent = [headers.join(','), ...rows.map(row => row.join(','))].join('\n')
      const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' })
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = `${props.orgDetail?.org_name || '设备详情'}_${new Date().toISOString().split('T')[0]}.csv`
      link.click()
      
      ElMessage.success('导出成功')
    } catch (error) {
      console.error('Export failed:', error)
      ElMessage.error('导出失败')
    } finally {
      tableLoading.value = false
    }
  }, 500)
}

const getChartColors = () => {
  const colors = getAllColors()
  return [
    colors.chart1,
    colors.chart2,
    colors.chart3,
    colors.chart4,
    colors.primary,
    colors.secondary,
    colors.success,
    colors.warning,
    colors.danger,
    colors.info
  ]
}

const createPieOption = (data) => {
  const colors = getAllColors()
  const chartColors = getChartColors()
  
  return {
    tooltip: {
      trigger: 'item',
      backgroundColor: colors.panelBgStart,
      borderColor: colors.border,
      textStyle: { color: colors.text },
      formatter: '{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      right: '5%',
      top: 'center',
      textStyle: { color: colors.textSecondary, fontSize: 10 },
      itemStyle: {
        borderRadius: 6,
        borderWidth: 1,
        borderColor: colors.panelBgStart
      }
    },
    series: [{
      type: 'pie',
      radius: ['35%', '60%'],
      center: ['35%', '50%'],
      avoidLabelOverlap: false,
      itemStyle: {
        borderRadius: 6,
        borderColor: colors.panelBgStart,
        borderWidth: 1
      },
      label: {
        show: true,
        position: 'outside',
        formatter: '{b}: {c}\n{d}%',
        color: colors.textSecondary,
        fontSize: 10
      },
      emphasis: {
        label: {
          show: true,
          fontSize: 12,
          fontWeight: 'bold',
          color: colors.text
        }
      },
      labelLine: {
        show: true,
        lineStyle: { color: colors.border }
      },
      data: data.map((item, index) => ({
        name: item.name,
        value: item.value,
        itemStyle: { color: chartColors[index % chartColors.length] }
      }))
    }]
  }
}

const createBarOption = (data) => {
  const colors = getAllColors()
  const chartColors = getChartColors()
  
  return {
    tooltip: {
      trigger: 'axis',
      backgroundColor: colors.panelBgStart,
      borderColor: colors.border,
      textStyle: { color: colors.text },
      formatter: '{b}: {c}'
    },
    grid: {
      left: '3%',
      right: '15%',
      bottom: '3%',
      top: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: colors.border } },
      axisLabel: { color: colors.textSecondary, fontSize: 10 },
      splitLine: { lineStyle: { color: colors.borderLight } }
    },
    yAxis: {
      type: 'category',
      data: data.map(d => d.name),
      axisLine: { lineStyle: { color: colors.border } },
      axisLabel: { color: colors.textSecondary, fontSize: 10 }
    },
    series: [{
      type: 'bar',
      data: data.map((item, index) => ({
        value: item.value,
        itemStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 1, y2: 0,
            colorStops: [
              { offset: 0, color: chartColors[index % chartColors.length] },
              { offset: 1, color: chartColors[index % chartColors.length] + '4D' }
            ]
          },
          borderRadius: [0, 4, 4, 0]
        },
        label: { show: true, position: 'right', formatter: '{c}', color: colors.textSecondary, fontSize: 10 }
      }))
    }]
  }
}

const gpuTierPieOption = computed(() => {
  const data = distributionData.value?.gpu_tier || []
  return createPieOption(data)
})

const networkPieOption = computed(() => {
  const data = distributionData.value?.network || []
  return createPieOption(data)
})

const purposePieOption = computed(() => {
  const data = distributionData.value?.purpose || []
  return createPieOption(data)
})

const fetchDistributionData = async () => {
  if (!props.orgId) return
  
  distributionLoading.value = true
  try {
    const data = await dashboardApi.getOrgDistribution(props.orgId)
    distributionData.value = data
  } catch (error) {
    console.error('Failed to fetch distribution data:', error)
  } finally {
    distributionLoading.value = false
  }
}

const fetchPurposeDict = async () => {
  try {
    const data = await dashboardApi.getPurposeDict()
    purposeDict.value = data || []
  } catch (error) {
    console.error('Failed to fetch purpose dict:', error)
    purposeDict.value = []
  }
}

watch(() => props.orgId, (newVal) => {
  if (newVal) {
    fetchDistributionData()
  }
})

onMounted(() => {
  fetchPurposeDict()
  if (props.orgId) {
    fetchDistributionData()
  }
})
</script>

<style lang="scss" scoped>
.device-detail-tab {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow: hidden;
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
  flex-shrink: 0;
  overflow: visible;
  padding: 2px;
  
  .stat-card {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 16px;
    background: linear-gradient(135deg, var(--theme-hover-bg) 0%, var(--theme-shadow) 100%);
    border: 1px solid var(--theme-border);
    border-radius: 10px;
    transition: all 0.3s ease;
    
    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 4px 12px var(--theme-glow);
      border-color: var(--theme-primary);
    }
    
    .stat-icon {
      width: 48px;
      height: 48px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: linear-gradient(135deg, var(--theme-primary) 0%, var(--theme-secondary) 100%);
      border-radius: 10px;
      box-shadow: 0 4px 10px var(--theme-glow);
      
      svg {
        width: 24px;
        height: 24px;
        color: white;
      }
    }
    
    .stat-content {
      flex: 1;
      
      .stat-value {
        font-size: 24px;
        font-weight: 700;
        background: linear-gradient(90deg, var(--theme-primary) 0%, var(--theme-secondary) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        line-height: 1.2;
        
        .unit {
          font-size: 12px;
          font-weight: 500;
        }
      }
      
      .stat-label {
        font-size: 12px;
        color: var(--theme-text-secondary);
        margin-top: 2px;
      }
    }
  }
}

.distribution-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 40px;
  color: var(--theme-text-secondary);
  font-size: 13px;
}

.charts-grid-standalone {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  padding: 0;
  
  .chart-card {
    background: var(--theme-shadow);
    border: 1px solid var(--theme-border);
    border-radius: 12px;
    overflow: hidden;
    
    .chart-wrapper {
      height: 220px;
      padding: 12px;
      
      :deep(.echarts) {
        width: 100%;
        height: 100%;
      }
    }
  }
}

.device-table-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--theme-shadow);
  border: 1px solid var(--theme-border);
  border-radius: 12px;
  overflow: hidden;
  min-height: 0;
  
  .table-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 16px;
    border-bottom: 1px solid var(--theme-border);
    background: linear-gradient(90deg, var(--theme-hover-bg) 0%, var(--theme-shadow) 100%);
    flex-shrink: 0;
    
    h4 {
      margin: 0;
      font-size: 14px;
      font-weight: 600;
      color: var(--theme-text);
    }
    
    .table-controls {
      display: flex;
      gap: 10px;
    }
  }
  
  :deep(.el-table) {
    flex: 1;
    background: transparent;
    
    th.el-table__cell {
      background: var(--theme-hover-bg) !important;
      color: var(--theme-text);
      font-weight: 600;
      font-size: 12px;
    }
    
    td.el-table__cell {
      background: transparent;
      color: var(--theme-text);
      font-size: 12px;
    }
    
    .el-table__row:hover td {
      background: var(--theme-hover-bg) !important;
    }
    
    tr.el-table__row--striped td {
      background: var(--theme-shadow);
    }
  }
  
  .pagination-container {
    display: flex;
    justify-content: flex-end;
    padding: 12px 16px;
    border-top: 1px solid var(--theme-border);
    flex-shrink: 0;
    
    :deep(.el-pagination) {
      .el-pager li {
        background: var(--theme-shadow);
        color: var(--theme-text);
        border: 1px solid var(--theme-border);
        
        &.is-active {
          background: var(--theme-primary);
          color: white;
          border-color: var(--theme-primary);
        }
      }
      
      button {
        background: var(--theme-shadow);
        color: var(--theme-text);
        border: 1px solid var(--theme-border);
        
        &:hover:not(:disabled) {
          color: var(--theme-primary);
          border-color: var(--theme-primary);
        }
      }
      
      .el-pagination__sizes {
        .el-select {
          .el-input__wrapper {
            background: var(--theme-shadow);
            border: 1px solid var(--theme-border);
            box-shadow: none;
          }
        }
      }
      
      .el-pagination__jump {
        color: var(--theme-text-secondary);
        
        .el-input__wrapper {
          background: var(--theme-shadow);
          border: 1px solid var(--theme-border);
          box-shadow: none;
        }
      }
    }
  }
}
</style>
