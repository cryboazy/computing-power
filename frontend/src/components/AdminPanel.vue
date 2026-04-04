<template>
  <div class="admin-panel">
    <el-tabs v-model="activeTab" class="admin-tabs">
      <el-tab-pane label="系统配置" name="system">
        <div class="panel-section">
          <div class="section-content">
            <div class="config-item">
              <label>工作时段开始时间</label>
              <el-input-number v-model="config.work_hour_start" :min="0" :max="23" />
              <span class="unit">时</span>
            </div>
            <div class="config-item">
              <label>工作时段结束时间</label>
              <el-input-number v-model="config.work_hour_end" :min="0" :max="23" />
              <span class="unit">时</span>
            </div>
            <div class="config-item">
              <label>高使用率阈值</label>
              <el-input-number v-model="config.high_usage_threshold" :min="0" :max="100" :precision="1" />
              <span class="unit">%</span>
            </div>
            <div class="config-item">
              <label>低使用率阈值</label>
              <el-input-number v-model="config.low_usage_threshold" :min="0" :max="100" :precision="1" />
              <span class="unit">%</span>
            </div>
            <el-button type="primary" @click="saveConfig" :loading="configLoading">
              保存配置
            </el-button>
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="数据聚合" name="aggregation">
        <div class="panel-section">
          <div class="section-content">
            <div class="status-info">
              <div class="status-item">
                <span class="status-label">日汇总记录:</span>
                <span class="status-value">{{ aggregationStatus.daily_summary_count }}</span>
              </div>
              <div class="status-item">
                <span class="status-label">设备汇总记录:</span>
                <span class="status-value">{{ aggregationStatus.device_summary_count }}</span>
              </div>
              <div class="status-item">
                <span class="status-label">组织汇总记录:</span>
                <span class="status-value">{{ aggregationStatus.org_summary_count }}</span>
              </div>
              <div class="status-item">
                <span class="status-label">统计数据记录:</span>
                <span class="status-value">{{ aggregationStatus.statistics_count }}</span>
              </div>
              <div class="status-item">
                <span class="status-label">组织小时数据:</span>
                <span class="status-value">{{ aggregationStatus.org_hourly_count }}</span>
              </div>
              <div class="status-item">
                <span class="status-label">最近聚合时间:</span>
                <span class="status-value">{{ aggregationStatus.latest_aggregation_time || '无' }}</span>
              </div>
            </div>
            <div class="scheduled-config">
              <div class="scheduled-config-header">
                <span class="config-title">定时更新配置</span>
                <el-switch v-model="config.auto_aggregation_enabled" @change="saveConfig" />
              </div>
              <div class="scheduled-config-body" v-if="config.auto_aggregation_enabled">
                <div class="scheduled-time">
                  <span class="time-label">每天执行时间:</span>
                  <el-input-number v-model="config.auto_aggregation_hour" :min="0" :max="23" @change="saveConfig" />
                  <span class="time-separator">:</span>
                  <el-input-number v-model="config.auto_aggregation_minute" :min="0" :max="59" @change="saveConfig" />
                  <span class="time-hint">(时:分)</span>
                </div>
              </div>
            </div>
            <div class="action-buttons">
              <div class="action-row">
                <el-radio-group v-model="aggregationMode" @change="resetRefreshDays">
                  <el-radio-button value="days">按天数</el-radio-button>
                  <el-radio-button value="dateRange">按时间段</el-radio-button>
                </el-radio-group>
              </div>
              <div class="action-row" v-if="aggregationMode === 'days'">
                <el-input-number v-model="refreshDays" :min="1" :max="365" />
                <span class="action-label">天</span>
                <el-button type="primary" @click="refreshAggregation" :loading="refreshLoading"
                  :disabled="refreshLoading">
                  刷新聚合数据
                </el-button>
              </div>
              <div class="action-row" v-else>
                <el-date-picker
                  v-model="dateRange"
                  type="daterange"
                  range-separator="至"
                  start-placeholder="开始日期"
                  end-placeholder="结束日期"
                  :picker-options="pickerOptions"
                  style="width: 240px"
                />
                <el-button type="primary" @click="refreshAggregationByDateRange" :loading="refreshLoading"
                  :disabled="refreshLoading || !dateRange || dateRange.length !== 2">
                  刷新聚合数据
                </el-button>
              </div>
              <div v-if="refreshProgress.show" class="progress-container">
                <div class="progress-header">
                  <span>进度: {{ refreshProgress.day }}/{{ refreshProgress.totalDays }} 天</span>
                  <span>{{ refreshProgress.percent }}%</span>
                </div>
                <el-progress :percentage="refreshProgress.percent" :stroke-width="12" :show-text="false" />
                <div class="progress-task">{{ refreshProgress.currentTask }}</div>
                <el-button v-if="refreshLoading" type="warning" size="small" @click="cancelCurrentTask" style="margin-top: 10px;">
                  取消任务
                </el-button>
              </div>
              <div v-if="recentTasks.length > 0" class="recent-tasks">
                <div class="recent-tasks-header">最近任务</div>
                <div v-for="task in recentTasks" :key="task.task_id" class="recent-task-item">
                  <div class="task-info">
                    <span class="task-status" :class="task.status">{{ getStatusText(task.status) }}</span>
                    <span class="task-time">{{ formatTaskTime(task.create_time) }}</span>
                  </div>
                  <div class="task-detail">
                    <span>{{ task.total_days }}天</span>
                    <span v-if="task.status === 'completed'">{{ task.progress }}%</span>
                    <span v-else-if="task.status === 'failed'" class="error-text">{{ task.error_message }}</span>
                  </div>
                </div>
              </div>
              <div class="action-row">
                <el-button type="danger" @click="resetAggregation" :loading="resetLoading">
                  重置聚合数据
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="设备用途管理" name="purpose">
        <div class="panel-section">
          <div class="section-content">
            <div class="purpose-header">
              <el-button type="primary" @click="openAddPurposeDialog">
                添加设备用途
              </el-button>
            </div>
            <el-table :data="purposeList" style="width: 100%" border>
              <el-table-column prop="dict_value" label="值" width="100" />
              <el-table-column prop="dict_label" label="标签" />
              <el-table-column prop="dict_sort" label="排序" width="100" />
              <el-table-column prop="status" label="状态" width="100">
                <template #default="scope">
                  <el-switch v-model="scope.row.status" @change="updatePurposeStatus(scope.row)" :active-value="1"
                    :inactive-value="0" />
                </template>
              </el-table-column>
              <el-table-column label="操作" width="150" fixed="right">
                <template #default="scope">
                  <el-button size="small" @click="openEditPurposeDialog(scope.row)">
                    编辑
                  </el-button>
                  <el-button size="small" type="danger" @click="deletePurpose(scope.row.id)">
                    删除
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="GPU档次管理" name="gpu-tier">
        <div class="panel-section">
          <div class="section-content">
            <div class="tier-header">
              <el-button type="primary" @click="openAddTierDialog">
                添加档次
              </el-button>
              <el-button @click="batchDeleteTier" :disabled="selectedTiers.length === 0">
                批量删除
              </el-button>
            </div>
            <el-table :data="tierList" style="width: 100%" border @selection-change="handleTierSelection">
              <el-table-column type="selection" width="55" />
              <el-table-column prop="dict_value" label="档次值" width="100">
                <template #default="scope">
                  <el-tag type="info">{{ scope.row.dict_value }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="dict_label" label="档次名称" />
              <el-table-column prop="dict_sort" label="排序" width="100" />
              <el-table-column prop="status" label="状态" width="100">
                <template #default="scope">
                  <el-switch v-model="scope.row.status" @change="updateTierStatus(scope.row)" :active-value="1"
                    :inactive-value="0" />
                </template>
              </el-table-column>
              <el-table-column label="操作" width="200" fixed="right">
                <template #default="scope">
                  <el-button size="small" @click="openEditTierDialog(scope.row)">
                    编辑
                  </el-button>
                  <el-button size="small" type="danger" @click="deleteTier(scope.row.id)">
                    删除
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="密码管理" name="password">
        <div class="panel-section">
          <div class="section-content">
            <div class="password-form">
              <div class="form-item">
                <label>原密码</label>
                <el-input v-model="passwordForm.old_password" type="password" show-password placeholder="请输入原密码" />
              </div>
              <div class="form-item">
                <label>新密码</label>
                <el-input v-model="passwordForm.new_password" type="password" show-password
                  placeholder="请输入新密码(至少6位)" />
              </div>
              <div class="form-item">
                <label>确认新密码</label>
                <el-input v-model="passwordForm.confirm_password" type="password" show-password
                  placeholder="请再次输入新密码" />
              </div>
              <el-button type="primary" @click="changePassword" :loading="passwordLoading">
                修改密码
              </el-button>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="数据库状态" name="database">
        <div class="panel-section">
          <div class="section-content">
            <div class="database-header">
              <el-button type="primary" @click="refreshDatabaseStatus" :loading="dbStatusLoading">
                刷新状态
              </el-button>
              <el-button @click="testDatabaseConnection" :loading="dbTestLoading">
                测试连接
              </el-button>
            </div>
            
            <div class="database-section">
              <div class="section-title">
                <span class="title-icon main-db"></span>
                主数据库 (远程)
                <el-tag :type="dbStatus.main_database?.status === 'connected' ? 'success' : 'danger'" size="small">
                  {{ dbStatus.main_database?.status === 'connected' ? '已连接' : '未连接' }}
                </el-tag>
              </div>
              <div class="db-info-grid" v-if="dbStatus.main_database">
                <div class="db-info-item">
                  <span class="info-label">主机地址</span>
                  <span class="info-value">{{ dbStatus.main_database.host || '-' }}</span>
                </div>
                <div class="db-info-item">
                  <span class="info-label">端口</span>
                  <span class="info-value">{{ dbStatus.main_database.port || '-' }}</span>
                </div>
                <div class="db-info-item">
                  <span class="info-label">数据库名</span>
                  <span class="info-value">{{ dbStatus.main_database.database || '-' }}</span>
                </div>
                <div class="db-info-item" v-if="dbStatus.main_database.connection_pool">
                  <span class="info-label">连接池状态</span>
                  <span class="info-value">
                    {{ dbStatus.main_database.connection_pool.checked_out }}/{{ dbStatus.main_database.connection_pool.size }} 使用中
                    <span class="pool-detail">(溢出: {{ dbStatus.main_database.connection_pool.overflow }})</span>
                  </span>
                </div>
                <div class="db-info-item full-width" v-if="dbStatus.main_database.error">
                  <span class="info-label error">错误信息</span>
                  <span class="info-value error">{{ dbStatus.main_database.error }}</span>
                </div>
              </div>
            </div>

            <div class="database-section">
              <div class="section-title">
                <span class="title-icon local-db"></span>
                本地缓存数据库 (SQLite)
                <el-tag :type="dbStatus.local_database?.status === 'connected' ? 'success' : 'danger'" size="small">
                  {{ dbStatus.local_database?.status === 'connected' ? '已连接' : '未连接' }}
                </el-tag>
              </div>
              <div class="db-info-grid" v-if="dbStatus.local_database">
                <div class="db-info-item">
                  <span class="info-label">文件路径</span>
                  <span class="info-value path">{{ dbStatus.local_database.path || '-' }}</span>
                </div>
                <div class="db-info-item">
                  <span class="info-label">文件大小</span>
                  <span class="info-value">{{ dbStatus.local_database.size_human || '0 Bytes' }}</span>
                </div>
                <div class="db-info-item" v-if="dbStatus.local_database.sqlite_info">
                  <span class="info-label">日志模式</span>
                  <span class="info-value">{{ dbStatus.local_database.sqlite_info.journal_mode }}</span>
                </div>
                <div class="db-info-item" v-if="dbStatus.local_database.sqlite_info">
                  <span class="info-label">同步模式</span>
                  <span class="info-value">{{ dbStatus.local_database.sqlite_info.synchronous }}</span>
                </div>
                <div class="db-info-item full-width" v-if="dbStatus.local_database.error">
                  <span class="info-label error">错误信息</span>
                  <span class="info-value error">{{ dbStatus.local_database.error }}</span>
                </div>
              </div>
              
              <div class="tables-section" v-if="dbStatus.local_database?.tables">
                <div class="tables-title">数据表统计</div>
                <div class="tables-grid">
                  <div class="table-item" v-for="(table, tableName) in dbStatus.local_database.tables" :key="tableName">
                    <span class="table-name">{{ table.display_name }}</span>
                    <span class="table-count">{{ formatNumber(table.count) }} 条</span>
                  </div>
                </div>
              </div>
            </div>

            <div class="database-section" v-if="dbStatus.cache_status && dbStatus.cache_status.length > 0">
              <div class="section-title">
                <span class="title-icon cache"></span>
                缓存同步状态
              </div>
              <el-table :data="dbStatus.cache_status" style="width: 100%" border size="small">
                <el-table-column prop="cache_name" label="缓存名称" width="150" />
                <el-table-column prop="record_count" label="记录数" width="100">
                  <template #default="scope">
                    {{ formatNumber(scope.row.record_count) }}
                  </template>
                </el-table-column>
                <el-table-column prop="last_sync_time" label="最后同步时间">
                  <template #default="scope">
                    {{ scope.row.last_sync_time ? formatDateTime(scope.row.last_sync_time) : '-' }}
                  </template>
                </el-table-column>
                <el-table-column prop="status" label="状态" width="100">
                  <template #default="scope">
                    <el-tag :type="scope.row.status === 'success' ? 'success' : 'danger'" size="small">
                      {{ scope.row.status === 'success' ? '成功' : '失败' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="error_message" label="错误信息">
                  <template #default="scope">
                    <span v-if="scope.row.error_message" class="error-text">{{ scope.row.error_message }}</span>
                    <span v-else>-</span>
                  </template>
                </el-table-column>
              </el-table>
            </div>

            <div class="database-section" v-if="connectionTest.main_database || connectionTest.local_database">
              <div class="section-title">
                <span class="title-icon test"></span>
                连接测试结果
              </div>
              <div class="test-results">
                <div class="test-item" v-if="connectionTest.main_database">
                  <span class="test-label">主数据库</span>
                  <el-tag :type="connectionTest.main_database.success ? 'success' : 'danger'" size="small">
                    {{ connectionTest.main_database.success ? '连接成功' : '连接失败' }}
                  </el-tag>
                  <span v-if="connectionTest.main_database.latency_ms" class="latency">
                    延迟: {{ connectionTest.main_database.latency_ms }} ms
                  </span>
                  <span v-if="connectionTest.main_database.error" class="error-text">
                    {{ connectionTest.main_database.error }}
                  </span>
                </div>
                <div class="test-item" v-if="connectionTest.local_database">
                  <span class="test-label">本地数据库</span>
                  <el-tag :type="connectionTest.local_database.success ? 'success' : 'danger'" size="small">
                    {{ connectionTest.local_database.success ? '连接成功' : '连接失败' }}
                  </el-tag>
                  <span v-if="connectionTest.local_database.latency_ms" class="latency">
                    延迟: {{ connectionTest.local_database.latency_ms }} ms
                  </span>
                  <span v-if="connectionTest.local_database.error" class="error-text">
                    {{ connectionTest.local_database.error }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="数据导出" name="export">
        <div class="panel-section">
          <div class="section-content">
            <div class="export-header">
              <div class="export-date-range">
                <span class="export-label">导出日期范围:</span>
                <el-date-picker
                  v-model="exportDateRange"
                  type="daterange"
                  range-separator="至"
                  start-placeholder="开始日期"
                  end-placeholder="结束日期"
                  :disabled-date="disabledExportDate"
                  style="width: 280px"
                />
              </div>
              <el-button 
                type="primary" 
                @click="handleExportData" 
                :loading="exportLoading"
                :disabled="!exportDateRange || exportDateRange.length !== 2"
              >
                <el-icon class="el-icon--left"><Download /></el-icon>
                导出Excel
              </el-button>
            </div>
            
            <div class="export-info">
              <div class="info-title">导出说明</div>
              <ul class="info-list">
                <li>数据将按照组织机构、设备用途、运行网络、时间类型进行分类汇总</li>
                <li>静态数据（设备数、GPU数、总算力、显存总量）取时间区间最后一天的数据</li>
                <li>使用率数据为区间内日均值的平均值，与大屏显示数据一致</li>
                <li>总算力采用 FP16 精度计算</li>
                <li>日期范围最大不超过365天</li>
              </ul>
            </div>

            <div v-if="exportProgress.show" class="export-progress">
              <el-progress :percentage="exportProgress.percent" :status="exportProgress.status" />
              <span class="progress-text">{{ exportProgress.text }}</span>
            </div>

            <div v-if="exportResult.total > 0" class="export-result">
              <div class="result-header">
                <span class="result-title">导出结果预览</span>
                <span class="result-count">共 {{ exportResult.total }} 条数据</span>
              </div>
              <el-table 
                :data="exportResult.data.slice(0, 10)" 
                style="width: 100%" 
                border 
                size="small"
                max-height="300"
              >
                <el-table-column prop="组织机构名称" label="组织机构" width="150" show-overflow-tooltip />
                <el-table-column prop="实际起始日期" label="实际起始" width="100" />
                <el-table-column prop="实际结束日期" label="实际结束" width="100" />
                <el-table-column prop="设备用途" label="设备用途" width="100" />
                <el-table-column prop="运行网络" label="运行网络" width="100" />
                <el-table-column prop="时间类型" label="时间类型" width="100" />
                <el-table-column prop="设备数" label="设备数" width="80" />
                <el-table-column prop="GPU数" label="GPU数" width="80" />
                <el-table-column prop="总算力" label="总算力(TF)" width="100" />
                <el-table-column prop="显存总量(GB)" label="显存(GB)" width="100" />
                <el-table-column prop="平均GPU使用率(%)" label="GPU使用率(%)" width="110" />
                <el-table-column prop="平均显存使用率(%)" label="显存使用率(%)" width="120" />
                <el-table-column prop="平均显存利用率(%)" label="显存利用率(%)" width="120" />
              </el-table>
              <div v-if="exportResult.total > 10" class="result-hint">
                仅显示前10条数据，完整数据已导出到Excel文件
              </div>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="报告管理" name="reports">
        <div class="panel-section">
          <div class="section-content">
            <div class="report-upload-section">
              <div class="section-title">上传报告</div>
              <div class="upload-form">
                <div class="form-row">
                  <div class="form-item">
                    <label>组织单位：</label>
                    <el-tree-select
                      v-model="reportForm.org_id"
                      :data="organizationTree"
                      :props="{ label: 'name', value: 'id', children: 'children' }"
                      placeholder="选择组织单位"
                      filterable
                      check-strictly
                      style="width: 300px"
                    />
                  </div>
                  <div class="form-item">
                    <label>报告标题：</label>
                    <el-input v-model="reportForm.title" placeholder="输入报告标题" style="width: 300px" />
                  </div>
                </div>
                <div class="form-row">
                  <el-upload
                    ref="uploadRef"
                    :auto-upload="false"
                    :show-file-list="true"
                    :limit="1"
                    accept=".md,.markdown"
                    :on-change="handleReportFileChange"
                    :on-exceed="handleExceed"
                  >
                    <template #trigger>
                      <el-button type="primary">
                        <el-icon class="el-icon--left"><Upload /></el-icon>
                        选择文件
                      </el-button>
                    </template>
                    <el-button class="ml-3" type="success" @click="uploadReport" :loading="uploadLoading" :disabled="!reportForm.org_id || !reportForm.title || !reportForm.file">
                      上传报告
                    </el-button>
                    <template #tip>
                      <div class="upload-tip">仅支持 .md 或 .markdown 文件，文件大小不超过 10MB</div>
                    </template>
                  </el-upload>
                </div>
              </div>
            </div>

            <div class="report-batch-section">
              <div class="section-title">批量上传</div>
              <div class="batch-form">
                <div class="form-row">
                  <div class="form-item">
                    <label>组织单位：</label>
                    <el-tree-select
                      v-model="batchReportForm.org_id"
                      :data="organizationTree"
                      :props="{ label: 'name', value: 'id', children: 'children' }"
                      placeholder="选择组织单位"
                      filterable
                      check-strictly
                      style="width: 300px"
                    />
                  </div>
                </div>
                <div class="form-row">
                  <el-upload
                    ref="batchUploadRef"
                    :auto-upload="false"
                    :show-file-list="true"
                    :limit="20"
                    multiple
                    accept=".md,.markdown"
                    :on-change="handleBatchReportFileChange"
                    :on-exceed="handleBatchExceed"
                  >
                    <template #trigger>
                      <el-button type="primary">
                        <el-icon class="el-icon--left"><Upload /></el-icon>
                        选择多个文件
                      </el-button>
                    </template>
                    <el-button class="ml-3" type="success" @click="batchUploadReports" :loading="batchUploadLoading" :disabled="!batchReportForm.org_id || batchReportForm.files.length === 0">
                      批量上传
                    </el-button>
                    <template #tip>
                      <div class="upload-tip">批量上传时以文件名作为报告标题，最多上传20个文件</div>
                    </template>
                  </el-upload>
                </div>
              </div>
            </div>

            <div class="report-list-section">
              <div class="section-header">
                <div class="section-title">报告列表</div>
                <div class="filter-row">
                  <el-tree-select
                    v-model="reportFilterOrg"
                    :data="organizationTree"
                    :props="{ label: 'name', value: 'id', children: 'children' }"
                    placeholder="全部组织"
                    clearable
                    filterable
                    check-strictly
                    style="width: 250px"
                    @change="loadReportList"
                  />
                </div>
              </div>
              <el-table :data="reportList" style="width: 100%" border @selection-change="handleReportSelection">
                <el-table-column type="selection" width="55" />
                <el-table-column prop="org_name" label="组织单位" width="200" show-overflow-tooltip />
                <el-table-column prop="title" label="报告标题" show-overflow-tooltip>
                  <template #default="scope">
                    <div class="report-title-cell clickable" @click="viewReport(scope.row)">
                      <el-icon class="report-icon"><Document /></el-icon>
                      <span>{{ scope.row.title }}</span>
                    </div>
                  </template>
                </el-table-column>
                <el-table-column prop="create_time" label="上传日期" width="120">
                  <template #default="scope">
                    {{ formatReportDate(scope.row.create_time) }}
                  </template>
                </el-table-column>
                <el-table-column prop="file_size" label="大小" width="100">
                  <template #default="scope">
                    {{ formatReportFileSize(scope.row.file_size) }}
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="150" fixed="right">
                  <template #default="scope">
                    <el-button size="small" @click="openEditReportDialog(scope.row)">编辑</el-button>
                    <el-button size="small" type="danger" @click="deleteReportItem(scope.row.id)">删除</el-button>
                  </template>
                </el-table-column>
              </el-table>
              <div class="batch-actions">
                <el-button type="danger" @click="batchDeleteReports" :disabled="selectedReports.length === 0">
                  批量删除 ({{ selectedReports.length }})
                </el-button>
                <el-pagination
                  v-model:current-page="reportPage"
                  :page-size="20"
                  :total="reportTotal"
                  layout="total, prev, pager, next"
                  @current-change="loadReportList"
                />
              </div>
            </div>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 添加/编辑设备用途对话框 -->
    <el-dialog v-model="purposeDialogVisible" width="500px" :show-close="false">
      <template #header>
        <div class="dialog-header">
          <div class="header-decoration">
            <span class="decoration-line"></span>
            <span class="decoration-dot"></span>
          </div>
          <h3 class="dialog-title">{{ purposeDialogTitle }}</h3>
          <div class="header-decoration right">
            <span class="decoration-dot"></span>
            <span class="decoration-line"></span>
          </div>
          <button class="close-btn" @click="purposeDialogVisible = false">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
      </template>
      <el-form :model="purposeForm" label-width="80px">
        <el-form-item label="标签">
          <el-input v-model="purposeForm.dict_label" placeholder="请输入设备用途标签" />
        </el-form-item>
        <el-form-item label="值">
          <el-input-number v-model="purposeForm.dict_value" :min="1" :max="999" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="purposeForm.dict_sort" :min="0" :max="999" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="purposeForm.status" :active-value="1" :inactive-value="0" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="purposeForm.remark" type="textarea" placeholder="请输入备注信息" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="purposeDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="savePurpose" :loading="purposeLoading">
            保存
          </el-button>
        </span>
      </template>
    </el-dialog>

    <el-dialog v-model="tierDialogVisible" width="500px" :show-close="false">
      <template #header>
        <div class="dialog-header">
          <div class="header-decoration">
            <span class="decoration-line"></span>
            <span class="decoration-dot"></span>
          </div>
          <h3 class="dialog-title">{{ tierDialogTitle }}</h3>
          <div class="header-decoration right">
            <span class="decoration-dot"></span>
            <span class="decoration-line"></span>
          </div>
          <button class="close-btn" @click="tierDialogVisible = false">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
      </template>
      <el-form :model="tierForm" label-width="80px">
        <el-form-item label="档次值">
          <el-input-number v-model="tierForm.dict_value" :min="1" :max="10" />
          <span class="form-tip">对应 GPU 卡的 card_type 值</span>
        </el-form-item>
        <el-form-item label="档次名称">
          <el-input v-model="tierForm.dict_label" placeholder="如：高端卡、中端卡" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="tierForm.dict_sort" :min="0" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="tierForm.status" :active-value="1" :inactive-value="0" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="tierForm.remark" type="textarea" placeholder="请输入备注信息" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="tierDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveTier" :loading="tierLoading">
            保存
          </el-button>
        </span>
      </template>
    </el-dialog>

    <el-dialog v-model="reportEditDialogVisible" width="500px" :show-close="false">
      <template #header>
        <div class="dialog-header">
          <div class="header-decoration">
            <span class="decoration-line"></span>
            <span class="decoration-dot"></span>
          </div>
          <h3 class="dialog-title">编辑报告</h3>
          <div class="header-decoration right">
            <span class="decoration-dot"></span>
            <span class="decoration-line"></span>
          </div>
          <button class="close-btn" @click="reportEditDialogVisible = false">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
      </template>
      <el-form :model="reportEditForm" label-width="80px">
        <el-form-item label="报告标题">
          <el-input v-model="reportEditForm.title" placeholder="请输入报告标题" />
        </el-form-item>
        <el-form-item label="组织单位">
          <el-tree-select
            v-model="reportEditForm.org_id"
            :data="organizationTree"
            :props="{ label: 'name', value: 'id', children: 'children' }"
            placeholder="选择组织单位"
            filterable
            check-strictly
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="reportEditDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveReportEdit" :loading="reportEditLoading">
            保存
          </el-button>
        </span>
      </template>
    </el-dialog>

    <el-dialog
      v-model="viewReportDialogVisible"
      width="80%"
      top="5vh"
      :close-on-click-modal="false"
      :fullscreen="isViewReportMaximized"
      :show-close="false"
      class="report-detail-dialog"
      append-to-body
      @closed="handleViewReportDialogClosed"
    >
      <template #header>
        <div class="report-dialog-header">
          <div class="header-left">
            <div class="report-title">{{ viewReportData?.title || '报告详情' }}</div>
            <div class="report-meta" v-if="viewReportData">
              {{ viewReportData.org_name }} · {{ formatReportDate(viewReportData.create_time) }} · {{ formatReportFileSize(viewReportData.file_size) }}
            </div>
          </div>
          <div class="header-right">
            <button class="control-btn" @click="toggleViewReportMaximize" :title="isViewReportMaximized ? '还原' : '最大化'">
              <svg v-if="!isViewReportMaximized" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
              </svg>
              <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M8 3v3a2 2 0 0 1-2 2H3m18 0h-3a2 2 0 0 1-2-2V3m0 18v-3a2 2 0 0 1 2-2h3M3 16h3a2 2 0 0 1 2 2v3"></path>
              </svg>
            </button>
            <button class="control-btn close-btn" @click="viewReportDialogVisible = false" title="关闭">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
          </div>
        </div>
      </template>
      
      <div class="report-body-wrapper">
        <div v-if="viewReportLoading" class="loading-container">
          <el-icon class="is-loading" :size="32"><Loading /></el-icon>
          <span>加载报告内容...</span>
        </div>
        
        <div v-else-if="viewReportContent" class="markdown-content" v-html="renderedReportMarkdown"></div>
      </div>
      
      <template #footer>
        <el-button @click="viewReportDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Download, Upload, Document, Loading } from '@element-plus/icons-vue'
import axios from 'axios'
import * as XLSX from 'xlsx'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { exportApi, reportApi } from '../api'

const activeTab = ref('system')

const config = ref({
  work_hour_start: 9,
  work_hour_end: 18,
  high_usage_threshold: 60.0,
  low_usage_threshold: 30.0,
  auto_aggregation_enabled: true,
  auto_aggregation_hour: 1,
  auto_aggregation_minute: 0
})

const aggregationStatus = ref({
  daily_summary_count: 0,
  device_summary_count: 0,
  org_summary_count: 0,
  statistics_count: 0,
  org_hourly_count: 0,
  latest_aggregation_time: null
})

const passwordForm = ref({
  old_password: '',
  new_password: '',
  confirm_password: ''
})

const refreshDays = ref(1)
const configLoading = ref(false)
const refreshLoading = ref(false)
const resetLoading = ref(false)
const passwordLoading = ref(false)
const refreshProgress = ref({
  show: false,
  percent: 0,
  currentTask: '',
  day: 0,
  totalDays: 0
})
const currentTaskId = ref(null)
const pollInterval = ref(null)
const recentTasks = ref([])

// 时间段聚合相关
const aggregationMode = ref('days') // 'days' 或 'dateRange'
const dateRange = ref([])
const pickerOptions = ref({
  disabledDate(time) {
    return time.getTime() > Date.now()
  }
})

// 设备用途管理相关状态
const purposeList = ref([])
const purposeDialogVisible = ref(false)
const purposeDialogTitle = ref('添加设备用途')
const purposeForm = ref({
  id: null,
  dict_label: '',
  dict_value: 1,
  dict_sort: 0,
  status: 1,
  remark: ''
})
const purposeLoading = ref(false)

// GPU 档次管理相关状态
const tierList = ref([])
const tierDialogVisible = ref(false)
const tierDialogTitle = ref('添加档次')
const tierForm = ref({
  id: null,
  dict_value: 1,
  dict_label: '',
  dict_sort: 0,
  status: 1,
  remark: ''
})
const tierLoading = ref(false)
const selectedTiers = ref([])

const dbStatus = ref({
  main_database: null,
  local_database: null,
  cache_status: []
})
const dbStatusLoading = ref(false)
const dbTestLoading = ref(false)
const connectionTest = ref({
  main_database: null,
  local_database: null
})

const exportDateRange = ref([])
const exportLoading = ref(false)
const exportProgress = ref({
  show: false,
  percent: 0,
  status: '',
  text: ''
})
const exportResult = ref({
  total: 0,
  data: []
})

const organizationList = ref([])
const organizationTree = ref([])

const buildOrgTree = (orgs) => {
  const map = {}
  const roots = []
  
  orgs.forEach(org => {
    map[org.id] = { ...org, children: [] }
  })
  
  orgs.forEach(org => {
    const node = map[org.id]
    if (org.parent_id === 0 || !map[org.parent_id]) {
      roots.push(node)
    } else {
      map[org.parent_id].children.push(node)
    }
  })
  
  const sortChildren = (nodes) => {
    nodes.sort((a, b) => (a.sort || 0) - (b.sort || 0))
    nodes.forEach(node => {
      if (node.children && node.children.length > 0) {
        sortChildren(node.children)
      }
    })
  }
  
  sortChildren(roots)
  return roots
}
const reportList = ref([])
const reportTotal = ref(0)
const reportPage = ref(1)
const reportFilterOrg = ref(null)
const selectedReports = ref([])
const uploadLoading = ref(false)
const batchUploadLoading = ref(false)
const reportEditDialogVisible = ref(false)
const reportEditLoading = ref(false)
const reportEditForm = ref({
  id: null,
  title: '',
  org_id: null
})
const reportForm = ref({
  org_id: null,
  title: '',
  file: null,
  content: '',
  file_size: 0
})
const batchReportForm = ref({
  org_id: null,
  files: []
})

const viewReportDialogVisible = ref(false)
const viewReportLoading = ref(false)
const viewReportContent = ref('')
const viewReportData = ref(null)
const isViewReportMaximized = ref(false)

const renderedReportMarkdown = computed(() => {
  if (!viewReportContent.value) return ''
  try {
    const rawHtml = marked(viewReportContent.value)
    return DOMPurify.sanitize(rawHtml)
  } catch (e) {
    console.error('Markdown render error:', e)
    return viewReportContent.value
  }
})

const loadConfig = async () => {
  try {
    const response = await axios.get('/api/admin/config')
    config.value = response.data
  } catch (error) {
    ElMessage.error('加载配置失败')
  }
}

const loadAggregationStatus = async () => {
  try {
    const response = await axios.get('/api/admin/aggregation/status')
    aggregationStatus.value = response.data
  } catch (error) {
    ElMessage.error('加载聚合状态失败')
  }
}

const loadPurposeList = async () => {
  try {
    const response = await axios.get('/api/dict/purpose')
    purposeList.value = response.data
  } catch (error) {
    ElMessage.error('加载设备用途失败')
  }
}

const saveConfig = async () => {
  configLoading.value = true
  try {
    await axios.put('/api/admin/config', config.value)
    ElMessage.success('配置保存成功')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '保存配置失败')
  } finally {
    configLoading.value = false
  }
}

const refreshAggregation = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要刷新最近 ${refreshDays.value} 天的聚合数据吗？`,
      '确认操作',
      { type: 'warning' }
    )

    refreshLoading.value = true
    refreshProgress.value = {
      show: true,
      percent: 0,
      currentTask: '正在创建任务...',
      day: 0,
      totalDays: refreshDays.value
    }

    const response = await axios.post('/api/admin/aggregation/tasks', {
      days: refreshDays.value
    })

    if (response.data.success) {
      currentTaskId.value = response.data.task_id
      startPolling()
    } else {
      refreshLoading.value = false
      refreshProgress.value.show = false
      ElMessage.error(response.data.message || '创建任务失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      refreshLoading.value = false
      refreshProgress.value.show = false
      ElMessage.error(error.response?.data?.detail || '刷新失败')
    }
  }
}

const startPolling = () => {
  if (pollInterval.value) {
    clearInterval(pollInterval.value)
  }
  
  pollInterval.value = setInterval(async () => {
    if (!currentTaskId.value) {
      clearInterval(pollInterval.value)
      return
    }
    
    try {
      const response = await axios.get(`/api/admin/aggregation/tasks/${currentTaskId.value}`)
      const task = response.data
      
      refreshProgress.value.percent = task.progress
      refreshProgress.value.currentTask = task.current_step || ''
      refreshProgress.value.day = task.processed_days
      refreshProgress.value.totalDays = task.total_days
      
      if (task.status === 'completed') {
        clearInterval(pollInterval.value)
        pollInterval.value = null
        refreshLoading.value = false
        refreshProgress.value.show = false
        currentTaskId.value = null
        ElMessage.success('聚合数据刷新完成')
        loadAggregationStatus()
        loadRecentTasks()
      } else if (task.status === 'failed') {
        clearInterval(pollInterval.value)
        pollInterval.value = null
        refreshLoading.value = false
        refreshProgress.value.show = false
        currentTaskId.value = null
        ElMessage.error(`刷新失败: ${task.error_message || '未知错误'}`)
        loadRecentTasks()
      } else if (task.status === 'cancelled') {
        clearInterval(pollInterval.value)
        pollInterval.value = null
        refreshLoading.value = false
        refreshProgress.value.show = false
        currentTaskId.value = null
        ElMessage.warning('任务已取消')
        loadRecentTasks()
      }
    } catch (error) {
      console.error('轮询任务状态失败:', error)
    }
  }, 2000)
}

const cancelCurrentTask = async () => {
  if (!currentTaskId.value) return
  
  try {
    await axios.post(`/api/admin/aggregation/tasks/${currentTaskId.value}/cancel`)
    if (pollInterval.value) {
      clearInterval(pollInterval.value)
      pollInterval.value = null
    }
    refreshLoading.value = false
    refreshProgress.value.show = false
    currentTaskId.value = null
    ElMessage.success('任务已取消')
    loadRecentTasks()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '取消任务失败')
  }
}

const loadRecentTasks = async () => {
  try {
    const response = await axios.get('/api/admin/aggregation/tasks?limit=5')
    recentTasks.value = response.data.tasks
  } catch (error) {
    console.error('加载任务列表失败:', error)
  }
}

const resetAggregation = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要重置所有聚合数据吗？此操作不可恢复！',
      '危险操作',
      { type: 'error', confirmButtonText: '确定重置', cancelButtonText: '取消' }
    )

    resetLoading.value = true
    const response = await axios.post('/api/admin/aggregation/reset')

    if (response.data.success) {
      ElMessage.success(response.data.message)
      loadAggregationStatus()
    } else {
      ElMessage.error(response.data.message)
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '重置失败')
    }
  } finally {
    resetLoading.value = false
  }
}

const resetRefreshDays = () => {
  // 切换模式时重置相关参数
  if (aggregationMode.value === 'days') {
    refreshDays.value = 1
  } else {
    dateRange.value = []
  }
}

const refreshAggregationByDateRange = async () => {
  if (!dateRange.value || dateRange.value.length !== 2) {
    ElMessage.warning('请选择有效的日期范围')
    return
  }

  try {
    const startDate = dateRange.value[0]
    const endDate = dateRange.value[1]
    const days = Math.ceil((endDate - startDate) / (1000 * 60 * 60 * 24)) + 1

    if (days > 365) {
      ElMessage.warning('日期范围不能超过365天')
      return
    }

    await ElMessageBox.confirm(
      `确定要刷新 ${startDate.getFullYear()}-${(startDate.getMonth() + 1).toString().padStart(2, '0')}-${startDate.getDate().toString().padStart(2, '0')} 至 ${endDate.getFullYear()}-${(endDate.getMonth() + 1).toString().padStart(2, '0')}-${endDate.getDate().toString().padStart(2, '0')} 的聚合数据吗？`,
      '确认操作',
      { type: 'warning' }
    )

    refreshLoading.value = true
    refreshProgress.value = {
      show: true,
      percent: 0,
      currentTask: '正在创建任务...',
      day: 0,
      totalDays: days
    }

    const startDateStr = `${startDate.getFullYear()}-${(startDate.getMonth() + 1).toString().padStart(2, '0')}-${startDate.getDate().toString().padStart(2, '0')}`
    const endDateStr = `${endDate.getFullYear()}-${(endDate.getMonth() + 1).toString().padStart(2, '0')}-${endDate.getDate().toString().padStart(2, '0')}`

    const response = await axios.post('/api/admin/aggregation/tasks', {
      start_date: startDateStr,
      end_date: endDateStr
    })

    if (response.data.success) {
      currentTaskId.value = response.data.task_id
      startPolling()
    } else {
      refreshLoading.value = false
      refreshProgress.value.show = false
      ElMessage.error(response.data.message || '创建任务失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      refreshLoading.value = false
      refreshProgress.value.show = false
      ElMessage.error(error.response?.data?.detail || '刷新失败')
    }
  }
}

const changePassword = async () => {
  if (!passwordForm.value.old_password) {
    ElMessage.warning('请输入原密码')
    return
  }
  if (!passwordForm.value.new_password || passwordForm.value.new_password.length < 6) {
    ElMessage.warning('新密码长度不能少于6位')
    return
  }
  if (passwordForm.value.new_password !== passwordForm.value.confirm_password) {
    ElMessage.warning('两次输入的新密码不一致')
    return
  }

  passwordLoading.value = true
  try {
    const response = await axios.post('/api/admin/change-password', {
      old_password: passwordForm.value.old_password,
      new_password: passwordForm.value.new_password
    })
    ElMessage.success(response.data.message)
    passwordForm.value = {
      old_password: '',
      new_password: '',
      confirm_password: ''
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '修改密码失败')
  } finally {
    passwordLoading.value = false
  }
}

// 设备用途管理相关方法
const openAddPurposeDialog = () => {
  purposeDialogTitle.value = '添加设备用途'
  purposeForm.value = {
    id: null,
    dict_label: '',
    dict_value: 1,
    dict_sort: 0,
    status: 1,
    remark: ''
  }
  purposeDialogVisible.value = true
}

const openEditPurposeDialog = (row) => {
  purposeDialogTitle.value = '编辑设备用途'
  purposeForm.value = {
    id: row.id,
    dict_label: row.dict_label,
    dict_value: row.dict_value,
    dict_sort: row.dict_sort,
    status: row.status,
    remark: row.remark || ''
  }
  purposeDialogVisible.value = true
}

const savePurpose = async () => {
  if (!purposeForm.value.dict_label) {
    ElMessage.warning('请输入设备用途标签')
    return
  }

  purposeLoading.value = true
  try {
    if (purposeForm.value.id) {
      // 编辑
      await axios.put(`/api/admin/dict/purpose/${purposeForm.value.id}`, purposeForm.value)
    } else {
      // 添加
      await axios.post('/api/admin/dict/purpose', purposeForm.value)
    }
    ElMessage.success('保存成功')
    purposeDialogVisible.value = false
    loadPurposeList()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '保存失败')
  } finally {
    purposeLoading.value = false
  }
}

const updatePurposeStatus = async (row) => {
  try {
    await axios.patch(`/api/admin/dict/purpose/${row.id}/status`, {
      status: row.status
    })
    ElMessage.success('状态更新成功')
  } catch (error) {
    ElMessage.error('状态更新失败')
    // 恢复原状态
    loadPurposeList()
  }
}

const deletePurpose = async (id) => {
  try {
    await ElMessageBox.confirm(
      '确定要删除这个设备用途吗？',
      '确认操作',
      { type: 'warning' }
    )

    await axios.delete(`/api/admin/dict/purpose/${id}`)
    ElMessage.success('删除成功')
    loadPurposeList()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// GPU 档次管理函数
const loadTierList = async () => {
  try {
    const response = await axios.get('/api/admin/dict/gpu-tier')
    tierList.value = response.data || []
  } catch (error) {
    console.error('加载GPU档次列表失败:', error)
  }
}

const openAddTierDialog = () => {
  tierDialogTitle.value = '添加档次'
  tierForm.value = {
    id: null,
    dict_value: 1,
    dict_label: '',
    dict_sort: 0,
    status: 1,
    remark: ''
  }
  tierDialogVisible.value = true
}

const openEditTierDialog = (row) => {
  tierDialogTitle.value = '编辑档次'
  tierForm.value = {
    id: row.id,
    dict_value: row.dict_value,
    dict_label: row.dict_label,
    dict_sort: row.dict_sort,
    status: row.status,
    remark: row.remark || ''
  }
  tierDialogVisible.value = true
}

const saveTier = async () => {
  if (!tierForm.value.dict_label) {
    ElMessage.warning('请输入档次名称')
    return
  }

  tierLoading.value = true
  try {
    if (tierForm.value.id) {
      await axios.put(`/api/admin/dict/gpu-tier/${tierForm.value.id}`, tierForm.value)
    } else {
      await axios.post('/api/admin/dict/gpu-tier', tierForm.value)
    }
    ElMessage.success('保存成功')
    tierDialogVisible.value = false
    loadTierList()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '保存失败')
  } finally {
    tierLoading.value = false
  }
}

const updateTierStatus = async (row) => {
  try {
    await axios.patch(`/api/admin/dict/gpu-tier/${row.id}/status`, {
      status: row.status
    })
    ElMessage.success('状态更新成功')
  } catch (error) {
    ElMessage.error('状态更新失败')
    loadTierList()
  }
}

const deleteTier = async (id) => {
  try {
    await ElMessageBox.confirm(
      '确定要删除这个档次吗？',
      '确认操作',
      { type: 'warning' }
    )

    await axios.delete(`/api/admin/dict/gpu-tier/${id}`)
    ElMessage.success('删除成功')
    loadTierList()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleTierSelection = (selection) => {
  selectedTiers.value = selection
}

const batchDeleteTier = async () => {
  if (selectedTiers.value.length === 0) {
    ElMessage.warning('请选择要删除的档次')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedTiers.value.length} 个档次吗？`,
      '确认操作',
      { type: 'warning' }
    )

    for (const tier of selectedTiers.value) {
      await axios.delete(`/api/admin/dict/gpu-tier/${tier.id}`)
    }

    ElMessage.success('批量删除成功')
    selectedTiers.value = []
    loadTierList()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量删除失败')
    }
  }
}

const refreshDatabaseStatus = async () => {
  dbStatusLoading.value = true
  try {
    const response = await axios.get('/api/admin/database/status')
    dbStatus.value = response.data
  } catch (error) {
    ElMessage.error('获取数据库状态失败')
  } finally {
    dbStatusLoading.value = false
  }
}

const testDatabaseConnection = async () => {
  dbTestLoading.value = true
  connectionTest.value = {
    main_database: null,
    local_database: null
  }
  try {
    const response = await axios.get('/api/admin/database/test-connection')
    connectionTest.value = response.data
    if (response.data.main_database?.success && response.data.local_database?.success) {
      ElMessage.success('所有数据库连接正常')
    } else if (!response.data.main_database?.success || !response.data.local_database?.success) {
      ElMessage.warning('部分数据库连接异常，请查看详情')
    }
  } catch (error) {
    ElMessage.error('测试连接失败')
  } finally {
    dbTestLoading.value = false
  }
}

const formatNumber = (num) => {
  if (num === null || num === undefined) return '0'
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

const formatDateTime = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}-${date.getDate().toString().padStart(2, '0')} ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}:${date.getSeconds().toString().padStart(2, '0')}`
}

const disabledExportDate = (time) => {
  return time.getTime() > Date.now()
}

const handleExportData = async () => {
  if (!exportDateRange.value || exportDateRange.value.length !== 2) {
    ElMessage.warning('请选择日期范围')
    return
  }

  const startDate = exportDateRange.value[0]
  const endDate = exportDateRange.value[1]
  const daysDiff = Math.ceil((endDate - startDate) / (1000 * 60 * 60 * 24)) + 1

  if (daysDiff > 365) {
    ElMessage.warning('日期范围不能超过365天')
    return
  }

  const startDateStr = `${startDate.getFullYear()}-${(startDate.getMonth() + 1).toString().padStart(2, '0')}-${startDate.getDate().toString().padStart(2, '0')}`
  const endDateStr = `${endDate.getFullYear()}-${(endDate.getMonth() + 1).toString().padStart(2, '0')}-${endDate.getDate().toString().padStart(2, '0')}`

  exportLoading.value = true
  exportProgress.value = {
    show: true,
    percent: 0,
    status: '',
    text: '正在获取数据...'
  }
  exportResult.value = { total: 0, data: [] }

  try {
    exportProgress.value.percent = 30
    exportProgress.value.text = '正在从数据库查询数据...'
    
    const response = await exportApi.getUsageData(startDateStr, endDateStr)
    
    if (!response.success || !response.data) {
      throw new Error(response.message || '获取数据失败')
    }

    exportProgress.value.percent = 60
    exportProgress.value.text = `获取到 ${response.total} 条数据，正在生成Excel...`

    const data = response.data
    exportResult.value = {
      total: response.total,
      data: data
    }

    exportProgress.value.percent = 80
    exportProgress.value.text = '正在生成Excel文件...'

    const headers = [
      '起始日期', '结束日期', '实际起始日期', '实际结束日期', '组织机构名称', '设备数', 'GPU数', 
      '总算力', '显存总量(GB)', '设备用途', '运行网络', '时间类型',
      '平均GPU使用率(%)', '平均显存使用率(%)', '平均显存利用率(%)'
    ]
    
    const wsData = [headers]
    data.forEach(row => {
      wsData.push([
        row['起始日期'],
        row['结束日期'],
        row['实际起始日期'],
        row['实际结束日期'],
        row['组织机构名称'],
        row['设备数'],
        row['GPU数'],
        row['总算力'],
        row['显存总量(GB)'],
        row['设备用途'],
        row['运行网络'],
        row['时间类型'],
        row['平均GPU使用率(%)'],
        row['平均显存使用率(%)'],
        row['平均显存利用率(%)']
      ])
    })

    const ws = XLSX.utils.aoa_to_sheet(wsData)
    
    const colWidths = [
      { wch: 12 }, { wch: 12 }, { wch: 12 }, { wch: 12 }, { wch: 30 }, { wch: 10 }, { wch: 10 },
      { wch: 12 }, { wch: 14 }, { wch: 15 }, { wch: 15 }, { wch: 12 },
      { wch: 16 }, { wch: 16 }, { wch: 16 }
    ]
    ws['!cols'] = colWidths

    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, '使用率数据')

    exportProgress.value.percent = 95
    exportProgress.value.text = '正在下载文件...'

    const fileName = `使用率数据导出_${startDateStr}_${endDateStr}.xlsx`
    XLSX.writeFile(wb, fileName)

    exportProgress.value.percent = 100
    exportProgress.value.status = 'success'
    exportProgress.value.text = '导出完成！'

    ElMessage.success(`成功导出 ${response.total} 条数据`)

    setTimeout(() => {
      exportProgress.value.show = false
    }, 2000)

  } catch (error) {
    console.error('导出失败:', error)
    exportProgress.value.status = 'exception'
    exportProgress.value.text = `导出失败: ${error.message || '未知错误'}`
    ElMessage.error(error.response?.data?.detail || error.message || '导出失败')
  } finally {
    exportLoading.value = false
  }
}

const loadOrganizationList = async () => {
  try {
    const response = await reportApi.getOrganizations()
    organizationList.value = response.data || []
    organizationTree.value = buildOrgTree(response.data || [])
  } catch (error) {
    console.error('加载组织列表失败:', error)
  }
}

const loadReportList = async () => {
  try {
    const params = { page: reportPage.value, page_size: 20 }
    if (reportFilterOrg.value) {
      params.org_id = reportFilterOrg.value
    }
    const response = await reportApi.getAdminReports(params)
    reportList.value = response.data || []
    reportTotal.value = response.total || 0
  } catch (error) {
    console.error('加载报告列表失败:', error)
    ElMessage.error('加载报告列表失败')
  }
}

const handleReportFileChange = (file) => {
  const validTypes = ['.md', '.markdown']
  const fileName = file.name.toLowerCase()
  const isValidType = validTypes.some(ext => fileName.endsWith(ext))
  
  if (!isValidType) {
    ElMessage.error('仅支持 .md 或 .markdown 文件')
    return false
  }
  
  if (file.size > 10 * 1024 * 1024) {
    ElMessage.error('文件大小不能超过 10MB')
    return false
  }
  
  reportForm.value.file = file.raw
  reportForm.value.file_size = file.size
  
  if (!reportForm.value.title) {
    const baseName = file.name.replace(/\.(md|markdown)$/i, '')
    reportForm.value.title = baseName
  }
  
  return true
}

const handleExceed = () => {
  ElMessage.warning('一次只能上传一个文件')
}

const handleBatchReportFileChange = (file, fileList) => {
  const validTypes = ['.md', '.markdown']
  const fileName = file.name.toLowerCase()
  const isValidType = validTypes.some(ext => fileName.endsWith(ext))
  
  if (!isValidType) {
    ElMessage.error(`文件 ${file.name} 不是 Markdown 文件`)
    return false
  }
  
  if (file.size > 10 * 1024 * 1024) {
    ElMessage.error(`文件 ${file.name} 超过 10MB`)
    return false
  }
  
  batchReportForm.value.files = fileList.map(f => ({
    file: f.raw,
    title: f.name.replace(/\.(md|markdown)$/i, ''),
    file_size: f.size
  }))
  
  return true
}

const handleBatchExceed = () => {
  ElMessage.warning('一次最多上传20个文件')
}

const readFileContent = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = (e) => resolve(e.target.result)
    reader.onerror = (e) => reject(e)
    reader.readAsText(file)
  })
}

const uploadReport = async () => {
  if (!reportForm.value.org_id) {
    ElMessage.warning('请选择组织单位')
    return
  }
  if (!reportForm.value.title) {
    ElMessage.warning('请输入报告标题')
    return
  }
  if (!reportForm.value.file) {
    ElMessage.warning('请选择文件')
    return
  }
  
  uploadLoading.value = true
  try {
    const content = await readFileContent(reportForm.value.file)
    const org = organizationList.value.find(o => o.id === reportForm.value.org_id)
    
    await reportApi.createReport({
      org_id: reportForm.value.org_id,
      org_name: org?.name || '',
      title: reportForm.value.title,
      content: content,
      file_size: reportForm.value.file_size
    })
    
    ElMessage.success('报告上传成功')
    reportForm.value = { org_id: null, title: '', file: null, content: '', file_size: 0 }
    loadReportList()
  } catch (error) {
    console.error('上传失败:', error)
    ElMessage.error(error.response?.data?.detail || '上传失败')
  } finally {
    uploadLoading.value = false
  }
}

const batchUploadReports = async () => {
  if (!batchReportForm.value.org_id) {
    ElMessage.warning('请选择组织单位')
    return
  }
  if (batchReportForm.value.files.length === 0) {
    ElMessage.warning('请选择文件')
    return
  }
  
  batchUploadLoading.value = true
  try {
    const org = organizationList.value.find(o => o.id === batchReportForm.value.org_id)
    let successCount = 0
    let failCount = 0
    
    for (const item of batchReportForm.value.files) {
      try {
        const content = await readFileContent(item.file)
        await reportApi.createReport({
          org_id: batchReportForm.value.org_id,
          org_name: org?.name || '',
          title: item.title,
          content: content,
          file_size: item.file_size
        })
        successCount++
      } catch (e) {
        failCount++
        console.error(`上传 ${item.title} 失败:`, e)
      }
    }
    
    if (successCount > 0) {
      ElMessage.success(`成功上传 ${successCount} 个报告${failCount > 0 ? `，失败 ${failCount} 个` : ''}`)
    } else {
      ElMessage.error('所有报告上传失败')
    }
    
    batchReportForm.value = { org_id: null, files: [] }
    loadReportList()
  } catch (error) {
    console.error('批量上传失败:', error)
    ElMessage.error('批量上传失败')
  } finally {
    batchUploadLoading.value = false
  }
}

const handleReportSelection = (selection) => {
  selectedReports.value = selection
}

const openEditReportDialog = (row) => {
  reportEditForm.value = {
    id: row.id,
    title: row.title,
    org_id: row.org_id
  }
  reportEditDialogVisible.value = true
}

const saveReportEdit = async () => {
  if (!reportEditForm.value.title) {
    ElMessage.warning('请输入报告标题')
    return
  }
  if (!reportEditForm.value.org_id) {
    ElMessage.warning('请选择组织单位')
    return
  }
  
  reportEditLoading.value = true
  try {
    const org = organizationList.value.find(o => o.id === reportEditForm.value.org_id)
    await reportApi.updateReport(reportEditForm.value.id, {
      title: reportEditForm.value.title,
      org_id: reportEditForm.value.org_id,
      org_name: org?.name || ''
    })
    ElMessage.success('报告更新成功')
    reportEditDialogVisible.value = false
    loadReportList()
  } catch (error) {
    console.error('更新失败:', error)
    ElMessage.error(error.response?.data?.detail || '更新失败')
  } finally {
    reportEditLoading.value = false
  }
}

const deleteReportItem = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除这个报告吗？', '确认操作', { type: 'warning' })
    await reportApi.deleteReport(id)
    ElMessage.success('删除成功')
    loadReportList()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const batchDeleteReports = async () => {
  if (selectedReports.value.length === 0) {
    ElMessage.warning('请选择要删除的报告')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedReports.value.length} 个报告吗？`,
      '确认操作',
      { type: 'warning' }
    )
    
    const ids = selectedReports.value.map(r => r.id)
    await reportApi.batchDeleteReports(ids)
    ElMessage.success('批量删除成功')
    selectedReports.value = []
    loadReportList()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量删除失败')
    }
  }
}

const formatReportDate = (dateStr) => {
  if (!dateStr) return '-'
  return dateStr.split(' ')[0]
}

const formatReportFileSize = (bytes) => {
  if (!bytes || bytes === 0) return '-'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

onMounted(() => {
  loadConfig()
  loadAggregationStatus()
  loadPurposeList()
  loadTierList()
  loadRecentTasks()
  checkRunningTask()
  refreshDatabaseStatus()
  loadOrganizationList()
  loadReportList()
})

const checkRunningTask = async () => {
  try {
    const response = await axios.get('/api/admin/aggregation/status')
    if (response.data.running_task_id) {
      currentTaskId.value = response.data.running_task_id
      refreshLoading.value = true
      refreshProgress.value.show = true
      startPolling()
    }
  } catch (error) {
    console.error('检查运行中任务失败:', error)
  }
}

const getStatusText = (status) => {
  const statusMap = {
    'pending': '等待中',
    'running': '运行中',
    'completed': '已完成',
    'failed': '失败',
    'cancelled': '已取消'
  }
  return statusMap[status] || status
}

const formatTaskTime = (timeStr) => {
  if (!timeStr) return ''
  const date = new Date(timeStr)
  return `${date.getMonth() + 1}/${date.getDate()} ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
}

const viewReport = async (row) => {
  viewReportData.value = row
  viewReportDialogVisible.value = true
  viewReportLoading.value = true
  viewReportContent.value = ''
  
  try {
    const data = await reportApi.getReportDetail(row.id)
    if (data.error) {
      viewReportContent.value = `# 加载失败\n\n${data.error}`
    } else {
      viewReportContent.value = data.content || '# 无内容'
      viewReportData.value = { ...row, ...data }
    }
  } catch (error) {
    console.error('Failed to fetch report detail:', error)
    viewReportContent.value = '# 加载失败\n\n请稍后重试'
  } finally {
    viewReportLoading.value = false
  }
}

const toggleViewReportMaximize = () => {
  isViewReportMaximized.value = !isViewReportMaximized.value
}

const handleViewReportDialogClosed = () => {
  viewReportData.value = null
  viewReportContent.value = ''
  isViewReportMaximized.value = false
}
</script>

<style lang="scss" scoped>
.admin-panel {
  padding: 20px;
  height: 100%;
  overflow-y: auto;

  &::-webkit-scrollbar {
    width: 6px;
  }

  &::-webkit-scrollbar-thumb {
    background: var(--theme-border);
    border-radius: 3px;
  }

  &::-webkit-scrollbar-track {
    background: transparent;
  }
}

.admin-tabs {
  :deep(.el-tabs__header) {
    margin-bottom: 20px;

    .el-tabs__nav {
      background: var(--theme-panel-bg);
      border: 1px solid var(--theme-border);
      border-radius: 8px 8px 0 0;
      padding: 0 10px;
    }

    .el-tabs__item {
      padding: 12px 24px;
      font-size: 14px;
      color: var(--theme-text-secondary);

      &.is-active {
        color: var(--theme-primary);
        font-weight: 600;
      }
    }

    .el-tabs__active-bar {
      background: linear-gradient(90deg, var(--theme-primary) 0%, var(--theme-secondary) 100%);
      height: 3px;
    }
  }
}

.panel-section {
  background: var(--theme-panel-bg);
  border: 1px solid var(--theme-border);
  border-radius: 8px;
  margin-bottom: 20px;
  overflow: hidden;

  .section-content {
    padding: 20px;
  }
}

.config-item {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 15px;

  label {
    width: 140px;
    color: var(--theme-text);
    font-size: 14px;
  }

  .unit {
    color: var(--theme-text-secondary);
    font-size: 14px;
  }
}

.status-info {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-bottom: 20px;

  .status-item {
    display: flex;
    justify-content: space-between;
    padding: 10px 15px;
    background: var(--theme-hover-bg);
    border-radius: 6px;

    .status-label {
      color: var(--theme-text-secondary);
      font-size: 13px;
    }

    .status-value {
      color: var(--theme-primary);
      font-weight: 600;
      font-size: 14px;
    }
  }
}

.scheduled-config {
  background: var(--theme-hover-bg);
  border-radius: 8px;
  padding: 15px;
  margin-bottom: 20px;
  border: 1px solid var(--theme-border);

  .scheduled-config-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;

    .config-title {
      font-size: 14px;
      font-weight: 600;
      color: var(--theme-text);
    }
  }

  .scheduled-config-body {
    padding-top: 10px;
    border-top: 1px solid var(--theme-border);

    .scheduled-time {
      display: flex;
      align-items: center;
      gap: 10px;

      .time-label {
        font-size: 13px;
        color: var(--theme-text-secondary);
      }

      .time-separator {
        font-size: 16px;
        font-weight: 600;
        color: var(--theme-text);
      }

      .time-hint {
        font-size: 12px;
        color: var(--theme-text-secondary);
        margin-left: 5px;
      }
    }
  }
}

.action-buttons {
  display: flex;
  flex-direction: column;
  gap: 15px;

  .action-row {
    display: flex;
    align-items: center;
    gap: 10px;

    .action-label {
      color: var(--theme-text-secondary);
      font-size: 14px;
    }
  }
}

.progress-container {
  background: var(--theme-hover-bg);
  border-radius: 8px;
  padding: 15px;
  margin-top: 5px;

  .progress-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 10px;
    font-size: 13px;
    color: var(--theme-text-secondary);
  }

  .progress-task {
    margin-top: 8px;
    font-size: 12px;
    color: var(--theme-primary);
    text-align: center;
  }

  :deep(.el-progress-bar__outer) {
    background-color: var(--theme-border);
  }

  :deep(.el-progress-bar__inner) {
    background: linear-gradient(90deg, var(--theme-primary) 0%, var(--theme-secondary) 100%);
  }
}

.recent-tasks {
  background: var(--theme-hover-bg);
  border-radius: 8px;
  padding: 15px;
  margin-top: 10px;

  .recent-tasks-header {
    font-size: 13px;
    color: var(--theme-text-secondary);
    margin-bottom: 10px;
    font-weight: 500;
  }

  .recent-task-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 0;
    border-bottom: 1px solid var(--theme-border);

    &:last-child {
      border-bottom: none;
    }

    .task-info {
      display: flex;
      align-items: center;
      gap: 10px;

      .task-status {
        font-size: 12px;
        padding: 2px 8px;
        border-radius: 4px;

        &.completed {
          background: rgba(103, 194, 58, 0.2);
          color: #67c23a;
        }

        &.running {
          background: rgba(64, 158, 255, 0.2);
          color: #409eff;
        }

        &.failed {
          background: rgba(245, 108, 108, 0.2);
          color: #f56c6c;
        }

        &.cancelled {
          background: rgba(144, 147, 153, 0.2);
          color: #909399;
        }

        &.pending {
          background: rgba(230, 162, 60, 0.2);
          color: #e6a23c;
        }
      }

      .task-time {
        font-size: 12px;
        color: var(--theme-text-secondary);
      }
    }

    .task-detail {
      font-size: 12px;
      color: var(--theme-text-secondary);

      .error-text {
        color: #f56c6c;
        margin-left: 8px;
      }
    }
  }
}

.password-form {
  .form-item {
    display: flex;
    align-items: center;
    gap: 15px;
    margin-bottom: 15px;

    label {
      width: 100px;
      color: var(--theme-text);
      font-size: 14px;
    }

    .el-input {
      flex: 1;
      max-width: 300px;
    }
  }
}

.purpose-header {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 15px;
}

:deep(.el-table) {
  background: var(--theme-panel-bg);
  border: 1px solid var(--theme-border);
  border-radius: 8px;
  overflow: hidden;

  .el-table__header-wrapper th {
    background: var(--theme-hover-bg);
    color: var(--theme-text);
    font-weight: 600;
    border-bottom: 1px solid var(--theme-border);
    text-align: center;
  }

  .el-table__body-wrapper tr {
    &:hover {
      background: var(--theme-hover-bg);
    }
  }

  .el-table__body-wrapper td {
    border-bottom: 1px solid var(--theme-border);
    text-align: center;
  }
}

:deep(.el-input-number) {
  width: 120px;
}

:deep(.el-button--primary) {
  background: linear-gradient(135deg, var(--theme-primary) 0%, var(--theme-secondary) 100%);
  border: none;

  &:hover {
    opacity: 0.9;
  }
}

:deep(.el-button--danger) {
  background: linear-gradient(135deg, #f56c6c 0%, #e6423e 100%);
  border: none;

  &:hover {
    opacity: 0.9;
  }
}

:deep(.el-dialog) {
  background: var(--theme-panel-bg);
  border-radius: 8px;

  .el-dialog__header {
    background: linear-gradient(90deg, var(--theme-hover-bg) 0%, var(--theme-shadow) 100%);
    border-bottom: 1px solid var(--theme-border);

    .el-dialog__title {
      color: var(--theme-primary);
      font-weight: 600;
    }
  }

  .el-dialog__body {
    padding: 20px;
  }

  .el-dialog__footer {
    border-top: 1px solid var(--theme-border);
    padding: 15px 20px;
  }
}

:deep(.el-form-item__label) {
  color: var(--theme-text);
  font-size: 14px;
}

:deep(.el-switch__core) {
  background-color: var(--theme-border);

  &:after {
    background-color: #fff;
  }

  &.is-active {
    background-color: var(--theme-primary);
  }
}

.dialog-header {
  display: flex;
  align-items: center;
  padding: 18px 25px;
  background: linear-gradient(90deg, 
    var(--theme-hover-bg) 0%, 
    var(--theme-shadow) 20%,
    var(--theme-shadow) 80%,
    var(--theme-hover-bg) 100%
  );
  border-bottom: 1px solid var(--theme-border);
  position: relative;
  
  &::before {
    content: '';
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(90deg, 
      transparent 0%, 
      var(--theme-glow) 50%, 
      transparent 100%
    );
  }
  
  .header-decoration {
    display: flex;
    align-items: center;
    gap: 8px;
    
    &.right {
      .decoration-line {
        background: linear-gradient(90deg, var(--theme-glow) 0%, transparent 100%);
      }
    }
    
    .decoration-line {
      width: 40px;
      height: 2px;
      background: linear-gradient(90deg, transparent 0%, var(--theme-glow) 100%);
    }
    
    .decoration-dot {
      width: 8px;
      height: 8px;
      background: var(--theme-primary);
      border-radius: 50%;
      box-shadow: 0 0 10px var(--theme-glow-heavy);
    }
  }
  
  .dialog-title {
    flex: 1;
    text-align: center;
    margin: 0 20px;
    font-size: 20px;
    font-weight: 600;
    background: linear-gradient(90deg, var(--theme-primary) 0%, var(--theme-secondary) 50%, var(--theme-primary) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: 4px;
    text-shadow: 0 0 30px var(--theme-glow);
    white-space: nowrap;
  }
  
  .close-btn {
    position: absolute;
    right: 20px;
    top: 50%;
    transform: translateY(-50%);
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
      width: 18px;
      height: 18px;
      color: var(--theme-primary);
      transition: all 0.3s ease;
    }
    
    &:hover {
      background: linear-gradient(135deg, var(--theme-border-light) 0%, var(--theme-hover-bg) 100%);
      border-color: var(--theme-primary);
      box-shadow: 0 0 15px var(--theme-glow);
      transform: translateY(-50%) scale(1.05);
      
      svg {
        color: var(--theme-secondary);
      }
    }
    
    &:active {
      transform: translateY(-50%) scale(0.95);
    }
  }
}

:deep(.el-dialog) {
  .el-dialog__header {
    padding: 0;
    margin: 0;
  }
  
  .el-dialog__body {
    padding: 30px 20px;
  }
  
  .el-form {
    margin-top: 10px;
  }
  
  .el-form-item {
    margin-bottom: 16px;
  }
}

.database-header {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.database-section {
  background: var(--theme-hover-bg);
  border-radius: 8px;
  padding: 15px;
  margin-bottom: 15px;

  .section-title {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 15px;
    font-weight: 600;
    color: var(--theme-text);
    margin-bottom: 15px;
    padding-bottom: 10px;
    border-bottom: 1px solid var(--theme-border);

    .title-icon {
      width: 12px;
      height: 12px;
      border-radius: 50%;

      &.main-db {
        background: linear-gradient(135deg, #409eff 0%, #67c23a 100%);
        box-shadow: 0 0 8px rgba(64, 158, 255, 0.5);
      }

      &.local-db {
        background: linear-gradient(135deg, #e6a23c 0%, #f56c6c 100%);
        box-shadow: 0 0 8px rgba(230, 162, 60, 0.5);
      }

      &.cache {
        background: linear-gradient(135deg, #909399 0%, #c0c4cc 100%);
        box-shadow: 0 0 8px rgba(144, 147, 153, 0.5);
      }

      &.test {
        background: linear-gradient(135deg, var(--theme-primary) 0%, var(--theme-secondary) 100%);
        box-shadow: 0 0 8px var(--theme-glow);
      }
    }
  }
}

.db-info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;

  .db-info-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 12px;
    background: var(--theme-panel-bg);
    border-radius: 6px;
    border: 1px solid var(--theme-border);

    &.full-width {
      grid-column: 1 / -1;
    }

    .info-label {
      color: var(--theme-text-secondary);
      font-size: 13px;

      &.error {
        color: #f56c6c;
      }
    }

    .info-value {
      color: var(--theme-text);
      font-size: 13px;
      font-weight: 500;

      &.path {
        font-family: monospace;
        font-size: 11px;
        word-break: break-all;
        max-width: 200px;
        text-align: right;
      }

      &.error {
        color: #f56c6c;
        font-size: 12px;
      }

      .pool-detail {
        color: var(--theme-text-secondary);
        font-size: 11px;
        margin-left: 5px;
      }
    }
  }
}

.tables-section {
  margin-top: 15px;

  .tables-title {
    font-size: 13px;
    color: var(--theme-text-secondary);
    margin-bottom: 10px;
    font-weight: 500;
  }

  .tables-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;

    .table-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 8px 12px;
      background: var(--theme-panel-bg);
      border-radius: 6px;
      border: 1px solid var(--theme-border);

      .table-name {
        color: var(--theme-text-secondary);
        font-size: 12px;
      }

      .table-count {
        color: var(--theme-primary);
        font-size: 12px;
        font-weight: 600;
      }
    }
  }
}

.test-results {
  display: flex;
  flex-direction: column;
  gap: 10px;

  .test-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 15px;
    background: var(--theme-panel-bg);
    border-radius: 6px;
    border: 1px solid var(--theme-border);

    .test-label {
      color: var(--theme-text);
      font-size: 13px;
      font-weight: 500;
      min-width: 80px;
    }

    .latency {
      color: var(--theme-text-secondary);
      font-size: 12px;
      margin-left: 10px;
    }

    .error-text {
      color: #f56c6c;
      font-size: 12px;
      margin-left: 10px;
    }
  }
}

.error-text {
  color: #f56c6c;
}

.export-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  padding: 15px;
  background: var(--theme-hover-bg);
  border-radius: 8px;
  border: 1px solid var(--theme-border);

  .export-date-range {
    display: flex;
    align-items: center;
    gap: 10px;

    .export-label {
      font-size: 14px;
      color: var(--theme-text);
      font-weight: 500;
    }
  }
}

.export-info {
  background: var(--theme-hover-bg);
  border-radius: 8px;
  padding: 15px;
  margin-bottom: 20px;
  border: 1px solid var(--theme-border);

  .info-title {
    font-size: 14px;
    font-weight: 600;
    color: var(--theme-primary);
    margin-bottom: 10px;
  }

  .info-list {
    margin: 0;
    padding-left: 20px;
    color: var(--theme-text-secondary);
    font-size: 13px;
    line-height: 1.8;

    li {
      margin-bottom: 5px;
    }
  }
}

.export-progress {
  background: var(--theme-hover-bg);
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
  border: 1px solid var(--theme-border);

  .progress-text {
    display: block;
    text-align: center;
    margin-top: 10px;
    font-size: 13px;
    color: var(--theme-text-secondary);
  }
}

.export-result {
  background: var(--theme-hover-bg);
  border-radius: 8px;
  padding: 15px;
  border: 1px solid var(--theme-border);

  .result-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;

    .result-title {
      font-size: 14px;
      font-weight: 600;
      color: var(--theme-text);
    }

    .result-count {
      font-size: 13px;
      color: var(--theme-primary);
    }
  }

  .result-hint {
    text-align: center;
    padding: 10px;
    color: var(--theme-text-secondary);
    font-size: 12px;
    margin-top: 10px;
    background: var(--theme-panel-bg);
    border-radius: 4px;
  }
}

.report-upload-section,
.report-batch-section,
.report-list-section {
  background: var(--theme-hover-bg);
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
  border: 1px solid var(--theme-border);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.upload-form,
.batch-form {
  .form-row {
    display: flex;
    align-items: center;
    gap: 20px;
    margin-bottom: 15px;
    flex-wrap: wrap;
    
    .form-item {
      display: flex;
      align-items: center;
      gap: 10px;
      
      label {
        font-size: 14px;
        color: var(--theme-text);
        white-space: nowrap;
      }
    }
  }
  
  .upload-tip {
    font-size: 12px;
    color: var(--theme-text-secondary);
    margin-top: 8px;
  }
}

.ml-3 {
  margin-left: 12px;
}

.filter-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.batch-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid var(--theme-border);
}

.report-title-cell {
  display: flex;
  align-items: center;
  gap: 8px;
  
  .report-icon {
    color: var(--theme-primary);
  }
  
  &.clickable {
    cursor: pointer;
    transition: all 0.3s ease;
    
    &:hover {
      color: var(--theme-secondary);
      
      .report-icon {
        color: var(--theme-secondary);
      }
    }
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

.report-body-wrapper {
  flex: 1;
  overflow: auto;
  padding: 0;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 40px;
  color: var(--theme-text-secondary);
  
  .is-loading {
    animation: rotate 1s linear infinite;
  }
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
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
