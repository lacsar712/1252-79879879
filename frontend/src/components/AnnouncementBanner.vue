<template>
  <div
    v-if="visible"
    class="announcement-banner"
    :class="{ 'is-pinned': announcement.is_pinned }"
  >
    <div class="banner-content">
      <el-icon v-if="announcement.is_pinned" class="pin-icon"><Top /></el-icon>
      <span class="banner-title">{{ announcement.title }}</span>
      <span class="banner-divider">|</span>
      <span class="banner-text">{{ announcement.content }}</span>
    </div>
    <el-icon class="close-btn" @click="handleClose"><Close /></el-icon>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { api } from '@/api'
import type { Announcement } from '@/types'
import { ElMessage } from 'element-plus'
import { Top, Close } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

const props = defineProps<{
  announcement: Announcement
}>()

const emit = defineEmits<{
  close: [id: number]
}>()

const userStore = useUserStore()
const visible = ref(true)

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
.announcement-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color: #fff;
  padding: 12px 24px;
  border-radius: 8px;
  margin-bottom: 16px;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
  animation: slideDown 0.3s ease;
}

.announcement-banner.is-pinned {
  background: linear-gradient(135deg, #ec4899 0%, #f472b6 100%);
  box-shadow: 0 4px 12px rgba(236, 72, 153, 0.3);
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.banner-content {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  overflow: hidden;
}

.pin-icon {
  font-size: 18px;
  flex-shrink: 0;
}

.banner-title {
  font-weight: 600;
  font-size: 15px;
  flex-shrink: 0;
}

.banner-divider {
  opacity: 0.6;
  flex-shrink: 0;
}

.banner-text {
  font-size: 14px;
  opacity: 0.95;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.close-btn {
  font-size: 20px;
  cursor: pointer;
  opacity: 0.8;
  transition: opacity 0.2s;
  flex-shrink: 0;
  margin-left: 16px;
}

.close-btn:hover {
  opacity: 1;
}
</style>
