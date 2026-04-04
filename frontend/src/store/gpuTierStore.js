import { ref, computed } from 'vue'
import axios from 'axios'

const DEFAULT_TIER_CONFIG = {
  1: { label: '高端卡', key: 'high' },
  2: { label: '中端卡', key: 'medium' },
  3: { label: '低端卡', key: 'low' }
}

const DEFAULT_TIER_KEYS = ['high', 'medium', 'low', 'unknown']
const DEFAULT_TIER_NAMES = ['高端卡', '中端卡', '低端卡', '未知']

const tierList = ref([])
const isLoading = ref(false)
const error = ref(null)

const tierConfig = computed(() => {
  if (tierList.value.length === 0) {
    return { ...DEFAULT_TIER_CONFIG }
  }
  const config = {}
  tierList.value.forEach(item => {
    config[item.dict_value] = {
      label: item.dict_label,
      key: item.dict_label
    }
  })
  return config
})

const tierKeys = computed(() => {
  if (tierList.value.length === 0) {
    return [...DEFAULT_TIER_KEYS]
  }
  const keys = tierList.value.map(t => t.dict_label)
  keys.push('未知')
  return keys
})

const tierNames = computed(() => {
  if (tierList.value.length === 0) {
    return [...DEFAULT_TIER_NAMES]
  }
  const names = tierList.value.map(t => t.dict_label)
  names.push('未知')
  return names
})

export async function loadTierList() {
  if (isLoading.value) return tierList.value

  isLoading.value = true
  error.value = null

  try {
    const response = await axios.get('/api/admin/dict/gpu-tier')
    tierList.value = response.data || []
    return tierList.value
  } catch (err) {
    error.value = err.message
    console.error('加载GPU档次列表失败:', err)
    return []
  } finally {
    isLoading.value = false
  }
}

export function getTierList() {
  return tierList.value
}

export function getTierKeys() {
  return tierKeys.value
}

export function getTierNames() {
  return tierNames.value
}

export function getTierConfig() {
  return tierConfig.value
}

export function getTierKey(cardType) {
  const config = tierConfig.value[cardType]
  if (config) {
    return config.key
  }
  const defaultConfig = DEFAULT_TIER_CONFIG[cardType]
  return defaultConfig ? defaultConfig.key : 'unknown'
}

export function getTierLabel(cardType) {
  const config = tierConfig.value[cardType]
  if (config) {
    return config.label
  }
  const defaultConfig = DEFAULT_TIER_CONFIG[cardType]
  return defaultConfig ? defaultConfig.label : '未知'
}

export function getTierColors(themeColors) {
  return {
    high: themeColors.danger,
    medium: themeColors.warning,
    low: themeColors.success,
    unknown: themeColors.info
  }
}

export function getTierConfigForChart(themeColors) {
  const colors = themeColors 
    ? Object.values(getTierColors(themeColors))
    : [undefined, undefined, undefined, undefined]

  if (tierList.value.length === 0) {
    return {
      names: [...DEFAULT_TIER_NAMES],
      keys: [...DEFAULT_TIER_KEYS],
      colors
    }
  }

  const names = tierList.value.map(t => t.dict_label)
  const keys = tierList.value.map(t => t.dict_label)
  names.push('未知')
  keys.push('未知')

  return {
    names,
    keys,
    colors
  }
}

export function formatTierData(data, getTierLabelFn) {
  if (!data || !Array.isArray(data)) {
    return []
  }
  return data.map(item => ({
    name: item.name || (getTierLabelFn ? getTierLabelFn(item.value) : item.value),
    value: item.value || 0
  }))
}

export function extractTierCounts(data, keys) {
  if (!data) {
    return null
  }

  const result = {}

  keys.forEach(key => {
    result[key] = 0
  })

  if (Array.isArray(data)) {
    data.forEach(item => {
      if (item.name && result.hasOwnProperty(item.name)) {
        result[item.name] = item.value || 0
      }
    })
  }

  return result
}

export function calculateTierTotal(data) {
  if (!data || !Array.isArray(data)) {
    return 0
  }
  return data.reduce((sum, item) => sum + (item.value || 0), 0)
}

export default {
  tierList,
  isLoading,
  error,
  loadTierList,
  getTierList,
  getTierKeys,
  getTierNames,
  getTierConfig,
  getTierKey,
  getTierLabel,
  getTierColors,
  getTierConfigForChart,
  formatTierData,
  extractTierCounts,
  calculateTierTotal
}
