<template>
  <div class="promotion-detail" v-loading="loading">
    <div v-if="promotion" class="detail-container">
      <div class="promotion-header">
        <div class="promotion-cover">
          <img
            :src="promotion.cover_image || defaultCover"
            :alt="promotion.name"
            @error="handleImageError"
          >
        </div>
        <div class="promotion-info">
          <div class="status-bar">
            <el-tag :type="getStatusType(promotion.status)" effect="dark" size="large">
              {{ getStatusText(promotion.status) }}
            </el-tag>
            <span v-if="promotion.is_displayed === false" class="hidden-tag">
              <el-tag type="info" size="small">已隐藏</el-tag>
            </span>
          </div>
          
          <h1 class="promotion-title">{{ promotion.name }}</h1>
          
          <div class="promotion-time">
            <el-icon><Clock /></el-icon>
            <span>活动时间：{{ formatFullDate(promotion.start_time) }} - {{ formatFullDate(promotion.end_time) }}</span>
          </div>
          
          <div class="countdown-section" v-if="promotion.status !== 'ended'">
            <div class="countdown-title">
              {{ promotion.status === 'pending' ? '距离活动开始' : '距离活动结束' }}
            </div>
            <div class="countdown-display">
              <div class="countdown-item">
                <span class="countdown-number">{{ countdown.days }}</span>
                <span class="countdown-label">天</span>
              </div>
              <div class="countdown-item">
                <span class="countdown-number">{{ countdown.hours }}</span>
                <span class="countdown-label">时</span>
              </div>
              <div class="countdown-item">
                <span class="countdown-number">{{ countdown.minutes }}</span>
                <span class="countdown-label">分</span>
              </div>
              <div class="countdown-item">
                <span class="countdown-number">{{ countdown.seconds }}</span>
                <span class="countdown-label">秒</span>
              </div>
            </div>
          </div>
          
          <div class="promotion-ended-notice" v-if="promotion.status === 'ended'">
            <el-icon><Warning /></el-icon>
            <span>活动已结束，感谢参与！</span>
          </div>
          
          <div v-if="promotion.description" class="promotion-description">
            <h3>活动说明</h3>
            <p>{{ promotion.description }}</p>
          </div>
        </div>
      </div>
      
      <div class="books-section">
        <div class="section-header">
          <h2>参与图书</h2>
          <span class="book-count">共 {{ promotion.books.length }} 本图书</span>
        </div>
        
        <div class="books-grid">
          <el-row :gutter="24">
            <el-col v-for="promoBook in promotion.books" :key="promoBook.id" :xs="24" :sm="12" :md="8" :lg="6">
              <div class="book-card">
                <div class="book-cover" @click="goToBookDetail(promoBook.book_id)">
                  <img
                    :src="promoBook.book?.cover_image || defaultBookCover"
                    :alt="promoBook.book?.title"
                    @error="handleBookImageError"
                  >
                  <div class="discount-badge">
                    {{ getDiscount(promoBook.original_price, promoBook.promotion_price) }}折
                  </div>
                </div>
                <div class="book-info">
                  <h4 class="book-title" @click="goToBookDetail(promoBook.book_id)">
                    {{ promoBook.book?.title }}
                  </h4>
                  <p class="book-author">{{ promoBook.book?.author }}</p>
                  <div class="price-section">
                    <span class="original-price">¥{{ promoBook.original_price?.toFixed(2) }}</span>
                    <span class="promotion-price">¥{{ promoBook.promotion_price.toFixed(2) }}</span>
                    <span class="save-amount">省¥{{ (promoBook.original_price! - promoBook.promotion_price).toFixed(2) }}</span>
                  </div>
                  <div class="stock-section">
                    <div class="stock-info">
                      <span class="stock-label">剩余库存：</span>
                      <span class="stock-value" :class="{ 'low-stock': promoBook.remaining_stock! <= 10 }">
                        {{ promoBook.remaining_stock }} 件
                      </span>
                    </div>
                    <div class="stock-progress">
                      <el-progress
                        :percentage="getStockPercentage(promoBook)"
                        :stroke-width="6"
                        :color="getStockColor(promoBook)"
                        show-text="false"
                      />
                    </div>
                  </div>
                  <div v-if="promoBook.purchase_limit" class="limit-section">
                    <el-icon><Tickets /></el-icon>
                    <span>每单限购 {{ promoBook.purchase_limit }} 件</span>
                  </div>
                  <div class="action-section">
                    <el-input-number
                      v-model="purchaseQuantities[promoBook.id]"
                      :min="1"
                      :max="getMaxQuantity(promoBook)"
                      :disabled="!canPurchase(promoBook)"
                      controls-position="right"
                      style="width: 120px"
                    />
                    <el-button
                      type="primary"
                      :disabled="!canPurchase(promoBook)"
                      :loading="deductingId === promoBook.id"
                      @click="handlePurchase(promoBook)"
                    >
                      <el-icon><ShoppingCart /></el-icon>
                      {{ getButtonText(promoBook) }}
                    </el-button>
                  </div>
                  <div v-if="!canPurchase(promoBook)" class="purchase-disabled-reason">
                    {{ getDisabledReason(promoBook) }}
                  </div>
                </div>
              </div>
            </el-col>
          </el-row>
        </div>
        
        <el-empty v-if="promotion.books.length === 0" description="暂无参与图书" />
      </div>
    </div>
    
    <el-empty v-if="!loading && !promotion" description="活动不存在" />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '@/api'
import type { Promotion, PromotionBook } from '@/types'
import { ElMessage } from 'element-plus'
import {
  Clock, Warning, Tickets, ShoppingCart
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const promotion = ref<Promotion | null>(null)
const defaultCover = 'https://via.placeholder.com/600x300/6366f1/ffffff?text=Promotion'
const defaultBookCover = 'https://via.placeholder.com/200x280/6366f1/ffffff?text=Book'

const countdown = reactive({
  days: '00',
  hours: '00',
  minutes: '00',
  seconds: '00'
})

const purchaseQuantities = ref<Record<number, number>>({})
const deductingId = ref<number | null>(null)

let countdownInterval: number | null = null

onMounted(async () => {
  await fetchPromotionDetail()
  startCountdown()
})

onUnmounted(() => {
  stopCountdown()
})

watch(() => route.params.id, () => {
  fetchPromotionDetail()
})

async function fetchPromotionDetail() {
  const id = Number(route.params.id)
  if (!id) return
  
  loading.value = true
  try {
    promotion.value = await api.getPromotion(id)
    
    promotion.value.books.forEach(book => {
      purchaseQuantities.value[book.id] = 1
    })
    
    if (promotion.value.remaining_seconds !== null) {
      updateCountdown(promotion.value.remaining_seconds)
    }
  } catch (error) {
    console.error('获取活动详情失败:', error)
  } finally {
    loading.value = false
  }
}

function startCountdown() {
  countdownInterval = window.setInterval(() => {
    if (!promotion.value) return
    
    let remaining = promotion.value.remaining_seconds ?? 0
    if (remaining > 0) {
      remaining -= 1
      promotion.value.remaining_seconds = remaining
      updateCountdown(remaining)
    } else if (promotion.value.status === 'pending') {
      promotion.value.status = 'active'
      ElMessage.success('活动已开始！')
    } else if (promotion.value.status === 'active') {
      promotion.value.status = 'ended'
      ElMessage.warning('活动已结束！')
      stopCountdown()
    }
  }, 1000)
}

function stopCountdown() {
  if (countdownInterval) {
    clearInterval(countdownInterval)
    countdownInterval = null
  }
}

function updateCountdown(totalSeconds: number) {
  if (totalSeconds <= 0) {
    countdown.days = '00'
    countdown.hours = '00'
    countdown.minutes = '00'
    countdown.seconds = '00'
    return
  }
  
  const days = Math.floor(totalSeconds / 86400)
  const hours = Math.floor((totalSeconds % 86400) / 3600)
  const minutes = Math.floor((totalSeconds % 3600) / 60)
  const seconds = totalSeconds % 60
  
  countdown.days = days.toString().padStart(2, '0')
  countdown.hours = hours.toString().padStart(2, '0')
  countdown.minutes = minutes.toString().padStart(2, '0')
  countdown.seconds = seconds.toString().padStart(2, '0')
}

function formatFullDate(dateStr: string) {
  return new Date(dateStr).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
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
    case 'active': return '火热进行中'
    case 'ended': return '已结束'
    default: return status
  }
}

function getDiscount(originalPrice: number | undefined, promotionPrice: number) {
  if (!originalPrice) return '-'
  return ((promotionPrice / originalPrice) * 10).toFixed(1)
}

function getStockPercentage(promoBook: PromotionBook) {
  if (promoBook.promotion_stock === 0) return 0
  return Math.round((promoBook.remaining_stock! / promoBook.promotion_stock) * 100)
}

function getStockColor(promoBook: PromotionBook) {
  const percentage = getStockPercentage(promoBook)
  if (percentage <= 10) return '#ef4444'
  if (percentage <= 30) return '#f97316'
  return '#10b981'
}

function getMaxQuantity(promoBook: PromotionBook) {
  const remaining = promoBook.remaining_stock ?? 0
  const limit = promoBook.purchase_limit ?? Infinity
  return Math.min(remaining, limit)
}

function canPurchase(promoBook: PromotionBook) {
  if (!promotion.value) return false
  if (promotion.value.status !== 'active') return false
  if (promoBook.remaining_stock === 0) return false
  return true
}

function getButtonText(promoBook: PromotionBook) {
  if (!promotion.value) return '购买'
  if (promotion.value.status === 'pending') return '活动未开始'
  if (promotion.value.status === 'ended') return '活动已结束'
  if (promoBook.remaining_stock === 0) return '已售罄'
  return '立即购买'
}

function getDisabledReason(promoBook: PromotionBook) {
  if (!promotion.value) return ''
  if (promotion.value.status === 'pending') return '活动尚未开始，敬请期待'
  if (promotion.value.status === 'ended') return '活动已结束，无法购买'
  if (promoBook.remaining_stock === 0) return '该图书已售罄'
  return ''
}

async function handlePurchase(promoBook: PromotionBook) {
  if (!promotion.value || !canPurchase(promoBook)) return
  
  const quantity = purchaseQuantities.value[promoBook.id] || 1
  
  deductingId.value = promoBook.id
  try {
    await api.deductPromotionStock(promotion.value.id, promoBook.id, quantity)
    
    promoBook.sold_stock += quantity
    promoBook.remaining_stock = (promoBook.remaining_stock ?? 0) - quantity
    
    ElMessage.success(`购买成功！已扣减 ${quantity} 件库存`)
  } catch (error) {
    console.error('购买失败:', error)
  } finally {
    deductingId.value = null
  }
}

function goToBookDetail(bookId: number) {
  router.push(`/books/${bookId}`)
}

function handleImageError(e: Event) {
  const img = e.target as HTMLImageElement
  img.src = defaultCover
}

function handleBookImageError(e: Event) {
  const img = e.target as HTMLImageElement
  img.src = defaultBookCover
}
</script>

<style scoped>
.promotion-detail {
  min-height: 400px;
}

.detail-container {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.promotion-header {
  display: flex;
  gap: 32px;
  background: var(--bg-secondary);
  border-radius: 20px;
  overflow: hidden;
  box-shadow: var(--shadow);
}

.promotion-cover {
  flex: 0 0 45%;
  min-height: 300px;
  background: linear-gradient(135deg, #667eea, #764ba2);
}

.promotion-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.promotion-info {
  flex: 1;
  padding: 32px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.status-bar {
  display: flex;
  align-items: center;
  gap: 12px;
}

.hidden-tag {
  opacity: 0.7;
}

.promotion-title {
  font-size: 28px;
  font-weight: 700;
  margin: 0;
  color: var(--text-primary);
}

.promotion-time {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-secondary);
  font-size: 15px;
}

.countdown-section {
  background: linear-gradient(135deg, #fef2f2, #fee2e2);
  border-radius: 12px;
  padding: 20px;
  border: 1px solid #fecaca;
}

.countdown-title {
  color: var(--danger-color);
  font-weight: 600;
  margin-bottom: 12px;
  font-size: 15px;
}

.countdown-display {
  display: flex;
  gap: 12px;
}

.countdown-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  background: var(--danger-color);
  color: white;
  border-radius: 8px;
  padding: 8px 16px;
  min-width: 60px;
}

.countdown-number {
  font-size: 24px;
  font-weight: 700;
  font-family: 'Courier New', monospace;
}

.countdown-label {
  font-size: 12px;
  opacity: 0.9;
}

.promotion-ended-notice {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #f3f4f6;
  color: var(--text-secondary);
  padding: 16px;
  border-radius: 8px;
}

.promotion-description h3 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 8px;
  color: var(--text-primary);
}

.promotion-description p {
  color: var(--text-secondary);
  line-height: 1.7;
  margin: 0;
}

.books-section {
  background: var(--bg-secondary);
  border-radius: 16px;
  padding: 24px;
  box-shadow: var(--shadow);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-color);
}

.section-header h2 {
  font-size: 20px;
  font-weight: 600;
  margin: 0;
}

.book-count {
  color: var(--text-secondary);
  font-size: 14px;
}

.books-grid {
  min-height: 300px;
}

.book-card {
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  transition: transform 0.3s, box-shadow 0.3s;
  margin-bottom: 24px;
}

.book-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.book-cover {
  position: relative;
  width: 100%;
  aspect-ratio: 3/4;
  overflow: hidden;
  background: #f1f5f9;
  cursor: pointer;
}

.book-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s;
}

.book-card:hover .book-cover img {
  transform: scale(1.05);
}

.discount-badge {
  position: absolute;
  top: 12px;
  left: 12px;
  background: var(--secondary-color);
  color: white;
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
}

.book-info {
  padding: 16px;
}

.book-title {
  font-size: 15px;
  font-weight: 600;
  margin: 0 0 6px 0;
  cursor: pointer;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  transition: color 0.2s;
}

.book-title:hover {
  color: var(--primary-color);
}

.book-author {
  font-size: 13px;
  color: var(--text-secondary);
  margin: 0 0 12px 0;
}

.price-section {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.original-price {
  color: var(--text-secondary);
  text-decoration: line-through;
  font-size: 13px;
}

.promotion-price {
  color: var(--secondary-color);
  font-size: 22px;
  font-weight: 700;
}

.save-amount {
  background: rgba(239, 68, 68, 0.1);
  color: var(--danger-color);
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.stock-section {
  margin-bottom: 12px;
}

.stock-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
}

.stock-label {
  color: var(--text-secondary);
  font-size: 13px;
}

.stock-value {
  font-weight: 600;
  color: var(--success-color);
  font-size: 13px;
}

.stock-value.low-stock {
  color: var(--danger-color);
}

.limit-section {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #f97316;
  font-size: 12px;
  margin-bottom: 12px;
  padding: 6px 10px;
  background: rgba(249, 115, 22, 0.1);
  border-radius: 6px;
}

.action-section {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}

.purchase-disabled-reason {
  color: var(--text-secondary);
  font-size: 12px;
  text-align: center;
  padding: 8px;
  background: var(--bg-light);
  border-radius: 6px;
}

@media (max-width: 768px) {
  .promotion-header {
    flex-direction: column;
  }
  
  .promotion-cover {
    flex: none;
    height: 200px;
  }
  
  .promotion-info {
    padding: 20px;
  }
  
  .promotion-title {
    font-size: 22px;
  }
  
  .countdown-display {
    gap: 8px;
  }
  
  .countdown-item {
    min-width: 50px;
    padding: 6px 12px;
  }
  
  .countdown-number {
    font-size: 20px;
  }
}
</style>
