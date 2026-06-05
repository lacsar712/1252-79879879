<template>
  <div class="compare-page" v-loading="isLoading">
    <div class="page-header">
      <el-button text @click="router.back()">
        <el-icon><ArrowLeft /></el-icon>
        返回
      </el-button>
      <h1 class="page-title">图书对比</h1>
      <div class="header-actions">
        <el-button @click="clearCompare">
          <el-icon><Delete /></el-icon>
          清空对比
        </el-button>
        <el-button type="primary" @click="router.push('/books')">
          <el-icon><Plus /></el-icon>
          添加图书
        </el-button>
      </div>
    </div>

    <div v-if="compareData.length === 0 && !isLoading" class="empty-state">
      <el-empty description="请先添加至少2本图书到对比栏">
        <el-button type="primary" @click="router.push('/books')">
          去选择图书
        </el-button>
      </el-empty>
    </div>

    <div v-else class="compare-content">
      <div class="compare-table-wrapper">
        <table class="compare-table">
          <thead>
            <tr>
              <th class="field-label">对比项</th>
              <th
                v-for="book in compareData"
                :key="book.id"
                class="book-header"
                :class="{ 'invalid': !book.is_valid }"
              >
                <div class="book-header-content">
                  <div class="book-cover-wrapper">
                    <img
                      v-if="book.is_valid"
                      :src="book.cover_image || defaultCover"
                      :alt="book.title"
                      class="book-cover"
                      @error="handleImageError"
                    />
                    <div v-else class="invalid-cover">
                      <el-icon><Warning /></el-icon>
                    </div>
                  </div>
                  <div class="book-title-wrapper">
                    <h3 class="book-title" :title="book.title">
                      {{ book.title }}
                    </h3>
                    <el-button
                      v-if="book.is_valid"
                      size="small"
                      text
                      type="primary"
                      @click="goToDetail(book.id)"
                    >
                      查看详情
                    </el-button>
                    <el-button
                      size="small"
                      text
                      type="danger"
                      @click="removeBook(book.id)"
                    >
                      移除
                    </el-button>
                  </div>
                </div>
              </th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td class="field-label">
                <el-icon><User /></el-icon>
                作者
              </td>
              <td
                v-for="book in compareData"
                :key="book.id"
                class="field-value"
                :class="{ highlight: isHighest('author', book) }"
              >
                <span v-if="book.is_valid">{{ book.author }}</span>
                <span v-else class="invalid-text">-</span>
              </td>
            </tr>

            <tr>
              <td class="field-label">
                <el-icon><OfficeBuilding /></el-icon>
                出版社
              </td>
              <td
                v-for="book in compareData"
                :key="book.id"
                class="field-value"
              >
                <span v-if="book.is_valid">{{ book.publisher || '未知' }}</span>
                <span v-else class="invalid-text">-</span>
              </td>
            </tr>

            <tr>
              <td class="field-label">
                <el-icon><Collection /></el-icon>
                分类
              </td>
              <td
                v-for="book in compareData"
                :key="book.id"
                class="field-value"
              >
                <el-tag v-if="book.is_valid && book.category" type="info">
                  {{ book.category }}
                </el-tag>
                <span v-else-if="book.is_valid">未分类</span>
                <span v-else class="invalid-text">-</span>
              </td>
            </tr>

            <tr>
              <td class="field-label">
                <el-icon><Money /></el-icon>
                价格
              </td>
              <td
                v-for="book in compareData"
                :key="book.id"
                class="field-value"
                :class="{ 'highlight-lowest': isLowest('price', book), 'invalid': !book.is_valid }"
              >
                <span v-if="book.is_valid" class="price-value">
                  ¥{{ book.price.toFixed(2) }}
                </span>
                <span v-else class="invalid-text">-</span>
              </td>
            </tr>

            <tr>
              <td class="field-label">
                <el-icon><Box /></el-icon>
                库存
              </td>
              <td
                v-for="book in compareData"
                :key="book.id"
                class="field-value"
                :class="{ 'highlight-highest': isHighest('stock', book) }"
              >
                <span
                  v-if="book.is_valid"
                  class="stock-value"
                  :class="{ 'out-of-stock': book.stock === 0 }"
                >
                  {{ book.stock > 0 ? `${book.stock} 本` : '缺货' }}
                </span>
                <span v-else class="invalid-text">-</span>
              </td>
            </tr>

            <tr>
              <td class="field-label">
                <el-icon><Star /></el-icon>
                评分
              </td>
              <td
                v-for="book in compareData"
                :key="book.id"
                class="field-value"
                :class="{ 'highlight-highest': isHighest('rating', book) }"
              >
                <div v-if="book.is_valid" class="rating-wrapper">
                  <el-rate
                    v-model="book.rating"
                    disabled
                    show-score
                    text-color="#ff9900"
                    score-template="{value}"
                  />
                  <span class="review-count">
                    ({{ book.review_count }} 条评价)
                  </span>
                </div>
                <span v-else class="invalid-text">-</span>
              </td>
            </tr>

            <tr>
              <td class="field-label">
                <el-icon><PriceTag /></el-icon>
                标签
              </td>
              <td
                v-for="book in compareData"
                :key="book.id"
                class="field-value"
              >
                <div v-if="book.is_valid" class="tags-wrapper">
                  <el-tag
                    v-for="tag in book.tags"
                    :key="tag"
                    size="small"
                    type="success"
                    effect="light"
                    class="book-tag"
                  >
                    {{ tag }}
                  </el-tag>
                  <span v-if="book.tags.length === 0" class="no-tags">
                    暂无标签
                  </span>
                </div>
                <span v-else class="invalid-text">-</span>
              </td>
            </tr>

            <tr>
              <td class="field-label description-label">
                <el-icon><Document /></el-icon>
                简介
              </td>
              <td
                v-for="book in compareData"
                :key="book.id"
                class="field-value description-value"
              >
                <p v-if="book.is_valid && book.description" class="description">
                  {{ book.description }}
                </p>
                <span v-else-if="book.is_valid" class="no-description">
                  暂无简介
                </span>
                <span v-else class="invalid-text">-</span>
              </td>
            </tr>

            <tr>
              <td class="field-label">
                <el-icon><Document /></el-icon>
                ISBN
              </td>
              <td
                v-for="book in compareData"
                :key="book.id"
                class="field-value"
              >
                <span v-if="book.is_valid && book.isbn">{{ book.isbn }}</span>
                <span v-else-if="book.is_valid">未知</span>
                <span v-else class="invalid-text">-</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="compareData.length < 2" class="compare-tip">
        <el-alert
          title="请添加至少2本图书进行对比"
          type="info"
          :closable="false"
          show-icon
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useCompareStore } from '@/stores/compare'
import type { BookCompareData } from '@/types'
import {
  ArrowLeft, Delete, Plus, User, OfficeBuilding,
  Collection, Money, Box, Star, PriceTag,
  Document, Warning
} from '@element-plus/icons-vue'

const router = useRouter()
const compareStore = useCompareStore()

const {
  compareData,
  isLoading,
  fetchCompareData,
  removeFromCompare,
  clearCompare
} = compareStore

const defaultCover = 'https://via.placeholder.com/120x160/6366f1/ffffff?text=Book'

const validBooks = computed(() => compareData.value.filter(b => b.is_valid))

function isHighest(field: keyof BookCompareData, book: BookCompareData): boolean {
  if (!book.is_valid) return false
  const values = validBooks.value.map(b => b[field])
  const maxValue = Math.max(...values.filter(v => typeof v === 'number') as number[])
  return (book[field] as number) === maxValue
}

function isLowest(field: keyof BookCompareData, book: BookCompareData): boolean {
  if (!book.is_valid) return false
  const values = validBooks.value.map(b => b[field])
  const minValue = Math.min(...values.filter(v => typeof v === 'number') as number[])
  return (book[field] as number) === minValue
}

function goToDetail(bookId: number) {
  router.push(`/books/${bookId}`)
}

function removeBook(bookId: number) {
  removeFromCompare(bookId)
}

function handleImageError(e: Event) {
  const img = e.target as HTMLImageElement
  img.src = defaultCover
}

onMounted(async () => {
  await fetchCompareData()
})
</script>

<style scoped>
.compare-page {
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px;
}

.page-header {
  display: flex;
  align-items: center;
  gap: 24px;
  margin-bottom: 32px;
  padding: 16px 24px;
  background: var(--bg-secondary);
  border-radius: 16px;
  box-shadow: var(--shadow);
}

.page-title {
  flex: 1;
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.empty-state {
  padding: 80px 0;
}

.compare-content {
  background: var(--bg-secondary);
  border-radius: 16px;
  box-shadow: var(--shadow);
  overflow: hidden;
}

.compare-table-wrapper {
  overflow-x: auto;
}

.compare-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  min-width: 800px;
}

.compare-table thead th {
  position: sticky;
  top: 0;
  z-index: 10;
  background: var(--bg-tertiary);
  border-bottom: 2px solid var(--border-color);
  padding: 0;
  text-align: left;
}

.field-label {
  width: 120px;
  padding: 16px 24px !important;
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  font-weight: 600;
  font-size: 14px;
  white-space: nowrap;
  display: flex;
  align-items: center;
  gap: 8px;
  border-right: 1px solid var(--border-color);
}

td.field-label {
  border-right: 1px solid var(--border-color-light);
  border-bottom: 1px solid var(--border-color-light);
}

.book-header {
  min-width: 220px;
  padding: 24px 20px !important;
  text-align: center !important;
  border-right: 1px solid var(--border-color-light);
}

.book-header.invalid {
  background: rgba(239, 68, 68, 0.05);
}

.book-header-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.book-cover-wrapper {
  width: 120px;
  height: 160px;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: var(--shadow);
}

.book-cover {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.invalid-cover {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-tertiary);
  color: var(--danger-color);
  font-size: 48px;
}

.book-title-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.book-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.compare-table tbody td {
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color-light);
  border-right: 1px solid var(--border-color-light);
  vertical-align: top;
  font-size: 14px;
}

.compare-table tbody tr:last-child td {
  border-bottom: none;
}

.field-value {
  text-align: center;
  color: var(--text-primary);
}

.field-value.highlight,
.field-value.highlight-highest {
  background: rgba(16, 185, 129, 0.08);
}

.field-value.highlight-lowest {
  background: rgba(245, 158, 11, 0.08);
}

.price-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--secondary-color);
}

.stock-value {
  font-weight: 500;
}

.stock-value.out-of-stock {
  color: var(--danger-color);
}

.rating-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.review-count {
  font-size: 12px;
  color: var(--text-secondary);
}

.tags-wrapper {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  justify-content: center;
}

.book-tag {
  margin: 0;
}

.no-tags {
  color: var(--text-tertiary);
  font-size: 13px;
}

.description-label {
  vertical-align: top;
  padding-top: 20px !important;
}

.description-value {
  text-align: left !important;
}

.description {
  margin: 0;
  line-height: 1.8;
  color: var(--text-secondary);
  font-size: 13px;
  display: -webkit-box;
  -webkit-line-clamp: 4;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.no-description {
  color: var(--text-tertiary);
  font-size: 13px;
}

.invalid-text {
  color: var(--text-tertiary);
}

.compare-tip {
  padding: 24px;
  border-top: 1px solid var(--border-color-light);
}

@media (max-width: 768px) {
  .compare-page {
    padding: 12px;
  }

  .page-header {
    flex-wrap: wrap;
    gap: 12px;
    padding: 12px;
  }

  .page-title {
    font-size: 20px;
  }

  .field-label {
    width: 100px;
    padding: 12px !important;
    font-size: 12px;
  }

  .book-header {
    min-width: 180px;
    padding: 16px 12px !important;
  }

  .book-cover-wrapper {
    width: 80px;
    height: 110px;
  }

  .book-title {
    font-size: 14px;
    max-width: 140px;
  }

  .compare-table tbody td {
    padding: 12px;
    font-size: 13px;
  }

  .price-value {
    font-size: 18px;
  }
}
</style>
