<template>
  <div class="reader-page" v-loading="loading">
    <template v-if="book && chapters.length > 0">
      <div class="reader-header">
        <div class="header-left">
          <el-button text @click="handleBack">
            <el-icon><ArrowLeft /></el-icon>
            返回图书详情
          </el-button>
        </div>
        <div class="header-center">
          <span class="book-title">{{ book.title }}</span>
        </div>
        <div class="header-right">
          <el-button-group>
            <el-button @click="handlePrevChapter" :disabled="currentIndex === 0">
              <el-icon><ArrowUp /></el-icon>
              上一章
            </el-button>
            <el-button @click="handleNextChapter" :disabled="currentIndex === chapters.length - 1">
              下一章
              <el-icon><ArrowDown /></el-icon>
            </el-button>
          </el-button-group>
          <el-button text @click="toggleCatalog">
            <el-icon><List /></el-icon>
            目录
          </el-button>
          <el-dropdown trigger="click">
            <el-button text>
              <el-icon><EditPen /></el-icon>
              字号
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="setFontSize('small')">
                  <span :class="{ active: fontSize === 'small' }">小</span>
                </el-dropdown-item>
                <el-dropdown-item @click="setFontSize('medium')">
                  <span :class="{ active: fontSize === 'medium' }">中</span>
                </el-dropdown-item>
                <el-dropdown-item @click="setFontSize('large')">
                  <span :class="{ active: fontSize === 'large' }">大</span>
                </el-dropdown-item>
                <el-dropdown-item @click="setFontSize('xlarge')">
                  <span :class="{ active: fontSize === 'xlarge' }">特大</span>
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>

      <div class="reader-container">
        <div class="catalog-sidebar" :class="{ visible: catalogVisible }">
          <div class="catalog-header">
            <h3>
              <el-icon><Collection /></el-icon>
              章节目录
            </h3>
            <el-button text @click="toggleCatalog">
              <el-icon><Close /></el-icon>
            </el-button>
          </div>
          <div class="catalog-list">
            <div
              v-for="(chapter, index) in chapters"
              :key="chapter.id"
              class="catalog-item"
              :class="{ active: currentChapter?.id === chapter.id }"
              @click="handleSelectChapter(chapter.id)"
            >
              <span class="catalog-index">第 {{ index + 1 }} 章</span>
              <span class="catalog-title">{{ chapter.title }}</span>
            </div>
          </div>
        </div>

        <div class="catalog-overlay" v-if="catalogVisible" @click="toggleCatalog"></div>

        <div class="reader-content" :class="`font-${fontSize}`">
          <template v-if="currentChapter">
            <h1 class="chapter-title">{{ currentChapter.title }}</h1>
            <div class="chapter-meta">
              <el-tag size="small" type="info">第 {{ currentIndex + 1 }} 章 / 共 {{ chapters.length }} 章</el-tag>
              <span class="update-time">更新于 {{ formatDate(currentChapter.updated_at) }}</span>
            </div>
            <div class="chapter-content">
              {{ currentChapter.content }}
            </div>
            <div class="chapter-navigation">
              <el-button
                type="primary"
                plain
                @click="handlePrevChapter"
                :disabled="currentIndex === 0"
              >
                <el-icon><ArrowUp /></el-icon>
                上一章
              </el-button>
              <el-button
                type="primary"
                plain
                @click="handleNextChapter"
                :disabled="currentIndex === chapters.length - 1"
              >
                下一章
                <el-icon><ArrowDown /></el-icon>
              </el-button>
            </div>
          </template>
        </div>
      </div>
    </template>

    <el-empty
      v-else-if="!loading && chapters.length === 0"
      description="暂无试读章节"
    >
      <el-button type="primary" @click="handleBack">返回图书详情</el-button>
    </el-empty>

    <el-empty v-else-if="!loading" description="加载失败" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { api } from '@/api'
import type { Book, BookChapterPublic } from '@/types'
import {
  ArrowLeft, ArrowUp, ArrowDown, List, EditPen,
  Collection, Close
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const router = useRouter()
const route = useRoute()

const loading = ref(false)
const book = ref<Book | null>(null)
const chapters = ref<BookChapterPublic[]>([])
const currentChapter = ref<BookChapterPublic | null>(null)
const currentChapterId = ref<number | null>(null)
const catalogVisible = ref(false)
const fontSize = ref<'small' | 'medium' | 'large' | 'xlarge'>('medium')

const currentIndex = computed(() => {
  if (!currentChapter.value || chapters.value.length === 0) return 0
  return chapters.value.findIndex(c => c.id === currentChapter.value!.id)
})

onMounted(async () => {
  const bookId = Number(route.params.bookId)
  const chapterId = Number(route.params.chapterId)
  
  if (!bookId) {
    router.push('/books')
    return
  }
  
  currentChapterId.value = chapterId || null
  await loadData(bookId)
})

watch(() => route.params.chapterId, (newChapterId) => {
  const chapterId = Number(newChapterId)
  if (chapterId && chapters.value.length > 0) {
    const chapter = chapters.value.find(c => c.id === chapterId)
    if (chapter) {
      currentChapter.value = chapter
      currentChapterId.value = chapterId
      scrollToTop()
    }
  }
})

async function loadData(bookId: number) {
  loading.value = true
  try {
    const [bookData, chaptersData] = await Promise.all([
      api.getBook(bookId),
      api.getPublicChapters(bookId)
    ])
    
    book.value = bookData
    chapters.value = chaptersData.items
    
    if (chapters.value.length > 0) {
      const targetChapterId = currentChapterId.value || chapters.value[0].id
      const chapter = chapters.value.find(c => c.id === targetChapterId)
      currentChapter.value = chapter || chapters.value[0]
      currentChapterId.value = currentChapter.value.id
    }
  } catch (error) {
    console.error('加载数据失败:', error)
    ElMessage.error('加载失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

function handleBack() {
  if (book.value) {
    router.push(`/books/${book.value.id}`)
  } else {
    router.push('/books')
  }
}

function handlePrevChapter() {
  if (currentIndex.value > 0) {
    const prevChapter = chapters.value[currentIndex.value - 1]
    router.push(`/books/${book.value!.id}/reader/${prevChapter.id}`)
  }
}

function handleNextChapter() {
  if (currentIndex.value < chapters.value.length - 1) {
    const nextChapter = chapters.value[currentIndex.value + 1]
    router.push(`/books/${book.value!.id}/reader/${nextChapter.id}`)
  }
}

function handleSelectChapter(chapterId: number) {
  router.push(`/books/${book.value!.id}/reader/${chapterId}`)
  catalogVisible.value = false
}

function toggleCatalog() {
  catalogVisible.value = !catalogVisible.value
}

function setFontSize(size: 'small' | 'medium' | 'large' | 'xlarge') {
  fontSize.value = size
  localStorage.setItem('readerFontSize', size)
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

function scrollToTop() {
  const content = document.querySelector('.reader-content')
  if (content) {
    content.scrollTop = 0
  }
}

const savedFontSize = localStorage.getItem('readerFontSize') as 'small' | 'medium' | 'large' | 'xlarge' | null
if (savedFontSize && ['small', 'medium', 'large', 'xlarge'].includes(savedFontSize)) {
  fontSize.value = savedFontSize
}
</script>

<style scoped>
.reader-page {
  min-height: 100vh;
  background: var(--bg-primary);
  display: flex;
  flex-direction: column;
}

.reader-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 24px;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: var(--shadow-sm);
}

.header-left,
.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-center .book-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  max-width: 400px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.reader-container {
  flex: 1;
  display: flex;
  position: relative;
  overflow: hidden;
}

.catalog-sidebar {
  width: 300px;
  background: var(--bg-secondary);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  transition: transform 0.3s ease;
  z-index: 50;
}

.catalog-sidebar.visible {
  transform: translateX(0);
}

.catalog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
}

.catalog-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
}

.catalog-header h3 .el-icon {
  color: var(--primary-color);
}

.catalog-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
}

.catalog-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px 20px;
  cursor: pointer;
  transition: all 0.2s ease;
  border-left: 3px solid transparent;
}

.catalog-item:hover {
  background: var(--bg-tertiary);
}

.catalog-item.active {
  background: rgba(99, 102, 241, 0.08);
  border-left-color: var(--primary-color);
}

.catalog-index {
  font-size: 12px;
  color: var(--primary-color);
  font-weight: 500;
}

.catalog-title {
  font-size: 14px;
  color: var(--text-primary);
  font-weight: 500;
}

.catalog-item.active .catalog-title {
  color: var(--primary-color);
}

.catalog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 40;
}

.reader-content {
  flex: 1;
  overflow-y: auto;
  padding: 40px 20%;
  background: var(--bg-primary);
}

.chapter-title {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  text-align: center;
  margin-bottom: 16px;
  line-height: 1.4;
}

.chapter-meta {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  margin-bottom: 32px;
  padding-bottom: 24px;
  border-bottom: 1px solid var(--border-color);
}

.update-time {
  font-size: 13px;
  color: var(--text-tertiary);
}

.chapter-content {
  font-size: 16px;
  line-height: 2;
  color: var(--text-primary);
  white-space: pre-wrap;
  word-break: break-word;
  text-indent: 2em;
}

.chapter-navigation {
  display: flex;
  justify-content: space-between;
  margin-top: 48px;
  padding-top: 24px;
  border-top: 1px solid var(--border-color);
}

.reader-content.font-small .chapter-content {
  font-size: 14px;
  line-height: 1.8;
}

.reader-content.font-medium .chapter-content {
  font-size: 16px;
  line-height: 2;
}

.reader-content.font-large .chapter-content {
  font-size: 18px;
  line-height: 2.2;
}

.reader-content.font-xlarge .chapter-content {
  font-size: 20px;
  line-height: 2.4;
}

.reader-content.font-small .chapter-title {
  font-size: 24px;
}

.reader-content.font-medium .chapter-title {
  font-size: 28px;
}

.reader-content.font-large .chapter-title {
  font-size: 32px;
}

.reader-content.font-xlarge .chapter-title {
  font-size: 36px;
}

.el-dropdown-menu .el-dropdown-item span {
  display: block;
  width: 100%;
}

.el-dropdown-menu .el-dropdown-item span.active {
  color: var(--primary-color);
  font-weight: 600;
}

@media (max-width: 768px) {
  .reader-header {
    padding: 8px 12px;
    flex-wrap: wrap;
    gap: 8px;
  }

  .header-center {
    order: -1;
    width: 100%;
    text-align: center;
  }

  .header-center .book-title {
    max-width: 100%;
    font-size: 14px;
  }

  .header-left,
  .header-right {
    flex: 1;
    justify-content: center;
  }

  .catalog-sidebar {
    position: fixed;
    top: 0;
    left: 0;
    height: 100vh;
    width: 280px;
    transform: translateX(-100%);
    box-shadow: var(--shadow-lg);
  }

  .catalog-sidebar.visible {
    transform: translateX(0);
  }

  .reader-content {
    padding: 24px 16px;
  }

  .chapter-title {
    font-size: 22px;
  }

  .chapter-content {
    font-size: 15px;
    line-height: 1.9;
  }

  .reader-content.font-small .chapter-content {
    font-size: 13px;
  }

  .reader-content.font-medium .chapter-content {
    font-size: 15px;
  }

  .reader-content.font-large .chapter-content {
    font-size: 17px;
  }

  .reader-content.font-xlarge .chapter-content {
    font-size: 19px;
  }
}
</style>
