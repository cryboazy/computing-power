<template>
  <div class="usage-detail-tab">
    <div v-if="usageDataAll?.warning" class="warning-banner" :class="usageDataAll.warning.type">
      <el-icon :size="24"><Warning /></el-icon>
      <div class="warning-content">
        <strong>使用率预警</strong>
        <p>{{ usageDataAll.warning.message }}</p>
      </div>
    </div>
    
    <div v-if="loading" class="loading-container">
      <el-icon class="is-loading" :size="40"><Loading /></el-icon>
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
</template>

<script setup>
import { ref, watch, onMounted, nextTick, inject } from 'vue'
import { Loading, Warning } from '@element-plus/icons-vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent, MarkLineComponent } from 'echarts/components'
import { dashboardApi } from '../../api'
import { useTheme } from '../../composables/useTheme'

use([
  CanvasRenderer,
  LineChart,
  BarChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  MarkLineComponent
])

const props = defineProps({
  orgId: {
    type: [Number, String],
    required: true
  },
  dateRange: {
    type: Array,
    default: null
  },
  purpose: {
    type: Number,
    default: null
  }
})

const usageThresholds = inject('usageThresholds', ref({ high: 60.0, low: 30.0 }))
const { getAllColors } = useTheme()

const getUsageColor = (value) => {
  const colors = getAllColors()
  if (value >= usageThresholds.value.high) {
    return colors.usageHigh
  } else if (value >= usageThresholds.value.low) {
    return colors.usageMedium
  }
  return colors.usageLow
}

const loading = ref(false)
const usageDataAll = ref(null)
const usageDataWork = ref(null)
const usageDataNonwork = ref(null)
const dataLoaded = ref(false)
const monthlyOption = ref({})
const dailyOption = ref({})
const hourlyOption = ref({})

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

initializeEmptyOptions()

const fetchData = async () => {
  console.log('[UsageDetailTab] fetchData called with orgId:', props.orgId, 'dateRange:', props.dateRange, 'purpose:', props.purpose)
  if (!props.orgId) {
    console.log('[UsageDetailTab] No orgId provided')
    return
  }
  
  loading.value = true
  dataLoaded.value = false
  
  try {
    let startDate = null
    let endDate = null
    
    if (props.dateRange && props.dateRange.length === 2) {
      startDate = props.dateRange[0]
      endDate = props.dateRange[1]
    }
    
    const apiParams = { timeType: 'all', startDate, endDate }
    if (props.purpose) {
      apiParams.purpose = props.purpose
    }
    
    console.log('[UsageDetailTab] Calling API for all time types')
    const [dataAll, dataWork, dataNonwork] = await Promise.all([
      dashboardApi.getOrgUsageTrend(props.orgId, 'all', startDate, endDate, props.purpose),
      dashboardApi.getOrgUsageTrend(props.orgId, 'work', startDate, endDate, props.purpose),
      dashboardApi.getOrgUsageTrend(props.orgId, 'nonwork', startDate, endDate, props.purpose)
    ])
    
    console.log('[UsageDetailTab] API responses received')
    usageDataAll.value = dataAll
    usageDataWork.value = dataWork
    usageDataNonwork.value = dataNonwork
    
    await nextTick()
    updateChartOptions()
    dataLoaded.value = true
    console.log('[UsageDetailTab] dataLoaded set to true')
  } catch (error) {
    console.error('[UsageDetailTab] Failed to fetch usage trend:', error)
    console.error('[UsageDetailTab] Error details:', error.response?.data || error.message)
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
  
  console.log('[UsageDetailTab] updateChartOptions called')
  
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
        return `${data.axisValue}<br/>使用率: <span style="color: ${usageColor}; font-weight: bold;">${data.value}%</span>`
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
        return `${data.axisValue}<br/>使用率: <span style="color: ${usageColor}; font-weight: bold;">${data.value}%</span>`
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
      data: hourlyData.map(d => `${d.hour}:00`),
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
    series: [{
      type: 'line',
      smooth: true,
      symbol: 'circle',
      symbolSize: 6,
      data: hourlyData.map(d => d.avg_usage),
      lineStyle: { color: colors.chart2, width: 2 },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: colors.chart2 + '4D' },
            { offset: 1, color: colors.chart2 + '0D' }
          ]
        }
      },
      itemStyle: { color: colors.chart2 }
    }]
  }
  
  console.log('[UsageDetailTab] updateChartOptions completed, monthlyOption:', monthlyOption.value)
}

watch(() => props.orgId, (newVal) => {
  if (newVal) {
    fetchData()
  }
})

watch(() => props.dateRange, (newVal) => {
  if (newVal && props.orgId) {
    fetchData()
  }
}, { deep: true })

watch(() => props.purpose, (newVal) => {
  if (props.orgId) {
    fetchData()
  }
})

onMounted(() => {
  fetchData()
})
</script>

<style lang="scss" scoped>
.usage-detail-tab {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow: hidden;
}

.warning-banner {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  border-radius: 12px;
  border: 1px solid;
  flex-shrink: 0;
  
  &.high {
    background: linear-gradient(90deg, rgba(245, 108, 108, 0.15) 0%, rgba(245, 108, 108, 0.05) 100%);
    border-color: var(--theme-danger);
    
    .el-icon {
      color: var(--theme-danger);
    }
    
    strong {
      color: var(--theme-danger);
    }
  }
  
  &.low {
    background: linear-gradient(90deg, rgba(230, 162, 60, 0.15) 0%, rgba(230, 162, 60, 0.05) 100%);
    border-color: var(--theme-warning);
    
    .el-icon {
      color: var(--theme-warning);
    }
    
    strong {
      color: var(--theme-warning);
    }
  }
  
  .warning-content {
    flex: 1;
    
    strong {
      display: block;
      font-size: 14px;
      font-weight: 600;
      margin-bottom: 4px;
    }
    
    p {
      margin: 0;
      font-size: 13px;
      color: var(--theme-text-secondary);
    }
  }
}

.loading-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  color: var(--theme-text-secondary);
  font-size: 14px;
}

.charts-container {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr;
  grid-template-rows: repeat(3, minmax(250px, 1fr));
  gap: 16px;
  overflow: hidden;
  min-height: 750px;
}

.chart-section {
  display: flex;
  flex-direction: column;
  background: var(--theme-shadow);
  border: 1px solid var(--theme-border);
  border-radius: 12px;
  overflow: hidden;
  min-height: 250px;
  
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
    min-height: 200px;
    width: 100%;
    
    :deep(.echarts) {
      width: 100% !important;
      height: 100% !important;
      min-height: 200px;
    }
  }
}
</style>
