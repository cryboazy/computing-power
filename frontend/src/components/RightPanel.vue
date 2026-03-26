<template>
  <div class="right-panel-content">
    <div class="panel ranking-section">
      <div class="panel-header clickable" @click="handleTitleClick('all', '全国排名')">
        <span class="panel-title">全国使用率Top5</span>
      </div>
      <div class="panel-content">
        <div v-if="!allRanking.length" class="no-data">
          暂无数据
        </div>
        <div v-else class="ranking-list">
          <div 
            v-for="(item, index) in allRanking" 
            :key="index"
            class="ranking-item"
            @click="handleRankingItemClick(item)"
          >
            <span :class="['rank-badge', `rank-${index + 1}`]">{{ index + 1 }}</span>
            <span class="org-name">{{ item.org_name }}</span>
            <span class="usage-value" :style="{ color: getUsageColor(item.avg_gpu_usage) }">{{ formatNumber(item.avg_gpu_usage, 2) }}%</span>
          </div>
        </div>
      </div>
    </div>
    
    <div v-for="(rankings, groupName) in groupRankings" :key="groupName" class="panel ranking-section">
      <div class="panel-header clickable" @click="handleTitleClick('group', `${groupName}排名`, groupName)">
        <span class="panel-title">{{ groupName }}使用率Top5</span>
      </div>
      <div class="panel-content">
        <div v-if="!rankings.length" class="no-data">
          暂无数据
        </div>
        <div v-else class="ranking-list">
          <div 
            v-for="(item, index) in rankings" 
            :key="index"
            class="ranking-item"
            @click="handleRankingItemClick(item)"
          >
            <span :class="['rank-badge', `rank-${index + 1}`]">{{ index + 1 }}</span>
            <span class="org-name">{{ item.org_name }}</span>
            <span class="usage-value" :style="{ color: getUsageColor(item.avg_gpu_usage) }">{{ formatNumber(item.avg_gpu_usage, 2) }}%</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, inject } from 'vue'
import { dashboardApi } from '../api'
import { useTheme } from '../composables/useTheme'

const showPanelExpand = inject('showPanelExpand')
const showOrgDetail = inject('showOrgDetail')
const timeType = inject('timeType')
const activeTab = inject('globalTimeRange')
const globalNetworkFilter = inject('globalNetworkFilter')
const globalPurposeFilter = inject('globalPurposeFilter')
const usageThresholds = inject('usageThresholds', ref({ high: 60.0, low: 30.0 }))
const { getAllColors } = useTheme()
const allRanking = ref([])
const groupRankings = ref({})

const getUsageColor = (usage) => {
  const colors = getAllColors()
  if (!usage || usage === 0) return colors.info
  if (usage >= usageThresholds.value.high) return colors.usageHigh
  if (usage >= usageThresholds.value.low) return colors.usageMedium
  return colors.success
}

const formatNumber = (num, decimals = 0) => {
  if (!num && num !== 0) return '0'
  return Number(num).toFixed(decimals)
}

const fetchData = async () => {
  try {
    const network = globalNetworkFilter?.value === 'all' ? null : globalNetworkFilter?.value
    const purpose = globalPurposeFilter?.value === 'all' ? null : globalPurposeFilter?.value
    const [all, groups] = await Promise.all([
      dashboardApi.getAllRanking(activeTab.value, timeType.value, network, purpose),
      dashboardApi.getAllGroupRankings(activeTab.value, timeType.value, network, purpose)
    ])
    
    allRanking.value = all.slice(0, 5)
    groupRankings.value = groups
  } catch (error) {
    console.error('Failed to fetch right panel data:', error)
  }
}

const handleTitleClick = (subType, title, groupName) => {
  const params = { timeRange: activeTab.value }
  if (groupName) {
    params.groupName = groupName
  }
  showPanelExpand('right', subType, title, params)
}

const handleRankingItemClick = (item) => {
  if (item.org_id) {
    showOrgDetail(item.org_id, 'devices')
  }
}

watch(activeTab, fetchData)
watch(timeType, fetchData)
watch(() => globalNetworkFilter?.value, fetchData)
watch(() => globalPurposeFilter?.value, fetchData)

onMounted(fetchData)
</script>

<style lang="scss" scoped>
.right-panel-content {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.ranking-section {
  flex: 1;
  min-height: 0;
  
  .panel-content {
    height: calc(100% - 38px);
    overflow: hidden;
  }
  
  .ranking-list {
    display: flex;
    flex-direction: column;
    gap: 6px;
    height: 100%;
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
    
    .usage-value {
      font-size: 12px;
      font-weight: bold;
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
</style>
