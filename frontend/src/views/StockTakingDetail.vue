<template>
  <div class="stock-taking-detail">
    <div class="page-header">
      <div class="header-left">
        <el-button @click="goBack" :icon="ArrowLeft">返回</el-button>
        <h2 class="page-title">盘点任务详情</h2>
      </div>
      <div class="header-actions">
        <el-button
          v-if="task?.status === 'draft'"
          type="primary"
          @click="handleStart"
          :loading="starting"
        >
          <el-icon><VideoPlay /></el-icon>
          开始盘点
        </el-button>
        <el-button
          v-if="task?.status === 'in_progress'"
          type="success"
          @click="handleConfirm"
          :loading="confirming"
          :disabled="task.completed_count < task.total_books"
        >
          <el-icon><Check /></el-icon>
          确认盘点
        </el-button>
        <el-button
          v-if="task?.status === 'in_progress' || task?.status === 'draft'"
          type="warning"
          @click="handleCancel"
          :loading="cancelling"
        >
          <el-icon><Close /></el-icon>
          取消盘点
        </el-button>
      </div>
    </div>

    <div v-loading="loading" class="detail-content">
      <div v-if="task" class="task-info-card">
        <div class="info-row">
          <div class="info-item">
            <span class="label">任务编号:</span>
            <span class="value">{{ task.task_no }}</span>
          </div>
          <div class="info-item">
            <span class="label">任务名称:</span>
            <span class="value">{{ task.name }}</span>
          </div>
          <div class="info-item">
            <span class="label">状态:</span>
            <el-tag :type="getStatusType(task.status)" size="small">
              {{ getStatusText(task.status) }}
            </el-tag>
          </div>
        </div>
        <div class="info-row">
          <div class="info-item">
            <span class="label">盘点范围:</span>
            <span class="value">{{ getScopeText(task.scope) }}</span>
          </div>
          <div class="info-item">
            <span class="label">负责人:</span>
            <span class="value">{{ task.person_in_charge || '-' }}</span>
          </div>
          <div class="info-item">
            <span class="label">创建人:</span>
            <span class="value">{{ task.created_by_name || '-' }}</span>
          </div>
        </div>
        <div class="info-row">
          <div class="info-item">
            <span class="label">创建时间:</span>
            <span class="value">{{ formatDate(task.created_at) }}</span>
          </div>
          <div class="info-item" v-if="task.confirmed_at">
            <span class="label">确认时间:</span>
            <span class="value">{{ formatDate(task.confirmed_at) }}</span>
          </div>
          <div class="info-item" v-if="task.confirmed_by_name">
            <span class="label">操作人:</span>
            <span class="value">{{ task.confirmed_by_name }}</span>
          </div>
        </div>
        <div class="info-row" v-if="task.remark">
          <div class="info-item full-width">
            <span class="label">备注:</span>
            <span class="value">{{ task.remark }}</span>
          </div>
        </div>
        <div class="progress-bar">
          <div class="progress-info">
            <span>盘点进度: {{ task.completed_count }}/{{ task.total_books }}</span>
            <span v-if="task.difference_count > 0" class="difference-info">
              <el-icon><Warning /></el-icon>
              差异: {{ task.difference_count }} 本
            </span>
          </div>
          <el-progress 
            :percentage="task.total_books > 0 ? Math.round((task.completed_count / task.total_books) * 100) : 0"
            :status="task.completed_count === task.total_books ? 'success' : undefined"
          />
        </div>
      </div>

      <div v-if="task" class="entry-tools">
        <div class="tools-left">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索图书名称、作者..."
            clearable
            style="width: 260px"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          <el-select
            v-model="filterStatus"
            placeholder="筛选状态"
            clearable
            style="width: 140px"
          >
            <el-option label="未盘点" value="pending" />
            <el-option label="已盘点" value="completed" />
            <el-option label="有差异" value="difference" />
          </el-select>
        </div>
        <div class="tools-right">
          <el-button
            v-if="canEdit"
            type="primary"
            :disabled="pendingItems.length === 0"
            @click="handleBatchFillExpected"
          >
            <el-icon><CopyDocument /></el-icon>
            批量填充账面库存
          </el-button>
          <el-button
            v-if="canEdit"
            type="success"
            @click="handleSaveBatch"
            :loading="saving"
            :disabled="modifiedItems.size === 0"
          >
            <el-icon><Upload /></el-icon>
            保存修改 ({{ modifiedItems.size }})
          </el-button>
        </div>
      </div>

      <div v-if="task" class="items-table-container">
        <el-table
          :data="filteredItems"
          stripe
          style="width: 100%"
          :row-class-name="getRowClassName"
          height="500"
        >
          <el-table-column prop="id" label="ID" width="70" />
          <el-table-column label="封面" width="80">
            <template #default="{ row }">
              <img
                :src="row.book?.cover_image || defaultCover"
                :alt="row.book?.title"
                class="book-thumbnail"
                @error="handleImageError"
              >
            </template>
          </el-table-column>
          <el-table-column label="图书名称" min-width="180">
            <template #default="{ row }">
              <span class="book-title">{{ row.book?.title }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="book.author" label="作者" width="120" />
          <el-table-column label="分类" width="100">
            <template #default="{ row }">
              <el-tag v-if="row.book?.category" size="small">{{ row.book.category }}</el-tag>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column label="账面库存" width="120" align="center">
            <template #default="{ row }">
              <span class="expected-stock">{{ row.expected_stock }}</span>
            </template>
          </el-table-column>
          <el-table-column label="实际库存" width="150" align="center">
            <template #default="{ row }">
              <el-input-number
                v-if="canEdit"
                v-model="row.actual_stock"
                :min="0"
                size="small"
                controls-position="right"
                style="width: 130px"
                @change="handleStockChange(row)"
                placeholder="请输入"
              />
              <span v-else class="actual-stock">
                {{ row.actual_stock !== null ? row.actual_stock : '-' }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="差异数量" width="120" align="center">
            <template #default="{ row }">
              <span
                :class="{
                  'difference-positive': row.difference !== null && row.difference > 0,
                  'difference-negative': row.difference !== null && row.difference < 0,
                  'difference-zero': row.difference === 0
                }"
                class="difference-value"
              >
                {{ row.difference !== null ? (row.difference > 0 ? '+' + row.difference : row.difference) : '-' }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="100" align="center">
            <template #default="{ row }">
              <el-tag
                v-if="row.actual_stock === null"
                type="info"
                size="small"
              >
                未盘点
              </el-tag>
              <el-tag
                v-else-if="row.difference !== 0"
                type="danger"
                size="small"
              >
                有差异
              </el-tag>
              <el-tag
                v-else
                type="success"
                size="small"
              >
                已核对
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="快捷操作" width="100" align="center" v-if="canEdit">
            <template #default="{ row }">
              <el-button
                link
                type="primary"
                size="small"
                @click="handleQuickFill(row)"
              >
                等于账面
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <el-empty
        v-if="task && task.items.length === 0"
        description="暂无盘点图书"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '@/api'
import type { StockTaking, StockTakingItem } from '@/types'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  ArrowLeft, Check, Close, VideoPlay, Search, Warning, 
  CopyDocument, Upload 
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const starting = ref(false)
const confirming = ref(false)
const cancelling = ref(false)
const saving = ref(false)

const task = ref<StockTaking | null>(null)
const searchKeyword = ref('')
const filterStatus = ref('')
const modifiedItems = ref<Set<number>>(new Set())

const defaultCover = 'https://via.placeholder.com/60x80/6366f1/ffffff?text=Book'

const canEdit = computed(() => {
  return task.value?.status === 'draft' || task.value?.status === 'in_progress'
})

const pendingItems = computed(() => {
  return task.value?.items.filter(item => item.actual_stock === null) || []
})

const filteredItems = computed(() => {
  if (!task.value) return []
  
  let items = [...task.value.items]
  
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    items = items.filter(item => 
      item.book?.title.toLowerCase().includes(keyword) ||
      item.book?.author.toLowerCase().includes(keyword)
    )
  }
  
  if (filterStatus.value) {
    switch (filterStatus.value) {
      case 'pending':
        items = items.filter(item => item.actual_stock === null)
        break
      case 'completed':
        items = items.filter(item => item.actual_stock !== null)
        break
      case 'difference':
        items = items.filter(item => item.difference !== null && item.difference !== 0)
        break
    }
  }
  
  return items
})

function getStatusType(status: string): 'success' | 'warning' | 'info' | 'danger' {
  switch (status) {
    case 'draft': return 'info'
    case 'in_progress': return 'warning'
    case 'confirmed': return 'success'
    case 'cancelled': return 'danger'
    default: return 'info'
  }
}

function getStatusText(status: string): string {
  switch (status) {
    case 'draft': return '草稿'
    case 'in_progress': return '盘点中'
    case 'confirmed': return '已确认'
    case 'cancelled': return '已取消'
    default: return status
  }
}

function getScopeText(scope: string): string {
  const scopeMap: Record<string, string> = {
    all: '全库盘点',
    category: '按分类盘点',
    low_stock: '低库存盘点',
    custom: '自定义范围'
  }
  return scopeMap[scope] || scope
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleString('zh-CN')
}

function getRowClassName({ row }: { row: StockTakingItem }) {
  if (row.difference !== null && row.difference !== 0) {
    return 'row-difference'
  }
  if (row.actual_stock === null) {
    return 'row-pending'
  }
  return ''
}

function handleImageError(e: Event) {
  const img = e.target as HTMLImageElement
  img.src = defaultCover
}

function handleStockChange(row: StockTakingItem) {
  if (row.actual_stock !== null) {
    row.difference = row.actual_stock - row.expected_stock
  } else {
    row.difference = null
  }
  modifiedItems.value.add(row.id)
}

function handleQuickFill(row: StockTakingItem) {
  row.actual_stock = row.expected_stock
  row.difference = 0
  modifiedItems.value.add(row.id)
  ElMessage.success('已填充为账面库存')
}

function handleBatchFillExpected() {
  pendingItems.value.forEach(item => {
    item.actual_stock = item.expected_stock
    item.difference = 0
    modifiedItems.value.add(item.id)
  })
  ElMessage.success(`已批量填充 ${pendingItems.value.length} 本图书`)
}

async function handleSaveBatch() {
  if (!task.value || modifiedItems.value.size === 0) return
  
  const items = task.value.items
    .filter(item => modifiedItems.value.has(item.id) && item.actual_stock !== null)
    .map(item => ({
      item_id: item.id,
      actual_stock: item.actual_stock!
    }))
  
  if (items.length === 0) {
    ElMessage.warning('没有需要保存的修改')
    return
  }
  
  saving.value = true
  try {
    const result = await api.batchEntryStock(task.value.id, { items })
    task.value = result
    modifiedItems.value.clear()
    ElMessage.success('保存成功')
  } catch (error) {
    console.error('保存失败:', error)
  } finally {
    saving.value = false
  }
}

async function handleStart() {
  if (!task.value) return
  
  try {
    await ElMessageBox.confirm(
      '确认开始盘点吗？开始后任务状态将变为「盘点中」',
      '确认操作',
      {
        confirmButtonText: '确认开始',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    starting.value = true
    const result = await api.startStockTaking(task.value.id)
    task.value = result
    ElMessage.success('盘点已开始')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('开始失败:', error)
    }
  } finally {
    starting.value = false
  }
}

async function handleConfirm() {
  if (!task.value) return
  
  const uncompleted = task.value.items.filter(item => item.actual_stock === null)
  if (uncompleted.length > 0) {
    ElMessage.warning(`还有 ${uncompleted.length} 本图书未完成盘点，请全部录入后再确认`)
    return
  }
  
  const differences = task.value.items.filter(item => item.difference !== 0)
  const diffMessage = differences.length > 0 
    ? `\n\n本次盘点发现 ${differences.length} 本图书存在差异，确认后将批量修正图书库存。`
    : ''
  
  try {
    await ElMessageBox.confirm(
      `确认完成盘点吗？确认后将不可修改。${diffMessage}`,
      '确认盘点',
      {
        confirmButtonText: '确认完成',
        cancelButtonText: '取消',
        type: 'warning',
        dangerouslyUseHTMLString: true
      }
    )
    
    confirming.value = true
    const result = await api.confirmStockTaking(task.value.id)
    task.value = result
    ElMessage.success('盘点已确认，库存已更新')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('确认失败:', error)
    }
  } finally {
    confirming.value = false
  }
}

async function handleCancel() {
  if (!task.value) return
  
  try {
    await ElMessageBox.confirm(
      '确认取消该盘点任务吗？取消后将不可恢复。',
      '确认取消',
      {
        confirmButtonText: '确认取消',
        cancelButtonText: '返回',
        type: 'error'
      }
    )
    
    cancelling.value = true
    const result = await api.cancelStockTaking(task.value.id)
    task.value = result
    ElMessage.success('盘点已取消')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('取消失败:', error)
    }
  } finally {
    cancelling.value = false
  }
}

function goBack() {
  router.back()
}

async function fetchTask() {
  const id = Number(route.params.id)
  if (!id) return
  
  loading.value = true
  try {
    task.value = await api.getStockTaking(id)
  } catch (error) {
    console.error('获取任务详情失败:', error)
    ElMessage.error('获取任务详情失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchTask()
})
</script>

<style scoped>
.stock-taking-detail {
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

.header-actions {
  display: flex;
  gap: 12px;
}

.detail-content {
  background: var(--bg-card);
  border-radius: 12px;
  padding: 24px;
}

.task-info-card {
  background: var(--bg-page);
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
}

.info-row {
  display: flex;
  gap: 40px;
  margin-bottom: 12px;
}

.info-row:last-child {
  margin-bottom: 0;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.info-item.full-width {
  flex: 1;
}

.label {
  color: var(--text-secondary);
  font-size: 14px;
  min-width: 70px;
}

.value {
  color: var(--text-primary);
  font-weight: 500;
}

.progress-bar {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--border-color);
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 14px;
}

.difference-info {
  color: var(--danger-color);
  display: flex;
  align-items: center;
  gap: 4px;
}

.entry-tools {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding: 16px;
  background: var(--bg-page);
  border-radius: 8px;
}

.tools-left,
.tools-right {
  display: flex;
  gap: 12px;
  align-items: center;
}

.items-table-container {
  border-radius: 8px;
  overflow: hidden;
}

.book-thumbnail {
  width: 50px;
  height: 65px;
  object-fit: cover;
  border-radius: 4px;
}

.book-title {
  font-weight: 500;
  color: var(--text-primary);
}

.expected-stock {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.actual-stock {
  font-size: 16px;
  font-weight: 600;
  color: var(--primary-color);
}

.difference-value {
  font-size: 16px;
  font-weight: 700;
}

.difference-positive {
  color: var(--success-color);
}

.difference-negative {
  color: var(--danger-color);
}

.difference-zero {
  color: var(--text-secondary);
}

:deep(.row-difference) {
  background-color: rgba(239, 68, 68, 0.08) !important;
}

:deep(.row-difference:hover) {
  background-color: rgba(239, 68, 68, 0.12) !important;
}

:deep(.row-pending) {
  background-color: rgba(250, 204, 21, 0.06);
}
</style>
