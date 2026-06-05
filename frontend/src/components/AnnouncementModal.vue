<template>
  <el-dialog
    v-model="visible"
    :title="announcement.title"
    width="500px"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    class="announcement-modal"
  >
    <div class="modal-content">
      <div class="modal-header">
        <el-tag v-if="announcement.is_pinned" type="danger" effect="light">
          <el-icon><Top /></el-icon>
          置顶
        </el-tag>
        <span class="modal-time">
          {{ formatTime(announcement.start_time) }} - {{ formatTime(announcement.end_time) }}
        </span>
      </div>
      <div class="modal-body">
        <p class="modal-text">{{ announcement.content }}</p>
      </div>
    </div>
    <template #footer>
      <el-button @click="handleClose">我知道了</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { api } from '@/api'
import type { Announcement } from '@/types'
import { ElMessage } from 'element-plus'
import { Top } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

const props = defineProps<{
  announcement: Announcement
  modelValue: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  close: [id: number]
}>()

const userStore = useUserStore()

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

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

watch(() => props.announcement, () => {
  visible.value = true
}, { immediate: true })
</script>

<style scoped>
.announcement-modal :deep(.el-dialog__header) {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  margin-right: 0;
  padding: 20px 24px;
}

.announcement-modal :deep(.el-dialog__title) {
  color: #fff;
  font-size: 18px;
  font-weight: 600;
}

.announcement-modal :deep(.el-dialog__headerbtn .el-dialog__close) {
  color: #fff;
}

.modal-content {
  padding: 8px 0;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-color);
}

.modal-time {
  font-size: 13px;
  color: var(--text-secondary);
}

.modal-body {
  min-height: 80px;
}

.modal-text {
  font-size: 15px;
  line-height: 1.8;
  color: var(--text-primary);
  white-space: pre-wrap;
}
</style>
