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
  getOverviewStats: (timeRange = 'month', timeType = 'work', network = null, purpose = null) => {
    const params = { time_range: timeRange, time_type: timeType }
    if (network) params.network = network
    if (purpose && purpose !== 'all') params.purpose = parseInt(purpose)
    return api.get('/overview/stats', { params })
  },
  
  getDeviceCountTrend: (timeRange = 'month', timeType = 'work', network = null) => {
    const params = { time_range: timeRange, time_type: timeType }
    if (network) params.network = network
    return api.get('/trend/device-count', { params })
  },
  
  getGpuCountTrend: (timeRange = 'month', timeType = 'work', network = null) => {
    const params = { time_range: timeRange, time_type: timeType }
    if (network) params.network = network
    return api.get('/trend/gpu-count', { params })
  },
  
  getMemoryTotalTrend: (timeRange = 'month', timeType = 'work', network = null) => {
    const params = { time_range: timeRange, time_type: timeType }
    if (network) params.network = network
    return api.get('/trend/memory-total', { params })
  },
  
  getComputeTotalTrend: (timeRange = 'month', timeType = 'work', network = null) => {
    const params = { time_range: timeRange, time_type: timeType }
    if (network) params.network = network
    return api.get('/trend/compute-total', { params })
  },
  
  getGpuUsageTrend: (timeRange = 'month', timeType = 'work', network = null, purpose = null) => {
    const params = { time_range: timeRange, time_type: timeType }
    if (network) params.network = network
    if (purpose && purpose !== 'all') params.purpose = parseInt(purpose)
    return api.get('/trend/gpu-usage', { params })
  },
  
  getUsageWarningBar: (timeRange = 'month', timeType = 'work', network = null, purpose = null) => {
    const params = { time_range: timeRange, time_type: timeType }
    if (network) params.network = network
    if (purpose && purpose !== 'all') params.purpose = parseInt(purpose)
    return api.get('/warning/usage-bar', { params })
  },
  
  getOrgGroups: () => api.get('/org/groups'),
  getOrgTypeDistribution: (timeType = 'work', network = null, purpose = null) => {
    const params = { time_type: timeType }
    if (network) params.network = network
    if (purpose && purpose !== 'all') params.purpose = parseInt(purpose)
    return api.get('/distribution/org-type', { params })
  },
  getNetworkDistribution: (network = null, purpose = null) => {
    const params = {}
    if (network) params.network = network
    if (purpose && purpose !== 'all') params.purpose = parseInt(purpose)
    return api.get('/distribution/network', { params })
  },
  getNetworkDistributionByOrg: (network = null, purpose = null) => {
    const params = {}
    if (network) params.network = network
    if (purpose && purpose !== 'all') params.purpose = parseInt(purpose)
    return api.get('/distribution/network-by-org', { params })
  },
  getNetworkList: () => api.get('/network/list'),
  getGpuTierDistribution: (network = null, purpose = null) => {
    const params = {}
    if (network) params.network = network
    if (purpose && purpose !== 'all') params.purpose = parseInt(purpose)
    return api.get('/distribution/gpu-tier', { params })
  },
  getGpuTierByOrgDistribution: (network = null, purpose = null) => {
    const params = {}
    if (network) params.network = network
    if (purpose && purpose !== 'all') params.purpose = parseInt(purpose)
    return api.get('/distribution/gpu-tier-by-org', { params })
  },
  getPurposeDistribution: (network = null, purpose = null) => {
    const params = {}
    if (network) params.network = network
    if (purpose && purpose !== 'all') params.purpose = parseInt(purpose)
    return api.get('/distribution/purpose', { params })
  },
  getPurposeDistributionByOrg: (network = null, purpose = null) => {
    const params = {}
    if (network) params.network = network
    if (purpose && purpose !== 'all') params.purpose = parseInt(purpose)
    return api.get('/distribution/purpose-by-org', { params })
  },
  getPurposeDict: () => api.get('/dict/purpose'),

  getProvinceDistribution: (timeType = 'work', network = null, purpose = null) => {
    const params = { time_type: timeType }
    if (network) params.network = network
    if (purpose && purpose !== 'all') params.purpose = parseInt(purpose)
    return api.get('/map/province', { params })
  },
  getLocalStats: (timeRange = 'month', timeType = 'work', network = null, purpose = null) => {
    const params = { time_range: timeRange, time_type: timeType }
    if (network) params.network = network
    if (purpose && purpose !== 'all') params.purpose = parseInt(purpose)
    return api.get('/local/stats', { params })
  },
  getLocalGpuTier: (network = null, purpose = null) => {
    const params = {}
    if (network) params.network = network
    if (purpose && purpose !== 'all') params.purpose = parseInt(purpose)
    return api.get('/local/gpu-tier', { params })
  },
  getLocalPurpose: (network = null, purpose = null) => {
    const params = {}
    if (network) params.network = network
    if (purpose && purpose !== 'all') params.purpose = parseInt(purpose)
    return api.get('/local/purpose', { params })
  },
  getLocalNetwork: (network = null, purpose = null) => {
    const params = {}
    if (network) params.network = network
    if (purpose && purpose !== 'all') params.purpose = parseInt(purpose)
    return api.get('/local/network', { params })
  },
  getLocalTrend: (timeRange = 'month', timeType = 'work', network = null) => {
    const params = { time_range: timeRange, time_type: timeType }
    if (network) params.network = network
    return api.get('/local/trend', { params })
  },
  getCentralBubble: (timeType = 'work', network = null, purpose = null) => {
    const params = { time_type: timeType }
    if (network) params.network = network
    if (purpose && purpose !== 'all') params.purpose = parseInt(purpose)
    return api.get('/bubble/central', { params })
  },
  getCentralStats: (timeRange = 'month', timeType = 'work', network = null, purpose = null) => {
    const params = { time_range: timeRange, time_type: timeType }
    if (network) params.network = network
    if (purpose && purpose !== 'all') params.purpose = parseInt(purpose)
    return api.get('/central/stats', { params })
  },
  getCentralGpuTier: (network = null, purpose = null) => {
    const params = {}
    if (network) params.network = network
    if (purpose && purpose !== 'all') params.purpose = parseInt(purpose)
    return api.get('/central/gpu-tier', { params })
  },
  getCentralPurpose: (network = null, purpose = null) => {
    const params = {}
    if (network) params.network = network
    if (purpose && purpose !== 'all') params.purpose = parseInt(purpose)
    return api.get('/central/purpose', { params })
  },
  getCentralTrend: (timeRange = 'month', timeType = 'work', network = null) => {
    const params = { time_range: timeRange, time_type: timeType }
    if (network) params.network = network
    return api.get('/central/trend', { params })
  },
  
  getAllRanking: (timeRange = 'month', timeType = 'work', network = null, purpose = null) => {
    const params = { time_range: timeRange, time_type: timeType }
    if (network) params.network = network
    if (purpose && purpose !== 'all') params.purpose = parseInt(purpose)
    return api.get('/ranking/all', { params })
  },
  getGroupRanking: (groupId, timeRange = 'month', timeType = 'work', network = null, purpose = null) => {
    const params = { time_range: timeRange, time_type: timeType }
    if (network) params.network = network
    if (purpose && purpose !== 'all') params.purpose = parseInt(purpose)
    return api.get(`/ranking/group/${groupId}`, { params })
  },
  getAllGroupRankings: (timeRange = 'month', timeType = 'work', network = null, purpose = null) => {
    const params = { time_range: timeRange, time_type: timeType }
    if (network) params.network = network
    if (purpose && purpose !== 'all') params.purpose = parseInt(purpose)
    return api.get('/ranking/groups', { params })
  },
  getLocalRanking: (timeRange = 'month', timeType = 'work', purpose = null) => {
    const params = { time_range: timeRange, time_type: timeType }
    if (purpose && purpose !== 'all') params.purpose = parseInt(purpose)
    return api.get('/ranking/local', { params })
  },
  getCentralRanking: (timeRange = 'month', timeType = 'work', purpose = null) => {
    const params = { time_range: timeRange, time_type: timeType }
    if (purpose && purpose !== 'all') params.purpose = parseInt(purpose)
    return api.get('/ranking/central', { params })
  },
  getProvinceRanking: (provinceName, timeRange = 'month', timeType = 'work', purpose = null) => {
    const params = { time_range: timeRange, time_type: timeType }
    if (purpose && purpose !== 'all') params.purpose = parseInt(purpose)
    return api.get(`/ranking/province/${encodeURIComponent(provinceName)}`, { params })
  },
  
  getCarouselUsageTrend: (timeType = 'work', orgType = null, orgName = null, timeGrain = 'day', startDate = null, endDate = null, drillDate = null, drillOrgId = null, network = null, purpose = null) => {
    const params = { time_type: timeType }
    if (orgType) params.org_type = orgType
    if (orgName) params.org_name = orgName
    if (timeGrain) params.time_grain = timeGrain
    if (startDate) params.start_date = startDate
    if (endDate) params.end_date = endDate
    if (drillDate) params.drill_date = drillDate
    if (drillOrgId) params.drill_org_id = drillOrgId
    if (network) params.network = network
    if (purpose && purpose !== 'all') params.purpose = parseInt(purpose)
    return api.get('/carousel/usage-trend', { params })
  },
  
  getOrgDetail: (orgId, timeRange = 'month', timeType = 'work') => {
    const params = { time_range: timeRange, time_type: timeType }
    return api.get(`/org/detail/${orgId}`, { params })
  },
  getOrgUsageTrend: (orgId, timeType = 'all', startDate = null, endDate = null, purpose = null, network = null) => {
    const params = { time_type: timeType }
    if (startDate) params.start_date = startDate
    if (endDate) params.end_date = endDate
    if (purpose) params.purpose = purpose
    if (network) params.network = network
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

export const adminApi = {
  getGpuTierDict: () => api.get('/admin/dict/gpu-tier'),
  createGpuTier: (data) => api.post('/admin/dict/gpu-tier', data),
  updateGpuTier: (id, data) => api.put(`/admin/dict/gpu-tier/${id}`, data),
  deleteGpuTier: (id) => api.delete(`/admin/dict/gpu-tier/${id}`),
  updateGpuTierStatus: (id, status) => api.patch(`/admin/dict/gpu-tier/${id}/status`, { status })
}

export const exportApi = {
  getUsageData: (startDate, endDate) => api.post('/admin/export/usage-data', {
    start_date: startDate,
    end_date: endDate
  })
}

export const reportApi = {
  getOrgReports: (orgId) => api.get(`/org/${orgId}/reports`),
  getReportDetail: (reportId) => api.get(`/reports/${reportId}`),
  getAdminReports: (params) => api.get('/admin/reports', { params }),
  createReport: (data) => api.post('/admin/reports', data),
  updateReport: (id, data) => api.put(`/admin/reports/${id}`, data),
  deleteReport: (id) => api.delete(`/admin/reports/${id}`),
  batchDeleteReports: (ids) => api.post('/admin/reports/batch-delete', { ids }),
  getOrganizations: () => api.get('/admin/organizations')
}

export default api
