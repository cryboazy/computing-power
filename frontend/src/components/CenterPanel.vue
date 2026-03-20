<template>
  <div class="center-panel-content">
    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-label">设备总数</div>
        <div class="stat-value">
          {{ overviewStats.total_devices }}
          <span class="stat-unit">台</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-label">显存总量</div>
        <div class="stat-value">
          {{ formatNumber(overviewStats.total_memory_gb) }}
          <span class="stat-unit">GB</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-label">总算力</div>
        <div class="stat-value">
          {{ formatNumber(overviewStats.total_compute_tflops / 1000, 2) }}
          <span class="stat-unit">PFLOPS</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-label">平均使用率</div>
        <div class="stat-value" :style="{ color: overviewUsageColor }">
          {{ overviewStats.avg_gpu_usage }}
          <span class="stat-unit">%</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-label">显存使用率</div>
        <div class="stat-value" :title="`显存已用量: ${formatNumber(overviewStats.memory_used_gb)} GB`">
          {{ overviewStats.memory_usage_rate }}
          <span class="stat-unit">%</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-label">显存利用率</div>
        <div class="stat-value">
          {{ overviewStats.avg_memory_utilization }}
          <span class="stat-unit">%</span>
        </div>
      </div>
    </div>
    
    <div class="panel charts-section">
      <div class="panel-header">
        <el-tabs v-model="activeTab" class="chart-tabs">
          <el-tab-pane label="全国" name="all"></el-tab-pane>
          <el-tab-pane label="地方厅局" name="local"></el-tab-pane>
          <el-tab-pane label="部机关" name="central"></el-tab-pane>
        </el-tabs>
        <div class="global-page-size">
          <span class="label">分组:</span>
          <div class="page-size-selector">
            <span 
              v-for="size in PAGE_SIZE_OPTIONS" 
              :key="size"
              :class="['size-btn', { active: globalPageSize === size }]"
              @click="setGlobalPageSize(size)"
            >{{ size === 'all' ? '全部' : size }}</span>
          </div>
        </div>
      </div>
      <div class="panel-content">
        <div v-show="activeTab === 'all'" class="charts-grid">
          <div class="chart-item org-type-panel">
            <div class="chart-title">
              <span>机构类型分布</span>
              <div class="title-right">
                <div class="chart-type-switch">
                  <span 
                    :class="['type-btn', { active: orgTypeChartType === 'bar' }]"
                    @click="orgTypeChartType = 'bar'"
                  >柱形图</span>
                  <span 
                    :class="['type-btn', { active: orgTypeChartType === 'pie' }]"
                    @click="orgTypeChartType = 'pie'"
                  >饼图</span>
                </div>
                <div v-show="orgTypeChartType === 'bar'" class="carousel-indicator">
                  <span 
                    v-for="i in orgTypePageCount" 
                    :key="i" 
                    :class="['indicator-dot', { active: orgTypePageIndex === i - 1 }]"
                    @click="orgTypePageIndex = i - 1"
                  ></span>
                </div>
              </div>
            </div>
            <div v-show="orgTypeChartType === 'pie'" class="dual-pie-container">
              <div v-for="(data, groupName) in orgTypeData" :key="groupName" class="pie-wrapper">
                <div class="pie-label">{{ groupName }}</div>
                <v-chart :option="getPieOption(data, groupName)" autoresize />
              </div>
            </div>
            <div v-show="orgTypeChartType === 'bar'" class="org-type-bar-container">
              <v-chart :option="orgTypeBarOption" autoresize />
            </div>
          </div>
          <div class="chart-item carousel-chart">
            <div class="chart-title">
              <span>运行网络分布</span>
              <div class="title-right">
                <div class="chart-type-switch">
                  <span 
                    :class="['type-btn', { active: networkChartType === 'bar' }]"
                    @click="networkChartType = 'bar'"
                  >柱形图</span>
                  <span 
                    :class="['type-btn', { active: networkChartType === 'pie' }]"
                    @click="networkChartType = 'pie'"
                  >饼图</span>
                </div>
                <div v-show="networkChartType === 'bar'" class="carousel-indicator">
                  <span 
                    v-for="i in networkPageCount" 
                    :key="i" 
                    :class="['indicator-dot', { active: networkPageIndex === i - 1 }]"
                    @click="networkPageIndex = i - 1"
                  ></span>
                </div>
              </div>
            </div>
            <v-chart v-show="networkChartType === 'bar'" :option="networkOption" autoresize />
            <v-chart v-show="networkChartType === 'pie'" :option="networkPieOption" autoresize />
          </div>
          <div class="chart-item carousel-chart">
            <div class="chart-title">
              <span>GPU档次分布</span>
              <div class="title-right">
                <div class="chart-type-switch">
                  <span 
                    :class="['type-btn', { active: gpuTierChartType === 'area' }]"
                    @click="gpuTierChartType = 'area'"
                  >面积图</span>
                  <span 
                    :class="['type-btn', { active: gpuTierChartType === 'pie' }]"
                    @click="gpuTierChartType = 'pie'"
                  >饼图</span>
                </div>
                <div v-show="gpuTierChartType === 'area'" class="carousel-indicator">
                  <span 
                    v-for="i in gpuTierPageCount" 
                    :key="i" 
                    :class="['indicator-dot', { active: gpuTierPageIndex === i - 1 }]"
                    @click="gpuTierPageIndex = i - 1"
                  ></span>
                </div>
              </div>
            </div>
            <v-chart :option="gpuTierOption" autoresize />
          </div>
          <div class="chart-item carousel-chart">
            <div class="chart-title">
              <span>用途分布</span>
              <div class="title-right">
                <div class="chart-type-switch">
                  <span 
                    :class="['type-btn', { active: purposeChartType === 'bar' }]"
                    @click="purposeChartType = 'bar'"
                  >柱形图</span>
                  <span 
                    :class="['type-btn', { active: purposeChartType === 'pie' }]"
                    @click="purposeChartType = 'pie'"
                  >饼图</span>
                </div>
                <div v-show="purposeChartType === 'bar'" class="carousel-indicator">
                  <span 
                    v-for="i in purposePageCount" 
                    :key="i" 
                    :class="['indicator-dot', { active: purposePageIndex === i - 1 }]"
                    @click="purposePageIndex = i - 1"
                  ></span>
                </div>
              </div>
            </div>
            <v-chart v-show="purposeChartType === 'bar'" :option="purposeOption" autoresize />
            <v-chart v-show="purposeChartType === 'pie'" :option="purposePieOption" autoresize />
          </div>
        </div>
        
        <div v-show="activeTab === 'local'" class="local-container">
          <div class="local-stats-row">
            <div class="local-stat-card">
              <div class="stat-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="2" y="3" width="20" height="14" rx="2" ry="2"/>
                  <line x1="8" y1="21" x2="16" y2="21"/>
                  <line x1="12" y1="17" x2="12" y2="21"/>
                </svg>
              </div>
              <div class="stat-info">
                <div class="stat-label">设备总数</div>
                <div class="stat-value">{{ localStats.total_devices }}<span class="stat-unit">台</span></div>
              </div>
            </div>
            <div class="local-stat-card">
              <div class="stat-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                  <path d="M2 17l10 5 10-5"/>
                  <path d="M2 12l10 5 10-5"/>
                </svg>
              </div>
              <div class="stat-info">
                <div class="stat-label">显存总量</div>
                <div class="stat-value">{{ formatNumber(localStats.total_memory_gb) }}<span class="stat-unit">GB</span></div>
              </div>
            </div>
            <div class="local-stat-card">
              <div class="stat-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
                </svg>
              </div>
              <div class="stat-info">
                <div class="stat-label">总算力</div>
                <div class="stat-value">{{ formatNumber(localStats.total_compute_tflops / 1000, 2) }}<span class="stat-unit">PFLOPS</span></div>
              </div>
            </div>
            <div class="local-stat-card">
              <div class="stat-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
                </svg>
              </div>
              <div class="stat-info">
                <div class="stat-label">平均使用率</div>
                <div class="stat-value" :style="{ color: localUsageColor }">{{ localStats.avg_gpu_usage }}<span class="stat-unit">%</span></div>
              </div>
            </div>
            <div class="local-stat-card">
              <div class="stat-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="10"/>
                  <polyline points="12 6 12 12 16 14"/>
                </svg>
              </div>
              <div class="stat-info">
                <div class="stat-label">显存使用率</div>
                <div class="stat-value" :title="`显存已用量: ${formatNumber(localStats.memory_used_gb)} GB`">{{ localStats.memory_usage_rate }}<span class="stat-unit">%</span></div>
              </div>
            </div>
            <div class="local-stat-card">
              <div class="stat-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M18 20V10"/>
                  <path d="M12 20V4"/>
                  <path d="M6 20v-6"/>
                </svg>
              </div>
              <div class="stat-info">
                <div class="stat-label">显存利用率</div>
                <div class="stat-value">{{ localStats.avg_memory_utilization }}<span class="stat-unit">%</span></div>
              </div>
            </div>
          </div>
          
          <div class="local-charts-grid">
            <div class="local-chart-item map-chart">
              <div class="chart-title">
                省份分布
              </div>
              <v-chart :option="mapOption" autoresize @click="handleMapClick" />
            </div>
            <div class="local-chart-item">
              <div class="chart-title">
                运行网络分布
              </div>
              <v-chart :option="localGpuTierOption" autoresize />
            </div>
            <div class="local-chart-item">
              <div class="chart-title">
                用途分布
              </div>
              <v-chart :option="localPurposeOption" autoresize />
            </div>
          </div>
        </div>
        
        <div v-show="activeTab === 'central'" class="central-container">
          <div class="central-stats-row">
            <div class="central-stat-card">
              <div class="stat-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="2" y="3" width="20" height="14" rx="2" ry="2"/>
                  <line x1="8" y1="21" x2="16" y2="21"/>
                  <line x1="12" y1="17" x2="12" y2="21"/>
                </svg>
              </div>
              <div class="stat-info">
                <div class="stat-label">设备总数</div>
                <div class="stat-value">{{ centralStats.total_devices }}<span class="stat-unit">台</span></div>
              </div>
            </div>
            <div class="central-stat-card">
              <div class="stat-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                  <path d="M2 17l10 5 10-5"/>
                  <path d="M2 12l10 5 10-5"/>
                </svg>
              </div>
              <div class="stat-info">
                <div class="stat-label">显存总量</div>
                <div class="stat-value">{{ formatNumber(centralStats.total_memory_gb) }}<span class="stat-unit">GB</span></div>
              </div>
            </div>
            <div class="central-stat-card">
              <div class="stat-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
                </svg>
              </div>
              <div class="stat-info">
                <div class="stat-label">总算力</div>
                <div class="stat-value">{{ formatNumber(centralStats.total_compute_tflops / 1000, 2) }}<span class="stat-unit">PFLOPS</span></div>
              </div>
            </div>
            <div class="central-stat-card">
              <div class="stat-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
                </svg>
              </div>
              <div class="stat-info">
                <div class="stat-label">平均使用率</div>
                <div class="stat-value" :style="{ color: centralUsageColor }">{{ centralStats.avg_gpu_usage }}<span class="stat-unit">%</span></div>
              </div>
            </div>
            <div class="central-stat-card">
              <div class="stat-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="10"/>
                  <polyline points="12 6 12 12 16 14"/>
                </svg>
              </div>
              <div class="stat-info">
                <div class="stat-label">显存使用率</div>
                <div class="stat-value" :title="`显存已用量: ${formatNumber(centralStats.memory_used_gb)} GB`">{{ centralStats.memory_usage_rate }}<span class="stat-unit">%</span></div>
              </div>
            </div>
            <div class="central-stat-card">
              <div class="stat-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M18 20V10"/>
                  <path d="M12 20V4"/>
                  <path d="M6 20v-6"/>
                </svg>
              </div>
              <div class="stat-info">
                <div class="stat-label">显存利用率</div>
                <div class="stat-value">{{ centralStats.avg_memory_utilization }}<span class="stat-unit">%</span></div>
              </div>
            </div>
          </div>
          
          <div class="central-charts-grid">
            <div class="central-chart-item">
              <div class="chart-title">
                <span>设备分布</span>
                <div class="title-right">
                  <div class="chart-type-switch">
                    <span 
                      :class="['type-btn', { active: centralDeviceViewType === 'chart' }]"
                      @click="centralDeviceViewType = 'chart'"
                    >图表</span>
                    <span 
                      :class="['type-btn', { active: centralDeviceViewType === 'list' }]"
                      @click="centralDeviceViewType = 'list'"
                    >列表</span>
                  </div>
                </div>
              </div>
              <v-chart v-show="centralDeviceViewType === 'chart'" :option="centralBarOption" autoresize />
              <div v-show="centralDeviceViewType === 'list'" class="central-device-list">
                <div 
                  v-for="item in centralData" 
                  :key="item.org_id" 
                  class="list-item"
                  @click="handleCentralOrgClick(item)"
                >
                  <span class="org-name">{{ item.name }}</span>
                  <span class="org-value">{{ item.value }}台</span>
                  <span class="org-value">{{ item.gpu_count }}张</span>
                  <span class="org-value">{{ formatNumber(item.memory_gb) }}GB</span>
                  <span class="org-value">{{ formatNumber(item.compute_tflops) }}TF</span>
                </div>
              </div>
            </div>
            <div class="central-chart-item">
              <div class="chart-title">
                运行网络分布
              </div>
              <v-chart :option="centralNetworkOption" autoresize />
            </div>
            <div class="central-chart-item">
              <div class="chart-title">
                GPU档次分布
              </div>
              <v-chart :option="centralTrendOption" autoresize />
            </div>
            <div class="central-chart-item">
              <div class="chart-title">
                用途分布
              </div>
              <v-chart :option="centralPurposeOption" autoresize />
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div class="panel carousel-section">
      <div class="panel-header clickable" @click="handleTitleClick('carousel', '单位使用率趋势')">
        <span class="panel-title">单位使用率趋势</span>
      </div>
      <div class="panel-content">
        <el-carousel 
          :interval="5000" 
          indicator-position="outside"
          height="100%"
          @change="handleCarouselChange"
        >
          <el-carousel-item v-for="(item, index) in carouselData" :key="index">
            <div class="carousel-item">
              <div class="carousel-title clickable" @click="handleOrgNameClick(item)">{{ item.org_name }}</div>
              <v-chart :option="getCarouselOption(item.trend)" autoresize @click="(params) => handleCarouselChartClick(params, item)" />
            </div>
          </el-carousel-item>
        </el-carousel>
      </div>
    </div>
  </div>
  
  <el-dialog
    v-model="drillDialogVisible"
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
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, inject, watch } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { 
  PieChart, 
  BarChart, 
  LineChart, 
  ScatterChart,
  MapChart 
} from 'echarts/charts'
import { 
  GridComponent, 
  TooltipComponent, 
  LegendComponent,
  VisualMapComponent,
  TitleComponent,
  GeoComponent
} from 'echarts/components'
import { dashboardApi } from '../api'
import chinaMapData from '../assets/china.json'
import * as echarts from 'echarts'
import { useTheme, watchThemeChange } from '../composables/useTheme'

const usageThresholds = inject('usageThresholds', ref({ high: 60.0, low: 30.0 }))

use([
  CanvasRenderer,
  PieChart,
  BarChart,
  LineChart,
  ScatterChart,
  MapChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  VisualMapComponent,
  TitleComponent,
  GeoComponent
])

echarts.registerMap('china', chinaMapData)

const adcodeToName = {}
chinaMapData.features.forEach(f => {
  if (f.properties.adcode && f.properties.name) {
    adcodeToName[f.properties.adcode] = f.properties.name
  }
})

const showPanelExpand = inject('showPanelExpand')
const showOrgDetail = inject('showOrgDetail')
const globalPageSize = inject('globalPageSize')
const setGlobalPageSizeFromInject = inject('setGlobalPageSize')
const globalTimeRange = inject('globalTimeRange')
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

const getUsageColorArray = (dataArray) => {
  return dataArray.map(d => ({
    value: d.value,
    itemStyle: { color: getUsageColor(d.value) }
  }))
}

const overviewUsageColor = computed(() => getUsageColor(overviewStats.value.avg_gpu_usage))
const localUsageColor = computed(() => getUsageColor(localStats.value.avg_gpu_usage))
const centralUsageColor = computed(() => getUsageColor(centralStats.value.avg_gpu_usage))

const activeTab = ref('all')
const timeType = inject('timeType')

const overviewStats = ref({
  total_devices: 0,
  total_memory_gb: 0,
  total_compute_tflops: 0,
  avg_gpu_usage: 0,
  memory_used_gb: 0,
  memory_usage_rate: 0,
  avg_memory_utilization: 0
})

const orgTypeData = ref({})
const networkData = ref([])
const networkByOrgData = ref({ networks: [], data: [] })
const gpuTierByOrgData = ref([])
const purposeData = ref([])
const purposeByOrgData = ref({ purposes: [], data: [] })
const provinceData = ref([])
const localStats = ref({
  total_devices: 0,
  total_memory_gb: 0,
  total_compute_tflops: 0,
  avg_gpu_usage: 0,
  memory_used_gb: 0,
  memory_usage_rate: 0,
  avg_memory_utilization: 0
})
const localGpuTierData = ref([])
const localPurposeData = ref([])
const centralData = ref([])
const centralStats = ref({
  total_devices: 0,
  total_memory_gb: 0,
  total_compute_tflops: 0,
  avg_gpu_usage: 0,
  memory_used_gb: 0,
  memory_usage_rate: 0,
  avg_memory_utilization: 0
})
const centralGpuTierData = ref([])
const centralPurposeData = ref([])
const centralTrendData = ref([])
const carouselData = ref([])
const drillDialogVisible = ref(false)
const drillLoading = ref(false)
const drillDate = ref('')
const drillOrgName = ref('')
const drillOrgId = ref(null)
const drillTrendData = ref([])

const ITEMS_PER_PAGE = 5
const CAROUSEL_INTERVAL = 5000
const PAGE_SIZE_OPTIONS = [10, 20, 'all']

const networkPageIndex = ref(0)
const gpuTierPageIndex = ref(0)
const purposePageIndex = ref(0)
const orgTypePageIndex = ref(0)

const gpuTierChartType = ref('area')
const centralDeviceViewType = ref('chart')

const getEffectivePageSize = (size, total) => {
  return size === 'all' ? total : size
}

const setGlobalPageSize = (size) => {
  setGlobalPageSizeFromInject(size)
  networkPageIndex.value = 0
  gpuTierPageIndex.value = 0
  purposePageIndex.value = 0
  orgTypePageIndex.value = 0
}

const orgTypeChartType = ref('pie')
const networkChartType = ref('bar')
const purposeChartType = ref('bar')

let networkTimer = null
let gpuTierTimer = null
let purposeTimer = null
let orgTypeTimer = null

const formatNumber = (num, decimals = 0) => {
  if (!num) return '0'
  return Number(num).toLocaleString('zh-CN', { 
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals 
  })
}

const createPieOption = (data, colors) => {
  const themeColors = getAllColors()
  return {
    tooltip: {
      trigger: 'item',
      backgroundColor: themeColors.panelBgStart,
      borderColor: themeColors.border,
      textStyle: { color: themeColors.text },
      formatter: (params) => {
        const originalData = data[params.dataIndex]
        return `${originalData.name}<br/>${originalData.value}台 (${params.percent}%)`
      }
    },
    series: [{
      type: 'pie',
      radius: ['35%', '60%'],
      center: ['50%', '55%'],
      avoidLabelOverlap: true,
      itemStyle: {
        borderRadius: 4,
        borderColor: themeColors.panelBgStart,
        borderWidth: 1
      },
      label: {
        show: false
      },
      emphasis: {
        label: {
          show: false
        }
      },
      labelLine: {
        show: false
      },
      data: data.map((d, i) => ({
        name: d.name,
        value: d.value,
        itemStyle: { color: colors[i % colors.length] }
      }))
    }]
  }
}

const getPieOption = (data, groupName) => {
  const colors = getAllColors()
  const colorPalette = [colors.chart1, colors.chart2, colors.chart4, colors.chart3, colors.chart5, colors.chart6, '#9b59b6', '#3498db', '#1abc9c', '#e74c3c']
  return createPieOption(data, colorPalette)
}

const orgTypePageCount = computed(() => {
  const allData = Object.values(orgTypeData.value).flat()
  const pageSize = getEffectivePageSize(globalPageSize.value, allData.length)
  return Math.ceil(allData.length / pageSize)
})

const orgTypeBarOption = computed(() => {
  const colors = getAllColors()
  const allData = Object.values(orgTypeData.value).flat()
  if (!allData || allData.length === 0) {
    return {}
  }
  const sortedData = allData.sort((a, b) => b.value - a.value)
  const pageSize = getEffectivePageSize(globalPageSize.value, sortedData.length)
  const startIdx = orgTypePageIndex.value * pageSize
  const endIdx = startIdx + pageSize
  const pageData = sortedData.slice(startIdx, endIdx)
  
  const chartColors = [colors.chart1, colors.chart2, colors.chart4, colors.chart3, colors.chart5, colors.chart6, '#9b59b6', '#3498db', '#1abc9c', '#e74c3c']
  
  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: colors.panelBgStart,
      borderColor: colors.border,
      textStyle: { color: colors.text },
      formatter: (params) => {
        const data = params[0]
        const originalName = pageData[data.dataIndex]?.name || data.name
        return `${originalName}<br/>设备数量: ${data.value}台`
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
      data: pageData.map(d => d.name.length > 4 ? d.name.substring(0, 4) + '..' : d.name),
      axisLine: { lineStyle: { color: colors.border } },
      axisLabel: { 
        color: colors.textSecondary, 
        fontSize: 9,
        rotate: 30
      }
    },
    yAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: colors.border } },
      axisLabel: { color: colors.textSecondary, fontSize: 10 },
      splitLine: { lineStyle: { color: colors.borderLight } }
    },
    series: [{
      type: 'bar',
      barWidth: '60%',
      itemStyle: {
        borderRadius: [4, 4, 0, 0],
        color: (params) => chartColors[params.dataIndex % chartColors.length]
      },
      data: pageData.map(d => d.value)
    }]
  }
})

const networkPageCount = computed(() => 
  Math.ceil(networkByOrgData.value.data.length / getEffectivePageSize(globalPageSize.value, networkByOrgData.value.data.length))
)

const networkOption = computed(() => {
  const colors = getAllColors()
  const pageSize = getEffectivePageSize(globalPageSize.value, networkByOrgData.value.data.length)
  const startIdx = networkPageIndex.value * pageSize
  const endIdx = startIdx + pageSize
  const pageOrgs = networkByOrgData.value.data.slice(startIdx, endIdx)
  const orgNames = pageOrgs.map(d => d.org_name)
  const networks = networkByOrgData.value.networks
  
  const chartColors = [colors.chart1, colors.chart2, colors.chart4, colors.chart3, colors.chart5, '#9b59b6', '#3498db', '#1abc9c']
  
  const series = networks.map((network, index) => ({
    name: network,
    type: 'bar',
    stack: 'total',
    barWidth: '50%',
    emphasis: {
      focus: 'series'
    },
    itemStyle: {
      color: chartColors[index % chartColors.length]
    },
    data: pageOrgs.map(org => org.networks[network] || 0)
  }))
  
  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: colors.panelBgStart,
      borderColor: colors.border,
      textStyle: { color: colors.text }
    },
    legend: {
      data: networks,
      textStyle: { color: colors.textSecondary },
      top: 5,
      type: 'scroll',
      pageTextStyle: { color: colors.textSecondary }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      top: '25%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: orgNames.map(name => name.length > 6 ? name.substring(0, 6) + '...' : name),
      axisLine: { lineStyle: { color: colors.border } },
      axisLabel: { color: colors.textSecondary, fontSize: 9, rotate: 30 }
    },
    yAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: colors.border } },
      axisLabel: { color: colors.textSecondary, fontSize: 10 },
      splitLine: { lineStyle: { color: colors.borderLight } }
    },
    series: series
  }
})

const networkPieOption = computed(() => {
  const colors = getAllColors()
  const networks = networkByOrgData.value.networks
  const chartColors = [colors.chart1, colors.chart2, colors.chart4, colors.chart3, colors.chart5, '#9b59b6', '#3498db', '#1abc9c']
  
  const totals = networks.map((network, index) => {
    const total = networkByOrgData.value.data.reduce((sum, org) => sum + (org.networks[network] || 0), 0)
    return {
      name: network,
      value: total
    }
  })
  
  return {
    tooltip: {
      trigger: 'item',
      backgroundColor: colors.panelBgStart,
      borderColor: colors.border,
      textStyle: { color: colors.text },
      formatter: (params) => {
        return `${params.name}<br/>${params.value}台 (${params.percent}%)`
      }
    },
    legend: {
      orient: 'vertical',
      right: '5%',
      top: 'middle',
      textStyle: { 
        color: colors.textSecondary,
        fontSize: 10
      }
    },
    series: [{
      type: 'pie',
      radius: ['30%', '50%'],
      center: ['35%', '50%'],
      avoidLabelOverlap: true,
      itemStyle: {
        borderRadius: 4,
        borderColor: colors.panelBgStart,
        borderWidth: 1
      },
      label: {
        show: true,
        fontSize: 9,
        color: colors.textSecondary,
        formatter: '{b}'
      },
      emphasis: {
        label: {
          show: true,
          fontSize: 10,
          fontWeight: 'bold',
          color: colors.text
        }
      },
      labelLine: {
        show: true,
        length: 3,
        length2: 3
      },
      data: totals.map((d, i) => ({
        name: d.name,
        value: d.value,
        itemStyle: { color: chartColors[i % chartColors.length] }
      }))
    }]
  }
})

const gpuTierPageCount = computed(() => 
  Math.ceil(gpuTierByOrgData.value.length / getEffectivePageSize(globalPageSize.value, gpuTierByOrgData.value.length))
)

const gpuTierOption = computed(() => {
  const colors = getAllColors()
  const tierColors = [colors.chart3, colors.chart4, colors.chart5, colors.chart6]
  const tierNames = ['高端卡', '中端卡', '低端卡', '未知']
  const tierKeys = ['high', 'medium', 'low', 'unknown']
  
  if (gpuTierChartType.value === 'pie') {
    const totals = tierKeys.map((key, index) => ({
      name: tierNames[index],
      value: gpuTierByOrgData.value.reduce((sum, d) => sum + (d[key] || 0), 0)
    }))
    
    return {
      tooltip: {
        trigger: 'item',
        backgroundColor: colors.panelBgStart,
        borderColor: colors.border,
        textStyle: { color: colors.text },
        formatter: '{b}: {c}张 ({d}%)'
      },
      legend: {
        data: tierNames,
        textStyle: { color: colors.textSecondary },
        top: 5
      },
      series: [{
        type: 'pie',
        radius: ['35%', '60%'],
        center: ['50%', '55%'],
        avoidLabelOverlap: true,
        itemStyle: {
          borderRadius: 4,
          borderColor: colors.panelBgStart,
          borderWidth: 1
        },
        label: {
          show: true,
          fontSize: 10,
          color: colors.textSecondary,
          formatter: '{b}\n{c}张'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 11,
            fontWeight: 'bold',
            color: colors.text
          }
        },
        labelLine: {
          show: true,
          length: 5,
          length2: 5
        },
        data: totals.map((d, i) => ({
          name: d.name,
          value: d.value,
          itemStyle: { color: tierColors[i] }
        }))
      }]
    }
  }
  
  const pageSize = getEffectivePageSize(globalPageSize.value, gpuTierByOrgData.value.length)
  const startIdx = gpuTierPageIndex.value * pageSize
  const endIdx = startIdx + pageSize
  const pageOrgs = gpuTierByOrgData.value.slice(startIdx, endIdx)
  const orgNames = pageOrgs.map(d => d.org_name)
  
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
      width: 1
    },
    itemStyle: {
      color: tierColors[index]
    },
    data: pageOrgs.map(d => d[tierKeys[index]])
  }))
  
  return {
    tooltip: {
      trigger: 'axis',
      backgroundColor: colors.panelBgStart,
      borderColor: colors.border,
      textStyle: { color: colors.text },
      axisPointer: {
        type: 'cross',
        label: {
          backgroundColor: colors.panelBgStart
        }
      }
    },
    legend: {
      data: tierNames,
      textStyle: { color: colors.textSecondary },
      top: 5
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      top: '25%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: orgNames.map(name => name.length > 6 ? name.substring(0, 6) + '...' : name),
      axisLine: { lineStyle: { color: colors.border } },
      axisLabel: { 
        color: colors.textSecondary, 
        fontSize: 9,
        rotate: 30
      }
    },
    yAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: colors.border } },
      axisLabel: { color: colors.textSecondary },
      splitLine: { lineStyle: { color: colors.borderLight } }
    },
    series: series
  }
})

const purposePageCount = computed(() => 
  Math.ceil(purposeByOrgData.value.data.length / getEffectivePageSize(globalPageSize.value, purposeByOrgData.value.data.length))
)

const purposeOption = computed(() => {
  const colors = getAllColors()
  const pageSize = getEffectivePageSize(globalPageSize.value, purposeByOrgData.value.data.length)
  const startIdx = purposePageIndex.value * pageSize
  const endIdx = startIdx + pageSize
  const pageOrgs = purposeByOrgData.value.data.slice(startIdx, endIdx)
  const orgNames = pageOrgs.map(d => d.org_name)
  const purposes = purposeByOrgData.value.purposes
  
  const purposeColors = [colors.chart1, colors.chart2, colors.chart4]
  
  const series = purposes.map((purpose, index) => ({
    name: purpose,
    type: 'bar',
    stack: 'total',
    barWidth: '50%',
    emphasis: {
      focus: 'series'
    },
    itemStyle: {
      color: purposeColors[index % purposeColors.length]
    },
    data: pageOrgs.map(org => org.purposes[purpose] || 0)
  }))
  
  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: colors.panelBgStart,
      borderColor: colors.border,
      textStyle: { color: colors.text }
    },
    legend: {
      data: purposes,
      textStyle: { color: colors.textSecondary },
      top: 5
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
      data: orgNames.map(name => name.length > 6 ? name.substring(0, 6) + '...' : name),
      axisLine: { lineStyle: { color: colors.border } },
      axisLabel: { color: colors.textSecondary, fontSize: 9, rotate: 30 }
    },
    yAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: colors.border } },
      axisLabel: { color: colors.textSecondary, fontSize: 10 },
      splitLine: { lineStyle: { color: colors.borderLight } }
    },
    series: series
  }
})

const purposePieOption = computed(() => {
  const colors = getAllColors()
  const purposes = purposeByOrgData.value.purposes
  const purposeColors = [colors.chart1, colors.chart2, colors.chart4, colors.chart3, colors.chart5]
  
  const totals = purposes.map((purpose, index) => {
    const total = purposeByOrgData.value.data.reduce((sum, org) => sum + (org.purposes[purpose] || 0), 0)
    return {
      name: purpose,
      value: total
    }
  })
  
  return {
    tooltip: {
      trigger: 'item',
      backgroundColor: colors.panelBgStart,
      borderColor: colors.border,
      textStyle: { color: colors.text },
      formatter: (params) => {
        return `${params.name}<br/>${params.value}台 (${params.percent}%)`
      }
    },
    legend: {
      orient: 'vertical',
      right: '5%',
      top: 'middle',
      textStyle: { 
        color: colors.textSecondary,
        fontSize: 10
      }
    },
    series: [{
      type: 'pie',
      radius: ['30%', '50%'],
      center: ['35%', '50%'],
      avoidLabelOverlap: true,
      itemStyle: {
        borderRadius: 4,
        borderColor: colors.panelBgStart,
        borderWidth: 1
      },
      label: {
        show: true,
        fontSize: 9,
        color: colors.textSecondary,
        formatter: '{b}'
      },
      emphasis: {
        label: {
          show: true,
          fontSize: 10,
          fontWeight: 'bold',
          color: colors.text
        }
      },
      labelLine: {
        show: true,
        length: 3,
        length2: 3
      },
      data: totals.map((d, i) => ({
        name: d.name,
        value: d.value,
        itemStyle: { color: purposeColors[i % purposeColors.length] }
      }))
    }]
  }
})

const mapOption = computed(() => {
  const colors = getAllColors()
  const maxValue = Math.max(...provinceData.value.map(d => d.value), 10)
  
  const provinceDataMap = {}
  provinceData.value.forEach(d => {
    const mappedName = adcodeToName[d.code] || d.name
    provinceDataMap[mappedName] = {
      value: d.value,
      gpu_count: d.gpu_count,
      memory_gb: d.memory_gb,
      compute_tflops: d.compute_tflops,
      avg_gpu_usage: d.avg_gpu_usage
    }
  })
  
  const mapData = []
  chinaMapData.features.forEach(f => {
    const provinceName = f.properties.name
    const data = provinceDataMap[provinceName]
    mapData.push({
      name: provinceName,
      value: data?.value ?? 0,
      adcode: f.properties.adcode,
      gpu_count: data?.gpu_count ?? 0,
      memory_gb: data?.memory_gb ?? 0,
      compute_tflops: data?.compute_tflops ?? 0,
      avg_gpu_usage: data?.avg_gpu_usage ?? 0
    })
  })
  
  return {
    tooltip: {
      trigger: 'item',
      backgroundColor: colors.panelBgStart,
      borderColor: colors.border,
      textStyle: { color: colors.text },
      confine: true,
      position: (point, params, dom, rect, size) => {
        const [x, y] = point
        const { contentSize, viewSize } = size
        const [boxWidth, boxHeight] = contentSize
        const [viewWidth, viewHeight] = viewSize
        
        let posX = x + 15
        let posY = y + 15
        
        if (posX + boxWidth > viewWidth - 10) {
          posX = x - boxWidth - 15
        }
        if (posY + boxHeight > viewHeight - 10) {
          posY = viewHeight - boxHeight - 10
        }
        if (posX < 10) posX = 10
        if (posY < 10) posY = 10
        
        return [posX, posY]
      },
      formatter: (params) => {
        if (params.data && params.data.value > 0) {
          const d = params.data
          const usageColor = getUsageColor(d.avg_gpu_usage)
          const computeDisplay = d.compute_tflops >= 1000 
            ? `${(d.compute_tflops / 1000).toFixed(2)} PFLOPS` 
            : `${d.compute_tflops.toFixed(2)} TFLOPS`
          const memoryDisplay = d.memory_gb >= 1024 
            ? `${(d.memory_gb / 1024).toFixed(2)} TB` 
            : `${d.memory_gb.toFixed(2)} GB`
          
          return `<div style="font-weight: bold; margin-bottom: 8px; font-size: 14px;">${params.name}</div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
              <span style="color: ${colors.textSecondary};">设备数量:</span>
              <span style="color: ${colors.chart1}; font-weight: bold;">${d.value} 台</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
              <span style="color: ${colors.textSecondary};">GPU数量:</span>
              <span style="color: ${colors.chart2}; font-weight: bold;">${d.gpu_count} 块</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
              <span style="color: ${colors.textSecondary};">显存总量:</span>
              <span style="color: ${colors.chart4}; font-weight: bold;">${memoryDisplay}</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
              <span style="color: ${colors.textSecondary};">总算力:</span>
              <span style="color: ${colors.chart3}; font-weight: bold;">${computeDisplay}</span>
            </div>
            <div style="display: flex; justify-content: space-between;">
              <span style="color: ${colors.textSecondary};">平均使用率:</span>
              <span style="color: ${usageColor}; font-weight: bold;">${d.avg_gpu_usage}%</span>
            </div>
            <div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid ${colors.border}; color: ${colors.info}; font-size: 11px;">
              点击查看该省份组织机构列表
            </div>`
        }
        return `<div style="font-weight: bold;">${params.name}</div><div style="color: ${colors.textSecondary}; font-size: 12px;">暂无设备数据</div>`
      }
    },
    visualMap: {
      min: 0,
      max: maxValue,
      left: 'left',
      bottom: '10%',
      text: ['高', '低'],
      textStyle: { color: colors.textSecondary },
      inRange: {
        color: [colors.bgMiddle, colors.chart1, colors.chart2]
      },
      calculable: true
    },
    series: [{
      name: '设备分布',
      type: 'map',
      map: 'china',
      roam: true,
      zoom: 1.2,
      center: [105, 36],
      scaleLimit: {
        min: 0.8,
        max: 5
      },
      itemStyle: {
        areaColor: colors.panelBgStart,
        borderColor: colors.glow,
        borderWidth: 1
      },
      emphasis: {
        itemStyle: {
          areaColor: colors.glow
        },
        label: { 
          show: true,
          color: colors.text 
        }
      },
      label: {
        show: false,
        color: colors.textSecondary
      },
      data: mapData
    }]
  }
})

const localGpuTierOption = computed(() => {
  const colors = getAllColors()
  const tierColors = [colors.chart3, colors.chart4, colors.chart5, colors.chart6]
  
  return {
    tooltip: {
      trigger: 'item',
      backgroundColor: colors.panelBgStart,
      borderColor: colors.border,
      textStyle: { color: colors.text },
      formatter: '{b}: {c}张 ({d}%)'
    },
    series: [{
      type: 'pie',
      radius: ['40%', '65%'],
      center: ['50%', '55%'],
      avoidLabelOverlap: true,
      itemStyle: {
        borderRadius: 6,
        borderColor: colors.panelBgStart,
        borderWidth: 2
      },
      label: {
        show: true,
        fontSize: 11,
        color: colors.textSecondary,
        formatter: '{b}\n{c}张'
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
        length: 8,
        length2: 8
      },
      data: networkData.value.map((d, i) => ({
        name: d.name,
        value: d.value,
        itemStyle: { color: tierColors[i % tierColors.length] }
      }))
    }]
  }
})

const localPurposeOption = computed(() => {
  const colors = getAllColors()
  const purposeColors = [colors.chart1, colors.chart2, colors.chart4]
  
  return {
    tooltip: {
      trigger: 'item',
      backgroundColor: colors.panelBgStart,
      borderColor: colors.border,
      textStyle: { color: colors.text },
      formatter: '{b}: {c}台 ({d}%)'
    },
    series: [{
      type: 'pie',
      radius: ['40%', '65%'],
      center: ['50%', '55%'],
      avoidLabelOverlap: true,
      itemStyle: {
        borderRadius: 6,
        borderColor: colors.panelBgStart,
        borderWidth: 2
      },
      label: {
        show: true,
        fontSize: 11,
        color: colors.textSecondary,
        formatter: '{b}\n{c}台'
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
        length: 8,
        length2: 8
      },
      data: localPurposeData.value.map((d, i) => ({
        name: d.name,
        value: d.value,
        itemStyle: { color: purposeColors[i % purposeColors.length] }
      }))
    }]
  }
})

const centralBarOption = computed(() => {
  const colors = getAllColors()
  const reversedData = [...centralData.value].reverse()
  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: colors.panelBgStart,
      borderColor: colors.border,
      textStyle: { color: colors.text },
      confine: true,
      position: (point, params, dom, rect, size) => {
        const [x, y] = point
        const { contentSize, viewSize } = size
        const [boxWidth, boxHeight] = contentSize
        const [viewWidth, viewHeight] = viewSize
        
        let posX = x + 15
        let posY = y + 15
        
        if (posX + boxWidth > viewWidth - 10) {
          posX = x - boxWidth - 15
        }
        if (posY + boxHeight > viewHeight - 10) {
          posY = viewHeight - boxHeight - 10
        }
        if (posX < 10) posX = 10
        if (posY < 10) posY = 10
        
        return [posX, posY]
      },
      formatter: (params) => {
        const data = params[0]
        const item = reversedData[data.dataIndex]
        if (!item) return data.name
        
        const computeDisplay = item.compute_tflops >= 1000 
          ? `${(item.compute_tflops / 1000).toFixed(2)} PFLOPS` 
          : `${item.compute_tflops?.toFixed(2) || 0} TFLOPS`
        const memoryDisplay = item.memory_gb >= 1024 
          ? `${(item.memory_gb / 1024).toFixed(2)} TB` 
          : `${item.memory_gb?.toFixed(2) || 0} GB`
        
        return `<div style="font-weight: bold; margin-bottom: 8px; font-size: 14px;">${item.name}</div>
          <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
            <span style="color: ${colors.textSecondary};">设备数量:</span>
            <span style="color: ${colors.chart1}; font-weight: bold;">${item.value} 台</span>
          </div>
          <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
            <span style="color: ${colors.textSecondary};">GPU数量:</span>
            <span style="color: ${colors.chart2}; font-weight: bold;">${item.gpu_count || 0} 块</span>
          </div>
          <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
            <span style="color: ${colors.textSecondary};">显存总量:</span>
            <span style="color: ${colors.chart4}; font-weight: bold;">${memoryDisplay}</span>
          </div>
          <div style="display: flex; justify-content: space-between;">
            <span style="color: ${colors.textSecondary};">总算力:</span>
            <span style="color: ${colors.chart3}; font-weight: bold;">${computeDisplay}</span>
          </div>
          <div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid ${colors.border}; color: ${colors.info}; font-size: 11px;">
            点击查看组织详情
          </div>`
      }
    },
    grid: {
      left: '3%',
      right: '10%',
      bottom: '10%',
      top: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'value',
      name: '设备数量',
      nameTextStyle: { color: colors.textSecondary },
      axisLine: { lineStyle: { color: colors.border } },
      axisLabel: { color: colors.textSecondary },
      splitLine: { lineStyle: { color: colors.borderLight } }
    },
    yAxis: {
      type: 'category',
      data: centralData.value.map(d => d.name).reverse(),
      axisLine: { lineStyle: { color: colors.border } },
      axisLabel: { color: colors.textSecondary }
    },
    series: [{
      type: 'bar',
      data: centralData.value.map(d => d.value).reverse(),
      itemStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 1, y2: 0,
          colorStops: [
            { offset: 0, color: colors.border },
            { offset: 1, color: colors.chart1 }
          ]
        },
        borderRadius: [0, 4, 4, 0]
      },
      label: {
        show: true,
        position: 'right',
        color: colors.chart1,
        formatter: '{c}台'
      }
    }]
  }
})

const centralNetworkOption = computed(() => {
  const colors = getAllColors()
  const networkColors = [colors.chart1, colors.chart2, colors.chart3, colors.chart4, colors.chart5, colors.chart6]
  
  return {
    tooltip: {
      trigger: 'item',
      backgroundColor: colors.panelBgStart,
      borderColor: colors.border,
      textStyle: { color: colors.text },
      formatter: '{b}: {c}张 ({d}%)'
    },
    series: [{
      type: 'pie',
      radius: ['40%', '65%'],
      center: ['50%', '55%'],
      avoidLabelOverlap: true,
      itemStyle: {
        borderRadius: 6,
        borderColor: colors.panelBgStart,
        borderWidth: 2
      },
      label: {
        show: true,
        fontSize: 11,
        color: colors.textSecondary,
        formatter: '{b}\n{c}张'
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
        length: 8,
        length2: 8
      },
      data: networkData.value.map((d, i) => ({
        name: d.name,
        value: d.value,
        itemStyle: { color: networkColors[i % networkColors.length] }
      }))
    }]
  }
})

const centralGpuTierOption = computed(() => {
  const colors = getAllColors()
  const tierColors = [colors.chart3, colors.chart4, colors.chart5, colors.chart6]
  
  return {
    tooltip: {
      trigger: 'item',
      backgroundColor: colors.panelBgStart,
      borderColor: colors.border,
      textStyle: { color: colors.text },
      formatter: '{b}: {c}张 ({d}%)'
    },
    series: [{
      type: 'pie',
      radius: ['40%', '65%'],
      center: ['50%', '55%'],
      avoidLabelOverlap: true,
      itemStyle: {
        borderRadius: 6,
        borderColor: colors.panelBgStart,
        borderWidth: 2
      },
      label: {
        show: true,
        fontSize: 11,
        color: colors.textSecondary,
        formatter: '{b}\n{c}张'
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
        length: 8,
        length2: 8
      },
      data: centralGpuTierData.value.map((d, i) => ({
        name: d.name,
        value: d.value,
        itemStyle: { color: tierColors[i % tierColors.length] }
      }))
    }]
  }
})

const centralPurposeOption = computed(() => {
  const colors = getAllColors()
  const purposeColors = [colors.chart1, colors.chart2, colors.chart4]
  
  return {
    tooltip: {
      trigger: 'item',
      backgroundColor: colors.panelBgStart,
      borderColor: colors.border,
      textStyle: { color: colors.text },
      formatter: '{b}: {c}台 ({d}%)'
    },
    series: [{
      type: 'pie',
      radius: ['40%', '65%'],
      center: ['50%', '55%'],
      avoidLabelOverlap: true,
      itemStyle: {
        borderRadius: 6,
        borderColor: colors.panelBgStart,
        borderWidth: 2
      },
      label: {
        show: true,
        fontSize: 11,
        color: colors.textSecondary,
        formatter: '{b}\n{c}台'
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
        length: 8,
        length2: 8
      },
      data: centralPurposeData.value.map((d, i) => ({
        name: d.name,
        value: d.value,
        itemStyle: { color: purposeColors[i % purposeColors.length] }
      }))
    }]
  }
})

const centralTrendOption = computed(() => {
  const colors = getAllColors()
  return {
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
      left: '5%',
      right: '5%',
      bottom: '15%',
      top: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: centralTrendData.value.map(d => d.date.substring(5)),
      axisLine: { lineStyle: { color: colors.border } },
      axisLabel: { color: colors.textSecondary, fontSize: 10 }
    },
    yAxis: {
      type: 'value',
      name: '使用率(%)',
      nameTextStyle: { color: colors.textSecondary, fontSize: 10 },
      axisLine: { lineStyle: { color: colors.border } },
      axisLabel: { color: colors.textSecondary, fontSize: 10 },
      splitLine: { lineStyle: { color: colors.borderLight } }
    },
    series: [{
      type: 'line',
      smooth: true,
      data: centralTrendData.value.map(d => d.value),
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
      itemStyle: { color: colors.chart1 },
      symbol: 'circle',
      symbolSize: 6
    }]
  }
})

const getCarouselOption = (trend) => {
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
      left: '5%',
      right: '5%',
      bottom: '15%',
      top: '18%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: trend.map(d => d.date),
      axisLine: { lineStyle: { color: colors.border } },
      axisLabel: { color: colors.textSecondary, fontSize: 10 },
      triggerEvent: true
    },
    yAxis: {
      type: 'value',
      name: '使用率(%)',
      nameTextStyle: { color: colors.textSecondary },
      axisLine: { lineStyle: { color: colors.border } },
      axisLabel: { color: colors.textSecondary },
      splitLine: { lineStyle: { color: colors.borderLight } },
      min: 0,
      max: 100
    },
    series: [
      {
        name: 'GPU使用率',
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 4,
        data: trend.map(d => d.gpu_usage || d.value),
        lineStyle: { color: colors.chart1, width: 2 },
        itemStyle: { color: colors.chart1 }
      },
      {
        name: '显存使用率',
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 4,
        data: trend.map(d => d.memory_usage_rate || 0),
        lineStyle: { color: colors.chart2, width: 2 },
        itemStyle: { color: colors.chart2 }
      },
      {
        name: '显存利用率',
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 4,
        data: trend.map(d => d.memory_utilization || 0),
        lineStyle: { color: colors.chart3, width: 2 },
        itemStyle: { color: colors.chart3 }
      }
    ]
  }
}

const drillChartOption = computed(() => {
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
      itemWidth: 12,
      itemHeight: 8
    },
    grid: {
      left: '10%',
      right: '5%',
      bottom: '18%',
      top: '18%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: drillTrendData.value.map(d => d.date),
      axisLine: { lineStyle: { color: colors.border } },
      axisLabel: { 
        color: colors.textSecondary, 
        fontSize: 11,
        interval: 1
      }
    },
    yAxis: {
      type: 'value',
      name: '使用率(%)',
      nameTextStyle: { color: colors.textSecondary, fontSize: 12 },
      axisLine: { lineStyle: { color: colors.border } },
      axisLabel: { color: colors.textSecondary },
      splitLine: { lineStyle: { color: colors.borderLight } },
      min: 0,
      max: 100
    },
    series: [
      {
        name: 'GPU使用率',
        type: 'line',
        smooth: true,
        data: drillTrendData.value.map(d => d.gpu_usage || d.value),
        lineStyle: { color: colors.chart1, width: 2 },
        itemStyle: { color: colors.chart1 }
      },
      {
        name: '显存使用率',
        type: 'line',
        smooth: true,
        data: drillTrendData.value.map(d => d.memory_usage_rate || 0),
        lineStyle: { color: colors.chart2, width: 2 },
        itemStyle: { color: colors.chart2 }
      },
      {
        name: '显存利用率',
        type: 'line',
        smooth: true,
        data: drillTrendData.value.map(d => d.memory_utilization || 0),
        lineStyle: { color: colors.chart3, width: 2 },
        itemStyle: { color: colors.chart3 }
      }
    ]
  }
})

const loadOverviewStats = async () => {
  try {
    overviewStats.value = await dashboardApi.getOverviewStats(globalTimeRange.value, timeType.value)
  } catch (error) {
    console.error('Failed to fetch overview stats:', error)
  }
}

const loadLocalStats = async () => {
  try {
    localStats.value = await dashboardApi.getLocalStats(globalTimeRange.value, timeType.value)
  } catch (error) {
    console.error('Failed to fetch local stats:', error)
  }
}

const loadCentralStats = async () => {
  try {
    centralStats.value = await dashboardApi.getCentralStats(globalTimeRange.value, timeType.value)
  } catch (error) {
    console.error('Failed to fetch central stats:', error)
  }
}

const fetchData = async () => {
  try {
    const [
      stats,
      orgType,
      network,
      networkByOrg,
      gpuTierByOrg,
      purpose,
      purposeByOrg,
      province,
      localStatsData,
      localGpuTier,
      localPurpose,
      central,
      centralStatsData,
      centralGpuTier,
      centralPurpose,
      centralTrend,
      carousel
    ] = await Promise.all([
      dashboardApi.getOverviewStats(globalTimeRange.value, timeType.value),
      dashboardApi.getOrgTypeDistribution(timeType.value),
      dashboardApi.getNetworkDistribution(),
      dashboardApi.getNetworkDistributionByOrg(),
      dashboardApi.getGpuTierByOrgDistribution(),
      dashboardApi.getPurposeDistribution(),
      dashboardApi.getPurposeDistributionByOrg(),
      dashboardApi.getProvinceDistribution(timeType.value),
      dashboardApi.getLocalStats(globalTimeRange.value, timeType.value),
      dashboardApi.getLocalGpuTier(),
      dashboardApi.getLocalPurpose(),
      dashboardApi.getCentralBubble(timeType.value),
      dashboardApi.getCentralStats(globalTimeRange.value, timeType.value),
      dashboardApi.getCentralGpuTier(),
      dashboardApi.getCentralPurpose(),
      dashboardApi.getCentralTrend(timeType.value),
      dashboardApi.getCarouselUsageTrend(timeType.value)
    ])
    
    overviewStats.value = stats
    orgTypeData.value = orgType
    networkData.value = network
    networkByOrgData.value = networkByOrg
    gpuTierByOrgData.value = gpuTierByOrg
    purposeData.value = purpose
    purposeByOrgData.value = purposeByOrg
    provinceData.value = province
    localStats.value = localStatsData
    localGpuTierData.value = localGpuTier
    localPurposeData.value = localPurpose
    centralData.value = central
    centralStats.value = centralStatsData
    centralGpuTierData.value = centralGpuTier
    centralPurposeData.value = centralPurpose
    centralTrendData.value = centralTrend
    carouselData.value = carousel
  } catch (error) {
    console.error('Failed to fetch center panel data:', error)
  }
}

const handleCarouselChange = (index) => {
}

const handleCarouselChartClick = async (params, item) => {
  if (params.componentType === 'series' || params.componentType === 'xAxis') {
    const clickedDate = params.name || params.value
    if (clickedDate && /^\d{4}-\d{2}-\d{2}$/.test(clickedDate)) {
      drillDate.value = clickedDate
      drillOrgName.value = item.org_name
      drillOrgId.value = item.org_id
      drillTrendData.value = []
      drillLoading.value = true
      drillDialogVisible.value = true
      
      try {
        const result = await dashboardApi.getCarouselUsageTrend(timeType.value, null, null, 'day', null, null, clickedDate, item.org_id)
        drillTrendData.value = result.trend || []
      } catch (error) {
        console.error('Failed to drill down:', error)
      } finally {
        drillLoading.value = false
      }
    }
  }
}

const handleTitleClick = (subType, title) => {
  showPanelExpand('center', subType, title, {})
}

const handleOrgNameClick = (item) => {
  if (item.org_id) {
    showOrgDetail(item.org_id, 'usage')
  }
}

const handleMapClick = (params) => {
  if (params.name) {
    const provinceName = params.name
    const provinceInfo = provinceData.value.find(p => p.name === provinceName)
    if (provinceInfo && provinceInfo.value > 0) {
      showPanelExpand('right', 'province', `${provinceName}组织机构列表`, { provinceName: provinceName })
    }
  }
}

const handleCentralOrgClick = (item) => {
  if (item.org_id && showOrgDetail) {
    showOrgDetail(item.org_id, 'devices')
  }
}


const startCarousel = () => {
  networkTimer = setInterval(() => {
    if (networkPageCount.value > 1) {
      networkPageIndex.value = (networkPageIndex.value + 1) % networkPageCount.value
    }
  }, CAROUSEL_INTERVAL)
  
  gpuTierTimer = setInterval(() => {
    if (gpuTierPageCount.value > 1) {
      gpuTierPageIndex.value = (gpuTierPageIndex.value + 1) % gpuTierPageCount.value
    }
  }, CAROUSEL_INTERVAL)
  
  purposeTimer = setInterval(() => {
    if (purposePageCount.value > 1) {
      purposePageIndex.value = (purposePageIndex.value + 1) % purposePageCount.value
    }
  }, CAROUSEL_INTERVAL)
  
  orgTypeTimer = setInterval(() => {
    if (orgTypePageCount.value > 1) {
      orgTypePageIndex.value = (orgTypePageIndex.value + 1) % orgTypePageCount.value
    }
  }, CAROUSEL_INTERVAL)
}

const stopCarousel = () => {
  if (networkTimer) {
    clearInterval(networkTimer)
    networkTimer = null
  }
  if (gpuTierTimer) {
    clearInterval(gpuTierTimer)
    gpuTierTimer = null
  }
  if (purposeTimer) {
    clearInterval(purposeTimer)
    purposeTimer = null
  }
  if (orgTypeTimer) {
    clearInterval(orgTypeTimer)
    orgTypeTimer = null
  }
}

let cleanup = null

onMounted(() => {
  fetchData()
  startCarousel()
  cleanup = watchThemeChange(() => {
    fetchData()
  })
})

watch(timeType, () => {
  fetchData()
})

onUnmounted(() => {
  stopCarousel()
  if (cleanup) cleanup()
})
</script>

<style lang="scss" scoped>
.center-panel-content {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.stats-row {
  display: flex;
  gap: 15px;
  flex-shrink: 0;
  
  .stat-card {
    flex: 1;
    padding: 12px 16px;
  }
}

.charts-section {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  
  .panel-header {
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 6px 12px;
    
    .global-page-size {
      display: flex;
      align-items: center;
      gap: 6px;
      
      .label {
        font-size: 11px;
        color: var(--theme-text-secondary);
      }
      
      .page-size-selector {
        display: flex;
        gap: 2px;
        background: var(--theme-shadow);
        border-radius: 4px;
        padding: 2px;
        
        .size-btn {
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
    }
  }
  
  .panel-content {
    flex: 1;
    min-height: 0;
    overflow: hidden;
  }
  
  .chart-tabs {
    :deep(.el-tabs__header) {
      margin: 0;
      border-bottom: none;
    }
    
    :deep(.el-tabs__nav-wrap::after) {
      display: none;
    }
    
    :deep(.el-tabs__item) {
      color: var(--theme-text-secondary);
      font-size: 13px;
      padding: 0 16px;
      
      &.is-active {
        color: var(--theme-primary);
      }
    }
    
    :deep(.el-tabs__active-bar) {
      background-color: var(--theme-primary);
    }
  }
  
  .charts-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    grid-template-rows: repeat(2, 1fr);
    gap: 10px;
    height: 100%;
    
    .chart-item {
      background: var(--theme-shadow);
      border: 1px solid var(--theme-border-light);
      border-radius: 6px;
      padding: 10px;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      
      .chart-title {
        font-size: 12px;
        color: var(--theme-text-secondary);
        margin-bottom: 5px;
        flex-shrink: 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
        
        .clickable {
          cursor: pointer;
          transition: all 0.3s ease;
          
          &:hover {
            color: var(--theme-primary);
          }
        }
        
        .title-right {
          display: flex;
          align-items: center;
          gap: 8px;
        }
        
        .chart-type-switch {
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
        
        .carousel-controls {
          display: flex;
          align-items: center;
          gap: 10px;
        }
        
        .page-size-selector {
          display: flex;
          gap: 2px;
          background: var(--theme-shadow);
          border-radius: 4px;
          padding: 2px;
          
          .size-btn {
            padding: 2px 6px;
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
              background: var(--theme-glow);
            }
            
            &.active {
              background: var(--theme-primary);
              transform: scale(1.2);
            }
          }
        }
      }
      
      :deep(.echarts) {
        flex: 1;
        min-height: 0;
      }
      
      &.org-type-panel {
        display: flex;
        flex-direction: column;
        
        .chart-title {
          flex-shrink: 0;
        }
        
        .dual-pie-container {
          flex: 1;
          display: flex;
          gap: 5px;
          min-height: 0;
          
          .pie-wrapper {
            flex: 1;
            display: flex;
            flex-direction: column;
            
            .pie-label {
              font-size: 11px;
              color: var(--theme-primary);
              text-align: center;
              padding: 2px 0;
              flex-shrink: 0;
            }
            
            :deep(.echarts) {
              flex: 1;
              min-height: 0;
            }
          }
        }
        
        .org-type-bar-container {
          flex: 1;
          min-height: 0;
          display: flex;
          flex-direction: column;
          
          :deep(.echarts) {
            width: 100%;
            flex: 1;
            min-height: 0;
          }
        }
      }
    }
  }
  
  .local-container {
    height: 100%;
    display: flex;
    flex-direction: column;
    gap: 10px;
    
    .local-stats-row {
      display: flex;
      gap: 10px;
      flex-shrink: 0;
      
      .local-stat-card {
        flex: 1;
        background: var(--theme-shadow);
        border: 1px solid var(--theme-border-light);
        border-radius: 8px;
        padding: 10px 12px;
        display: flex;
        align-items: center;
        gap: 10px;
        transition: all 0.3s ease;
        
        &:hover {
          border-color: var(--theme-secondary);
          box-shadow: 0 0 10px var(--theme-glow);
        }
        
        .stat-icon {
          width: 36px;
          height: 36px;
          border-radius: 8px;
          background: linear-gradient(135deg, var(--theme-secondary) 0%, var(--theme-chart2) 100%);
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
          
          svg {
            width: 20px;
            height: 20px;
            color: white;
          }
        }
        
        .stat-info {
          flex: 1;
          min-width: 0;
          
          .stat-label {
            font-size: 11px;
            color: var(--theme-text-secondary);
            margin-bottom: 2px;
          }
          
          .stat-value {
            font-size: 18px;
            font-weight: 600;
            color: var(--theme-text);
            
            .stat-unit {
              font-size: 12px;
              font-weight: normal;
              color: var(--theme-text-secondary);
              margin-left: 2px;
            }
          }
        }
      }
    }
    
    .local-charts-grid {
      flex: 1;
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      grid-template-rows: repeat(2, 1fr);
      gap: 10px;
      min-height: 0;
      
      .local-chart-item {
        background: var(--theme-shadow);
        border: 1px solid var(--theme-border-light);
        border-radius: 6px;
        padding: 10px;
        display: flex;
        flex-direction: column;
        overflow: hidden;
        
        .chart-title {
          font-size: 12px;
          color: var(--theme-text-secondary);
          margin-bottom: 5px;
          flex-shrink: 0;
          
          &.clickable {
            cursor: pointer;
            transition: all 0.3s ease;
            
            &:hover {
              color: var(--theme-secondary);
            }
          }
        }
        
        :deep(.echarts) {
          flex: 1;
          min-height: 0;
        }
        
        &.map-chart {
          grid-column: 1 / 2;
          grid-row: 1 / 3;
        }
      }
    }
  }
  
  .map-container {
    height: 100%;
    
    :deep(.echarts) {
      width: 100%;
      height: 100%;
    }
  }
  
  .central-container {
    height: 100%;
    display: flex;
    flex-direction: column;
    gap: 10px;
    
    .central-stats-row {
      display: flex;
      gap: 10px;
      flex-shrink: 0;
      
      .central-stat-card {
        flex: 1;
        background: var(--theme-shadow);
        border: 1px solid var(--theme-border-light);
        border-radius: 8px;
        padding: 10px 12px;
        display: flex;
        align-items: center;
        gap: 10px;
        transition: all 0.3s ease;
        
        &:hover {
          border-color: var(--theme-primary);
          box-shadow: 0 0 10px var(--theme-glow);
        }
        
        .stat-icon {
          width: 36px;
          height: 36px;
          border-radius: 8px;
          background: linear-gradient(135deg, var(--theme-primary) 0%, var(--theme-secondary) 100%);
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
          
          svg {
            width: 20px;
            height: 20px;
            color: white;
          }
        }
        
        .stat-info {
          flex: 1;
          min-width: 0;
          
          .stat-label {
            font-size: 11px;
            color: var(--theme-text-secondary);
            margin-bottom: 2px;
          }
          
          .stat-value {
            font-size: 18px;
            font-weight: 600;
            color: var(--theme-text);
            
            .stat-unit {
              font-size: 12px;
              font-weight: normal;
              color: var(--theme-text-secondary);
              margin-left: 2px;
            }
          }
        }
      }
    }
    
    .central-charts-grid {
      flex: 1;
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      grid-template-rows: repeat(2, 1fr);
      gap: 10px;
      min-height: 0;
      
      .central-chart-item {
        background: var(--theme-shadow);
        border: 1px solid var(--theme-border-light);
        border-radius: 6px;
        padding: 10px;
        display: flex;
        flex-direction: column;
        overflow: hidden;
        
        .chart-title {
          font-size: 12px;
          color: var(--theme-text-secondary);
          margin-bottom: 5px;
          flex-shrink: 0;
          display: flex;
          justify-content: space-between;
          align-items: center;
          
          &.clickable {
            cursor: pointer;
            transition: all 0.3s ease;
            
            &:hover {
              color: var(--theme-primary);
            }
          }
          
          .title-right {
            display: flex;
            align-items: center;
            gap: 8px;
          }
          
          .chart-type-switch {
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
        }
        
        .central-device-list {
          flex: 1;
          overflow-y: auto;
          min-height: 0;
          
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
          
          .list-item {
            display: grid;
            grid-template-columns: 1fr repeat(4, 80px);
            align-items: center;
            padding: 8px 10px;
            margin-bottom: 4px;
            background: var(--theme-bg-middle);
            border-radius: 4px;
            cursor: pointer;
            transition: all 0.3s ease;
            
            &:hover {
              background: var(--theme-hover-bg);
              box-shadow: 0 0 8px var(--theme-glow);
              
              .org-name {
                color: var(--theme-primary);
              }
            }
            
            .org-name {
              font-size: 12px;
              text-align: center;
              color: var(--theme-text);
              overflow: hidden;
              text-overflow: ellipsis;
              white-space: nowrap;
              transition: color 0.3s ease;
              min-width: 80px;
            }
            
            .org-value {
              font-size: 12px;
              color: var(--theme-primary);
              font-weight: 600;
              text-align: right;
              flex-shrink: 0;
            }
          }
        }
        
        :deep(.echarts) {
          flex: 1;
          min-height: 0;
        }
      }
    }
  }
}

.carousel-section {
  flex-shrink: 0;
  height: 180px;
  
  .panel-content {
    height: calc(100% - 45px);
    
    :deep(.el-carousel) {
      height: 100%;
    }
    
    :deep(.el-carousel__container) {
      height: calc(100% - 30px);
    }
    
    :deep(.el-carousel__indicators) {
      bottom: 0;
    }
    
    :deep(.el-carousel__indicator--horizontal .el-carousel__button) {
      background-color: var(--theme-border);
    }
    
    :deep(.el-carousel__indicator--horizontal.is-active .el-carousel__button) {
      background-color: var(--theme-primary);
    }
  }
  
  .carousel-item {
    height: 100%;
    display: flex;
    flex-direction: column;
    
    .carousel-title {
      font-size: 14px;
      color: var(--theme-primary);
      text-align: center;
      padding: 5px 0;
      flex-shrink: 0;
      
      &.clickable {
        cursor: pointer;
        transition: all 0.3s ease;
        
        &:hover {
          color: var(--theme-secondary);
          text-shadow: 0 0 10px var(--theme-glow);
        }
      }
    }
    
    :deep(.echarts) {
      flex: 1;
      min-height: 0;
    }
  }
}

.drill-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 400px;
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
    height: 400px;
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

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
