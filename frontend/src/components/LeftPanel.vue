<template>
  <div class="left-panel-content">
    <div class="panel trend-section">
      <div class="panel-header">
        <span class="panel-title">资源趋势</span>
      </div>
      <div class="panel-content">
        <div v-if="!deviceCountData.length && !gpuCountData.length && !memoryTotalData.length && !computeTotalData.length" class="no-data">
          暂无数据
        </div>
        <v-chart v-else :option="combinedTrendOption" autoresize />
      </div>
    </div>
    
    <div class="panel trend-section">
      <div class="panel-header">
        <span class="panel-title">使用率趋势</span>
      </div>
      <div class="panel-content">
        <div v-if="!gpuUsageData.length" class="no-data">
          暂无数据
        </div>
        <v-chart v-else :option="gpuUsageOption" autoresize />
      </div>
    </div>
    
    <div class="panel warning-section">
      <div class="panel-header">
        <span class="panel-title">使用率预警</span>
        <div class="carousel-controls">
          <div class="view-type-switch">
            <span 
              :class="['type-btn', { active: warningViewType === 'chart' }]"
              @click="warningViewType = 'chart'"
            >图表</span>
            <span 
              :class="['type-btn', { active: warningViewType === 'list' }]"
              @click="warningViewType = 'list'"
            >列表</span>
          </div>
          <select class="level-selector" v-model="warningLevel" @change="warningPageIndex = 0">
            <option v-for="level in WARNING_LEVEL_OPTIONS" :key="level.value" :value="level.value">
              {{ level.label }}
            </option>
          </select>
          <div v-show="warningViewType === 'chart'" class="carousel-indicator">
            <span 
              v-for="i in warningPageCount" 
              :key="i" 
              :class="['indicator-dot', { active: warningPageIndex === i - 1 }]"
              @click="warningPageIndex = i - 1"
            ></span>
          </div>
        </div>
      </div>
      <div class="panel-content">
        <div v-if="!warningData.length && warningViewType === 'chart'" class="no-data">
          暂无数据
        </div>
        <v-chart v-show="warningViewType === 'chart' && warningData.length" :option="warningBarOption" autoresize />
        <div v-show="warningViewType === 'list'" class="warning-list">
          <div class="list-header">
            <span class="col-name">单位名称</span>
            <span class="col-usage">使用率</span>
            <span class="col-status">状态</span>
          </div>
          <div class="list-body">
            <div v-if="!warningListData.length" class="no-data-list">
              暂无数据
            </div>
            <div 
              v-else
              v-for="(item, index) in warningListData" 
              :key="index"
              class="list-row"
              :class="item.level"
              @click="handleWarningItemClick(item)"
            >
              <span class="col-name" :title="item.org_name">{{ item.org_name }}</span>
              <span class="col-usage">{{ item.avg_usage.toFixed(1) }}%</span>
              <span class="col-status">{{ item.level === 'high' ? '高' : item.level === 'low' ? '低' : '中' }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, inject } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, BarChart } from 'echarts/charts'
import { 
  GridComponent, 
  TooltipComponent, 
  LegendComponent,
  DataZoomComponent 
} from 'echarts/components'
import { dashboardApi } from '../api'
import { useTheme, watchThemeChange } from '../composables/useTheme'

use([
  CanvasRenderer,
  LineChart,
  BarChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  DataZoomComponent
])

const globalPageSize = inject('globalPageSize')
const showOrgDetail = inject('showOrgDetail')
const timeType = inject('timeType')
const activeTab = inject('globalTimeRange')
const globalNetworkFilter = inject('globalNetworkFilter')
const globalPurposeFilter = inject('globalPurposeFilter')
const usageThresholds = inject('usageThresholds', ref({ high: 60.0, low: 30.0 }))
const { getAllColors, currentThemeKey } = useTheme()

const deviceCountData = ref([])
const gpuCountData = ref([])
const memoryTotalData = ref([])
const computeTotalData = ref([])
const gpuUsageData = ref([])
const warningData = ref([])

const WARNING_LEVEL_OPTIONS = [
  { label: '全部', value: 'all' },
  { label: '高', value: 'high' },
  { label: '中', value: 'medium' },
  { label: '低', value: 'low' }
]
const warningLevel = ref('all')
const warningViewType = ref('chart')
const warningPageIndex = ref(0)
let warningTimer = null

const getEffectivePageSize = (size, total) => {
  return size === 'all' ? total : size
}

const combinedTrendOption = computed(() => {
  const dates = deviceCountData.value.map(d => d.date)
  const colors = getAllColors()
  
  return {
    tooltip: {
      trigger: 'axis',
      backgroundColor: colors.panelBgStart,
      borderColor: colors.border,
      textStyle: { color: colors.text },
      formatter: (params) => {
        let result = params[0].axisValue + '<br/>'
        params.forEach(param => {
          let unit = ''
          let value = param.value
          if (param.seriesName.includes('设备')) {
            unit = '台'
          } else if (param.seriesName.includes('GPU卡')) {
            unit = '张'
          } else if (param.seriesName.includes('显存')) {
            if (value >= 1024) {
              value = (value / 1024).toFixed(2)
              unit = 'TB'
            } else {
              value = Math.round(value)
              unit = 'GB'
            }
          } else if (param.seriesName.includes('算力')) {
            unit = 'PF'
          }
          result += `${param.marker} ${param.seriesName}: ${value}${unit}<br/>`
        })
        return result
      }
    },
    legend: {
      data: ['设备数量', 'GPU卡数量', '显存总量', '算力'],
      textStyle: { color: colors.textSecondary, fontSize: 11 },
      top: 0,
      itemWidth: 15,
      itemHeight: 8
    },
    grid: {
      left: '3%',
      right: '3%',
      bottom: '3%',
      top: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: dates,
      axisLine: { lineStyle: { color: colors.border } },
      axisLabel: { color: colors.textSecondary, fontSize: 10 }
    },
    yAxis: [
      {
        type: 'value',
        position: 'left',
        axisLine: { lineStyle: { color: colors.chart1 } },
        axisLabel: { show: false },
        splitLine: { lineStyle: { color: colors.borderLight } }
      },
      {
        type: 'value',
        position: 'right',
        axisLine: { lineStyle: { color: colors.chart4 } },
        axisLabel: { show: false },
        splitLine: { show: false }
      },
      {
        type: 'value',
        position: 'right',
        offset: 40,
        axisLine: { lineStyle: { color: colors.chart2 } },
        axisLabel: { show: false },
        splitLine: { show: false }
      },
      {
        type: 'value',
        position: 'right',
        offset: 80,
        axisLine: { lineStyle: { color: colors.chart3 } },
        axisLabel: { show: false },
        splitLine: { show: false }
      }
    ],
    series: [
      {
        name: '设备数量',
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 4,
        yAxisIndex: 0,
        lineStyle: { color: colors.chart1, width: 2 },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: colors.chart1 + '33' },
              { offset: 1, color: colors.chart1 + '05' }
            ]
          }
        },
        itemStyle: { color: colors.chart1 },
        data: deviceCountData.value.map(d => d.value)
      },
      {
        name: 'GPU卡数量',
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 4,
        yAxisIndex: 1,
        lineStyle: { color: colors.chart4, width: 2 },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: colors.chart4 + '33' },
              { offset: 1, color: colors.chart4 + '05' }
            ]
          }
        },
        itemStyle: { color: colors.chart4 },
        data: gpuCountData.value.map(d => d.value)
      },
      {
        name: '显存总量',
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 4,
        yAxisIndex: 2,
        lineStyle: { color: colors.chart2, width: 2 },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: colors.chart2 + '33' },
              { offset: 1, color: colors.chart2 + '05' }
            ]
          }
        },
        itemStyle: { color: colors.chart2 },
        data: memoryTotalData.value.map(d => d.value)
      },
      {
        name: '算力',
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 4,
        yAxisIndex: 3,
        lineStyle: { color: colors.chart3, width: 2 },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: colors.chart3 + '33' },
              { offset: 1, color: colors.chart3 + '05' }
            ]
          }
        },
        itemStyle: { color: colors.chart3 },
        data: computeTotalData.value.map(d => d.value)
      }
    ]
  }
})

const gpuUsageOption = computed(() => {
  const colors = getAllColors()
  return {
    tooltip: {
      trigger: 'axis',
      backgroundColor: colors.panelBgStart,
      borderColor: colors.border,
      textStyle: { color: colors.text },
      formatter: (params) => {
        const date = params[0].axisValue
        let html = `${date}<br/>`
        params.forEach(p => {
          if (p.value !== null && p.value !== undefined) {
            html += `${p.marker} ${p.seriesName}: <strong>${p.value}%</strong><br/>`
          }
        })
        return html
      }
    },
    legend: {
      data: ['GPU使用率', '显存使用率', '显存利用率'],
      textStyle: { color: colors.textSecondary },
      top: 0,
      right: 0,
      itemWidth: 12,
      itemHeight: 8
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '18%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: gpuUsageData.value.map(d => d.date),
      axisLine: { lineStyle: { color: colors.border } },
      axisLabel: { color: colors.textSecondary, fontSize: 10 }
    },
    yAxis: {
      type: 'value',
      max: 100,
      axisLine: { lineStyle: { color: colors.border } },
      axisLabel: { 
        show: true, 
        color: colors.textSecondary, 
        fontSize: 10
      },
      splitLine: { lineStyle: { color: colors.borderLight } }
    },
    series: [
      {
        name: 'GPU使用率',
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 4,
        lineStyle: { color: colors.chart4, width: 2 },
        itemStyle: { color: colors.chart4 },
        data: gpuUsageData.value.map(d => d.gpu_usage)
      },
      {
        name: '显存使用率',
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 4,
        lineStyle: { color: colors.chart2, width: 2 },
        itemStyle: { color: colors.chart2 },
        data: gpuUsageData.value.map(d => d.memory_usage_rate)
      },
      {
        name: '显存利用率',
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 4,
        lineStyle: { color: colors.chart3, width: 2 },
        itemStyle: { color: colors.chart3 },
        data: gpuUsageData.value.map(d => d.memory_utilization)
      }
    ]
  }
})

const warningPageCount = computed(() => {
  const filteredData = warningLevel.value === 'all' 
    ? warningData.value 
    : warningData.value.filter(d => d.level === warningLevel.value)
  return Math.ceil(filteredData.length / getEffectivePageSize(globalPageSize.value, filteredData.length))
})

const simplifyOrgName = (name) => {
  if (!name) return ''
  if (name.length <= 4) return name
  return name.substring(0, 4) + '...'
}

const warningBarOption = computed(() => {
  const colors = getAllColors()
  const filteredData = warningLevel.value === 'all' 
    ? warningData.value 
    : warningData.value.filter(d => d.level === warningLevel.value)
  const pageSize = getEffectivePageSize(globalPageSize.value, filteredData.length)
  const startIdx = warningPageIndex.value * pageSize
  const endIdx = startIdx + pageSize
  const pageData = filteredData.slice(startIdx, endIdx)
  
  const levelColors = {
    high: colors.usageHigh,
    medium: colors.usageMedium,
    low: colors.usageLow
  }
  
  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: colors.panelBgStart,
      borderColor: colors.border,
      textStyle: { color: colors.text },
      formatter: (params) => {
        const data = params[0]
        const originalItem = pageData[data.dataIndex]
        return `${originalItem?.org_name || data.name}<br/>平均使用率: ${data.value}%<br/>状态: ${originalItem?.level === 'high' ? '高' : originalItem?.level === 'low' ? '低' : '中'}`
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
      data: pageData.map(d => simplifyOrgName(d.org_name)),
      axisLine: { lineStyle: { color: colors.border } },
      axisLabel: { 
        color: colors.textSecondary, 
        fontSize: 10
      }
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 100,
      interval: 20,
      axisLine: { lineStyle: { color: colors.border } },
      axisLabel: { 
        color: colors.textSecondary, 
        fontSize: 10,
        formatter: '{value}'
      },
      splitLine: { lineStyle: { color: colors.borderLight } }
    },
    series: [{
      type: 'bar',
      barWidth: '60%',
      itemStyle: {
        color: (params) => {
          const item = pageData[params.dataIndex]
          return levelColors[item?.level] || colors.warning
        },
        borderRadius: [4, 4, 0, 0]
      },
      data: pageData.map(d => d.avg_usage)
    }]
  }
})

const warningListData = computed(() => {
  const filteredData = warningLevel.value === 'all' 
    ? warningData.value 
    : warningData.value.filter(d => d.level === warningLevel.value)
  return filteredData
})

const fetchData = async () => {
  try {
    const network = globalNetworkFilter?.value === 'all' ? null : globalNetworkFilter?.value
    const purpose = globalPurposeFilter?.value === 'all' ? null : globalPurposeFilter?.value
    const [deviceCount, gpuCount, memoryTotal, computeTotal, gpuUsage, warning] = await Promise.all([
      dashboardApi.getDeviceCountTrend(activeTab.value, timeType.value, network),
      dashboardApi.getGpuCountTrend(activeTab.value, timeType.value, network),
      dashboardApi.getMemoryTotalTrend(activeTab.value, timeType.value, network),
      dashboardApi.getComputeTotalTrend(activeTab.value, timeType.value, network),
      dashboardApi.getGpuUsageTrend(activeTab.value, timeType.value, network, purpose),
      dashboardApi.getUsageWarningBar(activeTab.value, timeType.value, network, purpose)
    ])
    
    deviceCountData.value = deviceCount
    gpuCountData.value = gpuCount
    memoryTotalData.value = memoryTotal
    computeTotalData.value = computeTotal
    gpuUsageData.value = gpuUsage
    warningData.value = warning
  } catch (error) {
    console.error('Failed to fetch left panel data:', error)
  }
}





let cleanup = null

watch(activeTab, fetchData)
watch(timeType, fetchData)
watch(() => globalNetworkFilter?.value, fetchData)
watch(() => globalPurposeFilter?.value, fetchData)

const startWarningTimer = () => {
  if (warningTimer) clearInterval(warningTimer)
  warningTimer = setInterval(() => {
    if (warningPageCount.value > 1) {
      warningPageIndex.value = (warningPageIndex.value + 1) % warningPageCount.value
    }
  }, 5000)
}

const stopWarningTimer = () => {
  if (warningTimer) {
    clearInterval(warningTimer)
    warningTimer = null
  }
}

watch(globalPageSize, () => {
  warningPageIndex.value = 0
})

watch(warningLevel, () => {
  warningPageIndex.value = 0
})

onMounted(() => {
  fetchData()
  startWarningTimer()
  cleanup = watchThemeChange(() => {
    fetchData()
  })
})

const handleWarningItemClick = (item) => {
  if (showOrgDetail && item.org_id) {
    showOrgDetail(item.org_id, 'usage')
  }
}

onUnmounted(() => {
  stopWarningTimer()
  if (cleanup) cleanup()
})
</script>

<style lang="scss" scoped>
.left-panel-content {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.trend-section {
  flex: 1;
  min-height: 0;
  
  .panel-content {
    :deep(.echarts) {
      width: 100%;
      height: 100%;
    }
  }
}

.warning-section {
  flex: 1;
  min-height: 0;
  
  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .carousel-controls {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  
  .level-selector {
    padding: 2px 6px;
    font-size: 10px;
    color: var(--theme-text);
    background: var(--theme-shadow);
    border: 1px solid var(--theme-border);
    border-radius: 4px;
    cursor: pointer;
    outline: none;
    transition: all 0.3s ease;
    
    &:hover {
      border-color: var(--theme-primary);
    }
    
    &:focus {
      border-color: var(--theme-primary);
      box-shadow: 0 0 4px var(--theme-glow);
    }
    
    option {
      background: var(--theme-panel-bg-start);
      color: var(--theme-text);
    }
  }
  
  .carousel-indicator {
    display: flex;
    gap: 4px;
    
    .indicator-dot {
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: var(--theme-text-muted);
      cursor: pointer;
      transition: all 0.3s ease;
      
      &:hover {
        background: var(--theme-text-secondary);
      }
      
      &.active {
        background: var(--theme-primary);
        box-shadow: 0 0 4px var(--theme-glow);
      }
    }
  }
  
  .view-type-switch {
    display: flex;
    gap: 2px;
    background: var(--theme-shadow);
    border-radius: 4px;
    padding: 2px;
    
    .type-btn {
      padding: 2px 8px;
      font-size: 10px;
      color: var(--theme-text-secondary);
      cursor: pointer;
      border-radius: 3px;
      transition: all 0.3s ease;
      
      &:hover {
        color: var(--theme-primary);
        background: var(--theme-border-light);
      }
      
      &.active {
        color: var(--theme-text);
        background: linear-gradient(135deg, var(--theme-primary) 0%, var(--theme-secondary) 100%);
        box-shadow: 0 0 6px var(--theme-glow);
      }
    }
  }
  
  .panel-content {
    :deep(.echarts) {
      width: 100%;
      height: 100%;
    }
  }
  
  .warning-list {
    height: 100%;
    display: flex;
    flex-direction: column;
    font-size: 11px;
    
    .list-header {
      display: flex;
      padding: 6px 8px;
      background: var(--theme-shadow);
      border-radius: 4px;
      margin-bottom: 4px;
      color: var(--theme-text-secondary);
      font-weight: 500;
      flex-shrink: 0;
    }
    
    .list-body {
      flex: 1;
      overflow-y: auto;
      
      &::-webkit-scrollbar {
        width: 4px;
      }
      
      &::-webkit-scrollbar-track {
        background: var(--theme-shadow);
        border-radius: 2px;
      }
      
      &::-webkit-scrollbar-thumb {
        background: var(--theme-border);
        border-radius: 2px;
        
        &:hover {
          background: var(--theme-primary);
        }
      }
    }
    
    .list-row {
      display: flex;
      padding: 6px 8px;
      border-radius: 4px;
      cursor: pointer;
      transition: all 0.2s ease;
      margin-bottom: 2px;
      
      &:hover {
        background: var(--theme-shadow);
      }
      
      &.high {
        .col-status { color: var(--theme-danger, #f56c6c); }
      }
      
      &.medium {
        .col-status { color: var(--theme-warning, #e6a23c); }
      }
      
      &.low {
        .col-status { color: var(--theme-success, #67c23a); }
      }
    }
    
    .col-name {
      flex: 1;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    
    .col-usage {
      width: 60px;
      text-align: right;
      padding-right: 10px;
    }
    
    .col-status {
      width: 30px;
      text-align: center;
    }
  }
}

.no-data {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--theme-text-muted);
  font-size: 14px;
}

.no-data-list {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  color: var(--theme-text-muted);
  font-size: 13px;
}
</style>
