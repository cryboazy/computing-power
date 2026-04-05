import { ref, computed } from 'vue'
import axios from 'axios'

const tierList = ref([])
const isLoading = ref(false)
const error = ref(null)

const tierConfig = computed(() => {
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
  const keys = tierList.value.map(t => t.dict_label)
  keys.push('未知')
  return keys
})

const tierNames = computed(() => {
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
    const data = response.data || []
    tierList.value = data.filter(t => t.status === 1)
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
  return config ? config.key : '未知'
}

export function getTierLabel(cardType) {
  const config = tierConfig.value[cardType]
  return config ? config.label : '未知'
}

export function getTierColors(themeColors) {
  const tierColorKeys = ['danger', 'warning', 'success', 'primary', 'secondary']
  const result = {}
  tierList.value.forEach((t, i) => {
    const colorKey = tierColorKeys[i % tierColorKeys.length]
    result[t.dict_label] = themeColors[colorKey]
  })
  result['未知'] = themeColors.info
  return result
}

export function getTierConfigForChart(themeColors) {
  const tierColors = getTierColors(themeColors)
  const colors = tierList.value.map(t => tierColors[t.dict_label])
  colors.push(tierColors['未知'])

  const names = []
  const keys = []
  tierList.value.forEach(t => {
    names.push(t.dict_label)
    keys.push(t.dict_label)
  })
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

export function isTierLoaded() {
  return tierList.value.length > 0
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
  calculateTierTotal,
  isTierLoaded
}
