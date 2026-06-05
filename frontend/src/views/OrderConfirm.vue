<template>
  <div class="order-confirm" v-loading="loading">
    <div class="page-header">
      <el-button @click="goBack" link>
        <el-icon><ArrowLeft /></el-icon>
        返回
      </el-button>
      <h1>确认订单</h1>
    </div>

    <div class="order-content">
      <el-card class="address-section">
        <template #header>
          <div class="card-header">
            <span class="card-title">
              <el-icon><Location /></el-icon>
              收货地址
            </span>
          </div>
        </template>
        <AddressSelector
          v-model="selectedAddress"
          @change="handleAddressChange"
        />
      </el-card>

      <el-card class="goods-section">
        <template #header>
          <div class="card-header">
            <span class="card-title">
              <el-icon><Goods /></el-icon>
              商品信息
            </span>
          </div>
        </template>
        <el-table :data="goodsList" border stripe>
          <el-table-column label="商品" min-width="200">
            <template #default="{ row }">
              <div class="goods-info">
                <img
                  :src="row.cover_image || defaultCover"
                  :alt="row.title"
                  class="goods-cover"
                  @error="handleImageError"
                />
                <div class="goods-meta">
                  <div class="goods-title">{{ row.title }}</div>
                  <div class="goods-author">{{ row.author }}</div>
                </div>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="单价" width="120" align="center">
            <template #default="{ row }">
              ¥{{ row.price.toFixed(2) }}
            </template>
          </el-table-column>
          <el-table-column label="数量" width="120" align="center">
            <template #default="{ row }">
              <el-input-number
                v-model="row.quantity"
                :min="1"
                :max="row.stock"
                :precision="0"
                controls-position="right"
                size="small"
                @change="calculateTotal"
              />
            </template>
          </el-table-column>
          <el-table-column label="小计" width="130" align="center">
            <template #default="{ row }">
              <span class="price">¥{{ (row.price * row.quantity).toFixed(2) }}</span>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <el-card class="summary-section">
        <div class="summary-content">
          <div class="summary-row">
            <span class="summary-label">商品总计：</span>
            <span class="summary-value">¥{{ totalAmount.toFixed(2) }}</span>
          </div>
          <div class="summary-row">
            <span class="summary-label">运费：</span>
            <span class="summary-value free">包邮</span>
          </div>
          <div class="summary-row total">
            <span class="summary-label">应付金额：</span>
            <span class="summary-value total-price">¥{{ totalAmount.toFixed(2) }}</span>
          </div>
        </div>
        <div class="submit-section">
          <el-button
            type="primary"
            size="large"
            :disabled="!selectedAddress || goodsList.length === 0"
            @click="handleSubmitOrder"
          >
            提交订单
          </el-button>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/api'
import type { UserAddress, Book } from '@/types'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Location, Goods } from '@element-plus/icons-vue'
import AddressSelector from '@/components/AddressSelector.vue'

const router = useRouter()

const loading = ref(false)
const selectedAddress = ref<UserAddress | null>(null)
const defaultCover = 'https://via.placeholder.com/60x80/6366f1/ffffff?text=Book'

interface GoodsItem extends Book {
  quantity: number
}

const goodsList = reactive<GoodsItem[]>([])

const totalAmount = computed(() => {
  return goodsList.reduce((sum, item) => sum + item.price * item.quantity, 0)
})

async function fetchBooks() {
  loading.value = true
  try {
    const response = await api.getBooks({ page_size: 5 })
    goodsList.splice(0, goodsList.length, ...response.items.map(book => ({
      ...book,
      quantity: 1
    })))
  } catch (error) {
    console.error('获取商品列表失败:', error)
  } finally {
    loading.value = false
  }
}

function calculateTotal() {
}

function handleAddressChange(address: UserAddress) {
  console.log('选择的地址:', address)
}

function handleImageError(e: Event) {
  const target = e.target as HTMLImageElement
  target.src = defaultCover
}

function goBack() {
  router.back()
}

function handleSubmitOrder() {
  if (!selectedAddress.value) {
    ElMessage.warning('请选择收货地址')
    return
  }

  if (goodsList.length === 0) {
    ElMessage.warning('请选择商品')
    return
  }

  ElMessage.success('订单提交成功！（演示）')
  console.log('订单信息：', {
    address: selectedAddress.value,
    goods: goodsList,
    total: totalAmount.value
  })
}

onMounted(() => {
  fetchBooks()
})
</script>

<style scoped>
.order-confirm {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.page-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 8px;
}

.page-header h1 {
  flex: 1;
  font-size: 24px;
  font-weight: 600;
  margin: 0;
}

.order-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.card-header {
  display: flex;
  align-items: center;
}

.card-title {
  font-weight: 600;
  font-size: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.goods-info {
  display: flex;
  gap: 12px;
  align-items: center;
}

.goods-cover {
  width: 50px;
  height: 70px;
  object-fit: cover;
  border-radius: 4px;
}

.goods-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.goods-title {
  font-weight: 500;
}

.goods-author {
  color: var(--text-secondary);
  font-size: 13px;
}

.price {
  color: var(--secondary-color);
  font-weight: 600;
}

.summary-section {
  background: #fff;
}

.summary-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 20px;
  border-bottom: 1px solid var(--border-color);
}

.summary-row {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 16px;
}

.summary-label {
  color: var(--text-secondary);
  font-size: 15px;
}

.summary-value {
  font-size: 15px;
  color: var(--text-primary);
  min-width: 100px;
  text-align: right;
}

.summary-value.free {
  color: var(--success-color);
}

.summary-row.total {
  padding-top: 12px;
  border-top: 1px dashed var(--border-color);
}

.summary-row.total .summary-label {
  font-size: 17px;
  font-weight: 600;
  color: var(--text-primary);
}

.total-price {
  font-size: 24px;
  font-weight: 700;
  color: var(--danger-color) !important;
}

.submit-section {
  display: flex;
  justify-content: flex-end;
  padding: 20px;
}
</style>
