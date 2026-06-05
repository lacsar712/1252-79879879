<template>
  <div class="home-page">
    <!-- Hero 区域 -->
    <section class="hero">
      <div class="hero-content">
        <h1 class="hero-title">
          发现你的
          <span class="text-gradient">下一本好书</span>
        </h1>
        <p class="hero-subtitle">
          海量优质图书，便捷购书体验，让阅读成为一种生活方式
        </p>
        <div class="hero-actions">
          <el-button type="primary" size="large" @click="router.push('/books')">
            <el-icon><Search /></el-icon>
            浏览图书
          </el-button>
          <el-button size="large" @click="router.push('/register')" v-if="!userStore.isLoggedIn">
            立即注册
          </el-button>
        </div>
      </div>
      <div class="hero-illustration">
        <div class="book-stack">
          <div class="book book-1"></div>
          <div class="book book-2"></div>
          <div class="book book-3"></div>
        </div>
      </div>
    </section>
    
    <!-- 特色功能 -->
    <section class="features">
      <h2 class="section-title">为什么选择我们</h2>
      <div class="feature-grid">
        <div class="feature-card">
          <div class="feature-icon">
            <el-icon :size="32"><Collection /></el-icon>
          </div>
          <h3>海量图书</h3>
          <p>涵盖多个领域的优质图书，满足不同阅读需求</p>
        </div>
        <div class="feature-card">
          <div class="feature-icon">
            <el-icon :size="32"><Search /></el-icon>
          </div>
          <h3>智能搜索</h3>
          <p>支持书名、作者、出版社多维度快速检索</p>
        </div>
        <div class="feature-card">
          <div class="feature-icon">
            <el-icon :size="32"><Lock /></el-icon>
          </div>
          <h3>安全可靠</h3>
          <p>采用JWT认证，确保账户安全与数据隐私</p>
        </div>
        <div class="feature-card">
          <div class="feature-icon">
            <el-icon :size="32"><Monitor /></el-icon>
          </div>
          <h3>现代交互</h3>
          <p>基于Vue 3构建，带来流畅的使用体验</p>
        </div>
      </div>
    </section>
    
    <!-- 精选图书 -->
    <section class="featured-books">
      <div class="section-header">
        <h2 class="section-title">精选图书</h2>
        <el-button text @click="router.push('/books')">
          查看全部
          <el-icon><ArrowRight /></el-icon>
        </el-button>
      </div>
      <div class="book-grid" v-loading="loading">
        <div v-for="book in featuredBooks" :key="book.id" class="book-card" @click="router.push(`/books/${book.id}`)">
          <div class="book-cover">
            <img :src="book.cover_image || defaultCover" :alt="book.title" @error="handleImageError">
          </div>
          <div class="book-info">
            <h4 class="book-title">{{ book.title }}</h4>
            <p class="book-author">{{ book.author }}</p>
            <p class="book-publisher" v-if="book.publisher">{{ book.publisher }}</p>
            <p class="book-price">¥{{ book.price.toFixed(2) }}</p>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { api } from '@/api'
import type { Book } from '@/types'
import { Search, Collection, Lock, Monitor, ArrowRight } from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useUserStore()

const loading = ref(false)
const featuredBooks = ref<Book[]>([])
const defaultCover = 'https://via.placeholder.com/200x280/6366f1/ffffff?text=Book'

onMounted(async () => {
  loading.value = true
  try {
    const response = await api.getBooks({ page: 1, page_size: 6 })
    featuredBooks.value = response.items
  } catch (error) {
    console.error('获取图书失败:', error)
  } finally {
    loading.value = false
  }
})

function handleImageError(e: Event) {
  const img = e.target as HTMLImageElement
  img.src = defaultCover
}
</script>

<style scoped>
.home-page {
  display: flex;
  flex-direction: column;
  gap: 60px;
}

/* Hero 区域 */
.hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 48px;
  padding: 48px 0;
}

.hero-content {
  flex: 1;
  max-width: 560px;
}

.hero-title {
  font-size: 48px;
  font-weight: 800;
  line-height: 1.2;
  margin-bottom: 20px;
}

.hero-subtitle {
  font-size: 18px;
  color: var(--text-secondary);
  margin-bottom: 32px;
  line-height: 1.6;
}

.hero-actions {
  display: flex;
  gap: 16px;
}

.hero-illustration {
  flex-shrink: 0;
}

.book-stack {
  position: relative;
  width: 280px;
  height: 320px;
}

.book {
  position: absolute;
  width: 180px;
  height: 240px;
  border-radius: 8px;
  box-shadow: var(--shadow-lg);
}

.book-1 {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  transform: rotate(-8deg);
  left: 0;
  bottom: 0;
}

.book-2 {
  background: linear-gradient(135deg, #ec4899 0%, #f472b6 100%);
  transform: rotate(4deg);
  left: 50px;
  bottom: 20px;
}

.book-3 {
  background: linear-gradient(135deg, #10b981 0%, #34d399 100%);
  transform: rotate(-2deg);
  left: 90px;
  bottom: 40px;
}

/* 特色功能 */
.section-title {
  font-size: 32px;
  font-weight: 700;
  text-align: center;
  margin-bottom: 40px;
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
}

.feature-card {
  background: var(--bg-secondary);
  padding: 32px 24px;
  border-radius: 16px;
  text-align: center;
  box-shadow: var(--shadow);
  transition: transform 0.2s, box-shadow 0.2s;
}

.feature-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
}

.feature-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto 16px;
  background: rgba(99, 102, 241, 0.1);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--primary-color);
}

.feature-card h3 {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 8px;
}

.feature-card p {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.5;
}

/* 精选图书 */
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.section-header .section-title {
  margin-bottom: 0;
  text-align: left;
}

.book-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 24px;
}

.book-card {
  background: var(--bg-secondary);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: var(--shadow);
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.book-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
}

.book-cover {
  width: 100%;
  aspect-ratio: 3/4;
  overflow: hidden;
  background: #f1f5f9;
}

.book-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.book-info {
  padding: 16px;
}

.book-title {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.book-author {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.book-publisher {
  font-size: 11px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.book-price {
  font-size: 16px;
  font-weight: 700;
  color: var(--secondary-color);
}

@media (max-width: 1200px) {
  .book-grid {
    grid-template-columns: repeat(4, 1fr);
  }
  
  .feature-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .hero {
    flex-direction: column;
    text-align: center;
  }
  
  .hero-title {
    font-size: 32px;
  }
  
  .hero-illustration {
    display: none;
  }
  
  .book-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .feature-grid {
    grid-template-columns: 1fr;
  }
}
</style>
