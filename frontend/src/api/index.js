import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000
})

api.interceptors.response.use(
  response => response.data,
  error => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

export const dashboardApi = {
  getOverviewStats: (timeRange = 'month', timeType = 'work') => 
    api.get('/overview/stats', { params: { time_range: timeRange, time_type: timeType } }),
  
  getDeviceCountTrend: (timeRange = 'month', timeType = 'work') => 
    api.get('/trend/device-count', { params: { time_range: timeRange, time_type: timeType } }),
  
  getMemoryTotalTrend: (timeRange = 'month', timeType = 'work') => 
    api.get('/trend/memory-total', { params: { time_range: timeRange, time_type: timeType } }),
  
  getComputeTotalTrend: (timeRange = 'month', timeType = 'work') => 
    api.get('/trend/compute-total', { params: { time_range: timeRange, time_type: timeType } }),
  
  getGpuUsageTrend: (timeRange = 'month', timeType = 'work') => 
    api.get('/trend/gpu-usage', { params: { time_range: timeRange, time_type: timeType } }),
  
  getUsageWarningBar: (timeRange = 'month', timeType = 'work') => 
    api.get('/warning/usage-bar', { params: { time_range: timeRange, time_type: timeType } }),
  
  getOrgGroups: () => api.get('/org/groups'),
  getOrgTypeDistribution: (timeType = 'work') => api.get('/distribution/org-type', { params: { time_type: timeType } }),
  getNetworkDistribution: () => api.get('/distribution/network'),
  getNetworkDistributionByOrg: () => api.get('/distribution/network-by-org'),
  getGpuTierDistribution: () => api.get('/distribution/gpu-tier'),
  getGpuTierByOrgDistribution: () => api.get('/distribution/gpu-tier-by-org'),
  getPurposeDistribution: () => api.get('/distribution/purpose'),
  getPurposeDistributionByOrg: () => api.get('/distribution/purpose-by-org'),
  getPurposeDict: () => api.get('/dict/purpose'),
  
  getProvinceDistribution: (timeType = 'work') => api.get('/map/province', { params: { time_type: timeType } }),
  getLocalStats: (timeRange = 'month', timeType = 'work') => 
    api.get('/local/stats', { params: { time_range: timeRange, time_type: timeType } }),
  getLocalGpuTier: () => api.get('/local/gpu-tier'),
  getLocalPurpose: () => api.get('/local/purpose'),
  getLocalTrend: (timeType = 'work') => api.get('/local/trend', { params: { time_type: timeType } }),
  getCentralBubble: (timeType = 'work') => api.get('/bubble/central', { params: { time_type: timeType } }),
  getCentralStats: (timeRange = 'month', timeType = 'work') => 
    api.get('/central/stats', { params: { time_range: timeRange, time_type: timeType } }),
  getCentralGpuTier: () => api.get('/central/gpu-tier'),
  getCentralPurpose: () => api.get('/central/purpose'),
  getCentralTrend: (timeType = 'work') => api.get('/central/trend', { params: { time_type: timeType } }),
  
  getAllRanking: (timeRange = 'month', timeType = 'work') => 
    api.get('/ranking/all', { params: { time_range: timeRange, time_type: timeType } }),
  getGroupRanking: (groupId, timeRange = 'month', timeType = 'work') => 
    api.get(`/ranking/group/${groupId}`, { params: { time_range: timeRange, time_type: timeType } }),
  getAllGroupRankings: (timeRange = 'month', timeType = 'work') => 
    api.get('/ranking/groups', { params: { time_range: timeRange, time_type: timeType } }),
  getLocalRanking: (timeRange = 'month', timeType = 'work') => 
    api.get('/ranking/local', { params: { time_range: timeRange, time_type: timeType } }),
  getCentralRanking: (timeRange = 'month', timeType = 'work') => 
    api.get('/ranking/central', { params: { time_range: timeRange, time_type: timeType } }),
  getProvinceRanking: (provinceName, timeRange = 'month', timeType = 'work') => 
    api.get(`/ranking/province/${encodeURIComponent(provinceName)}`, { params: { time_range: timeRange, time_type: timeType } }),
  
  getCarouselUsageTrend: (timeType = 'work', orgType = null, orgName = null, timeGrain = 'day', startDate = null, endDate = null, drillDate = null, drillOrgId = null) => {
    const params = { time_type: timeType }
    if (orgType) params.org_type = orgType
    if (orgName) params.org_name = orgName
    if (timeGrain) params.time_grain = timeGrain
    if (startDate) params.start_date = startDate
    if (endDate) params.end_date = endDate
    if (drillDate) params.drill_date = drillDate
    if (drillOrgId) params.drill_org_id = drillOrgId
    return api.get('/carousel/usage-trend', { params })
  },
  
  getOrgDetail: (orgId, timeRange = 'month', timeType = 'work') => {
    const params = { time_range: timeRange, time_type: timeType }
    return api.get(`/org/detail/${orgId}`, { params })
  },
  getOrgUsageTrend: (orgId, timeType = 'all', startDate = null, endDate = null, purpose = null) => {
    const params = { time_type: timeType }
    if (startDate) params.start_date = startDate
    if (endDate) params.end_date = endDate
    if (purpose) params.purpose = purpose
    return api.get(`/org/usage-trend/${orgId}`, { params })
  },
  getOrgDistribution: (orgId) => api.get(`/org/distribution/${orgId}`),
  
  getDeviceUsageTrend: (deviceId, timeType = 'all', startDate = null, endDate = null) => {
    const params = { time_type: timeType }
    if (startDate) params.start_date = startDate
    if (endDate) params.end_date = endDate
    return api.get(`/device/usage-trend/${deviceId}`, { params })
  }
}

export default api
