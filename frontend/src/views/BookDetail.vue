<template>
  <div class="book-detail-page" v-loading="loading">
    <template v-if="book">
      <div class="book-header">
        <el-button text @click="router.back()">
          <el-icon><ArrowLeft /></el-icon>
          返回
        </el-button>
      </div>
      
      <div class="book-content">
        <div class="book-cover">
          <img :src="book.cover_image || defaultCover" :alt="book.title" @error="handleImageError">
        </div>
        
        <div class="book-info">
          <div class="book-category" v-if="book.category">
            <el-tag type="info">{{ book.category }}</el-tag>
          </div>
          
          <h1 class="book-title">{{ book.title }}</h1>
          
          <div class="book-meta">
            <div class="meta-item">
              <el-icon><User /></el-icon>
              <span>作者：{{ book.author }}</span>
            </div>
            <div class="meta-item" v-if="book.publisher">
              <el-icon><OfficeBuilding /></el-icon>
              <span>出版社：{{ book.publisher }}</span>
            </div>
            <div class="meta-item" v-if="book.isbn">
              <el-icon><Document /></el-icon>
              <span>ISBN：{{ book.isbn }}</span>
            </div>
          </div>
          
          <div class="book-price-section">
            <span class="price-label">价格</span>
            <span class="price-value">¥{{ book.price.toFixed(2) }}</span>
          </div>
          
          <div class="book-stock-section">
            <span class="stock-label">库存</span>
            <span class="stock-value" :class="{ 'out-of-stock': book.stock === 0 }">
              {{ book.stock > 0 ? `${book.stock} 本` : '暂时缺货' }}
            </span>
          </div>
          
          <div class="book-actions">
            <div class="book-preview-section" v-if="publicChapters.length > 0">
              <el-button type="success" size="large" @click="handleStartReading">
                <el-icon><Reading /></el-icon>
                开始试读（{{ publicChapters.length }} 章）
              </el-button>
            </div>
            <div class="book-preview-section" v-else-if="!loadingChapters">
              <el-button type="info" size="large" disabled>
                <el-icon><Reading /></el-icon>
                暂无试读章节
              </el-button>
            </div>
            <div class="book-preview-section" v-else>
              <el-button type="info" size="large" loading>
                加载中...
              </el-button>
            </div>

            <div class="book-compare-section">
              <el-button
                v-if="book"
                :type="compareStore.isInCompare(book.id) ? 'success' : 'primary'"
                size="large"
                @click="handleCompareToggle"
              >
                <el-icon>
                  <Check v-if="compareStore.isInCompare(book.id)" />
                  <Histogram v-else />
                </el-icon>
                {{ compareStore.isInCompare(book.id) ? '已加入对比' : '加入对比' }}
              </el-button>
              <el-button
                v-if="book && compareStore.compareCount >= 2"
                size="large"
                @click="goToCompare"
              >
                去对比
              </el-button>
            </div>
          </div>
          
        </div>
      </div>
      
      <div class="book-description" v-if="book.description">
        <h2>图书简介</h2>
        <p>{{ book.description }}</p>
      </div>
      
      <div class="book-chapters" v-if="publicChapters.length > 0">
        <h2>
          <el-icon><Collection /></el-icon>
          试读章节（共 {{ publicChapters.length }} 章）
        </h2>
        <div class="chapters-list">
          <div
            v-for="(chapter, index) in publicChapters"
            :key="chapter.id"
            class="chapter-item"
            @click="handleReadChapter(chapter.id)"
          >
            <span class="chapter-index">第 {{ index + 1 }} 章</span>
            <span class="chapter-name">{{ chapter.title }}</span>
            <el-icon class="chapter-arrow"><ArrowRight /></el-icon>
          </div>
        </div>
      </div>
    </template>
    
    <el-empty v-else-if="!loading" description="图书不存在" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { api } from '@/api'
import { useCompareStore } from '@/stores/compare'
import type { Book, BookChapterPublic } from '@/types'
import { ArrowLeft, User, OfficeBuilding, Document, Reading, Collection, ArrowRight, Histogram, Check } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const compareStore = useCompareStore()

const loading = ref(false)
const loadingChapters = ref(false)
const book = ref<Book | null>(null)
const publicChapters = ref<BookChapterPublic[]>([])
const defaultCover = 'https://via.placeholder.com/300x400/6366f1/ffffff?text=Book'

onMounted(async () => {
  const bookId = Number(route.params.id)
  if (!bookId) {
    router.push('/books')
    return
  }
  
  loading.value = true
  try {
    book.value = await api.getBook(bookId)
    await fetchPublicChapters(bookId)
  } catch (error) {
    console.error('获取图书详情失败:', error)
  } finally {
    loading.value = false
  }
})

async function fetchPublicChapters(bookId: number) {
  loadingChapters.value = true
  try {
    const response = await api.getPublicChapters(bookId)
    publicChapters.value = response.items
  } catch (error) {
    console.error('获取试读章节失败:', error)
  } finally {
    loadingChapters.value = false
  }
}

function handleStartReading() {
  if (publicChapters.value.length > 0 && book.value) {
    router.push(`/books/${book.value.id}/reader/${publicChapters.value[0].id}`)
  }
}

function handleReadChapter(chapterId: number) {
  if (book.value) {
    router.push(`/books/${book.value.id}/reader/${chapterId}`)
  }
}

function handleImageError(e: Event) {
  const img = e.target as HTMLImageElement
  img.src = defaultCover
}

function handleCompareToggle() {
  if (book.value) {
    if (compareStore.isInCompare(book.value.id)) {
      compareStore.removeFromCompare(book.value.id)
    } else {
      compareStore.addToCompare(book.value)
    }
  }
}

function goToCompare() {
  router.push('/books/compare')
}

watch(book, (newBook) => {
  if (newBook) {
    compareStore.hydrateBooks([newBook])
  }
})
</script>

<style scoped>
.book-detail-page {
  max-width: 1000px;
  margin: 0 auto;
}

.book-header {
  margin-bottom: 24px;
}

.book-content {
  display: flex;
  gap: 48px;
  padding: 32px;
  background: var(--bg-secondary);
  border-radius: 16px;
  box-shadow: var(--shadow);
}

.book-cover {
  flex-shrink: 0;
  width: 280px;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: var(--shadow-lg);
}

.book-cover img {
  width: 100%;
  height: auto;
  display: block;
}

.book-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.book-category {
  margin-bottom: 8px;
}

.book-title {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.3;
}

.book-meta {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-secondary);
  font-size: 14px;
}

.meta-item .el-icon {
  color: var(--primary-color);
}

.book-price-section,
.book-stock-section {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin-top: 8px;
}

.price-label,
.stock-label {
  font-size: 14px;
  color: var(--text-secondary);
}

.price-value {
  font-size: 32px;
  font-weight: 700;
  color: var(--secondary-color);
}

.stock-value {
  font-size: 16px;
  font-weight: 500;
  color: var(--success-color);
}

.stock-value.out-of-stock {
  color: var(--danger-color);
}

.book-description {
  margin-top: 32px;
  padding: 32px;
  background: var(--bg-secondary);
  border-radius: 16px;
  box-shadow: var(--shadow);
}

.book-description h2 {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 16px;
  color: var(--text-primary);
}

.book-description p {
  font-size: 15px;
  line-height: 1.8;
  color: var(--text-secondary);
}

.book-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 16px;
}

.book-preview-section {
  margin-top: 0;
}

.book-compare-section {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.book-chapters {
  margin-top: 32px;
  padding: 32px;
  background: var(--bg-secondary);
  border-radius: 16px;
  box-shadow: var(--shadow);
}

.book-chapters h2 {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 20px;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 8px;
}

.book-chapters h2 .el-icon {
  color: var(--primary-color);
}

.chapters-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.chapter-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  background: var(--bg-primary);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid transparent;
}

.chapter-item:hover {
  background: var(--bg-tertiary);
  border-color: var(--primary-color);
  transform: translateX(4px);
}

.chapter-index {
  flex-shrink: 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--primary-color);
  background: rgba(99, 102, 241, 0.1);
  padding: 4px 12px;
  border-radius: 6px;
}

.chapter-name {
  flex: 1;
  font-size: 15px;
  font-weight: 500;
  color: var(--text-primary);
}

.chapter-arrow {
  flex-shrink: 0;
  color: var(--text-tertiary);
  font-size: 18px;
  transition: transform 0.2s ease;
}

.chapter-item:hover .chapter-arrow {
  color: var(--primary-color);
  transform: translateX(4px);
}

@media (max-width: 768px) {
  .book-content {
    flex-direction: column;
    gap: 24px;
  }
  
  .book-cover {
    width: 100%;
    max-width: 280px;
    margin: 0 auto;
  }

  .chapter-item {
    padding: 12px 16px;
  }

  .chapter-index {
    font-size: 12px;
    padding: 3px 10px;
  }

  .chapter-name {
    font-size: 14px;
  }
}
</style>
