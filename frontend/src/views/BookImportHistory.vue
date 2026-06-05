<template>
  <div class="import-history-page">
    <div class="page-header">
      <div class="header-left">
        <el-button @click="goBack" :icon="ArrowLeft">返回</el-button>
        <h2 class="page-title">导入历史记录</h2>
      </div>
      <el-button type="primary" @click="goToImport" :icon="Upload">
        新建导入
      </el-button>
    </div>

    <div v-loading="loading" class="history-content">
      <div class="search-bar">
        <el-input
          v-model="keyword"
          placeholder="搜索文件名、导入单号..."
          clearable
          @keyup.enter="fetchHistory"
          style="max-width: 300px"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-select
          v-model="statusFilter"
          placeholder="状态筛选"
          clearable
          @change="fetchHistory"
          style="width: 150px"
        >
          <el-option
            v-for="status in statusOptions"
            :key="status.value"
            :label="status.label"
            :value="status.value"
          />
        </el-select>
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          value-format="YYYY-MM-DD"
          @change="handleDateChange"
          style="width: 280px"
        />
        <el-button @click="resetFilters" :icon="Refresh">
          重置
        </el-button>
      </div>

      <el-table
        :data="historyList"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="import_no" label="导入单号" width="200" />
        <el-table-column prop="file_name" label="文件名" min-width="200" />
        <el-table-column label="文件大小" width="120">
          <template #default="{ row }">
            {{ formatFileSize(row.file_size) }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="统计" width="280">
          <template #default="{ row }">
            <div class="stats-inline">
              <span class="stat-item success">
                <el-icon><CircleCheckFilled /></el-icon>
                {{ row.success_count }}
              </span>
              <span class="stat-item danger">
                <el-icon><CircleCloseFilled /></el-icon>
                {{ row.failed_count }}
              </span>
              <span class="stat-item info">
                <el-icon><Minus /></el-icon>
                {{ row.skipped_count }}
              </span>
              <span class="stat-total">
                共 {{ row.total_rows }} 条
              </span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="created_by_name" label="操作人" width="120" />
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="completed_at" label="完成时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.completed_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="viewDetail(row.id)">
              查看详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          layout="total, prev, pager, next"
          @current-change="fetchHistory"
        />
      </div>

      <el-empty
        v-if="historyList.length === 0 && !loading"
        description="暂无导入记录"
      />
    </div>

    <el-dialog
      v-model="detailVisible"
      title="导入详情"
      width="1200px"
      destroy-on-close
      class="detail-dialog"
    >
      <div v-if="currentDetail" class="detail-content">
        <div class="detail-header">
          <div class="detail-info">
            <h3>{{ currentDetail.file_name }}</h3>
            <div class="detail-meta">
              <span>导入单号：{{ currentDetail.import_no }}</span>
              <span>操作人：{{ currentDetail.created_by_name }}</span>
              <span>创建时间：{{ formatDate(currentDetail.created_at) }}</span>
            </div>
          </div>
          <el-tag :type="getStatusType(currentDetail.status)" size="large">
            {{ getStatusText(currentDetail.status) }}
          </el-tag>
        </div>

        <el-row :gutter="24" class="detail-stats">
          <el-col :span="6">
            <el-card class="stat-card">
              <div class="stat-number total">{{ currentDetail.total_rows }}</div>
              <div class="stat-label">总数据</div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="stat-card">
              <div class="stat-number success">{{ currentDetail.success_count }}</div>
              <div class="stat-label">成功</div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="stat-card">
              <div class="stat-number danger">{{ currentDetail.failed_count }}</div>
              <div class="stat-label">失败</div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="stat-card">
              <div class="stat-number info">{{ currentDetail.skipped_count }}</div>
              <div class="stat-label">跳过</div>
            </el-card>
          </el-col>
        </el-row>

        <div v-if="currentDetail.error_summary" class="error-summary">
          <el-alert
            title="错误摘要"
            type="error"
            :closable="false"
            show-icon
          >
            <pre>{{ currentDetail.error_summary }}</pre>
          </el-alert>
        </div>

        <div class="detail-filter">
          <el-radio-group v-model="itemStatusFilter" size="default" @change="loadDetailItems">
            <el-radio-button label="">全部</el-radio-button>
            <el-radio-button label="success">成功</el-radio-button>
            <el-radio-button label="failed">失败</el-radio-button>
            <el-radio-button label="skipped">跳过</el-radio-button>
          </el-radio-group>
        </div>

        <el-table
          :data="detailItems"
          v-loading="detailLoading"
          border
          stripe
          max-height="400"
          class="items-table"
        >
          <el-table-column label="行号" width="70" align="center" />
          <el-table-column label="状态" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="getItemStatusType(row.status)" size="small">
                {{ getItemStatusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="title" label="书名" min-width="150" />
          <el-table-column prop="author" label="作者" width="120" />
          <el-table-column prop="isbn" label="ISBN" width="140" />
          <el-table-column label="价格" width="100">
            <template #default="{ row }">
              <span v-if="row.price !== null">¥{{ row.price.toFixed(2) }}</span>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column label="库存" width="80">
            <template #default="{ row }">
              {{ row.stock ?? '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="category" label="分类" width="100" />
          <el-table-column label="错误信息" min-width="200">
            <template #default="{ row }">
              <span v-if="row.error_message" class="error-message">
                {{ row.error_message }}
              </span>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column label="关联图书" width="120">
            <template #default="{ row }">
              <el-button
                v-if="row.book_id"
                link
                type="primary"
                @click="goToBook(row.book_id!)"
              >
                查看图书
              </el-button>
              <span v-else>-</span>
            </template>
          </el-table-column>
        </el-table>

        <el-empty
          v-if="detailItems.length === 0 && !detailLoading"
          description="暂无明细数据"
          :image-size="80"
        />
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/api'
import type { BookImportRecord, BookImportRecordDetail, BookImportStatusOption } from '@/types'
import { ElMessage } from 'element-plus'
import {
  ArrowLeft, Upload, Search, Refresh,
  CircleCheckFilled, CircleCloseFilled, Minus
} from '@element-plus/icons-vue'

const router = useRouter()

const loading = ref(false)
const historyList = ref<BookImportRecord[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const keyword = ref('')
const statusFilter = ref('')
const dateRange = ref<string[]>([])
const startDate = ref('')
const endDate = ref('')

const statusOptions = ref<BookImportStatusOption[]>([])

const detailVisible = ref(false)
const detailLoading = ref(false)
const currentDetail = ref<BookImportRecordDetail | null>(null)
const detailItems = ref<any[]>([])
const itemStatusFilter = ref('')
const currentDetailId = ref<number | null>(null)

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

function getStatusType(status: string): string {
  const typeMap: Record<string, string> = {
    'pending': 'info',
    'processing': 'primary',
    'completed': 'success',
    'failed': 'danger'
  }
  return typeMap[status] || 'info'
}

function getStatusText(status: string): string {
  const textMap: Record<string, string> = {
    'pending': '待处理',
    'processing': '处理中',
    'completed': '已完成',
    'failed': '失败'
  }
  return textMap[status] || status
}

function getItemStatusType(status: string): string {
  const typeMap: Record<string, string> = {
    'pending': 'info',
    'success': 'success',
    'failed': 'danger',
    'skipped': 'info'
  }
  return typeMap[status] || 'info'
}

function getItemStatusText(status: string): string {
  const textMap: Record<string, string> = {
    'pending': '待处理',
    'success': '成功',
    'failed': '失败',
    'skipped': '跳过'
  }
  return textMap[status] || status
}

function handleDateChange(val: string[] | null) {
  if (val && val.length === 2) {
    startDate.value = val[0]
    endDate.value = val[1]
  } else {
    startDate.value = ''
    endDate.value = ''
  }
  fetchHistory()
}

function resetFilters() {
  keyword.value = ''
  statusFilter.value = ''
  dateRange.value = []
  startDate.value = ''
  endDate.value = ''
  page.value = 1
  fetchHistory()
}

async function fetchHistory() {
  loading.value = true
  try {
    const response = await api.getBookImportRecords({
      page: page.value,
      page_size: pageSize.value,
      status: statusFilter.value || undefined,
      keyword: keyword.value || undefined
    })
    historyList.value = response.items
    total.value = response.total
  } catch (error) {
    console.error('获取导入历史失败:', error)
    ElMessage.error('获取导入历史失败')
  } finally {
    loading.value = false
  }
}

async function viewDetail(id: number) {
  currentDetailId.value = id
  itemStatusFilter.value = ''
  detailVisible.value = true
  await loadDetailItems()
}

async function loadDetailItems() {
  if (!currentDetailId.value) return

  detailLoading.value = true
  try {
    const response = await api.getBookImportRecordDetail(currentDetailId.value, {
      status_filter: itemStatusFilter.value || undefined
    })
    currentDetail.value = response
    detailItems.value = response.items
  } catch (error) {
    console.error('获取导入详情失败:', error)
    ElMessage.error('获取导入详情失败')
  } finally {
    detailLoading.value = false
  }
}

function goToBook(bookId: number) {
  router.push(`/books/${bookId}`)
}

function goBack() {
  router.back()
}

function goToImport() {
  router.push('/books/import')
}

async function loadStatusOptions() {
  statusOptions.value = await api.getBookImportStatuses()
}

onMounted(() => {
  loadStatusOptions()
  fetchHistory()
})
</script>

<style scoped>
.import-history-page {
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-color);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.page-title {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
}

.history-content {
  background: var(--bg-card);
  border-radius: 12px;
  padding: 24px;
}

.search-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.stats-inline {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 2px;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 500;
}

.stat-item.success {
  color: var(--el-color-success);
  background: rgba(103, 194, 58, 0.1);
}

.stat-item.danger {
  color: var(--el-color-danger);
  background: rgba(245, 108, 108, 0.1);
}

.stat-item.info {
  color: var(--el-color-info);
  background: rgba(144, 147, 153, 0.1);
}

.stat-total {
  color: var(--text-secondary);
  margin-left: 8px;
  padding-left: 8px;
  border-left: 1px solid var(--border-color);
}

.pagination {
  display: flex;
  justify-content: center;
  margin-top: 16px;
}

.detail-dialog :deep(.el-dialog__body) {
  padding-top: 0;
}

.detail-content {
  padding-top: 16px;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-color);
}

.detail-info h3 {
  margin: 0 0 8px;
  font-size: 18px;
}

.detail-meta {
  display: flex;
  gap: 16px;
  color: var(--text-secondary);
  font-size: 13px;
}

.detail-stats {
  margin-bottom: 16px;
}

.stat-card {
  text-align: center;
  border: none;
  background: var(--bg-color);
}

.stat-card :deep(.el-card__body) {
  padding: 16px;
}

.stat-number {
  font-size: 32px;
  font-weight: 700;
  margin-bottom: 4px;
}

.stat-number.total {
  color: var(--text-primary);
}

.stat-number.success {
  color: var(--el-color-success);
}

.stat-number.danger {
  color: var(--el-color-danger);
}

.stat-number.info {
  color: var(--el-color-info);
}

.stat-label {
  font-size: 13px;
  color: var(--text-secondary);
}

.error-summary {
  margin-bottom: 16px;
}

.error-summary pre {
  margin: 0;
  white-space: pre-wrap;
  font-family: inherit;
  font-size: 13px;
}

.detail-filter {
  margin-bottom: 12px;
}

.items-table {
  margin-bottom: 16px;
}

.error-message {
  color: var(--el-color-danger);
  font-size: 12px;
}
</style>
