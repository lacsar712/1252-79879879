<template>
  <div class="api-key-management">
    <div class="page-header">
      <h1>API Key 管理</h1>
      <el-button type="primary" @click="handleCreateAPIKey">
        <el-icon><Plus /></el-icon>
        创建 API Key
      </el-button>
    </div>

    <div class="search-bar">
      <el-input
        v-model="searchQuery"
        placeholder="搜索名称、Key、备注..."
        clearable
        @keyup.enter="fetchAPIKeys"
        style="max-width: 300px"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      <el-select
        v-model="statusFilter"
        placeholder="状态筛选"
        clearable
        @change="fetchAPIKeys"
        style="width: 150px"
      >
        <el-option
          v-for="item in statusOptions"
          :key="item.value"
          :label="item.label"
          :value="item.value"
        />
      </el-select>
      <el-button @click="fetchAPIKeys">搜索</el-button>
      <el-button @click="resetFilters">
        <el-icon><Refresh /></el-icon>
        重置
      </el-button>
    </div>

    <el-table
      :data="apiKeys"
      v-loading="loading"
      stripe
      style="width: 100%"
    >
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="name" label="名称" min-width="150">
        <template #default="{ row }">
          <div class="name-with-risk">
            <span>{{ row.name }}</span>
            <el-tag
              v-if="row.risk_status"
              :type="getRiskTagType(row.risk_status)"
              size="small"
              class="risk-tag"
            >
              {{ getRiskText(row.risk_status) }}
            </el-tag>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="api_key" label="API Key" width="220">
        <template #default="{ row }">
          <div class="key-display">
            <span class="key-text">{{ maskKey(row.api_key) }}</span>
            <el-button
              link
              type="primary"
              @click="copyToClipboard(row.api_key, 'API Key')"
              size="small"
            >
              <el-icon><CopyDocument /></el-icon>
              复制
            </el-button>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.is_enabled ? 'success' : 'danger'" size="small">
            {{ row.is_enabled ? '已启用' : '已禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="过期时间" width="180">
        <template #default="{ row }">
          <span v-if="row.expires_at">{{ formatDate(row.expires_at) }}</span>
          <span v-else class="text-muted">永不过期</span>
        </template>
      </el-table-column>
      <el-table-column label="访问范围" width="120">
        <template #default="{ row }">
          <el-tag size="small">{{ getScopeText(row.access_scope) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="频率限制" width="120">
        <template #default="{ row }">
          {{ row.rate_limit }}次/{{ getPeriodText(row.rate_period) }}
        </template>
      </el-table-column>
      <el-table-column label="调用次数" width="100" align="center">
        <template #default="{ row }">
          {{ row.call_count }}
        </template>
      </el-table-column>
      <el-table-column label="创建人" width="100">
        <template #default="{ row }">
          {{ row.created_by_name || '-' }}
        </template>
      </el-table-column>
      <el-table-column label="最近使用" width="180">
        <template #default="{ row }">
          <span v-if="row.last_used_at">{{ formatDate(row.last_used_at) }}</span>
          <span v-else class="text-muted">从未使用</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="320" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="handleViewLogs(row)">
            <el-icon><Document /></el-icon>
            日志
          </el-button>
          <el-button link type="success" @click="handleToggle(row)">
            {{ row.is_enabled ? '禁用' : '启用' }}
          </el-button>
          <el-button link type="warning" @click="handleRotate(row)">
            <el-icon><RefreshRight /></el-icon>
            轮换
          </el-button>
          <el-button link type="info" @click="handleEdit(row)">
            <el-icon><Edit /></el-icon>
            编辑
          </el-button>
          <el-popconfirm
            title="确定要删除此 API Key 吗？删除后无法恢复。"
            @confirm="handleDelete(row.id)"
          >
            <template #reference>
              <el-button type="danger" link>
                <el-icon><Delete /></el-icon>
                删除
              </el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next"
        @current-change="fetchAPIKeys"
      />
    </div>

    <el-dialog
      v-model="createDialogVisible"
      :title="isEdit ? '编辑 API Key' : '创建 API Key'"
      width="600px"
      destroy-on-close
      class="api-key-dialog"
    >
      <el-alert
        v-if="!isEdit"
        title="API Key 和 Secret 仅在创建时显示一次，请妥善保存"
        type="warning"
        show-icon
        :closable="false"
        style="margin-bottom: 16px"
      />
      <el-form
        ref="apiKeyFormRef"
        :model="apiKeyForm"
        :rules="apiKeyRules"
        label-width="100px"
      >
        <el-form-item label="名称" prop="name">
          <el-input v-model="apiKeyForm.name" placeholder="请输入名称，用于标识" maxlength="100" show-word-limit />
        </el-form-item>
        <el-form-item label="备注" prop="remark">
          <el-input
            v-model="apiKeyForm.remark"
            type="textarea"
            :rows="2"
            placeholder="请输入备注信息"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="启用状态" prop="is_enabled">
              <el-switch
                v-model="apiKeyForm.is_enabled"
                active-text="启用"
                inactive-text="禁用"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="过期时间" prop="expires_at">
              <el-date-picker
                v-model="apiKeyForm.expires_at"
                type="datetime"
                placeholder="选择过期时间（不选则永不过期）"
                style="width: 100%"
                value-format="YYYY-MM-DDTHH:mm:ss.sssZ"
                :disabled="isEdit"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="访问范围" prop="access_scope">
          <el-select v-model="apiKeyForm.access_scope" placeholder="请选择访问范围" style="width: 100%">
            <el-option
              v-for="scope in accessScopeOptions"
              :key="scope.value"
              :label="scope.label"
              :value="scope.value"
            />
          </el-select>
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="频率限制" prop="rate_limit">
              <el-input-number
                v-model="apiKeyForm.rate_limit"
                :min="1"
                :max="10000"
                placeholder="调用次数"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="限制周期" prop="rate_period">
              <el-select v-model="apiKeyForm.rate_period" placeholder="请选择周期" style="width: 100%">
                <el-option
                  v-for="period in ratePeriodOptions"
                  :key="period.value"
                  :label="period.label"
                  :value="period.value"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="允许 IP" prop="allowed_ips">
          <el-input
            v-model="apiKeyForm.allowed_ips"
            placeholder="多个 IP 用逗号分隔，如: 192.168.1.1,10.0.0.1（不填则不限制）"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">
          {{ isEdit ? '保存' : '创建' }}
        </el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="secretDialogVisible"
      title="API Key 凭证"
      width="500px"
      :close-on-click-modal="false"
      class="secret-dialog"
    >
      <el-alert
        title="请妥善保存以下凭证，关闭后将无法再次查看"
        type="error"
        show-icon
        :closable="false"
      />
      <div class="secret-display">
        <div class="secret-item">
          <label>API Key:</label>
          <div class="secret-value-wrapper">
            <span class="secret-value">{{ currentSecret.api_key }}</span>
            <el-button type="primary" size="small" @click="copyToClipboard(currentSecret.api_key, 'API Key')">
              <el-icon><CopyDocument /></el-icon>
              复制
            </el-button>
          </div>
        </div>
        <div class="secret-item">
          <label>API Secret:</label>
          <div class="secret-value-wrapper">
            <span class="secret-value">{{ currentSecret.api_secret }}</span>
            <el-button type="primary" size="small" @click="copyToClipboard(currentSecret.api_secret, 'API Secret')">
              <el-icon><CopyDocument /></el-icon>
              复制
            </el-button>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button type="primary" @click="secretDialogVisible = false">我已保存</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="logsDialogVisible"
      title="调用日志"
      width="900px"
      destroy-on-close
      class="logs-dialog"
    >
      <div v-if="currentAPIKey" class="logs-header">
        <div class="key-info">
          <span class="label">API Key:</span>
          <span class="value">{{ currentAPIKey.name }} ({{ maskKey(currentAPIKey.api_key) }})</span>
        </div>
      </div>
      <div class="logs-filter">
        <el-select
          v-model="logStatusFilter"
          placeholder="调用状态"
          clearable
          @change="fetchLogs"
          style="width: 120px"
        >
          <el-option label="成功" value="success" />
          <el-option label="失败" value="failed" />
        </el-select>
        <el-date-picker
          v-model="logDateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          value-format="YYYY-MM-DD"
          @change="handleLogDateChange"
          style="width: 280px"
        />
        <el-button @click="fetchLogs">查询</el-button>
        <el-button @click="resetLogFilters">
          <el-icon><Refresh /></el-icon>
          重置
        </el-button>
      </div>
      <el-table
        :data="callLogs"
        v-loading="loadingLogs"
        stripe
        style="width: 100%; margin-top: 16px"
        max-height="400px"
      >
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="endpoint" label="接口" min-width="200" />
        <el-table-column prop="method" label="方法" width="80" />
        <el-table-column prop="ip_address" label="IP 地址" width="130" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status_code < 400 ? 'success' : 'danger'" size="small">
              {{ row.status_code < 400 ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status_code" label="状态码" width="80" align="center" />
        <el-table-column prop="response_time_ms" label="耗时(ms)" width="100" align="center" />
        <el-table-column label="失败原因" min-width="150" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.error_message" class="error-text">{{ row.error_message }}</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="调用时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination">
        <el-pagination
          v-model:current-page="logPage"
          v-model:page-size="logPageSize"
          :total="logTotal"
          layout="total, prev, pager, next"
          @current-change="fetchLogs"
        />
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import {
  Plus, Search, Refresh, CopyDocument, Document,
  RefreshRight, Edit, Delete
} from '@element-plus/icons-vue'
import { api } from '@/api'
import type {
  APIKey, APIKeyCreate, APIKeyUpdate, APIKeyCreateResponse,
  APIKeyAccessScopeOption, APIKeyRatePeriodOption,
  APIKeyStatusOption, APIKeyCallLog
} from '@/types'

const loading = ref(false)
const submitting = ref(false)
const loadingLogs = ref(false)

const apiKeys = ref<APIKey[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const searchQuery = ref('')
const statusFilter = ref('')

const accessScopeOptions = ref<APIKeyAccessScopeOption[]>([])
const ratePeriodOptions = ref<APIKeyRatePeriodOption[]>([])
const statusOptions = ref<APIKeyStatusOption[]>([])

const createDialogVisible = ref(false)
const isEdit = ref(false)
const editingId = ref<number | null>(null)
const apiKeyFormRef = ref<FormInstance>()
const apiKeyForm = reactive<APIKeyCreate>({
  name: '',
  remark: '',
  is_enabled: true,
  expires_at: '',
  access_scope: 'books:read',
  rate_limit: 100,
  rate_period: 'minute',
  allowed_ips: ''
})

const apiKeyRules: FormRules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  access_scope: [{ required: true, message: '请选择访问范围', trigger: 'change' }],
  rate_limit: [{ required: true, message: '请输入频率限制', trigger: 'blur' }],
  rate_period: [{ required: true, message: '请选择限制周期', trigger: 'change' }]
}

const secretDialogVisible = ref(false)
const currentSecret = reactive<APIKeyCreateResponse>({
  id: 0,
  api_key: '',
  api_secret: '',
  message: ''
})

const logsDialogVisible = ref(false)
const currentAPIKey = ref<APIKey | null>(null)
const callLogs = ref<APIKeyCallLog[]>([])
const logTotal = ref(0)
const logPage = ref(1)
const logPageSize = ref(20)
const logStatusFilter = ref('')
const logDateRange = ref<string[]>([])
const logStartDate = ref('')
const logEndDate = ref('')

const formatDate = (dateStr: string | null) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

const maskKey = (key: string) => {
  if (!key || key.length <= 8) return key
  return key.substring(0, 4) + '****' + key.substring(key.length - 4)
}

const copyToClipboard = async (text: string, label: string) => {
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success(`${label} 已复制到剪贴板`)
  } catch (err) {
    ElMessage.error('复制失败，请手动复制')
  }
}

const getRiskTagType = (status: string) => {
  const typeMap: Record<string, string> = {
    disabled: 'danger',
    expired: 'danger',
    expiring_soon: 'warning',
    high_risk: 'danger',
    medium_risk: 'warning',
    inactive: 'info'
  }
  return typeMap[status] || 'info'
}

const getRiskText = (status: string) => {
  const textMap: Record<string, string> = {
    disabled: '已禁用',
    expired: '已过期',
    expiring_soon: '即将过期',
    high_risk: '高风险',
    medium_risk: '中风险',
    inactive: '未使用'
  }
  return textMap[status] || status
}

const getScopeText = (scope: string) => {
  const textMap: Record<string, string> = {
    'books:read': '只读图书',
    'books:full': '图书完整',
    '*': '全部权限'
  }
  return textMap[scope] || scope
}

const getPeriodText = (period: string) => {
  const textMap: Record<string, string> = {
    second: '秒',
    minute: '分钟',
    hour: '小时',
    day: '天'
  }
  return textMap[period] || period
}

const fetchOptions = async () => {
  try {
    const [scopes, periods, statuses] = await Promise.all([
      api.getAPIAccessScopes(),
      api.getAPIRatePeriods(),
      api.getAPIKeyStatuses()
    ])
    accessScopeOptions.value = scopes
    ratePeriodOptions.value = periods
    statusOptions.value = statuses
  } catch (err) {
    console.error('获取选项失败', err)
  }
}

const fetchAPIKeys = async () => {
  loading.value = true
  try {
    const params: Record<string, any> = {
      page: currentPage.value,
      page_size: pageSize.value
    }
    if (searchQuery.value) params.search = searchQuery.value
    if (statusFilter.value) params.risk_status = statusFilter.value

    const response = await api.getAPIKeys(params)
    apiKeys.value = response.items
    total.value = response.total
  } catch (err) {
    ElMessage.error('获取 API Key 列表失败')
  } finally {
    loading.value = false
  }
}

const resetFilters = () => {
  searchQuery.value = ''
  statusFilter.value = ''
  currentPage.value = 1
  fetchAPIKeys()
}

const handleCreateAPIKey = () => {
  isEdit.value = false
  editingId.value = null
  Object.assign(apiKeyForm, {
    name: '',
    remark: '',
    is_enabled: true,
    expires_at: '',
    access_scope: 'books:read',
    rate_limit: 100,
    rate_period: 'minute',
    allowed_ips: ''
  })
  createDialogVisible.value = true
}

const handleEdit = (row: APIKey) => {
  isEdit.value = true
  editingId.value = row.id
  Object.assign(apiKeyForm, {
    name: row.name,
    remark: row.remark || '',
    is_enabled: row.is_enabled,
    expires_at: row.expires_at || '',
    access_scope: row.access_scope,
    rate_limit: row.rate_limit,
    rate_period: row.rate_period,
    allowed_ips: row.allowed_ips || ''
  })
  createDialogVisible.value = true
}

const handleSubmit = async () => {
  if (!apiKeyFormRef.value) return
  try {
    await apiKeyFormRef.value.validate()
    submitting.value = true

    if (isEdit.value && editingId.value) {
      const updateData: APIKeyUpdate = { ...apiKeyForm }
      await api.updateAPIKey(editingId.value, updateData)
      ElMessage.success('更新成功')
      createDialogVisible.value = false
      fetchAPIKeys()
    } else {
      const createData: APIKeyCreate = { ...apiKeyForm }
      const response = await api.createAPIKey(createData)
      createDialogVisible.value = false
      Object.assign(currentSecret, response)
      secretDialogVisible.value = true
      fetchAPIKeys()
    }
  } catch (err) {
    if (err !== false) {
      ElMessage.error(isEdit.value ? '更新失败' : '创建失败')
    }
  } finally {
    submitting.value = false
  }
}

const handleToggle = async (row: APIKey) => {
  try {
    await api.toggleAPIKey(row.id)
    ElMessage.success(row.is_enabled ? '已禁用' : '已启用')
    fetchAPIKeys()
  } catch (err) {
    ElMessage.error('操作失败')
  }
}

const handleRotate = async (row: APIKey) => {
  try {
    await ElMessageBox.confirm(
      '确定要轮换此 API Key 的密钥吗？轮换后旧密钥将失效，新密钥仅显示一次。',
      '确认轮换',
      { type: 'warning' }
    )
    const response = await api.rotateAPIKey(row.id)
    Object.assign(currentSecret, response)
    secretDialogVisible.value = true
    fetchAPIKeys()
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error('轮换失败')
    }
  }
}

const handleDelete = async (id: number) => {
  try {
    await api.deleteAPIKey(id)
    ElMessage.success('删除成功')
    fetchAPIKeys()
  } catch (err) {
    ElMessage.error('删除失败')
  }
}

const handleViewLogs = (row: APIKey) => {
  currentAPIKey.value = row
  logPage.value = 1
  logStatusFilter.value = ''
  logDateRange.value = []
  logStartDate.value = ''
  logEndDate.value = ''
  logsDialogVisible.value = true
  fetchLogs()
}

const fetchLogs = async () => {
  if (!currentAPIKey.value) return
  loadingLogs.value = true
  try {
    const params: Record<string, any> = {
      page: logPage.value,
      page_size: logPageSize.value
    }
    if (logStatusFilter.value) params.status = logStatusFilter.value
    if (logStartDate.value) params.start_date = logStartDate.value
    if (logEndDate.value) params.end_date = logEndDate.value

    const response = await api.getAPIKeyLogs(currentAPIKey.value.id, params)
    callLogs.value = response.items
    logTotal.value = response.total
  } catch (err) {
    ElMessage.error('获取日志失败')
  } finally {
    loadingLogs.value = false
  }
}

const handleLogDateChange = (val: string[]) => {
  if (val && val.length === 2) {
    logStartDate.value = val[0]
    logEndDate.value = val[1]
  } else {
    logStartDate.value = ''
    logEndDate.value = ''
  }
}

const resetLogFilters = () => {
  logStatusFilter.value = ''
  logDateRange.value = []
  logStartDate.value = ''
  logEndDate.value = ''
  logPage.value = 1
  fetchLogs()
}

onMounted(() => {
  fetchOptions()
  fetchAPIKeys()
})
</script>

<style scoped>
.api-key-management {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
}

.search-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  flex-wrap: wrap;
  align-items: center;
}

.name-with-risk {
  display: flex;
  align-items: center;
  gap: 8px;
}

.risk-tag {
  margin-left: 8px;
}

.key-display {
  display: flex;
  align-items: center;
  gap: 8px;
}

.key-text {
  font-family: monospace;
  font-size: 13px;
  color: #606266;
}

.text-muted {
  color: #909399;
  font-size: 13px;
}

.pagination {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.secret-display {
  padding: 20px 0;
}

.secret-item {
  margin-bottom: 20px;
}

.secret-item:last-child {
  margin-bottom: 0;
}

.secret-item label {
  display: block;
  font-weight: 600;
  margin-bottom: 8px;
  color: #303133;
}

.secret-value-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 4px;
}

.secret-value {
  flex: 1;
  font-family: monospace;
  font-size: 14px;
  word-break: break-all;
  color: #303133;
}

.logs-header {
  padding: 12px 16px;
  background: #f5f7fa;
  border-radius: 4px;
  margin-bottom: 16px;
}

.key-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.key-info .label {
  font-weight: 600;
  color: #606266;
}

.key-info .value {
  font-family: monospace;
  color: #303133;
}

.logs-filter {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}

.error-text {
  color: #f56c6c;
  font-size: 13px;
}

:deep(.el-dialog__body) {
  padding: 20px;
}
</style>
