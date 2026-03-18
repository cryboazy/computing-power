<template>
  <el-dialog ref="dialogRef" v-model="dialogVisible" :width="dialogWidth" :class="dialogClass" :close-on-click-modal="false"
    :show-close="false" destroy-on-close :style="dialogStyle">
    <template #header="{ close, titleId, titleClass }">
      <div class="dialog-header">
        <span :id="titleId" :class="titleClass" class="dialog-title">{{ dialogTitle }}</span>
        <div class="header-controls">
          <div class="quick-ranges">
            <el-radio-group v-model="selectedQuickRange" size="small" @change="handleQuickRangeChange">
              <el-radio-button value="1month">近一个月</el-radio-button>
              <el-radio-button value="3month">近三个月</el-radio-button>
              <el-radio-button value="6month">近半年</el-radio-button>
              <el-radio-button value="1year">近一年</el-radio-button>
            </el-radio-group>
          </div>
          <div class="custom-range">
            <el-date-picker v-model="dateRange" type="daterange" range-separator="至" start-placeholder="开始日期"
              end-placeholder="结束日期" size="small" @change="handleDateRangeChange" />
          </div>
        </div>
        <div class="header-actions">
          <button class="control-btn" type="button" @click="toggleMaximize" :title="isMaximized ? '还原' : '最大化'">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect v-if="!isMaximized" x="3" y="3" width="18" height="18" rx="2" ry="2"/>
              <path v-else d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"/>
            </svg>
          </button>
          <button class="control-btn close-btn" type="button" @click="close" aria-label="关闭" title="关闭">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
      </div>
    </template>
    <div class="dialog-content">

      <div v-if="loading" class="loading-container">
        <el-icon class="is-loading" :size="40">
          <Loading />
        </el-icon>
        <span>加载中...</span>
      </div>

      <div v-else class="charts-container">
        <div class="chart-section">
          <div class="chart-header">
            <h4>逐月平均使用率趋势</h4>
          </div>
          <div class="chart-wrapper">
            <v-chart :option="monthlyOption" autoresize style="width: 100%; height: 100%;" />
          </div>
        </div>

        <div class="chart-section">
          <div class="chart-header">
            <h4>逐日平均使用率趋势</h4>
          </div>
          <div class="chart-wrapper">
            <v-chart :option="dailyOption" autoresize style="width: 100%; height: 100%;" />
          </div>
        </div>

        <div class="chart-section">
          <div class="chart-header">
            <h4>分时段平均使用率趋势</h4>
          </div>
          <div class="chart-wrapper">
            <v-chart :option="hourlyOption" autoresize style="width: 100%; height: 100%;" />
          </div>
        </div>
      </div>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch, nextTick, inject } from 'vue'
import { Loading, Warning } from '@element-plus/icons-vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent, VisualMapComponent } from 'echarts/components'
import { dashboardApi } from '../api'
import { useTheme } from '../composables/useTheme'

const usageThresholds = inject('usageThresholds', ref({ high: 60.0, low: 30.0 }))

use([
  CanvasRenderer,
  LineChart,
  BarChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  VisualMapComponent
])

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  deviceId: {
    type: [Number, String],
    default: null
  },
  deviceName: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['update:modelValue'])

const { getAllColors } = useTheme()

const dialogVisible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const dialogTitle = computed(() => {
  return props.deviceName ? `${props.deviceName} - 使用率详情` : '设备使用率详情'
})

const dialogWidth = computed(() => {
  return isMaximized.value ? '98%' : '90%'
})

const selectedQuickRange = ref('3month')
const dateRange = ref([])
const loading = ref(false)
const usageDataAll = ref(null)
const usageDataWork = ref(null)
const usageDataNonwork = ref(null)
const monthlyOption = ref({})
const dailyOption = ref({})
const hourlyOption = ref({})
const isMaximized = ref(false)
const dialogRef = ref(null)

const dialogStyle = computed(() => {
  if (isMaximized.value) {
    return {
      '--el-dialog-margin-top': '1vh',
      '--el-dialog-height': '98vh',
      marginTop: '1vh',
      height: '98vh',
      maxHeight: '98vh'
    }
  }
  return {
    marginTop: '8vh',
    maxHeight: '84vh'
  }
})

const toggleMaximize = () => {
  isMaximized.value = !isMaximized.value
  // 对话框的类名会在模板中通过 :class 动态绑定
}

const dialogClass = computed(() => {
  return isMaximized.value ? 'device-usage-detail-dialog maximized' : 'device-usage-detail-dialog'
})

const getUsageColor = (value) => {
  const colors = getAllColors()
  if (value >= usageThresholds.value.high) return colors.usageHigh
  if (value >= usageThresholds.value.low) return colors.usageMedium
  return colors.usageLow
}

const initializeEmptyOptions = () => {
  const colors = getAllColors()
  monthlyOption.value = {
    tooltip: { trigger: 'axis' },
    legend: { data: ['工作时间', '非工作时间', '全天'], textStyle: { color: colors.textSecondary }, top: 0 },
    grid: { left: '3%', right: '4%', bottom: '3%', top: '15%', containLabel: true },
    xAxis: { type: 'category', data: [] },
    yAxis: { type: 'value', min: 0, max: 100 },
    series: [
      { name: '工作时间', type: 'bar', data: [] },
      { name: '非工作时间', type: 'bar', data: [] },
      { name: '全天', type: 'bar', data: [] }
    ]
  }
  dailyOption.value = {
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '4%', bottom: '3%', top: '10%', containLabel: true },
    xAxis: { type: 'category', data: [] },
    yAxis: { type: 'value', min: 0, max: 100 },
    series: [{ type: 'line', data: [] }]
  }
  hourlyOption.value = {
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '4%', bottom: '3%', top: '10%', containLabel: true },
    xAxis: { type: 'category', data: [] },
    yAxis: { type: 'value', min: 0, max: 100 },
    series: [{ type: 'bar', data: [] }]
  }
}

const handleQuickRangeChange = () => {
  const now = new Date()
  let startDate, endDate

  switch (selectedQuickRange.value) {
    case '1month':
      startDate = new Date(now.getFullYear(), now.getMonth() - 1, now.getDate())
      break
    case '3month':
      startDate = new Date(now.getFullYear(), now.getMonth() - 3, now.getDate())
      break
    case '6month':
      startDate = new Date(now.getFullYear(), now.getMonth() - 6, now.getDate())
      break
    case '1year':
      startDate = new Date(now.getFullYear() - 1, now.getMonth(), now.getDate())
      break
  }

  endDate = now

  dateRange.value = [
    startDate.toISOString().split('T')[0],
    endDate.toISOString().split('T')[0]
  ]

  fetchData()
}

const handleDateRangeChange = () => {
  if (dateRange.value && dateRange.value.length === 2) {
    selectedQuickRange.value = null
    fetchData()
  }
}

const fetchData = async () => {
  if (!props.deviceId) return

  loading.value = true

  try {
    let startDate = null
    let endDate = null

    if (dateRange.value && dateRange.value.length === 2) {
      startDate = dateRange.value[0]
      endDate = dateRange.value[1]
    }

    // 逐月趋势需要获取三个时间类型的数据
    const [dataAll, dataWork, dataNonwork] = await Promise.all([
      dashboardApi.getDeviceUsageTrend(props.deviceId, 'all', startDate, endDate),
      dashboardApi.getDeviceUsageTrend(props.deviceId, 'work', startDate, endDate),
      dashboardApi.getDeviceUsageTrend(props.deviceId, 'nonwork', startDate, endDate)
    ])

    usageDataAll.value = dataAll
    usageDataWork.value = dataWork
    usageDataNonwork.value = dataNonwork

    await nextTick()
    updateChartOptions()
  } catch (error) {
    console.error('Failed to fetch device usage trend:', error)
  } finally {
    loading.value = false
  }
}

const updateChartOptions = () => {
  const colors = getAllColors()
  const monthlyDataAll = usageDataAll.value?.monthly || []
  const monthlyDataWork = usageDataWork.value?.monthly || []
  const monthlyDataNonwork = usageDataNonwork.value?.monthly || []
  const dailyData = usageDataAll.value?.daily || []
  const hourlyData = usageDataAll.value?.hourly || []

  const months = [...new Set([
    ...monthlyDataAll.map(d => d.month),
    ...monthlyDataWork.map(d => d.month),
    ...monthlyDataNonwork.map(d => d.month)
  ])].sort()

  const getDataByMonth = (data, month) => {
    const item = data.find(d => d.month === month)
    return item ? item.avg_usage : null
  }

  monthlyOption.value = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: colors.panelBgStart,
      borderColor: colors.border,
      textStyle: { color: colors.text }
    },
    legend: {
      data: ['工作时间', '非工作时间', '全天'],
      textStyle: { color: colors.textSecondary },
      top: 0
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: months,
      axisLine: { lineStyle: { color: colors.border } },
      axisLabel: { color: colors.textSecondary, fontSize: 11 }
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 100,
      axisLine: { lineStyle: { color: colors.border } },
      axisLabel: { color: colors.textSecondary, fontSize: 11 },
      splitLine: { lineStyle: { color: colors.borderLight } }
    },
    series: [
      {
        name: '工作时间',
        type: 'bar',
        data: months.map(m => getDataByMonth(monthlyDataWork, m)),
        itemStyle: { color: colors.chart1, borderRadius: [4, 4, 0, 0] },
        label: { show: true, position: 'top', formatter: '{c}%', color: colors.textSecondary, fontSize: 10 }
      },
      {
        name: '非工作时间',
        type: 'bar',
        data: months.map(m => getDataByMonth(monthlyDataNonwork, m)),
        itemStyle: { color: colors.chart2, borderRadius: [4, 4, 0, 0] },
        label: { show: true, position: 'top', formatter: '{c}%', color: colors.textSecondary, fontSize: 10 }
      },
      {
        name: '全天',
        type: 'bar',
        data: months.map(m => getDataByMonth(monthlyDataAll, m)),
        itemStyle: { color: colors.chart4, borderRadius: [4, 4, 0, 0] },
        label: { show: true, position: 'top', formatter: '{c}%', color: colors.textSecondary, fontSize: 10 }
      }
    ]
  }

  dailyOption.value = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: colors.panelBgStart,
      borderColor: colors.border,
      textStyle: { color: colors.text },
      formatter: (params) => {
        const data = params[0]
        const usageColor = getUsageColor(data.value)
        return `${data.axisValue}<br/>使用率：<span style="color: ${usageColor}; font-weight: bold;">${data.value}%</span>`
      }
    },
    visualMap: {
      show: false,
      dimension: 1,
      pieces: [
        { gt: usageThresholds.value.high, color: colors.usageHigh },
        { gt: usageThresholds.value.low, lte: usageThresholds.value.high, color: colors.usageMedium },
        { lte: usageThresholds.value.low, color: colors.usageLow }
      ]
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: dailyData.map(d => d.date),
      axisLine: { lineStyle: { color: colors.border } },
      axisLabel: { color: colors.textSecondary, fontSize: 10, rotate: 45 }
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 100,
      axisLine: { lineStyle: { color: colors.border } },
      axisLabel: { color: colors.textSecondary, fontSize: 11 },
      splitLine: { lineStyle: { color: colors.borderLight } }
    },
    series: [{
      type: 'line',
      smooth: true,
      symbol: 'circle',
      symbolSize: 6,
      data: dailyData.map(d => d.avg_usage),
      lineStyle: { color: colors.chart1, width: 2 },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: colors.chart1 + '4D' },
            { offset: 1, color: colors.chart1 + '0D' }
          ]
        }
      },
      itemStyle: { color: colors.chart1 }
    }]
  }

  hourlyOption.value = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: colors.panelBgStart,
      borderColor: colors.border,
      textStyle: { color: colors.text },
      formatter: (params) => {
        const data = params[0]
        const usageColor = getUsageColor(data.value)
        return `${data.axisValue}<br/>使用率：<span style="color: ${usageColor}; font-weight: bold;">${data.value}%</span>`
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: hourlyData.length > 0 ? hourlyData.map(d => `${d.hour}:00`) : [],
      axisLine: { lineStyle: { color: colors.border } },
      axisLabel: { color: colors.textSecondary, fontSize: 10 }
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 100,
      axisLine: { lineStyle: { color: colors.border } },
      axisLabel: { color: colors.textSecondary, fontSize: 11 },
      splitLine: { lineStyle: { color: colors.borderLight } }
    },
    series: hourlyData.length > 0 ? [{
      type: 'bar',
      data: hourlyData.map(d => d.avg_usage),
      itemStyle: { color: colors.chart3, borderRadius: [4, 4, 0, 0] },
      label: { show: true, position: 'top', formatter: '{c}%', color: colors.textSecondary, fontSize: 10 }
    }] : []
  }
}

watch(() => props.modelValue, (newVal) => {
  if (newVal) {
    selectedQuickRange.value = '3month'
    handleQuickRangeChange()
  }
})

watch(() => props.deviceId, (newVal) => {
  if (newVal && props.modelValue) {
    handleQuickRangeChange()
  }
})
</script>

<style lang="scss">
.el-dialog.device-usage-detail-dialog {
  margin-top: 8vh !important;
  max-height: 84vh !important;
  height: 84vh !important;
  transition: all 0.3s ease;
  display: flex !important;
  flex-direction: column !important;
  overflow: hidden !important;
  
  .el-dialog__body {
    height: 0 !important;
  }
}

.el-dialog.device-usage-detail-dialog.maximized {
  margin-top: 1vh !important;
  max-height: 98vh !important;
  height: 98vh !important;
  min-height: 98vh !important;
  
  .el-dialog__body {
    height: 0 !important;
  }
}

.el-dialog.device-usage-detail-dialog {
  .el-dialog__header {
    margin-bottom: 0 !important;
    padding: 12px 20px !important;
    border-bottom: 1px solid var(--theme-border);
    flex-shrink: 0;
  }
  
  .el-dialog__title {
    margin-bottom: 0 !important;
    padding-bottom: 0 !important;
  }
  
  .el-dialog__body {
    padding: 0 !important;
    flex: 1 1 auto !important;
    overflow: hidden !important;
    display: flex !important;
    flex-direction: column !important;
    min-height: 0 !important;
  }
  
  .dialog-header {
    display: grid;
    grid-template-columns: auto 1fr auto;
    align-items: center;
    gap: 16px;
    width: 100%;
    
    .dialog-title {
      font-size: 16px;
      font-weight: 600;
      color: var(--theme-text);
      white-space: nowrap;
    }
    
    .header-controls {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 12px;
      
      .quick-ranges {
        display: flex;
        align-items: center;
        
        :deep(.el-radio-group) {
          .el-radio-button {
            .el-radio-button__inner {
              background: var(--theme-shadow);
              border-color: var(--theme-border);
              color: var(--theme-text);
              padding: 6px 12px;
              font-size: 12px;
              
              &:hover {
                color: var(--theme-primary);
              }
              
              &.is-active {
                background: var(--theme-primary);
                border-color: var(--theme-primary);
                color: white;
              }
            }
          }
        }
      }
      
      .custom-range {
        :deep(.el-date-range-picker) {
          width: 220px;
        }
      }
    }
    
    .header-actions {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-shrink: 0;
      
      .control-btn {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 32px;
        height: 32px;
        padding: 0;
        border: 1px solid var(--theme-border);
        border-radius: 4px;
        background: transparent;
        cursor: pointer;
        transition: all 0.3s;
        flex-shrink: 0;
        
        &:hover {
          background: var(--theme-hover-bg);
          border-color: var(--theme-primary);
          
          svg {
            stroke: var(--theme-primary);
          }
        }
        
        &.close-btn:hover {
          background: #ff4d4f;
          border-color: #ff4d4f;
          
          svg {
            stroke: white;
          }
        }
        
        svg {
          width: 18px;
          height: 18px;
          stroke: var(--theme-text-secondary);
        }
      }
    }
  }
  
  .dialog-content {
    display: flex;
    flex-direction: column;
    height: 100%;
    padding: 16px;
    overflow: hidden;
  }

  .date-range-selector {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 16px;
    background: var(--theme-shadow);
    border: 1px solid var(--theme-border);
    border-radius: 8px;
    flex-shrink: 0;

    .quick-ranges {
      display: flex;
      align-items: center;

      :deep(.el-radio-group) {
        .el-radio-button {
          .el-radio-button__inner {
            background: var(--theme-shadow);
            border-color: var(--theme-border);
            color: var(--theme-text);
            padding: 8px 16px;
            font-size: 13px;

            &:hover {
              color: var(--theme-primary);
            }

            &.is-active {
              background: var(--theme-primary);
              border-color: var(--theme-primary);
              color: white;
            }
          }
        }
      }
    }

    .custom-range {
      :deep(.el-date-range-picker) {
        width: 240px;
      }
    }
  }

  .loading-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 16px;
    padding: 60px;
    color: var(--theme-text-secondary);
    font-size: 14px;
  }

  .charts-container {
    display: grid;
    grid-template-columns: 1fr;
    grid-template-rows: repeat(3, 1fr);
    gap: 16px;
    flex: 1;
    min-height: 0;
    overflow: hidden;
  }

  .chart-section {
    display: flex;
    flex-direction: column;
    background: var(--theme-shadow);
    border: 1px solid var(--theme-border);
    border-radius: 12px;
    overflow: hidden;
    min-height: 0;

    .chart-header {
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
    }

    .chart-wrapper {
      flex: 1;
      min-height: 0;
      width: 100%;

      :deep(.echarts) {
        width: 100% !important;
        height: 100% !important;
      }
    }
  }
}

</style>
