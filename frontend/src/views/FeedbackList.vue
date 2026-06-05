<template>
  <div class="feedback-list-page">
    <div class="page-header">
      <div class="header-left">
        <h1>我的反馈</h1>
        <p class="page-desc">查看您提交的所有客服反馈及处理进度</p>
      </div>
      <el-button type="primary" size="large" @click="router.push('/feedback/submit')">
        <el-icon><Plus /></el-icon>
        提交新反馈
      </el-button>
    </div>

    <el-card class="filter-card">
      <div class="filter-bar">
        <el-select
          v-model="filterStatus"
          placeholder="处理状态"
          clearable
          @change="fetchFeedbacks"
          style="width: 150px"
        >
          <el-option
            v-for="item in statusOptions"
            :key="item.value"
            :label="item.label"
            :value="item.value"
          />
        </el-select>

        <el-select
          v-model="filterType"
          placeholder="问题类型"
          clearable
          @change="fetchFeedbacks"
          style="width: 150px"
        >
          <el-option
            v-for="item in typeOptions"
            :key="item.value"
            :label="item.label"
            :value="item.value"
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

        <el-button @click="resetFilters">
          <el-icon><Refresh /></el-icon>
          重置
        </el-button>
      </div>
    </el-card>

    <el-table
      :data="feedbacks"
      v-loading="loading"
      stripe
      style="width: 100%; margin-top: 16px"
      class="feedback-table"
    >
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="title" label="标题" min-width="200">
        <template #default="{ row }">
          <div class="feedback-title">
            <el-tag :type="getTypeTagType(row.type)" size="small" class="type-tag">
              {{ getTypeText(row.type) }}
            </el-tag>
            <span class="title-text">{{ row.title }}</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="getStatusTagType(row.status)" size="small">
            {{ getStatusText(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="关联信息" width="180">
        <template #default="{ row }">
          <div class="related-info">
            <span v-if="row.related_order_id" class="related-item">
              <el-icon><ShoppingCart /></el-icon>
              订单: {{ row.related_order_id }}
            </span>
            <span v-if="row.related_book" class="related-item">
              <el-icon><Collection /></el-icon>
              图书: {{ row.related_book.title }}
            </span>
            <span v-if="!row.related_order_id && !row.related_book" class="no-related">
              -
            </span>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="附件" width="80" align="center">
        <template #default="{ row }">
          <span v-if="row.attachments.length > 0" class="attachment-count">
            <el-icon><Picture /></el-icon>
            {{ row.attachments.length }}
          </span>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column label="回复数" width="80" align="center">
        <template #default="{ row }">
          <el-badge :value="row.replies.length" :max="99" />
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="提交时间" width="180">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="120" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="viewDetail(row.id)">
            查看详情
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next"
        @current-change="fetchFeedbacks"
      />
    </div>

    <el-dialog
      v-model="detailVisible"
      title="反馈详情"
      width="900px"
      destroy-on-close
      class="feedback-detail-dialog"
    >
      <div v-if="currentFeedback" class="feedback-detail">
        <div class="detail-header">
          <div class="detail-title">
            <el-tag :type="getTypeTagType(currentFeedback.type)" size="large" class="type-tag">
              {{ getTypeText(currentFeedback.type) }}
            </el-tag>
            <h2>{{ currentFeedback.title }}</h2>
          </div>
          <el-tag :type="getStatusTagType(currentFeedback.status)" size="large" effect="dark">
            {{ getStatusText(currentFeedback.status) }}
          </el-tag>
        </div>

        <div class="detail-meta">
          <span class="meta-item">
            <el-icon><User /></el-icon>
            {{ currentFeedback.username }}
          </span>
          <span class="meta-item">
            <el-icon><Clock /></el-icon>
            {{ formatDate(currentFeedback.created_at) }}
          </span>
          <span v-if="currentFeedback.contact_info" class="meta-item">
            <el-icon><Phone /></el-icon>
            {{ currentFeedback.contact_info }}
          </span>
          <span v-if="currentFeedback.related_order_id" class="meta-item">
            <el-icon><ShoppingCart /></el-icon>
            订单: {{ currentFeedback.related_order_id }}
          </span>
          <span v-if="currentFeedback.related_book" class="meta-item">
            <el-icon><Collection /></el-icon>
            图书: {{ currentFeedback.related_book.title }}
          </span>
        </div>

        <div class="detail-section">
          <h3>问题描述</h3>
          <p class="description-text">{{ currentFeedback.description }}</p>
        </div>

        <div v-if="currentFeedback.attachments.length > 0" class="detail-section">
          <h3>
            <el-icon><Picture /></el-icon>
            图片附件 ({{ currentFeedback.attachments.length }})
          </h3>
          <div class="attachment-list">
            <div
              v-for="att in currentFeedback.attachments"
              :key="att.id"
              class="attachment-item"
              @click="previewImage(att.file_path)"
            >
              <img :src="att.file_path" :alt="att.file_name" />
              <div class="attachment-name">{{ att.file_name }}</div>
            </div>
          </div>
        </div>

        <div class="detail-section">
          <h3>
            <el-icon><ChatDotRound /></el-icon>
            回复记录 ({{ currentFeedback.replies.length }})
          </h3>
          <div v-if="currentFeedback.replies.length > 0" class="timeline">
            <el-timeline>
              <el-timeline-item
                v-for="reply in currentFeedback.replies"
                :key="reply.id"
                :timestamp="formatDate(reply.created_at)"
                :type="reply.replier_type === 'admin' ? 'primary' : 'success'"
              >
                <div class="reply-item" :class="{ 'is-admin': reply.replier_type === 'admin' }">
                  <div class="reply-header">
                    <el-tag
                      :type="reply.replier_type === 'admin' ? 'primary' : 'success'"
                      size="small"
                    >
                      {{ reply.replier_type === 'admin' ? '客服' : '用户' }}
                    </el-tag>
                    <span class="replier-name">{{ reply.replier_name }}</span>
                    <el-tag
                      v-if="reply.status_change"
                      type="warning"
                      size="small"
                      effect="light"
                    >
                      状态变更: {{ getStatusText(reply.status_change) }}
                    </el-tag>
                  </div>
                  <div class="reply-content">{{ reply.content }}</div>
                </div>
              </el-timeline-item>
            </el-timeline>
          </div>
          <el-empty v-else description="暂无回复记录" :image-size="100" />
        </div>

        <div v-if="currentFeedback.status !== 'closed'" class="reply-section">
          <el-input
            v-model="replyContent"
            type="textarea"
            :rows="3"
            placeholder="输入您的回复..."
            maxlength="1000"
            show-word-limit
          />
          <div class="reply-actions">
            <el-button
              type="primary"
              :loading="submittingReply"
              :disabled="!replyContent.trim()"
              @click="submitReply"
            >
              <el-icon><Promotion /></el-icon>
              发送回复
            </el-button>
          </div>
        </div>

        <div v-if="currentFeedback.status === 'closed'" class="closed-notice">
          <el-alert
            title="此反馈已关闭"
            type="info"
            :closable="false"
            show-icon
          />
        </div>
      </div>
    </el-dialog>

    <el-image-viewer
      v-if="previewVisible"
      :url-list="previewImages"
      :initial-index="previewIndex"
      @close="previewVisible = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/api'
import type { Feedback, FeedbackTypeOption, FeedbackStatusOption } from '@/types'
import { ElMessage } from 'element-plus'
import {
  Plus,
  Refresh,
  Picture,
  User,
  Clock,
  Phone,
  ShoppingCart,
  Collection,
  ChatDotRound,
  Promotion
} from '@element-plus/icons-vue'

const router = useRouter()

const loading = ref(false)
const feedbacks = ref<Feedback[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)

const filterStatus = ref('')
const filterType = ref('')
const dateRange = ref<string[]>([])
const startDate = ref('')
const endDate = ref('')

const typeOptions = ref<FeedbackTypeOption[]>([])
const statusOptions = ref<FeedbackStatusOption[]>([])

const detailVisible = ref(false)
const currentFeedback = ref<Feedback | null>(null)
const replyContent = ref('')
const submittingReply = ref(false)

const previewVisible = ref(false)
const previewImages = ref<string[]>([])
const previewIndex = ref(0)

onMounted(async () => {
  await Promise.all([fetchTypeOptions(), fetchStatusOptions(), fetchFeedbacks()])
})

async function fetchTypeOptions() {
  try {
    typeOptions.value = await api.getFeedbackTypes()
  } catch (error) {
    console.error('获取反馈类型失败:', error)
  }
}

async function fetchStatusOptions() {
  try {
    statusOptions.value = await api.getFeedbackStatuses()
  } catch (error) {
    console.error('获取状态列表失败:', error)
  }
}

async function fetchFeedbacks() {
  loading.value = true
  try {
    const response = await api.getMyFeedbacks({
      page: currentPage.value,
      page_size: pageSize.value,
      status: filterStatus.value || undefined,
      type: filterType.value || undefined,
      start_date: startDate.value || undefined,
      end_date: endDate.value || undefined
    })
    feedbacks.value = response.items
    total.value = response.total
  } catch (error) {
    console.error('获取反馈列表失败:', error)
    ElMessage.error('获取反馈列表失败')
  } finally {
    loading.value = false
  }
}

function handleDateChange(val: string[] | null) {
  if (val && val.length === 2) {
    startDate.value = val[0]
    endDate.value = val[1]
  } else {
    startDate.value = ''
    endDate.value = ''
  }
  fetchFeedbacks()
}

function resetFilters() {
  filterStatus.value = ''
  filterType.value = ''
  dateRange.value = []
  startDate.value = ''
  endDate.value = ''
  currentPage.value = 1
  fetchFeedbacks()
}

async function viewDetail(id: number) {
  try {
    currentFeedback.value = await api.getFeedback(id)
    replyContent.value = ''
    detailVisible.value = true
  } catch (error) {
    console.error('获取反馈详情失败:', error)
    ElMessage.error('获取反馈详情失败')
  }
}

async function submitReply() {
  if (!currentFeedback.value || !replyContent.value.trim()) return

  submittingReply.value = true
  try {
    const newReply = await api.replyFeedback(currentFeedback.value.id, replyContent.value.trim())
    currentFeedback.value.replies.push(newReply)
    
    if (newReply.status_change) {
      currentFeedback.value.status = newReply.status_change as Feedback['status']
    } else if (currentFeedback.value.status === 'replied') {
      currentFeedback.value.status = 'processing'
    }
    
    replyContent.value = ''
    ElMessage.success('回复发送成功')
    fetchFeedbacks()
  } catch (error) {
    console.error('发送回复失败:', error)
    ElMessage.error('发送回复失败')
  } finally {
    submittingReply.value = false
  }
}

function previewImage(url: string) {
  if (currentFeedback.value) {
    previewImages.value = currentFeedback.value.attachments.map(a => a.file_path)
    previewIndex.value = previewImages.value.indexOf(url)
    previewVisible.value = true
  }
}

function getTypeText(type: string): string {
  const item = typeOptions.value.find(t => t.value === type)
  return item?.label || type
}

function getStatusText(status: string): string {
  const item = statusOptions.value.find(s => s.value === status)
  return item?.label || status
}

function getTypeTagType(type: string): 'primary' | 'success' | 'warning' | 'danger' | 'info' {
  const typeMap: Record<string, 'primary' | 'success' | 'warning' | 'danger' | 'info'> = {
    product: 'primary',
    order: 'success',
    account: 'warning',
    payment: 'danger',
    other: 'info'
  }
  return typeMap[type] || 'info'
}

function getStatusTagType(status: string): 'primary' | 'success' | 'warning' | 'danger' | 'info' {
  const statusMap: Record<string, 'primary' | 'success' | 'warning' | 'danger' | 'info'> = {
    pending: 'warning',
    processing: 'primary',
    replied: 'success',
    closed: 'info'
  }
  return statusMap[status] || 'info'
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleString('zh-CN')
}
</script>

<style scoped>
.feedback-list-page {
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 24px;
}

.page-header h1 {
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 4px;
  background: var(--gradient-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.page-desc {
  color: var(--text-secondary);
  font-size: 14px;
}

.filter-card {
  margin-bottom: 16px;
}

.filter-bar {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.feedback-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.type-tag {
  flex-shrink: 0;
}

.title-text {
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.related-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.related-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.no-related {
  color: var(--text-tertiary);
}

.attachment-count {
  display: flex;
  align-items: center;
  gap: 4px;
  color: var(--primary-color);
  font-size: 14px;
}

.pagination {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}

.feedback-detail-dialog :deep(.el-dialog__body) {
  max-height: 70vh;
  overflow-y: auto;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-color);
}

.detail-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.detail-title h2 {
  font-size: 20px;
  font-weight: 600;
  margin: 0;
}

.detail-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  padding: 12px 16px;
  background: var(--bg-secondary);
  border-radius: 8px;
  margin-bottom: 20px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 14px;
  color: var(--text-secondary);
}

.detail-section {
  margin-bottom: 24px;
}

.detail-section h3 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--text-primary);
}

.description-text {
  line-height: 1.8;
  color: var(--text-primary);
  padding: 16px;
  background: var(--bg-secondary);
  border-radius: 8px;
  white-space: pre-wrap;
  word-break: break-word;
}

.attachment-list {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.attachment-item {
  width: 120px;
  cursor: pointer;
  transition: transform 0.2s;
}

.attachment-item:hover {
  transform: scale(1.02);
}

.attachment-item img {
  width: 120px;
  height: 120px;
  object-fit: cover;
  border-radius: 8px;
}

.attachment-name {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.timeline {
  padding: 8px 0;
}

.reply-item {
  padding: 12px 16px;
  background: var(--bg-secondary);
  border-radius: 8px;
}

.reply-item.is-admin {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.08), rgba(99, 102, 241, 0.02));
  border-left: 3px solid var(--primary-color);
}

.reply-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.replier-name {
  font-weight: 500;
  color: var(--text-primary);
}

.reply-content {
  line-height: 1.6;
  color: var(--text-primary);
  white-space: pre-wrap;
  word-break: break-word;
}

.reply-section {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid var(--border-color);
}

.reply-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
}

.closed-notice {
  margin-top: 16px;
}
</style>
