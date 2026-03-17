<template>
  <div class="panel-expand-content">
    <div v-if="loading" class="loading-container">
      <div class="loading-spinner"></div>
      <span>加载中...</span>
    </div>
    
    <template v-else>
      <div v-if="panelType === 'left'" class="expand-panel">
        <div v-if="subType === 'combined'" class="chart-section">
          <v-chart :option="combinedTrendOption" autoresize />
        </div>
        <div v-else-if="subType === 'device'" class="chart-section">
          <v-chart :option="deviceCountOption" autoresize />
        </div>
        <div v-else-if="subType === 'memory'" class="chart-section">
          <v-chart :option="memoryTotalOption" autoresize />
        </div>
        <div v-else-if="subType === 'compute'" class="chart-section">
          <v-chart :option="computeTotalOption" autoresize />
        </div>
        <div v-else-if="subType === 'usage'" class="chart-section">
          <v-chart :option="gpuUsageOption" autoresize />
        </div>
        <div v-else-if="subType === 'warning'" class="chart-section">
          <v-chart :option="warningBarOption" autoresize @click="handleExpandWarningBarClick" />
        </div>
      </div>
      
      <div v-else-if="panelType === 'center'" class="expand-panel">
        <div v-if="subType === 'orgType'" class="dual-pie-section">
          <div class="pie-container">
            <div class="pie-wrapper">
              <div class="pie-label">部机关单位</div>
              <v-chart :option="centralPieOption" autoresize />
            </div>
            <div class="pie-wrapper">
              <div class="pie-label">地方厅局单位</div>
              <v-chart :option="localPieOption" autoresize />
            </div>
          </div>
        </div>
        <div v-else-if="subType === 'network'" class="chart-section">
          <v-chart :option="networkOption" autoresize @click="handleExpandNetworkChartClick" />
        </div>
        <div v-else-if="subType === 'gpuTier'" class="chart-section">
          <v-chart :option="gpuTierOption" autoresize @click="handleExpandGpuTierChartClick" />
        </div>
        <div v-else-if="subType === 'purpose'" class="chart-section">
          <v-chart :option="purposeOption" autoresize @click="handleExpandPurposeChartClick" />
        </div>
        <div v-else-if="subType === 'carousel'" class="carousel-section">
          <div class="filter-bar">
            <div class="filter-item">
              <label>单位类型</label>
              <el-select v-model="carouselOrgType" placeholder="全部" clearable size="small" @change="handleCarouselFilter">
                <el-option label="部机关" value="central" />
                <el-option label="地方厅局" value="local" />
              </el-select>
            </div>
            <div class="filter-item">
              <label>单位名称</label>
              <el-input 
                v-model="carouselOrgName" 
                placeholder="请输入单位名称" 
                size="small" 
                clearable 
                @keyup.enter="handleCarouselFilter"
                @clear="handleCarouselFilter"
              >
                <template #append>
                  <el-button icon="Search" @click="handleCarouselFilter" />
                </template>
              </el-input>
            </div>
            <div class="filter-item">
              <label>时间粒度</label>
              <el-radio-group v-model="carouselTimeGrain" size="small" @change="handleTimeGrainChange">
                <el-radio-button label="day">日</el-radio-button>
                <el-radio-button label="week">周</el-radio-button>
                <el-radio-button label="month">月</el-radio-button>
              </el-radio-group>
            </div>
            <div class="filter-item">
              <label>时间段</label>
              <el-date-picker
                v-model="carouselDateRange"
                type="daterange"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                size="small"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                @change="handleDateRangeChange"
              />
            </div>
          </div>
          <div class="carousel-grid-wrapper">
            <div class="carousel-grid">
              <div v-for="(item, index) in carouselData" :key="index" class="carousel-item">
                <div class="carousel-title" @click="handleExpandCarouselTitleClick(item)">{{ item.org_name }}</div>
                <v-chart 
                  :option="getCarouselOption(item.trend)" 
                  autoresize 
                  @click="(params) => handleChartClick(params, item.org_name, item.org_id)"
                />
              </div>
            </div>
          </div>
          
          <el-dialog
            v-model="drillDialogVisible"
            :title="`${drillOrgName} - ${drillDate} 使用率详情`"
            width="900px"
            :close-on-click-modal="false"
            class="drill-dialog"
            destroy-on-close
            top="8vh"
            append-to-body
            :show-close="false"
          >
            <template #header>
              <div class="drill-dialog-header">
                <span class="drill-title">{{ drillOrgName }} - {{ drillDate }} 使用率详情</span>
                <button class="drill-close-btn" @click="drillDialogVisible = false">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                  </svg>
                </button>
              </div>
            </template>
            <div v-if="drillLoading" class="drill-loading">
              <div class="loading-spinner"></div>
              <span>加载中...</span>
            </div>
            <div v-else class="drill-chart-container">
              <v-chart v-if="drillTrendData.length > 0" :option="drillChartOption" autoresize style="height: 400px" />
              <div v-else class="no-data">暂无数据</div>
            </div>
          </el-dialog>
        </div>
      </div>
      
      <div v-else-if="panelType === 'right'" class="expand-panel">
        <div v-if="subType === 'all'" class="ranking-table-section">
          <div class="table-header">
            <h3>全国排名</h3>
            <span class="total-count">共 {{ allRanking.length }} 个单位</span>
          </div>
          <el-table 
            :data="sortedAllRanking" 
            stripe 
            style="width: 100%"
            :header-cell-style="tableHeaderStyle"
            :cell-style="tableCellStyle"
            @sort-change="handleSortChange('all', $event)"
            @row-click="handleExpandRankingRowClick"
          >
            <el-table-column prop="rank" label="排名" width="80" fixed="left" sortable>
              <template #default="{ row }">
                <span :class="['rank-badge', `rank-${row.rank}`]">{{ row.rank }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="org_name" label="单位名称" min-width="140" fixed="left">
              <template #default="{ row }">
                <span class="org-name">{{ row.org_name }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="device_count" label="设备数" width="100" sortable>
              <template #default="{ row }">
                <span class="value-cell">{{ row.device_count }} 台</span>
              </template>
            </el-table-column>
            <el-table-column prop="gpu_count" label="GPU数" width="100" sortable>
              <template #default="{ row }">
                <span class="value-cell">{{ row.gpu_count }} 块</span>
              </template>
            </el-table-column>
            <el-table-column prop="memory_total" label="显存总量" width="115" sortable>
              <template #default="{ row }">
                <span class="value-cell memory">{{ formatMemory(row.memory_total) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="compute_total" label="总算力" width="140" sortable>
              <template #default="{ row }">
                <span class="value-cell compute">{{ formatCompute(row.compute_total) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="cpu_cores" label="CPU核数" width="115" sortable>
              <template #default="{ row }">
                <span class="value-cell cpu">{{ row.cpu_cores || 0 }} 核</span>
              </template>
            </el-table-column>
            <el-table-column prop="memory_capacity" label="内存容量" width="115" sortable>
              <template #default="{ row }">
                <span class="value-cell ram">{{ formatCapacity(row.memory_capacity) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="disk_capacity" label="存储容量" width="115" sortable>
              <template #default="{ row }">
                <span class="value-cell disk">{{ formatCapacity(row.disk_capacity) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="avg_gpu_usage" label="GPU使用率" width="130" sortable>
              <template #default="{ row }">
                <span class="value-cell usage" :style="{ color: getUsageColor(row.avg_gpu_usage) }">{{ row.avg_gpu_usage || 0 }}%</span>
              </template>
            </el-table-column>
          </el-table>
        </div>
        <div v-else-if="subType === 'group'" class="ranking-table-section">
          <div class="table-header">
            <h3>{{ groupName }}排名</h3>
            <span class="total-count">共 {{ groupRanking.length }} 个单位</span>
          </div>
          <el-table 
            :data="sortedGroupRanking" 
            stripe 
            style="width: 100%"
            :header-cell-style="tableHeaderStyle"
            :cell-style="tableCellStyle"
            @sort-change="handleSortChange('group', $event)"
            @row-click="handleExpandRankingRowClick"
          >
            <el-table-column prop="rank" label="排名" width="80" fixed="left" sortable>
              <template #default="{ row }">
                <span :class="['rank-badge', `rank-${row.rank}`]">{{ row.rank }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="org_name" label="单位名称" min-width="140" fixed="left">
              <template #default="{ row }">
                <span class="org-name">{{ row.org_name }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="device_count" label="设备数" width="100" sortable>
              <template #default="{ row }">
                <span class="value-cell">{{ row.device_count }} 台</span>
              </template>
            </el-table-column>
            <el-table-column prop="gpu_count" label="GPU数" width="100" sortable>
              <template #default="{ row }">
                <span class="value-cell">{{ row.gpu_count }} 块</span>
              </template>
            </el-table-column>
            <el-table-column prop="memory_total" label="显存总量" width="115" sortable>
              <template #default="{ row }">
                <span class="value-cell memory">{{ formatMemory(row.memory_total) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="compute_total" label="总算力" width="140" sortable>
              <template #default="{ row }">
                <span class="value-cell compute">{{ formatCompute(row.compute_total) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="cpu_cores" label="CPU核数" width="115" sortable>
              <template #default="{ row }">
                <span class="value-cell cpu">{{ row.cpu_cores || 0 }} 核</span>
              </template>
            </el-table-column>
            <el-table-column prop="memory_capacity" label="内存容量" width="115" sortable>
              <template #default="{ row }">
                <span class="value-cell ram">{{ formatCapacity(row.memory_capacity) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="disk_capacity" label="存储容量" width="115" sortable>
              <template #default="{ row }">
                <span class="value-cell disk">{{ formatCapacity(row.disk_capacity) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="avg_gpu_usage" label="GPU使用率" width="130" sortable>
              <template #default="{ row }">
                <span class="value-cell usage" :style="{ color: getUsageColor(row.avg_gpu_usage) }">{{ row.avg_gpu_usage || 0 }}%</span>
              </template>
            </el-table-column>
          </el-table>
        </div>
        <div v-else-if="subType === 'province'" class="ranking-table-section">
          <div class="table-header">
            <h3>{{ provinceName }}组织机构列表</h3>
            <span class="total-count">共 {{ provinceRanking.length }} 个单位</span>
          </div>
          <el-table 
            :data="sortedProvinceRanking" 
            stripe 
            style="width: 100%"
            :header-cell-style="tableHeaderStyle"
            :cell-style="tableCellStyle"
            @sort-change="handleSortChange('province', $event)"
            @row-click="handleExpandRankingRowClick"
          >
            <el-table-column prop="rank" label="排名" width="80" fixed="left" sortable>
              <template #default="{ row }">
                <span :class="['rank-badge', `rank-${row.rank}`]">{{ row.rank }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="org_name" label="单位名称" min-width="140" fixed="left">
              <template #default="{ row }">
                <span class="org-name">{{ row.org_name }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="device_count" label="设备数" width="100" sortable>
              <template #default="{ row }">
                <span class="value-cell">{{ row.device_count }} 台</span>
              </template>
            </el-table-column>
            <el-table-column prop="gpu_count" label="GPU数" width="100" sortable>
              <template #default="{ row }">
                <span class="value-cell">{{ row.gpu_count }} 块</span>
              </template>
            </el-table-column>
            <el-table-column prop="memory_total" label="显存总量" width="115" sortable>
              <template #default="{ row }">
                <span class="value-cell memory">{{ formatMemory(row.memory_total) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="compute_total" label="总算力" width="140" sortable>
              <template #default="{ row }">
                <span class="value-cell compute">{{ formatCompute(row.compute_total) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="cpu_cores" label="CPU核数" width="115" sortable>
              <template #default="{ row }">
                <span class="value-cell cpu">{{ row.cpu_cores || 0 }} 核</span>
              </template>
            </el-table-column>
            <el-table-column prop="memory_capacity" label="内存容量" width="115" sortable>
              <template #default="{ row }">
                <span class="value-cell ram">{{ formatCapacity(row.memory_capacity) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="disk_capacity" label="存储容量" width="115" sortable>
              <template #default="{ row }">
                <span class="value-cell disk">{{ formatCapacity(row.disk_capacity) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="avg_gpu_usage" label="GPU使用率" width="130" sortable>
              <template #default="{ row }">
                <span class="value-cell usage" :style="{ color: getUsageColor(row.avg_gpu_usage) }">{{ row.avg_gpu_usage || 0 }}%</span>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, inject } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, BarChart, PieChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import { dashboardApi } from '../api'
import { useTheme } from '../composables/useTheme'

use([
  CanvasRenderer,
  LineChart,
  BarChart,
  PieChart,
  GridComponent,
  TooltipComponent,
  LegendComponent
])

const showOrgDetail = inject('showOrgDetail')
const usageThresholds = inject('usageThresholds', ref({ high: 60.0, low: 30.0 }))
const { getAllColors } = useTheme()

const props = defineProps({
  panelType: {
    type: String,
    default: ''
  },
  subType: {
    type: String,
    default: ''
  },
  timeRange: {
    type: String,
    default: 'month'
  },
  groupName: {
    type: String,
    default: ''
  },
  provinceName: {
    type: String,
    default: ''
  }
})

const loading = ref(false)

const deviceCountData = ref([])
const memoryTotalData = ref([])
const computeTotalData = ref([])
const gpuUsageData = ref([])
const warningData = ref([])
const orgTypeData = ref({})
const networkByOrgData = ref({ networks: [], data: [] })
const gpuTierByOrgData = ref([])
const purposeByOrgData = ref({ purposes: [], data: [] })
const carouselData = ref([])
const carouselOrgType = ref('')
const carouselOrgName = ref('')
const carouselTimeGrain = ref('day')
const carouselDateRange = ref(null)
const drillDialogVisible = ref(false)
const drillLoading = ref(false)
const drillDate = ref('')
const drillOrgName = ref('')
const drillOrgId = ref(null)
const drillTrendData = ref([])
const allRanking = ref([])
const groupRanking = ref([])
const groupName = ref('')
const provinceRanking = ref([])
const provinceName = ref('')

const sortState = ref({
  all: { prop: 'rank', order: 'ascending' },
  group: { prop: 'rank', order: 'ascending' },
  province: { prop: 'rank', order: 'ascending' }
})

const tableHeaderStyle = {
  background: 'rgba(0, 180, 255, 0.1)',
  color: '#00b4ff',
  fontWeight: 'bold',
  borderBottom: '1px solid rgba(0, 180, 255, 0.3)'
}

const tableCellStyle = {
  color: 'rgba(255, 255, 255, 0.9)',
  borderBottom: '1px solid rgba(0, 180, 255, 0.1)'
}

const formatMemory = (mb) => {
  if (!mb || mb === 0) return '0 GB'
  if (mb >= 1024) {
    return (mb / 1024).toFixed(2) + ' TB'
  }
  return mb.toFixed(2) + ' GB'
}

const formatCompute = (tflops) => {
  if (!tflops || tflops === 0) return '0 TFLOPS'
  if (tflops >= 1000) {
    return (tflops / 1000).toFixed(2) + ' PFLOPS'
  }
  return tflops.toFixed(2) + ' TFLOPS'
}

const formatCapacity = (gb) => {
  if (!gb || gb === 0) return '0 GB'
  if (gb >= 1024) {
    return (gb / 1024).toFixed(2) + ' TB'
  }
  return gb.toFixed(0) + ' GB'
}

const getUsageColor = (usage) => {
  const colors = getAllColors()
  if (!usage || usage === 0) return colors.info
  if (usage >= usageThresholds.value.high) return colors.usageHigh
  if (usage >= usageThresholds.value.low) return colors.usageMedium
  return colors.usageLow
}

const sortData = (data, sortConfig) => {
  if (!sortConfig || !sortConfig.prop) return data
  
  const { prop, order } = sortConfig
  const sorted = [...data].sort((a, b) => {
    let aVal = a[prop]
    let bVal = b[prop]
    
    if (typeof aVal === 'string') {
      aVal = aVal.toLowerCase()
      bVal = bVal.toLowerCase()
    }
    
    if (aVal < bVal) return order === 'ascending' ? -1 : 1
    if (aVal > bVal) return order === 'ascending' ? 1 : -1
    return 0
  })
  
  return sorted
}

const sortedAllRanking = computed(() => sortData(allRanking.value, sortState.value.all))
const sortedGroupRanking = computed(() => sortData(groupRanking.value, sortState.value.group))
const sortedProvinceRanking = computed(() => sortData(provinceRanking.value, sortState.value.province))

const handleSortChange = (type, { prop, order }) => {
  sortState.value[type] = { prop, order }
}

const baseOption = {
  tooltip: {
    trigger: 'axis',
    backgroundColor: 'rgba(6, 30, 56, 0.9)',
    borderColor: 'rgba(0, 180, 255, 0.3)',
    textStyle: { color: '#fff' }
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '10%',
    top: '10%',
    containLabel: true
  },
  xAxis: {
    type: 'category',
    boundaryGap: false,
    axisLine: { lineStyle: { color: 'rgba(0, 180, 255, 0.3)' } },
    axisLabel: { color: 'rgba(255, 255, 255, 0.7)', fontSize: 11 }
  },
  yAxis: {
    type: 'value',
    axisLine: { lineStyle: { color: 'rgba(0, 180, 255, 0.3)' } },
    axisLabel: { color: 'rgba(255, 255, 255, 0.7)', fontSize: 11 },
    splitLine: { lineStyle: { color: 'rgba(0, 180, 255, 0.1)' } }
  }
}

const deviceCountOption = computed(() => ({
  ...baseOption,
  xAxis: { ...baseOption.xAxis, data: deviceCountData.value.map(d => d.date) },
  series: [{
    name: '设备总数',
    type: 'line',
    smooth: true,
    symbol: 'circle',
    symbolSize: 8,
    lineStyle: { color: '#00b4ff', width: 3 },
    areaStyle: {
      color: {
        type: 'linear',
        x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [
          { offset: 0, color: 'rgba(0, 180, 255, 0.4)' },
          { offset: 1, color: 'rgba(0, 180, 255, 0.05)' }
        ]
      }
    },
    itemStyle: { color: '#00b4ff' },
    data: deviceCountData.value.map(d => d.value)
  }]
}))

const combinedTrendOption = computed(() => {
  const dates = deviceCountData.value.map(d => d.date)
  
  return {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(6, 30, 56, 0.9)',
      borderColor: 'rgba(0, 180, 255, 0.3)',
      textStyle: { color: '#fff' },
      formatter: (params) => {
        let result = params[0].axisValue + '<br/>'
        params.forEach(param => {
          const unit = param.seriesName.includes('设备') ? '台' : 
                       param.seriesName.includes('显存') ? 'GB' : 
                       param.seriesName.includes('算力') ? 'PFLOPS' : ''
          result += `${param.marker} ${param.seriesName}: ${param.value}${unit}<br/>`
        })
        return result
      }
    },
    legend: {
      data: ['设备数量', '显存总量', '算力'],
      textStyle: { color: 'rgba(255, 255, 255, 0.7)', fontSize: 12 },
      top: 10,
      itemWidth: 20,
      itemHeight: 10
    },
    grid: {
      left: '3%',
      right: '3%',
      bottom: '3%',
      top: '12%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: dates,
      axisLine: { lineStyle: { color: 'rgba(0, 180, 255, 0.3)' } },
      axisLabel: { color: 'rgba(255, 255, 255, 0.7)', fontSize: 11 }
    },
    yAxis: [
      {
        type: 'value',
        position: 'left',
        axisLine: { lineStyle: { color: '#00b4ff' } },
        axisLabel: { color: 'rgba(255, 255, 255, 0.7)', fontSize: 11 },
        splitLine: { lineStyle: { color: 'rgba(0, 180, 255, 0.1)' } }
      },
      {
        type: 'value',
        position: 'right',
        offset: 50,
        axisLine: { lineStyle: { color: '#00ffcc' } },
        axisLabel: { color: 'rgba(255, 255, 255, 0.7)', fontSize: 11 },
        splitLine: { show: false }
      },
      {
        type: 'value',
        position: 'right',
        axisLine: { lineStyle: { color: '#f56c6c' } },
        axisLabel: { color: 'rgba(255, 255, 255, 0.7)', fontSize: 11 },
        splitLine: { show: false }
      }
    ],
    series: [
      {
        name: '设备数量',
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        yAxisIndex: 0,
        lineStyle: { color: '#00b4ff', width: 3 },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(0, 180, 255, 0.3)' },
              { offset: 1, color: 'rgba(0, 180, 255, 0.02)' }
            ]
          }
        },
        itemStyle: { color: '#00b4ff' },
        data: deviceCountData.value.map(d => d.value)
      },
      {
        name: '显存总量',
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        yAxisIndex: 1,
        lineStyle: { color: '#00ffcc', width: 3 },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(0, 255, 204, 0.3)' },
              { offset: 1, color: 'rgba(0, 255, 204, 0.02)' }
            ]
          }
        },
        itemStyle: { color: '#00ffcc' },
        data: memoryTotalData.value.map(d => d.value)
      },
      {
        name: '算力',
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        yAxisIndex: 2,
        lineStyle: { color: '#f56c6c', width: 3 },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(245, 108, 108, 0.3)' },
              { offset: 1, color: 'rgba(245, 108, 108, 0.02)' }
            ]
          }
        },
        itemStyle: { color: '#f56c6c' },
        data: computeTotalData.value.map(d => d.value)
      }
    ]
  }
})

const memoryTotalOption = computed(() => ({
  ...baseOption,
  xAxis: { ...baseOption.xAxis, data: memoryTotalData.value.map(d => d.date) },
  series: [{
    name: '显存总量(GB)',
    type: 'line',
    smooth: true,
    symbol: 'circle',
    symbolSize: 8,
    lineStyle: { color: '#00ffcc', width: 3 },
    areaStyle: {
      color: {
        type: 'linear',
        x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [
          { offset: 0, color: 'rgba(0, 255, 204, 0.4)' },
          { offset: 1, color: 'rgba(0, 255, 204, 0.05)' }
        ]
      }
    },
    itemStyle: { color: '#00ffcc' },
    data: memoryTotalData.value.map(d => d.value)
  }]
}))

const computeTotalOption = computed(() => ({
  ...baseOption,
  xAxis: { ...baseOption.xAxis, data: computeTotalData.value.map(d => d.date) },
  series: [{
    name: '算力(PFLOPS)',
    type: 'line',
    smooth: true,
    symbol: 'circle',
    symbolSize: 8,
    lineStyle: { color: '#f56c6c', width: 3 },
    areaStyle: {
      color: {
        type: 'linear',
        x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [
          { offset: 0, color: 'rgba(245, 108, 108, 0.4)' },
          { offset: 1, color: 'rgba(245, 108, 108, 0.05)' }
        ]
      }
    },
    itemStyle: { color: '#f56c6c' },
    data: computeTotalData.value.map(d => d.value)
  }]
}))

const gpuUsageOption = computed(() => ({
  ...baseOption,
  xAxis: { ...baseOption.xAxis, data: gpuUsageData.value.map(d => d.date) },
  series: [{
    name: 'GPU平均使用率(%)',
    type: 'line',
    smooth: true,
    symbol: 'circle',
    symbolSize: 8,
    lineStyle: { color: '#e6a23c', width: 3 },
    areaStyle: {
      color: {
        type: 'linear',
        x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [
          { offset: 0, color: 'rgba(230, 162, 60, 0.4)' },
          { offset: 1, color: 'rgba(230, 162, 60, 0.05)' }
        ]
      }
    },
    itemStyle: { color: '#e6a23c' },
    data: gpuUsageData.value.map(d => d.value)
  }]
}))

const warningBarOption = computed(() => ({
  tooltip: {
    trigger: 'axis',
    axisPointer: { type: 'shadow' },
    backgroundColor: 'rgba(6, 30, 56, 0.9)',
    borderColor: 'rgba(0, 180, 255, 0.3)',
    textStyle: { color: '#fff' },
    formatter: (params) => {
      const data = params[0]
      return `${data.name}<br/>平均使用率: ${data.value}%<br/>状态: ${warningData.value[data.dataIndex]?.level === 'high' ? '高' : warningData.value[data.dataIndex]?.level === 'low' ? '低' : '正常'}`
    }
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '10%',
    top: '10%',
    containLabel: true
  },
  xAxis: {
    type: 'category',
    data: warningData.value.map(d => d.org_name),
    axisLine: { lineStyle: { color: 'rgba(0, 180, 255, 0.3)' } },
    axisLabel: { 
      color: 'rgba(255, 255, 255, 0.7)', 
      fontSize: 11,
      rotate: 30
    },
    triggerEvent: true
  },
  yAxis: {
    type: 'value',
    name: '使用率(%)',
    nameTextStyle: { color: 'rgba(255, 255, 255, 0.7)' },
    axisLine: { lineStyle: { color: 'rgba(0, 180, 255, 0.3)' } },
    axisLabel: { color: 'rgba(255, 255, 255, 0.7)', fontSize: 11 },
    splitLine: { lineStyle: { color: 'rgba(0, 180, 255, 0.1)' } }
  },
  series: [{
    type: 'bar',
    barWidth: '50%',
    itemStyle: {
      color: (params) => {
        const item = warningData.value[params.dataIndex]
        return item?.color || '#00b4ff'
      },
      borderRadius: [6, 6, 0, 0]
    },
    data: warningData.value.map(d => d.avg_usage)
  }]
}))

const createPieOption = (data, colors) => ({
  tooltip: {
    trigger: 'item',
    backgroundColor: 'rgba(6, 30, 56, 0.9)',
    borderColor: 'rgba(0, 180, 255, 0.3)',
    textStyle: { color: '#fff' },
    formatter: '{b}: {c}台 ({d}%)'
  },
  legend: {
    orient: 'vertical',
    right: '5%',
    top: 'center',
    textStyle: { color: 'rgba(255, 255, 255, 0.7)', fontSize: 12 }
  },
  series: [{
    type: 'pie',
    radius: ['40%', '70%'],
    center: ['40%', '50%'],
    avoidLabelOverlap: true,
    itemStyle: {
      borderRadius: 6,
      borderColor: 'rgba(6, 30, 56, 0.8)',
      borderWidth: 2
    },
    label: {
      show: true,
      fontSize: 12,
      color: 'rgba(255, 255, 255, 0.8)',
      formatter: '{b}\n{c}台'
    },
    emphasis: {
      label: {
        show: true,
        fontSize: 14,
        fontWeight: 'bold',
        color: '#fff'
      }
    },
    labelLine: {
      show: true,
      length: 10,
      length2: 10
    },
    data: data.map((d, i) => ({
      name: d.name,
      value: d.value,
      itemStyle: { color: colors[i % colors.length] }
    }))
  }]
})

const centralPieOption = computed(() => createPieOption(
  orgTypeData.value.central,
  ['#f56c6c', '#e6a23c', '#00b4ff', '#67c23a', '#909399']
))

const localPieOption = computed(() => createPieOption(
  orgTypeData.value.local,
  ['#00b4ff', '#00ffcc', '#e6a23c', '#f56c6c', '#67c23a', '#909399', '#9b59b6', '#3498db', '#1abc9c', '#e74c3c']
))

const networkOption = computed(() => {
  const orgNames = networkByOrgData.value.data.map(d => d.org_name)
  const networks = networkByOrgData.value.networks
  
  const colors = ['#00b4ff', '#00ffcc', '#e6a23c', '#f56c6c', '#67c23a', '#9b59b6', '#3498db', '#1abc9c']
  
  const series = networks.map((network, index) => ({
    name: network,
    type: 'bar',
    stack: 'total',
    barWidth: '60%',
    emphasis: {
      focus: 'series'
    },
    itemStyle: {
      color: colors[index % colors.length]
    },
    data: networkByOrgData.value.data.map(org => org.networks[network] || 0)
  }))
  
  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: 'rgba(6, 30, 56, 0.9)',
      borderColor: 'rgba(0, 180, 255, 0.3)',
      textStyle: { color: '#fff' }
    },
    legend: {
      data: networks,
      textStyle: { color: 'rgba(255, 255, 255, 0.7)' },
      top: 10,
      type: 'scroll',
      pageTextStyle: { color: 'rgba(255, 255, 255, 0.7)' }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      top: '20%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: orgNames.map(name => name.length > 8 ? name.substring(0, 8) + '...' : name),
      axisLine: { lineStyle: { color: 'rgba(0, 180, 255, 0.3)' } },
      axisLabel: { color: 'rgba(255, 255, 255, 0.7)', fontSize: 10, rotate: 30 },
      triggerEvent: true
    },
    yAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: 'rgba(0, 180, 255, 0.3)' } },
      axisLabel: { color: 'rgba(255, 255, 255, 0.7)', fontSize: 11 },
      splitLine: { lineStyle: { color: 'rgba(0, 180, 255, 0.1)' } }
    },
    series: series
  }
})

const gpuTierOption = computed(() => {
  const orgNames = gpuTierByOrgData.value.map(d => d.org_name)
  
  const colors = ['#f56c6c', '#e6a23c', '#67c23a', '#909399']
  const tierNames = ['高端卡', '中端卡', '低端卡', '未知']
  const tierKeys = ['high', 'medium', 'low', 'unknown']
  
  const series = tierNames.map((name, index) => ({
    name: name,
    type: 'line',
    stack: 'Total',
    smooth: true,
    areaStyle: {
      opacity: 0.6
    },
    emphasis: {
      focus: 'series'
    },
    lineStyle: {
      width: 2
    },
    itemStyle: {
      color: colors[index]
    },
    data: gpuTierByOrgData.value.map(d => d[tierKeys[index]])
  }))
  
  return {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(6, 30, 56, 0.9)',
      borderColor: 'rgba(0, 180, 255, 0.3)',
      textStyle: { color: '#fff' },
      axisPointer: {
        type: 'cross',
        label: {
          backgroundColor: 'rgba(6, 30, 56, 0.9)'
        }
      }
    },
    legend: {
      data: tierNames,
      textStyle: { color: 'rgba(255, 255, 255, 0.7)' },
      top: 10
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      top: '20%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: orgNames.map(name => name.length > 8 ? name.substring(0, 8) + '...' : name),
      axisLine: { lineStyle: { color: 'rgba(0, 180, 255, 0.3)' } },
      axisLabel: { 
        color: 'rgba(255, 255, 255, 0.7)', 
        fontSize: 10,
        rotate: 30
      }
    },
    yAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: 'rgba(0, 180, 255, 0.3)' } },
      axisLabel: { color: 'rgba(255, 255, 255, 0.7)' },
      splitLine: { lineStyle: { color: 'rgba(0, 180, 255, 0.1)' } }
    },
    series: series
  }
})

const purposeOption = computed(() => {
  const orgNames = purposeByOrgData.value.data.map(d => d.org_name)
  const purposes = purposeByOrgData.value.purposes
  
  const colors = ['#00b4ff', '#00ffcc', '#e6a23c']
  
  const series = purposes.map((purpose, index) => ({
    name: purpose,
    type: 'bar',
    stack: 'total',
    barWidth: '60%',
    emphasis: {
      focus: 'series'
    },
    itemStyle: {
      color: colors[index % colors.length]
    },
    data: purposeByOrgData.value.data.map(org => org.purposes[purpose] || 0)
  }))
  
  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: 'rgba(6, 30, 56, 0.9)',
      borderColor: 'rgba(0, 180, 255, 0.3)',
      textStyle: { color: '#fff' }
    },
    legend: {
      data: purposes,
      textStyle: { color: 'rgba(255, 255, 255, 0.7)' },
      top: 10
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      top: '18%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: orgNames.map(name => name.length > 8 ? name.substring(0, 8) + '...' : name),
      axisLine: { lineStyle: { color: 'rgba(0, 180, 255, 0.3)' } },
      axisLabel: { color: 'rgba(255, 255, 255, 0.7)', fontSize: 10, rotate: 30 },
      triggerEvent: true
    },
    yAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: 'rgba(0, 180, 255, 0.3)' } },
      axisLabel: { color: 'rgba(255, 255, 255, 0.7)', fontSize: 11 },
      splitLine: { lineStyle: { color: 'rgba(0, 180, 255, 0.1)' } }
    },
    series: series
  }
})

const getCarouselOption = (trend) => {
  const colors = getAllColors()
  const primaryColor = colors.primary
  const borderColor = colors.border
  const textSecondary = colors.textSecondary
  
  const hexToRgba = (hex, alpha) => {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex)
    if (result) {
      return `rgba(${parseInt(result[1], 16)}, ${parseInt(result[2], 16)}, ${parseInt(result[3], 16)}, ${alpha})`
    }
    return hex
  }
  
  const areaColorStart = hexToRgba(primaryColor, 0.3)
  const areaColorEnd = hexToRgba(primaryColor, 0.05)
  const splitLineColor = borderColor.includes('rgba') 
    ? borderColor.replace(/[\d.]+\)$/, '0.1)') 
    : hexToRgba(primaryColor, 0.1)
  
  return {
    tooltip: {
      trigger: 'axis',
      backgroundColor: colors.panelBgStart,
      borderColor: borderColor,
      textStyle: { color: colors.text },
      formatter: (params) => {
        const data = params[0]
        const dateStr = data.axisValue
        const usageColor = getUsageColor(data.value)
        if (/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) {
          return `${dateStr}<br/>使用率: <span style="color: ${usageColor}; font-weight: bold;">${data.value}%</span><br/><span style="color: ${colors.info}; font-size: 12px;">点击查看24小时详情</span>`
        }
        return `${dateStr}<br/>使用率: <span style="color: ${usageColor}; font-weight: bold;">${data.value}%</span>`
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
      left: '5%',
      right: '5%',
      bottom: '15%',
      top: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: trend.map(d => d.date),
      axisLine: { lineStyle: { color: borderColor } },
      axisLabel: { 
        color: textSecondary, 
        fontSize: 10
      },
      triggerEvent: true
    },
    yAxis: {
      type: 'value',
      name: '使用率(%)',
      nameTextStyle: { color: textSecondary },
      axisLine: { lineStyle: { color: borderColor } },
      axisLabel: { color: textSecondary },
      splitLine: { lineStyle: { color: splitLineColor } },
      min: 0,
      max: 100
    },
    series: [{
      type: 'line',
      smooth: true,
      data: trend.map(d => d.value),
      lineStyle: { color: primaryColor, width: 2 },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: areaColorStart },
            { offset: 1, color: areaColorEnd }
          ]
        }
      },
      itemStyle: { color: primaryColor },
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowColor: primaryColor
        }
      }
    }]
  }
}

const drillChartOption = computed(() => {
  const colors = getAllColors()
  const primaryColor = colors.primary
  const borderColor = colors.border
  const textSecondary = colors.textSecondary
  
  const hexToRgba = (hex, alpha) => {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex)
    if (result) {
      return `rgba(${parseInt(result[1], 16)}, ${parseInt(result[2], 16)}, ${parseInt(result[3], 16)}, ${alpha})`
    }
    return hex
  }
  
  const areaColorStart = hexToRgba(primaryColor, 0.3)
  const areaColorEnd = hexToRgba(primaryColor, 0.05)
  const splitLineColor = borderColor.includes('rgba') 
    ? borderColor.replace(/[\d.]+\)$/, '0.1)') 
    : hexToRgba(primaryColor, 0.1)
  
  return {
    tooltip: {
      trigger: 'axis',
      backgroundColor: colors.panelBgStart,
      borderColor: borderColor,
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
      left: '10%',
      right: '5%',
      bottom: '18%',
      top: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: drillTrendData.value.map(d => d.date),
      axisLine: { lineStyle: { color: borderColor } },
      axisLabel: { 
        color: textSecondary, 
        fontSize: 11,
        interval: 1
      }
    },
    yAxis: {
      type: 'value',
      name: '使用率(%)',
      nameTextStyle: { color: textSecondary, fontSize: 12 },
      axisLine: { lineStyle: { color: borderColor } },
      axisLabel: { color: textSecondary },
      splitLine: { lineStyle: { color: splitLineColor } },
      min: 0,
      max: 100
    },
    series: [{
      type: 'line',
      smooth: true,
      data: drillTrendData.value.map(d => d.value),
      lineStyle: { color: primaryColor, width: 3 },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: areaColorStart },
            { offset: 1, color: areaColorEnd }
          ]
        }
      },
      itemStyle: { color: primaryColor },
      emphasis: {
        itemStyle: {
          shadowBlur: 15,
          shadowColor: primaryColor
        }
      },
      symbol: 'circle',
      symbolSize: 6
    }]
  }
})

const fetchLeftPanelData = async () => {
  try {
    const [deviceCount, memoryTotal, computeTotal, gpuUsage, warning] = await Promise.all([
      dashboardApi.getDeviceCountTrend(props.timeRange),
      dashboardApi.getMemoryTotalTrend(props.timeRange),
      dashboardApi.getComputeTotalTrend(props.timeRange),
      dashboardApi.getGpuUsageTrend(props.timeRange),
      dashboardApi.getUsageWarningBar(props.timeRange)
    ])

    deviceCountData.value = deviceCount || []
    memoryTotalData.value = memoryTotal || []
    computeTotalData.value = computeTotal || []
    gpuUsageData.value = gpuUsage || []
    warningData.value = warning || []
  } catch (error) {
    console.error('Failed to fetch left panel data:', error)
    deviceCountData.value = []
    memoryTotalData.value = []
    computeTotalData.value = []
    gpuUsageData.value = []
    warningData.value = []
  }
}

const fetchCenterPanelData = async () => {
  try {
    const startDate = carouselDateRange.value ? carouselDateRange.value[0] : null
    const endDate = carouselDateRange.value ? carouselDateRange.value[1] : null
    const [orgType, networkByOrg, gpuTierByOrg, purposeByOrg, carousel] = await Promise.all([
      dashboardApi.getOrgTypeDistribution(),
      dashboardApi.getNetworkDistributionByOrg(),
      dashboardApi.getGpuTierByOrgDistribution(),
      dashboardApi.getPurposeDistributionByOrg(),
      dashboardApi.getCarouselUsageTrend('work', carouselOrgType.value || null, carouselOrgName.value || null, carouselTimeGrain.value, startDate, endDate)
    ])
    
    orgTypeData.value = orgType
    networkByOrgData.value = networkByOrg
    gpuTierByOrgData.value = gpuTierByOrg
    purposeByOrgData.value = purposeByOrg
    carouselData.value = carousel
  } catch (error) {
    console.error('Failed to fetch center panel data:', error)
  }
}

const handleCarouselFilter = async () => {
  loading.value = true
  try {
    const startDate = carouselDateRange.value ? carouselDateRange.value[0] : null
    const endDate = carouselDateRange.value ? carouselDateRange.value[1] : null
    const carousel = await dashboardApi.getCarouselUsageTrend('work', carouselOrgType.value || null, carouselOrgName.value || null, carouselTimeGrain.value, startDate, endDate)
    carouselData.value = carousel
  } catch (error) {
    console.error('Failed to filter carousel data:', error)
  } finally {
    loading.value = false
  }
}

const handleTimeGrainChange = async () => {
  loading.value = true
  try {
    const startDate = carouselDateRange.value ? carouselDateRange.value[0] : null
    const endDate = carouselDateRange.value ? carouselDateRange.value[1] : null
    const carousel = await dashboardApi.getCarouselUsageTrend('work', carouselOrgType.value || null, carouselOrgName.value || null, carouselTimeGrain.value, startDate, endDate)
    carouselData.value = carousel
  } catch (error) {
    console.error('Failed to change time grain:', error)
  } finally {
    loading.value = false
  }
}

const handleDateRangeChange = async () => {
  loading.value = true
  try {
    const startDate = carouselDateRange.value ? carouselDateRange.value[0] : null
    const endDate = carouselDateRange.value ? carouselDateRange.value[1] : null
    const carousel = await dashboardApi.getCarouselUsageTrend('work', carouselOrgType.value || null, carouselOrgName.value || null, carouselTimeGrain.value, startDate, endDate)
    carouselData.value = carousel
  } catch (error) {
    console.error('Failed to change date range:', error)
  } finally {
    loading.value = false
  }
}

const handleChartClick = async (params, orgName, orgId) => {
  if (params.componentType === 'series' || params.componentType === 'xAxis') {
    const clickedDate = params.name || params.value
    if (clickedDate && /^\d{4}-\d{2}-\d{2}$/.test(clickedDate)) {
      drillDate.value = clickedDate
      drillOrgName.value = orgName
      drillOrgId.value = orgId
      drillTrendData.value = []
      drillLoading.value = true
      drillDialogVisible.value = true
      
      try {
        const result = await dashboardApi.getCarouselUsageTrend('work', null, null, 'day', null, null, clickedDate, orgId)
        console.log('Drill result:', result)
        drillTrendData.value = result.trend || []
      } catch (error) {
        console.error('Failed to drill down:', error)
      } finally {
        drillLoading.value = false
      }
    }
  }
}

const fetchRightPanelData = async () => {
  try {
    if (props.provinceName) {
      console.log('Fetching province ranking for:', props.provinceName)
      const ranking = await dashboardApi.getProvinceRanking(props.provinceName, props.timeRange)
      console.log('Province ranking data:', ranking)
      provinceRanking.value = ranking
      provinceName.value = props.provinceName
    } else if (props.groupName) {
      console.log('Fetching group ranking for:', props.groupName)
      const groups = await dashboardApi.getOrgGroups()
      console.log('Groups:', groups)
      const targetGroup = groups.find(g => g.name === props.groupName)
      console.log('Target group:', targetGroup)
      if (targetGroup) {
        const ranking = await dashboardApi.getGroupRanking(targetGroup.id, props.timeRange)
        console.log('Group ranking data:', ranking)
        groupRanking.value = ranking
        groupName.value = props.groupName
      }
    } else {
      console.log('Fetching all ranking')
      const all = await dashboardApi.getAllRanking(props.timeRange)
      console.log('All ranking data:', all)
      allRanking.value = all
    }
  } catch (error) {
    console.error('Failed to fetch right panel data:', error)
  }
}

const loadData = async () => {
  loading.value = true
  
  console.log('PanelExpandContent loadData:', props.panelType, props.subType, props.timeRange)
  
  try {
    if (props.panelType === 'left') {
      await fetchLeftPanelData()
      console.log('Left panel data loaded:', deviceCountData.value.length, memoryTotalData.value.length)
    } else if (props.panelType === 'center') {
      await fetchCenterPanelData()
      console.log('Center panel data loaded:', orgTypeData.value, networkByOrgData.value)
    } else if (props.panelType === 'right') {
      await fetchRightPanelData()
      console.log('Right panel data loaded:', allRanking.value.length, groupRanking.value.length)
    }
  } catch (error) {
    console.error('Failed to load panel data:', error)
  } finally {
    loading.value = false
  }
}

const handleExpandCarouselTitleClick = (item) => {
  if (showOrgDetail && item.org_id) {
    showOrgDetail(item.org_id, 'usage')
  }
}

const handleExpandRankingRowClick = (row) => {
  if (showOrgDetail && row.org_id) {
    showOrgDetail(row.org_id, 'devices')
  }
}

const handleExpandWarningBarClick = (params) => {
  if (showOrgDetail && warningData.value[params.dataIndex]) {
    const item = warningData.value[params.dataIndex]
    if (item.org_id) {
      showOrgDetail(item.org_id, 'usage')
    }
  }
}

const handleExpandNetworkChartClick = (params) => {
  if (showOrgDetail && networkByOrgData.value.data[params.dataIndex]) {
    const item = networkByOrgData.value.data[params.dataIndex]
    if (item.org_id) {
      showOrgDetail(item.org_id, 'devices')
    }
  }
}

const handleExpandGpuTierChartClick = (params) => {
  if (showOrgDetail && gpuTierByOrgData.value[params.dataIndex]) {
    const item = gpuTierByOrgData.value[params.dataIndex]
    if (item.org_id) {
      showOrgDetail(item.org_id, 'devices')
    }
  }
}

const handleExpandPurposeChartClick = (params) => {
  if (showOrgDetail && purposeByOrgData.value.data[params.dataIndex]) {
    const item = purposeByOrgData.value.data[params.dataIndex]
    if (item.org_id) {
      showOrgDetail(item.org_id, 'devices')
    }
  }
}

watch(
  () => [props.panelType, props.subType, props.timeRange, props.groupName, props.provinceName],
  ([newPanelType, newSubType, newTimeRange, newGroupName, newProvinceName]) => {
    console.log('watch triggered:', newPanelType, newSubType, newTimeRange, newGroupName, newProvinceName)
    if (newPanelType && newSubType) {
      loadData()
    }
  },
  { immediate: true }
)

onMounted(() => {
  console.log('PanelExpandContent mounted, props:', props.panelType, props.subType, props.timeRange)
})
</script>

<style lang="scss" scoped>
.panel-expand-content {
  height: 100%;
  padding: 20px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  
  .loading-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    flex: 1;
    min-height: 300px;
    color: var(--theme-text-secondary);
    
    .loading-spinner {
      width: 40px;
      height: 40px;
      border: 3px solid var(--theme-border);
      border-top-color: var(--theme-primary);
      border-radius: 50%;
      animation: spin 1s linear infinite;
      margin-bottom: 15px;
    }
  }
  
  .expand-panel {
    flex: 1;
    min-height: 0;
    display: flex;
    flex-direction: column;
  }
  
  .chart-section {
    flex: 1;
    min-height: 500px;
    display: flex;
    flex-direction: column;
    
    :deep(.echarts) {
      width: 100%;
      height: 100%;
      min-height: 400px;
    }
  }
  
  .dual-pie-section {
    flex: 1;
    min-height: 500px;
    display: flex;
    flex-direction: column;
    
    .pie-container {
      display: flex;
      flex: 1;
      gap: 20px;
      
      .pie-wrapper {
        flex: 1;
        display: flex;
        flex-direction: column;
        min-height: 400px;
        
        .pie-label {
          font-size: 14px;
          color: var(--theme-primary);
          text-align: center;
          padding: 10px 0;
          flex-shrink: 0;
        }
        
        :deep(.echarts) {
          flex: 1;
          min-height: 350px;
        }
      }
    }
  }
  
  .carousel-section {
    flex: 1;
    min-height: 500px;
    display: flex;
    flex-direction: column;
    
    .filter-bar {
      display: flex;
      gap: 20px;
      padding: 15px 0;
      border-bottom: 1px solid var(--theme-border);
      margin-bottom: 15px;
      flex-shrink: 0;
      flex-wrap: wrap;
      
      .filter-item {
        display: flex;
        align-items: center;
        gap: 10px;
        
        label {
          color: var(--theme-text-secondary);
          font-size: 14px;
          white-space: nowrap;
        }
        
        :deep(.el-select) {
          width: 150px;
          
          .el-input__wrapper {
            background: var(--theme-input-bg);
            border: 1px solid var(--theme-border);
            box-shadow: none;
            
            .el-input__inner {
              color: var(--theme-text);
            }
          }
        }
        
        :deep(.el-input) {
          width: 250px;
          
          .el-input__wrapper {
            background: var(--theme-input-bg);
            border: 1px solid var(--theme-border);
            box-shadow: none;
            
            .el-input__inner {
              color: var(--theme-text);
              
              &::placeholder {
                color: var(--theme-text-muted);
              }
            }
          }
          
          .el-input-group__append {
            background: var(--theme-hover-bg);
            border: 1px solid var(--theme-border);
            border-left: none;
            
            .el-button {
              color: var(--theme-primary);
              
              &:hover {
                color: var(--theme-glow);
              }
            }
          }
        }
        
        :deep(.el-radio-group) {
          .el-radio-button {
            .el-radio-button__inner {
              background: var(--theme-input-bg);
              border: 1px solid var(--theme-border);
              color: var(--theme-text-secondary);
              padding: 8px 15px;
              
              &:hover {
                color: var(--theme-primary);
              }
            }
            
            &.is-active .el-radio-button__inner {
              background: var(--theme-primary);
              border-color: var(--theme-primary);
              color: var(--theme-text);
              box-shadow: none;
            }
          }
        }
        
        :deep(.el-date-editor) {
          --el-date-editor-width: 240px;
          
          .el-range-input {
            background: transparent;
            color: var(--theme-text);
          }
          
          .el-range-separator {
            color: var(--theme-text-secondary);
          }
          
          .el-range__icon {
            color: var(--theme-primary);
          }
          
          .el-range-input::placeholder {
            color: var(--theme-text-muted);
          }
        }
      }
    }
    
    .carousel-grid-wrapper {
      flex: 1;
      min-height: 0;
      overflow-y: auto;
      overflow-x: hidden;
      
      &::-webkit-scrollbar {
        width: 8px;
      }
      
      &::-webkit-scrollbar-track {
        background: var(--theme-shadow);
        border-radius: 4px;
      }
      
      &::-webkit-scrollbar-thumb {
        background: var(--theme-border);
        border-radius: 4px;
        
        &:hover {
          background: var(--theme-primary);
        }
      }
    }
    
    .carousel-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: 15px;
      padding-bottom: 10px;
      
      .carousel-item {
        background: var(--theme-hover-bg);
        border: 1px solid var(--theme-border);
        border-radius: 8px;
        padding: 10px;
        display: flex;
        flex-direction: column;
        min-height: 200px;
        
        .carousel-title {
          font-size: 13px;
          color: var(--theme-primary);
          text-align: center;
          padding: 5px 0;
          flex-shrink: 0;
        }
        
        :deep(.echarts) {
          flex: 1;
          min-height: 150px;
        }
      }
    }
    
    .drill-loading {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      height: 100%;
      color: var(--theme-text-secondary);
      
      .loading-spinner {
        width: 32px;
        height: 32px;
        border: 3px solid var(--theme-border);
        border-top-color: var(--theme-primary);
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin-bottom: 10px;
      }
    }
    
    .drill-chart-container {
      height: 100%;
      width: 100%;
      
      .no-data {
        display: flex;
        align-items: center;
        justify-content: center;
        height: 100%;
        color: var(--theme-text-muted);
        font-size: 14px;
      }
    }
    
    .drill-dialog-header {
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 20px 70px 20px 20px;
      min-height: 60px;
      position: relative;
      background: linear-gradient(135deg, var(--theme-hover-bg) 0%, var(--theme-shadow) 100%);
      border-bottom: 1px solid var(--theme-border);
      margin: -20px -20px 0 -20px;
      
      .drill-title {
        font-size: 18px;
        font-weight: 600;
        color: var(--theme-primary);
        letter-spacing: 2px;
        text-align: center;
        line-height: 1.5;
      }
      
      .drill-close-btn {
        position: absolute;
        right: 15px;
        top: 50%;
        transform: translateY(-50%);
        width: 32px;
        height: 32px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: rgba(0, 180, 255, 0.15);
        border: 1px solid rgba(0, 180, 255, 0.4);
        border-radius: 6px;
        cursor: pointer;
        transition: all 0.3s ease;
        z-index: 10;
        
        svg {
          width: 16px;
          height: 16px;
          color: #00b4ff;
        }
        
        &:hover {
          background: rgba(0, 180, 255, 0.3);
          border-color: #00b4ff;
          box-shadow: 0 0 10px rgba(0, 180, 255, 0.5);
          
          svg {
            color: #fff;
          }
        }
      }
    }
  }
  
  .ranking-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 20px;
    flex: 1;
    
    .ranking-column {
      background: var(--theme-hover-bg);
      border: 1px solid var(--theme-border);
      border-radius: 8px;
      padding: 15px;
      display: flex;
      flex-direction: column;
      
      &.single {
        max-width: 500px;
        margin: 0 auto;
        width: 100%;
      }
      
      .ranking-header {
        font-size: 16px;
        color: var(--theme-primary);
        font-weight: bold;
        text-align: center;
        padding-bottom: 15px;
        border-bottom: 1px solid var(--theme-border);
        margin-bottom: 15px;
        flex-shrink: 0;
      }
      
      .ranking-list {
        flex: 1;
        display: flex;
        flex-direction: column;
        gap: 12px;
      }
      
      .ranking-item {
        display: flex;
        align-items: center;
        padding: 8px 10px;
        background: linear-gradient(90deg, var(--theme-shadow) 0%, transparent 100%);
        border-radius: 4px;
        cursor: pointer;
        transition: all 0.3s;
        
        &:hover {
          background: linear-gradient(90deg, var(--theme-border-light) 0%, transparent 100%);
          transform: translateX(5px);
        }
        
        .rank-badge {
          width: 22px;
          height: 22px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 4px;
          font-size: 11px;
          font-weight: bold;
          margin-right: 8px;
          
          &.rank-1 {
            background: linear-gradient(135deg, var(--theme-rank1) 0%, #ffaa00 100%);
            color: #1a1a1a;
          }
          
          &.rank-2 {
            background: linear-gradient(135deg, var(--theme-rank2) 0%, #a0a0a0 100%);
            color: #1a1a1a;
          }
          
          &.rank-3 {
            background: linear-gradient(135deg, var(--theme-rank3) 0%, #b87333 100%);
            color: #1a1a1a;
          }
          
          &:not(.rank-1):not(.rank-2):not(.rank-3) {
            background: var(--theme-border);
            color: var(--theme-text);
          }
        }
        
        .org-name {
          flex: 1;
          font-size: 12px;
          color: var(--theme-text);
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
        
        .device-count {
          font-size: 12px;
          color: var(--theme-primary);
          font-weight: bold;
        }
      }
    }
  }
  
  .ranking-single {
    flex: 1;
    display: flex;
    flex-direction: column;
  }
  
  .ranking-table-section {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-height: 0;
    
    .table-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 8px 12px;
      border-bottom: 1px solid var(--theme-border-light);
      background: linear-gradient(90deg, var(--theme-hover-bg) 0%, transparent 100%);
      margin-bottom: 12px;
      flex-shrink: 0;
      
      h3 {
        margin: 0;
        font-size: 14px;
        color: var(--theme-primary);
        font-weight: bold;
        display: flex;
        align-items: center;
        gap: 6px;
        
        &::before {
          content: '';
          display: inline-block;
          width: 3px;
          height: 14px;
          background: linear-gradient(180deg, var(--theme-primary) 0%, var(--theme-secondary) 100%);
          border-radius: 2px;
        }
      }
      
      .total-count {
        font-size: 12px;
        color: var(--theme-text-secondary);
      }
    }
    
    :deep(.el-table) {
      flex: 1;
      background: transparent;
      
      --el-table-bg-color: transparent;
      --el-table-tr-bg-color: transparent;
      --el-table-header-bg-color: var(--theme-hover-bg);
      --el-table-row-hover-bg-color: var(--theme-hover-bg);
      --el-table-border-color: var(--theme-border);
      
      .el-table__inner-wrapper::before {
        display: none;
      }
      
      th.el-table__cell {
        background: var(--theme-hover-bg) !important;
        color: var(--theme-primary) !important;
        font-weight: bold;
        border-bottom: 1px solid var(--theme-border-heavy) !important;
        white-space: nowrap !important;
        
        .cell {
          white-space: nowrap !important;
        }
        
        .caret-wrapper {
          .sort-caret {
            &.ascending {
              border-bottom-color: var(--theme-glow);
            }
            &.descending {
              border-top-color: var(--theme-glow);
            }
          }
        }
        
        &.is-sortable:hover {
          background: var(--theme-shadow-heavy) !important;
        }
      }
      
      td.el-table__cell {
        background: transparent !important;
        color: var(--theme-text);
        border-bottom: 1px solid var(--theme-border-light) !important;
        transition: all 0.3s ease;
      }
      
      tr {
        background: transparent !important;
        
        &:hover td.el-table__cell {
          background: var(--theme-hover-bg) !important;
        }
      }
      
      .el-table__empty-text {
        color: var(--theme-text-muted);
      }
      
      .org-name {
        font-size: 12px;
        color: var(--theme-text);
        font-weight: 500;
      }
      
      .value-cell {
        font-size: 12px;
        font-weight: bold;
        color: var(--theme-primary);
        
        &.memory {
          color: var(--theme-secondary);
        }
        
        &.compute {
          color: var(--theme-danger);
        }
        
        &.cpu {
          color: var(--theme-warning);
        }
        
        &.ram {
          color: var(--theme-success);
        }
        
        &.disk {
          color: var(--theme-info);
        }
        
        &.usage {
          font-weight: bold;
        }
      }
    }
    
    .rank-badge {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 22px;
      height: 22px;
      border-radius: 4px;
      font-size: 11px;
      font-weight: bold;
      
      &.rank-1 {
        background: linear-gradient(135deg, var(--theme-rank1) 0%, #ffaa00 100%);
        color: #1a1a1a;
      }
      
      &.rank-2 {
        background: linear-gradient(135deg, var(--theme-rank2) 0%, #a0a0a0 100%);
        color: #1a1a1a;
      }
      
      &.rank-3 {
        background: linear-gradient(135deg, var(--theme-rank3) 0%, #b87333 100%);
        color: #1a1a1a;
      }
      
      &:not(.rank-1):not(.rank-2):not(.rank-3) {
        background: var(--theme-border);
        color: var(--theme-text);
      }
    }
    
    .org-name-link {
      font-size: 12px;
      color: var(--theme-text);
      cursor: pointer;
      transition: all 0.3s ease;
      
      &:hover {
        color: var(--theme-primary);
      }
    }
  }
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
