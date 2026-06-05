<template>
  <div class="stock-taking-history">
    <div class="page-header">
      <div class="header-left">
        <el-button @click="goBack" :icon="ArrowLeft">返回</el-button>
        <h2 class="page-title">盘点历史记录</h2>
      </div>
    </div>

    <div v-loading="loading" class="history-content">
      <div class="search-bar">
        <el-input
          v-model="keyword"
          placeholder="搜索任务名称、编号..."
          clearable
          @keyup.enter="fetchHistory"
          style="max-width: 300px"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          value-format="YYYY-MM-DD"
          @change="handleDateChange"
          style="width: 280px"
        />
        <el-button @click="resetFilters" :icon="Refresh">
          重置
        </el-button>
      </div>

      <el-table
        :data="historyList"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="task_no" label="任务编号" width="160" />
        <el-table-column prop="name" label="任务名称" min-width="180" />
        <el-table-column label="盘点范围" width="120">
          <template #default="{ row }">
            {{ getScopeText(row.scope) }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'confirmed' ? 'success' : 'danger'" size="small">
              {{ row.status === 'confirmed' ? '已确认' : '已取消' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="盘点图书" width="100" align="center">
          <template #default="{ row }">
            {{ row.total_books }} 本
          </template>
        </el-table-column>
        <el-table-column label="差异数量" width="100" align="center">
          <template #default="{ row }">
            <el-badge
              v-if="row.difference_count > 0"
              :value="row.difference_count"
              type="danger"
              :max="99"
            />
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="person_in_charge" label="负责人" width="100">
          <template #default="{ row }">
            {{ row.person_in_charge || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="confirmed_by_name" label="操作人" width="100" />
        <el-table-column prop="confirmed_at" label="确认时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.confirmed_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="viewDetail(row.id)">
              查看详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          layout="total, prev, pager, next"
          @current-change="fetchHistory"
        />
      </div>

      <el-empty
        v-if="historyList.length === 0 && !loading"
        description="暂无历史记录"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/api'
import type { StockTaking } from '@/types'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Search, Refresh } from '@element-plus/icons-vue'

const router = useRouter()

const loading = ref(false)
const historyList = ref<StockTaking[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const keyword = ref('')
const dateRange = ref<string[]>([])
const startDate = ref('')
const endDate = ref('')

function getScopeText(scope: string): string {
  const scopeMap: Record<string, string> = {
    all: '全库盘点',
    category: '按分类盘点',
    low_stock: '低库存盘点',
    custom: '自定义范围'
  }
  return scopeMap[scope] || scope
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

function handleDateChange(val: string[] | null) {
  if (val && val.length === 2) {
    startDate.value = val[0]
    endDate.value = val[1]
  } else {
    startDate.value = ''
    endDate.value = ''
  }
  fetchHistory()
}

function resetFilters() {
  keyword.value = ''
  dateRange.value = []
  startDate.value = ''
  endDate.value = ''
  page.value = 1
  fetchHistory()
}

function viewDetail(id: number) {
  router.push(`/stock-taking/${id}`)
}

function goBack() {
  router.back()
}

async function fetchHistory() {
  loading.value = true
  try {
    const response = await api.getStockTakingHistory({
      page: page.value,
      page_size: pageSize.value,
      keyword: keyword.value || undefined,
      start_date: startDate.value || undefined,
      end_date: endDate.value || undefined
    })
    historyList.value = response.items
    total.value = response.total
  } catch (error) {
    console.error('获取历史记录失败:', error)
    ElMessage.error('获取历史记录失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchHistory()
})
</script>

<style scoped>
.stock-taking-history {
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-color);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.page-title {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
}

.history-content {
  background: var(--bg-card);
  border-radius: 12px;
  padding: 24px;
}

.search-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.pagination {
  display: flex;
  justify-content: center;
  margin-top: 16px;
}
</style>
