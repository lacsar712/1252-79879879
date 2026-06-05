<template>
  <div class="promotions-page">
    <div class="page-header">
      <h1>活动专题</h1>
      <p>精选优惠活动，限时抢购</p>
    </div>

    <div class="filter-tabs">
      <el-tabs v-model="activeStatus" @tab-change="handleStatusChange">
        <el-tab-pane label="全部" name="" />
        <el-tab-pane label="即将开始" name="pending" />
        <el-tab-pane label="进行中" name="active" />
        <el-tab-pane label="已结束" name="ended" />
      </el-tabs>
    </div>

    <div class="promotion-list" v-loading="loading">
      <el-row :gutter="24">
        <el-col v-for="promotion in promotions" :key="promotion.id" :xs="24" :sm="12" :md="8" :lg="6">
          <div class="promotion-card" @click="router.push(`/promotions/${promotion.id}`)">
            <div class="promotion-cover">
              <img
                :src="promotion.cover_image || defaultCover"
                :alt="promotion.name"
                @error="handleImageError"
              >
              <div class="promotion-status-tag">
                <el-tag :type="getStatusType(promotion.status)" effect="dark" size="small">
                  {{ getStatusText(promotion.status) }}
                </el-tag>
              </div>
              <div class="promotion-overlay">
                <el-button type="primary" circle>
                  <el-icon><View /></el-icon>
                </el-button>
              </div>
            </div>
            <div class="promotion-info">
              <h3 class="promotion-title" :title="promotion.name">{{ promotion.name }}</h3>
              <div class="promotion-time">
                <el-icon><Clock /></el-icon>
                <span>{{ formatDate(promotion.start_time) }} - {{ formatDate(promotion.end_time) }}</span>
              </div>
              <div class="promotion-countdown" v-if="promotion.status === 'active' || promotion.status === 'pending'">
                <span class="countdown-label">
                  {{ promotion.status === 'pending' ? '距开始' : '距结束' }}
                </span>
                <span class="countdown-time">
                  {{ getCountdownText(promotion.id, promotion.remaining_seconds) }}
                </span>
              </div>
              <div class="promotion-meta">
                <span class="book-count">
                  <el-icon><Reading /></el-icon>
                  {{ promotion.books.length }} 本图书
                </span>
                <span class="view-link">
                  查看详情
                  <el-icon><ArrowRight /></el-icon>
                </span>
              </div>
            </div>
          </div>
        </el-col>
      </el-row>

      <el-empty v-if="!loading && promotions.length === 0" description="暂无活动" />
    </div>

    <div class="pagination" v-if="total > 0">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[8, 16, 24, 32]"
        :total="total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="fetchPromotions"
        @current-change="fetchPromotions"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/api'
import type { Promotion } from '@/types'
import { View, Clock, Reading, ArrowRight } from '@element-plus/icons-vue'

const router = useRouter()

const loading = ref(false)
const promotions = ref<Promotion[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(8)
const activeStatus = ref('')
const defaultCover = 'https://via.placeholder.com/400x200/6366f1/ffffff?text=Promotion'

const countdownTexts = ref<Map<number, string>>(new Map())

onMounted(async () => {
  await fetchPromotions()
  startCountdownTimer()
})

onUnmounted(() => {
  stopCountdownTimer()
})

async function fetchPromotions() {
  loading.value = true
  try {
    const response = await api.getPromotions({
      page: currentPage.value,
      page_size: pageSize.value,
      status: activeStatus.value || undefined,
      is_displayed: true
    })
    promotions.value = response.items
    total.value = response.total
    
    promotions.value.forEach(p => {
      if (p.remaining_seconds !== null) {
        countdownTexts.value.set(p.id, formatCountdown(p.remaining_seconds))
      }
    })
  } catch (error) {
    console.error('获取活动列表失败:', error)
  } finally {
    loading.value = false
  }
}

function handleStatusChange() {
  currentPage.value = 1
  fetchPromotions()
}

let countdownInterval: number | null = null

function startCountdownTimer() {
  countdownInterval = window.setInterval(() => {
    promotions.value.forEach(promotion => {
      let remaining = promotion.remaining_seconds ?? 0
      if (remaining > 0) {
        remaining -= 1
        promotion.remaining_seconds = remaining
        countdownTexts.value.set(promotion.id, formatCountdown(remaining))
      } else if (promotion.status === 'pending') {
        promotion.status = 'active'
      } else if (promotion.status === 'active') {
        promotion.status = 'ended'
        countdownTexts.value.delete(promotion.id)
      }
    })
  }, 1000)
}

function stopCountdownTimer() {
  if (countdownInterval) {
    clearInterval(countdownInterval)
    countdownInterval = null
  }
}

function formatCountdown(seconds: number): string {
  if (seconds <= 0) return '00:00:00'
  
  const days = Math.floor(seconds / 86400)
  const hours = Math.floor((seconds % 86400) / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60
  
  if (days > 0) {
    return `${days}天 ${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }
  return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

function getCountdownText(promotionId: number, remainingSeconds: number | null): string {
  return countdownTexts.value.get(promotionId) || formatCountdown(remainingSeconds ?? 0)
}

function handleImageError(e: Event) {
  const img = e.target as HTMLImageElement
  img.src = defaultCover
}

function formatDate(dateStr: string) {
  const date = new Date(dateStr)
  return `${date.getMonth() + 1}月${date.getDate()}日 ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
}

function getStatusType(status: string) {
  switch (status) {
    case 'pending': return 'warning'
    case 'active': return 'success'
    case 'ended': return 'info'
    default: return 'info'
  }
}

function getStatusText(status: string) {
  switch (status) {
    case 'pending': return '即将开始'
    case 'active': return '火热进行'
    case 'ended': return '已结束'
    default: return status
  }
}
</script>

<style scoped>
.promotions-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.page-header {
  text-align: center;
  padding: 32px 0;
  background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
  border-radius: 16px;
  color: white;
}

.page-header h1 {
  font-size: 32px;
  font-weight: 700;
  margin-bottom: 8px;
}

.page-header p {
  font-size: 16px;
  opacity: 0.9;
}

.filter-tabs {
  background: var(--bg-secondary);
  border-radius: 12px;
  padding: 0 16px;
}

.filter-tabs :deep(.el-tabs__header) {
  margin: 0;
}

.promotion-list {
  min-height: 400px;
}

.promotion-card {
  background: var(--bg-secondary);
  border-radius: 16px;
  overflow: hidden;
  box-shadow: var(--shadow);
  cursor: pointer;
  transition: transform 0.3s, box-shadow 0.3s;
  margin-bottom: 24px;
}

.promotion-card:hover {
  transform: translateY(-8px);
  box-shadow: var(--shadow-lg);
}

.promotion-card:hover .promotion-overlay {
  opacity: 1;
}

.promotion-cover {
  position: relative;
  width: 100%;
  aspect-ratio: 2/1;
  overflow: hidden;
  background: linear-gradient(135deg, #667eea, #764ba2);
}

.promotion-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.5s;
}

.promotion-card:hover .promotion-cover img {
  transform: scale(1.1);
}

.promotion-status-tag {
  position: absolute;
  top: 12px;
  right: 12px;
}

.promotion-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s;
}

.promotion-info {
  padding: 20px;
}

.promotion-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.promotion-time {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--text-secondary);
  font-size: 13px;
  margin-bottom: 12px;
}

.promotion-countdown {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  background: rgba(239, 68, 68, 0.1);
  border-radius: 8px;
  margin-bottom: 12px;
}

.countdown-label {
  color: var(--text-secondary);
  font-size: 13px;
}

.countdown-time {
  color: var(--danger-color);
  font-weight: 700;
  font-size: 16px;
  font-family: 'Courier New', monospace;
}

.promotion-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid var(--border-color);
}

.book-count {
  display: flex;
  align-items: center;
  gap: 4px;
  color: var(--text-secondary);
  font-size: 13px;
}

.view-link {
  display: flex;
  align-items: center;
  gap: 4px;
  color: var(--primary-color);
  font-size: 13px;
  font-weight: 500;
}

.pagination {
  display: flex;
  justify-content: center;
  padding: 24px 0;
}
</style>
