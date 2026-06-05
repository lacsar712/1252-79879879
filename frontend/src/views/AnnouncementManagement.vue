<template>
  <div class="announcement-management">
    <div class="page-header">
      <h2 class="page-title">公告管理</h2>
      <el-button type="primary" @click="handleCreate">
        <el-icon><Plus /></el-icon>
        创建公告
      </el-button>
    </div>

    <div class="filter-bar">
      <el-form :inline="true" :model="filterForm" class="filter-form">
        <el-form-item label="状态">
          <el-select
            v-model="filterForm.status"
            placeholder="全部状态"
            clearable
            @change="loadAnnouncements"
          >
            <el-option
              v-for="status in statusOptions"
              :key="status.value"
              :label="status.label"
              :value="status.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="位置">
          <el-select
            v-model="filterForm.position"
            placeholder="全部位置"
            clearable
            @change="loadAnnouncements"
          >
            <el-option
              v-for="pos in positionOptions"
              :key="pos.value"
              :label="pos.label"
              :value="pos.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input
            v-model="filterForm.keyword"
            placeholder="搜索标题或内容"
            clearable
            @keyup.enter="loadAnnouncements"
          />
        </el-form-item>
        <el-form-item>
          <el-button @click="handleSearch">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          <el-button @click="handleReset">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </div>

    <div class="table-container">
      <el-table
        :data="announcements"
        v-loading="loading"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="id" label="ID" width="70" align="center" />
        <el-table-column label="标题" min-width="200">
          <template #default="{ row }">
            <div class="title-cell">
              <el-tag v-if="row.is_pinned" type="danger" size="small" effect="light">
                <el-icon><Top /></el-icon>
                置顶
              </el-tag>
              <span class="title-text">{{ row.title }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="content" label="内容" min-width="250" show-overflow-tooltip />
        <el-table-column label="展示位置" width="120">
          <template #default="{ row }">
            <el-tag size="small">{{ getPositionLabel(row.display_position) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="展示类型" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="getDisplayTypeTag(row.display_type)">
              {{ getDisplayTypeLabel(row.display_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="目标用户" width="100">
          <template #default="{ row }">
            <el-tag size="small" type="info">
              {{ getTargetUserLabel(row.target_user_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="优先级" width="80" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="getPriorityTag(row.priority)">
              {{ row.priority }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="有效期" width="200">
          <template #default="{ row }">
            <div class="time-range">
              <div class="time-item">
                <el-icon><Clock /></el-icon>
                <span>{{ formatDate(row.start_time) }}</span>
              </div>
              <div class="time-item">
                <el-icon><Warning /></el-icon>
                <span>{{ formatDate(row.end_time) }}</span>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag
              size="small"
              :type="getStatusTag(row.status)"
              effect="light"
            >
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="数据统计" width="140" align="center">
          <template #default="{ row }">
            <div class="stats">
              <span class="stat-item">
                <el-icon><View /></el-icon>
                {{ row.view_count }}
              </span>
              <span class="stat-item">
                <el-icon><Close /></el-icon>
                {{ row.close_count }}
              </span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right" align="center">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              link
              @click="handleEdit(row)"
            >
              编辑
            </el-button>
            <el-button
              :type="row.is_enabled ? 'warning' : 'success'"
              size="small"
              link
              @click="handleToggle(row)"
            >
              {{ row.is_enabled ? '停用' : '启用' }}
            </el-button>
            <el-popconfirm
              title="确定删除此公告吗？"
              confirm-button-text="删除"
              cancel-button-text="取消"
              @confirm="handleDelete(row)"
            >
              <template #reference>
                <el-button type="danger" size="small" link>删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <div class="pagination-container">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.page_size"
        :page-sizes="[10, 20, 50, 100]"
        :total="pagination.total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="loadAnnouncements"
        @current-change="loadAnnouncements"
      />
    </div>

    <AnnouncementEditDialog
      v-model="showEditDialog"
      :announcement="currentAnnouncement"
      @success="handleSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { api } from '@/api'
import type { Announcement } from '@/types'
import { ElMessage } from 'element-plus'
import {
  Plus,
  Search,
  Refresh,
  Top,
  Clock,
  Warning,
  View,
  Close
} from '@element-plus/icons-vue'
import AnnouncementEditDialog from '@/components/AnnouncementEditDialog.vue'

const loading = ref(false)
const announcements = ref<Announcement[]>([])
const positionOptions = ref<Array<{ value: string; label: string }>>([])
const typeOptions = ref<Array<{ value: string; label: string }>>([])
const targetUserOptions = ref<Array<{ value: string; label: string }>>([])
const statusOptions = ref<Array<{ value: string; label: string; type: string }>>([])

const filterForm = reactive({
  status: '',
  position: '',
  keyword: ''
})

const pagination = reactive({
  page: 1,
  page_size: 10,
  total: 0
})

const showEditDialog = ref(false)
const currentAnnouncement = ref<Announcement | null>(null)

async function loadOptions() {
  try {
    const [positions, types, targets, statuses] = await Promise.all([
      api.getAnnouncementPositions(),
      api.getAnnouncementTypes(),
      api.getAnnouncementTargetUserTypes(),
      api.getAnnouncementStatuses()
    ])
    positionOptions.value = positions
    typeOptions.value = types
    targetUserOptions.value = targets
    statusOptions.value = statuses
  } catch (error) {
    console.error('加载选项失败:', error)
  }
}

async function loadAnnouncements() {
  loading.value = true
  try {
    const params: any = {
      page: pagination.page,
      page_size: pagination.page_size
    }
    if (filterForm.status) params.status = filterForm.status
    if (filterForm.position) params.position = filterForm.position
    if (filterForm.keyword) params.keyword = filterForm.keyword

    const response = await api.getAnnouncements(params)
    announcements.value = response.items
    pagination.total = response.total
  } catch (error) {
    console.error('加载公告失败:', error)
  } finally {
    loading.value = false
  }
}

function getPositionLabel(value: string) {
  return positionOptions.value.find(p => p.value === value)?.label || value
}

function getDisplayTypeLabel(value: string) {
  return typeOptions.value.find(t => t.value === value)?.label || value
}

function getDisplayTypeTag(value: string) {
  const map: Record<string, string> = {
    banner: 'primary',
    modal: 'danger',
    list: 'success'
  }
  return map[value] || 'info'
}

function getTargetUserLabel(value: string) {
  return targetUserOptions.value.find(t => t.value === value)?.label || value
}

function getPriorityTag(priority: number) {
  if (priority >= 80) return 'danger'
  if (priority >= 50) return 'warning'
  if (priority >= 20) return 'primary'
  return 'info'
}

function getStatusLabel(status: string | null) {
  return statusOptions.value.find(s => s.value === status)?.label || status || '未知'
}

function getStatusTag(status: string | null) {
  const map: Record<string, string> = {
    pending: 'info',
    active: 'success',
    ended: 'warning',
    disabled: 'danger'
  }
  return map[status || ''] || 'info'
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function handleCreate() {
  currentAnnouncement.value = null
  showEditDialog.value = true
}

function handleEdit(row: Announcement) {
  currentAnnouncement.value = row
  showEditDialog.value = true
}

async function handleToggle(row: Announcement) {
  try {
    await api.toggleAnnouncement(row.id)
    ElMessage.success(`公告已${row.is_enabled ? '停用' : '启用'}`)
    loadAnnouncements()
  } catch (error) {
    console.error('切换状态失败:', error)
  }
}

async function handleDelete(row: Announcement) {
  try {
    await api.deleteAnnouncement(row.id)
    ElMessage.success('公告删除成功')
    loadAnnouncements()
  } catch (error) {
    console.error('删除公告失败:', error)
  }
}

function handleSearch() {
  pagination.page = 1
  loadAnnouncements()
}

function handleReset() {
  filterForm.status = ''
  filterForm.position = ''
  filterForm.keyword = ''
  pagination.page = 1
  loadAnnouncements()
}

function handleSuccess() {
  loadAnnouncements()
}

onMounted(() => {
  loadOptions()
  loadAnnouncements()
})
</script>

<style scoped>
.announcement-management {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  margin: 0;
}

.filter-bar {
  background: var(--bg-secondary);
  padding: 16px 20px;
  border-radius: 12px;
}

.filter-form {
  margin: 0;
}

.table-container {
  background: var(--bg-secondary);
  border-radius: 12px;
  padding: 20px;
  box-shadow: var(--shadow);
}

.title-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.title-text {
  font-weight: 500;
}

.time-range {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 12px;
}

.time-item {
  display: flex;
  align-items: center;
  gap: 4px;
  color: var(--text-secondary);
}

.stats {
  display: flex;
  justify-content: center;
  gap: 12px;
  font-size: 13px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
  color: var(--text-secondary);
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
}
</style>
