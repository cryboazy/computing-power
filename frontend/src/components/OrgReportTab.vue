<template>
  <div class="org-report-tab">
    <div v-if="loading" class="loading-container">
      <el-icon class="is-loading" :size="40"><Loading /></el-icon>
      <span>加载中...</span>
    </div>
    
    <div v-else-if="reports.length === 0" class="empty-state">
      <el-icon :size="48" color="var(--theme-text-muted)"><Document /></el-icon>
      <span>暂无分析报告</span>
    </div>
    
    <div v-else class="report-list-container">
      <el-table :data="reports" style="width: 100%" @row-click="viewReport">
        <el-table-column label="报告标题">
          <template #default="scope">
            <div class="report-title-cell">
              <el-icon class="report-icon"><Document /></el-icon>
              <span>{{ scope.row.title }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="上传日期" width="120">
          <template #default="scope">
            {{ formatDate(scope.row.create_time) }}
          </template>
        </el-table-column>
        <el-table-column label="大小" width="100">
          <template #default="scope">
            {{ formatFileSize(scope.row.file_size) }}
          </template>
        </el-table-column>
      </el-table>
    </div>
    
    <el-dialog
      v-model="reportDialogVisible"
      width="80%"
      top="5vh"
      :close-on-click-modal="false"
      :fullscreen="isReportMaximized"
      :show-close="false"
      class="report-detail-dialog"
      append-to-body
      @closed="handleReportDialogClosed"
    >
      <template #header>
        <div class="report-dialog-header">
          <div class="header-left">
            <div class="report-title">{{ selectedReport?.title || '报告详情' }}</div>
            <div class="report-meta" v-if="selectedReport">
              {{ selectedReport.org_name }} · {{ formatDate(selectedReport.create_time) }} · {{ formatFileSize(selectedReport.file_size) }}
            </div>
          </div>
          <div class="header-right">
            <button class="control-btn" @click="toggleReportMaximize" :title="isReportMaximized ? '还原' : '最大化'">
              <svg v-if="!isReportMaximized" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
              </svg>
              <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M8 3v3a2 2 0 0 1-2 2H3m18 0h-3a2 2 0 0 1-2-2V3m0 18v-3a2 2 0 0 1 2-2h3M3 16h3a2 2 0 0 1 2 2v3"></path>
              </svg>
            </button>
            <button class="control-btn close-btn" @click="reportDialogVisible = false" title="关闭">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
          </div>
        </div>
      </template>
      
      <div class="report-body-wrapper">
        <div v-if="reportLoading" class="loading-container">
          <el-icon class="is-loading" :size="32"><Loading /></el-icon>
          <span>加载报告内容...</span>
        </div>
        
        <div v-else-if="reportContent" class="markdown-content" v-html="renderedMarkdown"></div>
      </div>
      
      <template #footer>
        <el-button @click="reportDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { Loading, Document } from '@element-plus/icons-vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { reportApi } from '../api'

const props = defineProps({
  orgId: {
    type: [Number, String],
    required: true
  }
})

const loading = ref(false)
const reports = ref([])
const selectedReport = ref(null)
const reportDialogVisible = ref(false)
const reportLoading = ref(false)
const reportContent = ref('')
const isReportMaximized = ref(false)

const renderedMarkdown = computed(() => {
  if (!reportContent.value) return ''
  try {
    const rawHtml = marked(reportContent.value)
    return DOMPurify.sanitize(rawHtml)
  } catch (e) {
    console.error('Markdown render error:', e)
    return reportContent.value
  }
})

const fetchReports = async () => {
  if (!props.orgId) return
  
  loading.value = true
  try {
    const data = await reportApi.getOrgReports(props.orgId)
    reports.value = data || []
  } catch (error) {
    console.error('Failed to fetch reports:', error)
    reports.value = []
  } finally {
    loading.value = false
  }
}

const viewReport = async (row) => {
  selectedReport.value = row
  reportDialogVisible.value = true
  reportLoading.value = true
  reportContent.value = ''
  
  try {
    const data = await reportApi.getReportDetail(row.id)
    if (data.error) {
      reportContent.value = `# 加载失败\n\n${data.error}`
    } else {
      reportContent.value = data.content || '# 无内容'
      selectedReport.value = data
    }
  } catch (error) {
    console.error('Failed to fetch report detail:', error)
    reportContent.value = '# 加载失败\n\n请稍后重试'
  } finally {
    reportLoading.value = false
  }
}

const toggleReportMaximize = () => {
  isReportMaximized.value = !isReportMaximized.value
}

const handleReportDialogClosed = () => {
  selectedReport.value = null
  reportContent.value = ''
  isReportMaximized.value = false
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return dateStr.split(' ')[0]
}

const formatFileSize = (bytes) => {
  if (!bytes || bytes === 0) return '-'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

watch(() => props.orgId, () => {
  fetchReports()
}, { immediate: true })
</script>

<style lang="scss" scoped>
.org-report-tab {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.loading-container,
.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  color: var(--theme-text-secondary);
}

.report-list-container {
  flex: 1;
  overflow: auto;
  
  :deep(.el-table) {
    background: transparent;
    
    .el-table__header-wrapper th {
      background: var(--theme-hover-bg);
      color: var(--theme-text);
    }
    
    .el-table__body-wrapper tr {
      cursor: pointer;
      
      &:hover {
        background: var(--theme-hover-bg);
      }
    }
  }
}

.report-title-cell {
  display: flex;
  align-items: center;
  gap: 8px;
  
  .report-icon {
    color: var(--theme-primary);
  }
}

.report-detail-dialog {
  :deep(.el-dialog__header) {
    padding: 0;
    margin: 0;
  }
  
  :deep(.el-dialog__body) {
    padding: 0;
    max-height: calc(90vh - 120px);
    overflow: hidden;
    display: flex;
    flex-direction: column;
  }
  
  :deep(.el-dialog__footer) {
    padding: 12px 20px;
    border-top: 1px solid var(--theme-border);
  }
}

.report-body-wrapper {
  flex: 1;
  overflow: auto;
  padding: 0;
}

.report-dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: linear-gradient(90deg, 
    var(--theme-hover-bg) 0%, 
    var(--theme-shadow) 20%,
    var(--theme-shadow) 80%,
    var(--theme-hover-bg) 100%
  );
  border-bottom: 1px solid var(--theme-border);
  
  .header-left {
    display: flex;
    flex-direction: column;
    gap: 4px;
    
    .report-title {
      font-size: 18px;
      font-weight: 600;
      color: var(--theme-primary);
    }
    
    .report-meta {
      font-size: 12px;
      color: var(--theme-text-secondary);
    }
  }
  
  .header-right {
    display: flex;
    gap: 8px;
    
    .control-btn {
      width: 36px;
      height: 36px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: linear-gradient(135deg, var(--theme-hover-bg) 0%, var(--theme-shadow) 100%);
      border: 1px solid var(--theme-border-heavy);
      border-radius: 8px;
      cursor: pointer;
      transition: all 0.3s ease;
      
      svg {
        width: 16px;
        height: 16px;
        color: var(--theme-primary);
      }
      
      &:hover {
        border-color: var(--theme-primary);
        box-shadow: 0 0 15px var(--theme-glow);
      }
      
      &.close-btn:hover {
        border-color: var(--theme-danger);
        
        svg {
          color: var(--theme-danger);
        }
      }
    }
  }
}

.markdown-content {
  padding: 24px;
  line-height: 1.8;
  color: var(--theme-text);
  
  :deep(h1), :deep(h2), :deep(h3), :deep(h4), :deep(h5), :deep(h6) {
    margin-top: 24px;
    margin-bottom: 16px;
    font-weight: 600;
    color: var(--theme-primary);
  }
  
  :deep(h1) { font-size: 28px; border-bottom: 2px solid var(--theme-border); padding-bottom: 8px; }
  :deep(h2) { font-size: 24px; }
  :deep(h3) { font-size: 20px; }
  :deep(h4) { font-size: 18px; }
  :deep(h5) { font-size: 16px; }
  :deep(h6) { font-size: 14px; }
  
  :deep(p) {
    margin-bottom: 16px;
    line-height: 1.8;
  }
  
  :deep(ul), :deep(ol) {
    margin-bottom: 16px;
    padding-left: 24px;
    
    li {
      margin-bottom: 8px;
      line-height: 1.8;
    }
  }
  
  :deep(code) {
    background: var(--theme-hover-bg);
    padding: 2px 6px;
    border-radius: 4px;
    font-family: 'Consolas', 'Monaco', monospace;
    font-size: 0.9em;
  }
  
  :deep(pre) {
    background: var(--theme-hover-bg);
    padding: 16px;
    border-radius: 8px;
    overflow-x: auto;
    margin-bottom: 16px;
    
    code {
      background: none;
      padding: 0;
    }
  }
  
  :deep(blockquote) {
    border-left: 4px solid var(--theme-primary);
    padding-left: 16px;
    margin: 16px 0;
    color: var(--theme-text-secondary);
  }
  
  :deep(table) {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 16px;
    
    th, td {
      border: 1px solid var(--theme-border);
      padding: 12px;
      text-align: left;
    }
    
    th {
      background: var(--theme-hover-bg);
      font-weight: 600;
    }
  }
  
  :deep(hr) {
    border: none;
    border-top: 1px solid var(--theme-border);
    margin: 24px 0;
  }
  
  :deep(img) {
    max-width: 100%;
    height: auto;
  }
  
  :deep(a) {
    color: var(--theme-primary);
    text-decoration: none;
    
    &:hover {
      text-decoration: underline;
    }
  }
}
</style>