<template>
  <div
    v-if="visible"
    class="announcement-list-item"
    :class="{ 'is-pinned': announcement.is_pinned }"
  >
    <div class="item-header">
      <div class="item-title-wrapper">
        <el-icon v-if="announcement.is_pinned" class="pin-icon"><Top /></el-icon>
        <span class="item-title">{{ announcement.title }}</span>
        <el-tag v-if="announcement.is_pinned" type="danger" size="small" effect="light">置顶</el-tag>
      </div>
      <el-icon class="close-btn" @click="handleClose"><Close /></el-icon>
    </div>
    <div class="item-content">
      <p class="item-text">{{ announcement.content }}</p>
    </div>
    <div class="item-footer">
      <span class="item-time">
        <el-icon><Clock /></el-icon>
        {{ formatTime(announcement.start_time) }} - {{ formatTime(announcement.end_time) }}
      </span>
      <span class="item-views">
        <el-icon><View /></el-icon>
        {{ announcement.view_count }} 次浏览
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { api } from '@/api'
import type { Announcement } from '@/types'
import { ElMessage } from 'element-plus'
import { Top, Close, Clock, View } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

const props = defineProps<{
  announcement: Announcement
}>()

const emit = defineEmits<{
  close: [id: number]
}>()

const userStore = useUserStore()
const visible = ref(true)

function formatTime(time: string) {
  return new Date(time).toLocaleDateString('zh-CN')
}

async function handleClose() {
  if (userStore.isLoggedIn) {
    try {
      await api.closeAnnouncement(props.announcement.id)
    } catch (error) {
      console.error('关闭公告失败:', error)
    }
  } else {
    ElMessage.info('登录后可永久关闭此公告')
  }
  visible.value = false
  emit('close', props.announcement.id)
}
</script>

<style scoped>
.announcement-list-item {
  background: var(--bg-secondary);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 16px;
  box-shadow: var(--shadow);
  transition: all 0.3s ease;
  border-left: 4px solid transparent;
}

.announcement-list-item:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

.announcement-list-item.is-pinned {
  border-left-color: #ec4899;
  background: linear-gradient(to right, rgba(236, 72, 153, 0.05), var(--bg-secondary));
}

.item-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 12px;
}

.item-title-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.pin-icon {
  color: #ec4899;
  font-size: 16px;
}

.item-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.close-btn {
  font-size: 18px;
  color: var(--text-secondary);
  cursor: pointer;
  opacity: 0.6;
  transition: opacity 0.2s;
  flex-shrink: 0;
}

.close-btn:hover {
  opacity: 1;
  color: var(--text-primary);
}

.item-content {
  margin-bottom: 12px;
}

.item-text {
  font-size: 14px;
  line-height: 1.8;
  color: var(--text-secondary);
  margin: 0;
  white-space: pre-wrap;
}

.item-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 12px;
  border-top: 1px solid var(--border-color);
  font-size: 12px;
  color: var(--text-secondary);
}

.item-time,
.item-views {
  display: flex;
  align-items: center;
  gap: 4px;
}
</style>
