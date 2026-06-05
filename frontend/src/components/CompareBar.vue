<template>
  <div
    v-if="hasBooks"
    class="compare-bar-wrapper"
    :class="{ collapsed: isCollapsed }"
  >
    <div class="compare-bar">
      <div class="compare-bar-header">
        <div class="header-left">
          <el-icon class="bar-icon"><Histogram /></el-icon>
          <span class="bar-title">对比栏</span>
          <el-tag type="primary" effect="dark" size="small">
            {{ compareCount }}/{{ MAX_COMPARE_BOOKS }}
          </el-tag>
        </div>
        <div class="header-actions">
          <el-button
            v-if="!isCollapsed"
            size="small"
            text
            @click.stop="clearCompare"
          >
            <el-icon><Delete /></el-icon>
            清空
          </el-button>
          <el-button
            v-if="!isCollapsed && isLoggedIn"
            size="small"
            text
            @click.stop="saveToServer"
          >
            <el-icon><Upload /></el-icon>
            同步
          </el-button>
          <el-button
            v-if="!isCollapsed && compareCount >= 2"
            type="primary"
            size="small"
            @click.stop="goToCompare"
          >
            <el-icon><CopyDocument /></el-icon>
            开始对比
          </el-button>
          <el-button
            size="small"
            text
            @click.stop="toggleCollapse"
            class="collapse-btn"
          >
            <el-icon>
              <ArrowDown v-if="isCollapsed" />
              <ArrowUp v-else />
            </el-icon>
            {{ isCollapsed ? '展开' : '收起' }}
          </el-button>
        </div>
      </div>

      <div v-show="!isCollapsed" class="compare-bar-content">
        <div class="book-slots">
          <div
            v-for="bookId in compareBookIds"
            :key="bookId"
            class="book-slot"
          >
            <div
              v-if="compareBooks.has(bookId)"
              class="book-item"
            >
              <img
                :src="compareBooks.get(bookId)?.cover_image || defaultCover"
                :alt="compareBooks.get(bookId)?.title"
                class="book-thumb"
                @error="handleImageError"
              />
              <div class="book-info">
                <span class="book-title" :title="compareBooks.get(bookId)?.title">
                  {{ compareBooks.get(bookId)?.title }}
                </span>
                <span class="book-price">
                  ¥{{ compareBooks.get(bookId)?.price.toFixed(2) }}
                </span>
              </div>
              <el-button
                class="remove-btn"
                size="small"
                circle
                type="danger"
                @click.stop="removeFromCompare(bookId)"
              >
                <el-icon><Close /></el-icon>
              </el-button>
            </div>
          </div>

          <div
            v-for="i in emptySlots"
            :key="'empty-' + i"
            class="book-slot empty"
          >
            <div class="empty-slot">
              <el-icon class="empty-icon"><Plus /></el-icon>
              <span>添加图书</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useCompareStore } from '@/stores/compare'
import { useUserStore } from '@/stores/user'
import {
  Histogram, Delete, Upload, CopyDocument,
  ArrowUp, ArrowDown, Close, Plus
} from '@element-plus/icons-vue'

const router = useRouter()
const compareStore = useCompareStore()
const userStore = useUserStore()

const {
  compareBookIds,
  compareBooks,
  isCollapsed,
  compareCount,
  hasBooks,
  MAX_COMPARE_BOOKS,
  removeFromCompare,
  clearCompare,
  toggleCollapse,
  saveToServer
} = compareStore

const isLoggedIn = computed(() => userStore.isLoggedIn)

const emptySlots = computed(() => {
  return Math.max(0, MAX_COMPARE_BOOKS - compareCount.value)
})

const defaultCover = 'https://via.placeholder.com/80x100/6366f1/ffffff?text=Book'

function goToCompare() {
  router.push('/books/compare')
}

function handleImageError(e: Event) {
  const img = e.target as HTMLImageElement
  img.src = defaultCover
}
</script>

<style scoped>
.compare-bar-wrapper {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  background: var(--bg-primary);
  border-top: 1px solid var(--border-color);
  box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s ease;
}

.compare-bar-wrapper.collapsed {
  transform: translateY(calc(100% - 52px));
}

.compare-bar {
  max-width: 1400px;
  margin: 0 auto;
  padding: 12px 24px;
}

.compare-bar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-color-light);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.bar-icon {
  font-size: 20px;
  color: var(--primary-color);
}

.bar-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.collapse-btn {
  margin-left: 8px;
}

.compare-bar-content {
  padding-top: 16px;
}

.book-slots {
  display: flex;
  gap: 16px;
  overflow-x: auto;
  padding-bottom: 8px;
}

.book-slot {
  flex-shrink: 0;
  width: 240px;
}

.book-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: var(--bg-secondary);
  border-radius: 12px;
  border: 1px solid var(--border-color-light);
  position: relative;
  transition: all 0.2s ease;
}

.book-item:hover {
  border-color: var(--primary-color);
  box-shadow: 0 2px 12px rgba(99, 102, 241, 0.15);
}

.book-thumb {
  width: 48px;
  height: 64px;
  object-fit: cover;
  border-radius: 4px;
  flex-shrink: 0;
}

.book-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.book-title {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.book-price {
  font-size: 14px;
  font-weight: 600;
  color: var(--secondary-color);
}

.remove-btn {
  position: absolute;
  top: -8px;
  right: -8px;
  width: 24px !important;
  height: 24px !important;
  padding: 0 !important;
}

.book-slot.empty {
  border: 2px dashed var(--border-color);
  border-radius: 12px;
  background: var(--bg-secondary);
}

.empty-slot {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100px;
  color: var(--text-tertiary);
  gap: 8px;
}

.empty-icon {
  font-size: 24px;
}

.empty-slot span {
  font-size: 12px;
}

@media (max-width: 768px) {
  .compare-bar {
    padding: 8px 12px;
  }

  .bar-title {
    font-size: 14px;
  }

  .book-slot {
    width: 200px;
  }

  .book-item {
    padding: 8px;
  }
}
</style>
