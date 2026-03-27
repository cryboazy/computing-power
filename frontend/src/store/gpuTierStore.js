import { ref } from 'vue'
import axios from 'axios'
import {
  DEFAULT_TIER_NAMES,
  DEFAULT_TIER_KEYS,
  TIER_COLORS,
  updateTierConfig
} from '@/utils/gpuTierUtils'

const tierList = ref([])
const isLoading = ref(false)
const error = ref(null)

export async function loadTierList() {
  if (isLoading.value) return tierList.value

  isLoading.value = true
  error.value = null

  try {
    const response = await axios.get('/api/admin/dict/gpu-tier')
    tierList.value = response.data || []

    updateTierConfig(tierList.value)

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

export function getTierConfigForChart() {
  if (tierList.value.length === 0) {
    return {
      names: [...DEFAULT_TIER_NAMES],
      keys: [...DEFAULT_TIER_KEYS],
      colors: Object.values(TIER_COLORS)
    }
  }

  const names = tierList.value.map(t => t.dict_label)
  const keys = tierList.value.map(t => t.dict_label)
  names.push('未知')
  keys.push('未知')

  return {
    names,
    keys,
    colors: Object.values(TIER_COLORS)
  }
}

export default {
  tierList,
  isLoading,
  error,
  loadTierList,
  getTierList,
  getTierConfigForChart
}
