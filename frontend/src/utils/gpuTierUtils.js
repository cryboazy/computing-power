export const DEFAULT_TIER_CONFIG = {
  1: { label: '高端卡', key: 'high' },
  2: { label: '中端卡', key: 'medium' },
  3: { label: '低端卡', key: 'low' }
}

export const DEFAULT_TIER_KEYS = ['high', 'medium', 'low', 'unknown']

export const DEFAULT_TIER_NAMES = ['高端卡', '中端卡', '低端卡', '未知']

export const TIER_COLORS = {
  high: '#f56c6c',
  medium: '#e6a23c',
  low: '#67c23a',
  unknown: '#909399'
}

let tierConfig = { ...DEFAULT_TIER_CONFIG }
let tierKeys = [...DEFAULT_TIER_KEYS]
let tierNames = [...DEFAULT_TIER_NAMES]

export function updateTierConfig(config) {
  if (!config || !Array.isArray(config)) {
    tierConfig = { ...DEFAULT_TIER_CONFIG }
    tierKeys = [...DEFAULT_TIER_KEYS]
    tierNames = [...DEFAULT_TIER_NAMES]
    return
  }

  tierConfig = {}
  tierKeys = []
  tierNames = []

  config.forEach(item => {
    tierConfig[item.dict_value] = {
      label: item.dict_label,
      key: item.dict_label
    }
    tierKeys.push(item.dict_label)
    tierNames.push(item.dict_label)
  })

  tierKeys.push('unknown')
  tierNames.push('未知')
}

export function getTierKeys() {
  return tierKeys
}

export function getTierNames() {
  return tierNames
}

export function getTierConfig() {
  return { ...tierConfig }
}

export function getTierKey(cardType) {
  const config = tierConfig[cardType]
  if (config) {
    return config.key
  }
  const defaultConfig = DEFAULT_TIER_CONFIG[cardType]
  return defaultConfig ? defaultConfig.key : 'unknown'
}

export function getTierLabel(cardType) {
  const config = tierConfig[cardType]
  if (config) {
    return config.label
  }
  const defaultConfig = DEFAULT_TIER_CONFIG[cardType]
  return defaultConfig ? defaultConfig.label : '未知'
}

export function formatTierData(data) {
  if (!data || !Array.isArray(data)) {
    return []
  }
  return data.map(item => ({
    name: item.name || getTierLabel(item.value),
    value: item.value || 0
  }))
}

export function extractTierCounts(data, keys = null) {
  if (!data) {
    return null
  }

  const currentTierKeys = keys || getTierKeys()
  const result = {}

  currentTierKeys.forEach(key => {
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
