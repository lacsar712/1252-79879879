<template>
  <div class="book-import-page">
    <div class="page-header">
      <div class="header-left">
        <el-button @click="goBack" :icon="ArrowLeft">返回</el-button>
        <h2 class="page-title">图书批量导入</h2>
      </div>
      <el-button type="success" @click="goToHistory" :icon="Clock">
        导入记录
      </el-button>
    </div>

    <div class="import-content">
      <el-steps :active="currentStep" finish-status="success" align-center class="import-steps">
        <el-step title="上传文件" :icon="Upload" />
        <el-step title="字段映射" :icon="Operation" />
        <el-step title="数据预览" :icon="View" />
        <el-step title="确认导入" :icon="Check" />
        <el-step title="导入完成" :icon="CircleCheck" />
      </el-steps>

      <div class="step-content">
        <div v-show="currentStep === 0" class="step-upload">
          <el-upload
            drag
            :auto-upload="false"
            :on-change="handleFileChange"
            :limit="1"
            accept=".csv"
            class="upload-area"
          >
            <el-icon class="upload-icon"><UploadFilled /></el-icon>
            <div class="upload-text">点击或将 CSV 文件拖拽到这里上传</div>
            <div class="upload-hint">支持 UTF-8 或 GBK 编码的 CSV 文件，最大 10MB</div>
            <template #tip>
              <div class="upload-tip">
                <el-alert
                  title="CSV 文件格式要求"
                  type="info"
                  :closable="false"
                  show-icon
                >
                  <template #default>
                    <p>CSV 文件应包含以下列（可自定义映射关系）：</p>
                    <ul>
                      <li><strong>书名（必填）</strong>：图书名称，最多 200 字符</li>
                      <li><strong>作者（必填）</strong>：作者姓名，最多 100 字符</li>
                      <li><strong>价格（必填）</strong>：图书价格，大于 0 的数字</li>
                      <li><strong>出版社</strong>：出版社名称，最多 100 字符</li>
                      <li><strong>ISBN</strong>：10 或 13 位 ISBN 号，需唯一</li>
                      <li><strong>库存</strong>：库存数量，非负整数，默认为 0</li>
                      <li><strong>分类</strong>：图书分类，最多 50 字符</li>
                      <li><strong>描述</strong>：图书简介</li>
                      <li><strong>封面图片</strong>：封面图片 URL</li>
                    </ul>
                  </template>
                </el-alert>
              </div>
            </template>
          </el-upload>

          <div v-if="uploadedFile" class="file-info">
            <el-icon><Document /></el-icon>
            <span class="file-name">{{ uploadedFile.file_name }}</span>
            <span class="file-size">{{ formatFileSize(uploadedFile.file_size) }}</span>
            <span class="file-rows">共 {{ uploadedFile.total_rows }} 条数据</span>
            <el-button type="danger" link @click="removeFile" :icon="Delete">移除</el-button>
          </div>

          <div class="step-actions">
            <el-button type="primary" :disabled="!uploadedFile" @click="goToMapping">
              下一步：字段映射
            </el-button>
          </div>
        </div>

        <div v-show="currentStep === 1" class="step-mapping">
          <div class="mapping-header">
            <h3>字段映射配置</h3>
            <p>将 CSV 文件中的列与系统字段进行匹配，必填字段必须映射</p>
          </div>

          <el-table :data="fieldMappings" border stripe class="mapping-table">
            <el-table-column label="CSV 列名" prop="csv_column" min-width="180">
              <template #default="{ row }">
                <el-tag :type="getColumnTagType(row.csv_column)">{{ row.csv_column }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="映射到" min-width="200">
              <template #default="{ row }">
                <el-select
                  v-model="row.target_field"
                  placeholder="请选择目标字段"
                  style="width: 100%"
                  @change="handleMappingChange"
                >
                  <el-option label="-- 不导入该列 --" :value="null" />
                  <el-option
                    v-for="field in availableFields"
                    :key="field.field"
                    :label="`${field.label}${field.required ? '（必填）' : ''}`"
                    :value="field.field"
                    :disabled="isFieldMapped(field.field, row.csv_column)"
                  >
                    <span>{{ field.label }}</span>
                    <el-tag v-if="field.required" type="danger" size="small" style="margin-left: 8px">必填</el-tag>
                    <el-tag v-else size="small" type="info">可选</el-tag>
                  </el-option>
                </el-select>
              </template>
            </el-table-column>
            <el-table-column label="字段类型" width="120">
              <template #default="{ row }">
                <span v-if="getFieldInfo(row.target_field)?.type">
                  {{ getFieldTypeText(getFieldInfo(row.target_field)!.type) }}
                </span>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="120">
              <template #default="{ row }">
                <el-tag v-if="row.target_field" type="success" size="small">
                  已映射
                </el-tag>
                <el-tag v-else type="info" size="small">
                  忽略
                </el-tag>
              </template>
            </el-table-column>
          </el-table>

          <div class="mapping-summary">
            <el-alert
              :title="mappingValidationMessage"
              :type="isMappingValid ? 'success' : 'warning'"
              :closable="false"
              show-icon
            />
          </div>

          <div class="step-actions">
            <el-button @click="currentStep = 0">上一步</el-button>
            <el-button type="primary" :disabled="!isMappingValid" @click="goToPreview">
              下一步：数据预览
            </el-button>
          </div>
        </div>

        <div v-show="currentStep === 2" class="step-preview">
          <div class="preview-header">
            <div class="preview-stats">
              <el-statistic title="总数据条数" :value="previewData?.total_rows || 0" />
              <el-statistic title="错误条数" :value="previewData?.error_count || 0" value-style="color: var(--el-color-danger)" />
              <el-statistic title="警告条数" :value="previewData?.warning_count || 0" value-style="color: var(--el-color-warning)" />
            </div>
            <div class="preview-actions">
              <el-button @click="showFilterDialog = true" :icon="Filter">
                筛选
              </el-button>
              <el-button type="warning" @click="skipAllErrorRows" :icon="Warning" :disabled="!hasErrors">
                跳过所有错误行
              </el-button>
            </div>
          </div>

          <div v-if="activeFilter" class="filter-info">
            <el-tag closable @close="clearFilter">
              筛选：{{ filterLabel }}
            </el-tag>
          </div>

          <el-table
            :data="filteredPreviewRows"
            border
            stripe
            class="preview-table"
            :row-class-name="getRowClassName"
          >
            <el-table-column label="行号" width="70" align="center">
              <template #default="{ row }">
                <span :class="{ 'text-muted': row.is_skipped }">{{ row.row_number }}</span>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag v-if="row.is_skipped" type="info" size="small">已跳过</el-tag>
                <el-tag v-else-if="row.errors.length > 0" type="danger" size="small">错误</el-tag>
                <el-tag v-else-if="row.warnings.length > 0" type="warning" size="small">警告</el-tag>
                <el-tag v-else type="success" size="small">正常</el-tag>
              </template>
            </el-table-column>
            <el-table-column
              v-for="col in displayColumns"
              :key="col.field"
              :label="col.label"
              :min-width="col.minWidth"
            >
              <template #default="{ row }">
                <div v-if="row.is_skipped" class="skipped-content">
                  <span class="text-muted">{{ getRowValue(row, col.field) || '-' }}</span>
                </div>
                <div v-else>
                  <el-tooltip
                    v-if="getFieldErrors(row, col.field).length > 0"
                    :content="getFieldErrors(row, col.field).join('; ')"
                    placement="top"
                  >
                    <span class="error-cell">
                      {{ getRowValue(row, col.field) || '-' }}
                      <el-icon class="error-icon"><WarningFilled /></el-icon>
                    </span>
                  </el-tooltip>
                  <span v-else>{{ getRowValue(row, col.field) || '-' }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="问题" min-width="250">
              <template #default="{ row }">
                <div v-if="row.errors.length > 0" class="error-list">
                  <div v-for="(err, idx) in row.errors" :key="idx" class="error-item">
                    <el-icon><CircleCloseFilled /></el-icon>
                    <span>{{ err }}</span>
                  </div>
                </div>
                <div v-if="row.warnings.length > 0" class="warning-list">
                  <div v-for="(warn, idx) in row.warnings" :key="idx" class="warning-item">
                    <el-icon><WarningFilled /></el-icon>
                    <span>{{ warn }}</span>
                  </div>
                </div>
                <span v-if="row.errors.length === 0 && row.warnings.length === 0">-</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="180" fixed="right">
              <template #default="{ row }">
                <el-button
                  v-if="!row.is_skipped"
                  link
                  type="primary"
                  @click="editRow(row)"
                >
                  编辑
                </el-button>
                <el-button
                  link
                  :type="row.is_skipped ? 'success' : 'warning'"
                  @click="toggleSkipRow(row)"
                >
                  {{ row.is_skipped ? '恢复' : '跳过' }}
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <div class="preview-pagination">
            <el-pagination
              v-model:current-page="previewPage"
              v-model:page-size="previewPageSize"
              :total="filteredPreviewRows.length"
              layout="total, prev, pager, next"
              small
            />
          </div>

          <div class="step-actions">
            <el-button @click="currentStep = 1">上一步</el-button>
            <el-button
              type="primary"
              :disabled="!canProceedToImport"
              @click="goToConfirm"
            >
              下一步：确认导入
            </el-button>
          </div>
        </div>

        <div v-show="currentStep === 3" class="step-confirm">
          <div class="confirm-summary">
            <h3>确认导入信息</h3>
            <el-descriptions :column="2" border class="confirm-desc">
              <el-descriptions-item label="文件名">
                {{ uploadedFile?.file_name }}
              </el-descriptions-item>
              <el-descriptions-item label="文件大小">
                {{ uploadedFile ? formatFileSize(uploadedFile.file_size) : '-' }}
              </el-descriptions-item>
              <el-descriptions-item label="总数据条数">
                {{ previewData?.total_rows || 0 }}
              </el-descriptions-item>
              <el-descriptions-item label="将导入条数">
                <span class="import-count">{{ willImportCount }}</span>
              </el-descriptions-item>
              <el-descriptions-item label="跳过条数">
                <span class="skip-count">{{ skippedRows.length }}</span>
              </el-descriptions-item>
              <el-descriptions-item label="错误条数">
                <span class="error-count">{{ errorCountInImport }}</span>
              </el-descriptions-item>
            </el-descriptions>

            <el-alert
              v-if="errorCountInImport > 0"
              title="存在未修正的错误数据"
              type="warning"
              :closable="false"
              show-icon
            >
              导入将跳过包含错误的数据行，建议返回预览页面修正后再导入。
            </el-alert>

            <el-alert
              v-if="previewData?.warning_count && previewData.warning_count > 0"
              title="存在警告数据"
              type="info"
              :closable="false"
              show-icon
            >
              包含 {{ previewData.warning_count }} 条警告数据（如新分类、新出版社），导入时将自动创建。
            </el-alert>
          </div>

          <div class="step-actions">
            <el-button @click="currentStep = 2">上一步</el-button>
            <el-button
              type="primary"
              :loading="importing"
              @click="confirmImport"
            >
              确认导入
            </el-button>
          </div>
        </div>

        <div v-show="currentStep === 4" class="step-complete">
          <div v-if="importResult" class="complete-content">
            <div class="result-icon success">
              <el-icon :size="80"><CircleCheckFilled /></el-icon>
            </div>
            <h2>导入完成</h2>
            <p class="import-no">导入单号：{{ importResult.import_no }}</p>

            <el-row :gutter="24" class="result-stats">
              <el-col :span="8">
                <el-statistic title="成功导入" :value="importResult.success_count" value-style="color: var(--el-color-success)" />
              </el-col>
              <el-col :span="8">
                <el-statistic title="导入失败" :value="importResult.failed_count" value-style="color: var(--el-color-danger)" />
              </el-col>
              <el-col :span="8">
                <el-statistic title="跳过条数" :value="importResult.skipped_count" value-style="color: var(--el-color-info)" />
              </el-col>
            </el-row>

            <div v-if="importResult.error_summary" class="error-summary">
              <el-alert
                title="错误详情"
                type="error"
                :closable="false"
                show-icon
              >
                <pre>{{ importResult.error_summary }}</pre>
              </el-alert>
            </div>

            <div class="complete-actions">
              <el-button @click="resetImport">继续导入</el-button>
              <el-button type="primary" @click="goToHistory">查看导入记录</el-button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <el-dialog
      v-model="editDialogVisible"
      title="编辑数据"
      width="600px"
      destroy-on-close
    >
      <el-form
        v-if="editingRow"
        ref="editFormRef"
        :model="editForm"
        label-width="80px"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="书名">
              <el-input v-model="editForm.title" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="作者">
              <el-input v-model="editForm.author" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="出版社">
              <el-input v-model="editForm.publisher" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="ISBN">
              <el-input v-model="editForm.isbn" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="价格">
              <el-input-number
                v-model="editForm.price"
                :min="0.01"
                :precision="2"
                controls-position="right"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="库存">
              <el-input-number
                v-model="editForm.stock"
                :min="0"
                controls-position="right"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="分类">
          <el-input v-model="editForm.category" />
        </el-form-item>
        <el-form-item label="封面">
          <el-input v-model="editForm.cover_image" />
        </el-form-item>
        <el-form-item label="简介">
          <el-input v-model="editForm.description" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveEdit">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="showFilterDialog"
      title="筛选数据"
      width="400px"
      destroy-on-close
    >
      <el-radio-group v-model="filterType" style="width: 100%">
        <el-radio label="all" style="display: block; margin-bottom: 12px">显示全部</el-radio>
        <el-radio label="error" style="display: block; margin-bottom: 12px">仅显示错误行</el-radio>
        <el-radio label="warning" style="display: block; margin-bottom: 12px">仅显示警告行</el-radio>
        <el-radio label="skipped" style="display: block; margin-bottom: 12px">仅显示已跳过行</el-radio>
        <el-radio label="normal" style="display: block">仅显示正常行</el-radio>
      </el-radio-group>
      <template #footer>
        <el-button @click="showFilterDialog = false">取消</el-button>
        <el-button type="primary" @click="applyFilter">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/api'
import type {
  BookImportUploadResponse,
  BookImportPreviewResponse,
  BookImportPreviewRow,
  BookImportFieldMapping,
  BookImportFieldOption,
  BookImportRowUpdate,
  BookImportProgressResponse
} from '@/types'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowLeft, Clock, Upload, Operation, View, Check, CircleCheck,
  UploadFilled, Document, Delete, Filter, Warning, WarningFilled,
  CircleCloseFilled, CircleCheckFilled
} from '@element-plus/icons-vue'

const router = useRouter()

const currentStep = ref(0)
const uploadedFile = ref<BookImportUploadResponse | null>(null)
const fieldMappings = ref<BookImportFieldMapping[]>([])
const availableFields = ref<BookImportFieldOption[]>([])
const previewData = ref<BookImportPreviewResponse | null>(null)
const previewRows = ref<BookImportPreviewRow[]>([])
const rowUpdates = ref<BookImportRowUpdate[]>([])
const skippedRows = ref<number[]>([])
const importing = ref(false)
const importResult = ref<BookImportProgressResponse | null>(null)

const previewPage = ref(1)
const previewPageSize = ref(20)

const editDialogVisible = ref(false)
const editingRow = ref<BookImportPreviewRow | null>(null)
const editForm = ref<Record<string, any>>({})
const editFormRef = ref()

const showFilterDialog = ref(false)
const filterType = ref('all')
const activeFilter = ref('')
const filterLabel = ref('')

const displayColumns = [
  { field: 'title', label: '书名', minWidth: 180 },
  { field: 'author', label: '作者', minWidth: 120 },
  { field: 'price', label: '价格', minWidth: 100 },
  { field: 'isbn', label: 'ISBN', minWidth: 140 },
  { field: 'publisher', label: '出版社', minWidth: 140 },
  { field: 'category', label: '分类', minWidth: 100 },
  { field: 'stock', label: '库存', minWidth: 80 }
]

async function loadFields() {
  try {
    availableFields.value = await api.getBookImportFields()
  } catch (error) {
    console.error('加载字段列表失败:', error)
  }
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
}

function handleFileChange(file: any) {
  const rawFile = file.raw
  if (!rawFile) return

  if (!rawFile.name.toLowerCase().endsWith('.csv')) {
    ElMessage.error('请上传 CSV 格式的文件')
    return
  }

  if (rawFile.size > 10 * 1024 * 1024) {
    ElMessage.error('文件大小不能超过 10MB')
    return
  }

  uploadFile(rawFile)
}

async function uploadFile(file: File) {
  try {
    const result = await api.uploadBookImportFile(file)
    uploadedFile.value = result
    initFieldMappings(result.columns)
    ElMessage.success('文件上传成功')
  } catch (error) {
    console.error('文件上传失败:', error)
  }
}

function initFieldMappings(columns: string[]) {
  const lowerToOriginal: Record<string, string> = {}
  columns.forEach(col => {
    lowerToOriginal[col.toLowerCase()] = col
  })

  fieldMappings.value = columns.map(col => {
    const targetField = autoMapField(col)
    return {
      csv_column: col,
      target_field: targetField
    }
  })
}

function autoMapField(columnName: string): string | null {
  const colLower = columnName.toLowerCase().replace(/[_\s-]/g, '')
  
  const fieldMap: Record<string, string> = {
    '书名': 'title', 'title': 'title', '名称': 'title', '图书名称': 'title',
    '作者': 'author', 'author': 'author', '作者名': 'author',
    '出版社': 'publisher', 'publisher': 'publisher', '出版单位': 'publisher',
    'isbn': 'isbn', '书号': 'isbn', '图书编号': 'isbn',
    '价格': 'price', 'price': 'price', '定价': 'price', '售价': 'price',
    '库存': 'stock', 'stock': 'stock', '库存数量': 'stock', '数量': 'stock',
    '分类': 'category', 'category': 'category', '类别': 'category', '种类': 'category',
    '描述': 'description', 'description': 'description', '简介': 'description', '内容简介': 'description',
    '封面': 'cover_image', '封面图片': 'cover_image', 'cover': 'cover_image', 'coverimage': 'cover_image', '图片': 'cover_image'
  }

  return fieldMap[colLower] || null
}

function getColumnTagType(column: string): string {
  const mapped = fieldMappings.value.find(m => m.csv_column === column)
  if (!mapped?.target_field) return 'info'
  const field = availableFields.value.find(f => f.field === mapped.target_field)
  return field?.required ? 'danger' : 'primary'
}

function getFieldInfo(fieldName: string | null) {
  if (!fieldName) return null
  return availableFields.value.find(f => f.field === fieldName)
}

function getFieldTypeText(type: string): string {
  const typeMap: Record<string, string> = {
    'string': '文本',
    'float': '小数',
    'integer': '整数',
    'text': '长文本'
  }
  return typeMap[type] || type
}

function isFieldMapped(field: string, currentColumn: string): boolean {
  return fieldMappings.value.some(
    m => m.target_field === field && m.csv_column !== currentColumn
  )
}

function handleMappingChange() {
}

const isMappingValid = computed(() => {
  const requiredFields = availableFields.value.filter(f => f.required).map(f => f.field)
  const mappedFields = fieldMappings.value
    .filter(m => m.target_field)
    .map(m => m.target_field)
  
  return requiredFields.every(rf => mappedFields.includes(rf))
})

const mappingValidationMessage = computed(() => {
  const requiredFields = availableFields.value.filter(f => f.required)
  const mappedFields = fieldMappings.value
    .filter(m => m.target_field)
    .map(m => m.target_field)
  
  const missingFields = requiredFields.filter(rf => !mappedFields.includes(rf.field))
  
  if (missingFields.length === 0) {
    return '字段映射配置完成，所有必填字段已映射'
  }
  
  const missingNames = missingFields.map(f => f.label).join('、')
  return `还需映射以下必填字段：${missingNames}`
})

function removeFile() {
  uploadedFile.value = null
  fieldMappings.value = []
  previewData.value = null
  previewRows.value = []
  rowUpdates.value = []
  skippedRows.value = []
  currentStep.value = 0
}

async function goToMapping() {
  currentStep.value = 1
}

async function goToPreview() {
  if (!uploadedFile.value || !isMappingValid.value) return

  try {
    const result = await api.previewBookImport({
      file_id: uploadedFile.value.file_id,
      field_mappings: fieldMappings.value
    })
    previewData.value = result
    previewRows.value = result.preview_rows
    rowUpdates.value = []
    skippedRows.value = []
    currentStep.value = 2
  } catch (error) {
    console.error('预览数据失败:', error)
  }
}

const hasErrors = computed(() => {
  return previewRows.value.some(r => r.errors.length > 0 && !r.is_skipped)
})

const willImportCount = computed(() => {
  return previewRows.value.filter(r => !r.is_skipped).length
})

const errorCountInImport = computed(() => {
  return previewRows.value.filter(r => r.errors.length > 0 && !r.is_skipped).length
})

const canProceedToImport = computed(() => {
  return previewData.value !== null
})

const filteredPreviewRows = computed(() => {
  let rows = previewRows.value

  if (activeFilter.value === 'error') {
    rows = rows.filter(r => r.errors.length > 0)
  } else if (activeFilter.value === 'warning') {
    rows = rows.filter(r => r.errors.length === 0 && r.warnings.length > 0)
  } else if (activeFilter.value === 'skipped') {
    rows = rows.filter(r => r.is_skipped)
  } else if (activeFilter.value === 'normal') {
    rows = rows.filter(r => r.errors.length === 0 && r.warnings.length === 0 && !r.is_skipped)
  }

  return rows
})

function getRowClassName({ row }: { row: BookImportPreviewRow }) {
  if (row.is_skipped) return 'row-skipped'
  if (row.errors.length > 0) return 'row-error'
  if (row.warnings.length > 0) return 'row-warning'
  return ''
}

function getRowValue(row: BookImportPreviewRow, field: string): any {
  return (row as any)[field]
}

function getFieldErrors(row: BookImportPreviewRow, field: string): string[] {
  const fieldInfo = getFieldInfo(field)
  if (!fieldInfo) return []
  
  return row.errors.filter(e => e.includes(fieldInfo.label))
}

function editRow(row: BookImportPreviewRow) {
  editingRow.value = row
  editForm.value = {
    row_number: row.row_number,
    title: row.title || '',
    author: row.author || '',
    publisher: row.publisher || '',
    isbn: row.isbn || '',
    price: row.price ?? 0,
    stock: row.stock ?? 0,
    description: row.description || '',
    cover_image: row.cover_image || '',
    category: row.category || ''
  }
  editDialogVisible.value = true
}

function saveEdit() {
  if (!editingRow.value) return

  const update: BookImportRowUpdate = {
    row_number: editingRow.value.row_number,
    title: editForm.value.title || undefined,
    author: editForm.value.author || undefined,
    publisher: editForm.value.publisher || undefined,
    isbn: editForm.value.isbn || undefined,
    price: editForm.value.price,
    stock: editForm.value.stock,
    description: editForm.value.description || undefined,
    cover_image: editForm.value.cover_image || undefined,
    category: editForm.value.category || undefined
  }

  const existingIdx = rowUpdates.value.findIndex(u => u.row_number === update.row_number)
  if (existingIdx >= 0) {
    rowUpdates.value[existingIdx] = { ...rowUpdates.value[existingIdx], ...update }
  } else {
    rowUpdates.value.push(update)
  }

  const row = previewRows.value.find(r => r.row_number === editingRow.value!.row_number)
  if (row) {
    if (update.title !== undefined) row.title = update.title || null
    if (update.author !== undefined) row.author = update.author || null
    if (update.publisher !== undefined) row.publisher = update.publisher || null
    if (update.isbn !== undefined) row.isbn = update.isbn || null
    if (update.price !== undefined) row.price = update.price
    if (update.stock !== undefined) row.stock = update.stock
    if (update.description !== undefined) row.description = update.description || null
    if (update.cover_image !== undefined) row.cover_image = update.cover_image || null
    if (update.category !== undefined) row.category = update.category || null

    row.errors = []
    row.warnings = []
  }

  editDialogVisible.value = false
  ElMessage.success('修改已保存，将在导入时生效')
}

function toggleSkipRow(row: BookImportPreviewRow) {
  row.is_skipped = !row.is_skipped

  const update: BookImportRowUpdate = {
    row_number: row.row_number,
    is_skipped: row.is_skipped
  }

  const existingIdx = rowUpdates.value.findIndex(u => u.row_number === update.row_number)
  if (existingIdx >= 0) {
    rowUpdates.value[existingIdx] = { ...rowUpdates.value[existingIdx], is_skipped: row.is_skipped }
  } else {
    rowUpdates.value.push(update)
  }

  if (row.is_skipped) {
    if (!skippedRows.value.includes(row.row_number)) {
      skippedRows.value.push(row.row_number)
    }
  } else {
    skippedRows.value = skippedRows.value.filter(r => r !== row.row_number)
  }
}

function skipAllErrorRows() {
  ElMessageBox.confirm(
    '确定要跳过所有包含错误的行吗？',
    '确认操作',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    previewRows.value.forEach(row => {
      if (row.errors.length > 0 && !row.is_skipped) {
        toggleSkipRow(row)
      }
    })
    ElMessage.success('已跳过所有错误行')
  }).catch(() => {})
}

function applyFilter() {
  activeFilter.value = filterType.value
  const labelMap: Record<string, string> = {
    'all': '显示全部',
    'error': '仅显示错误行',
    'warning': '仅显示警告行',
    'skipped': '仅显示已跳过行',
    'normal': '仅显示正常行'
  }
  filterLabel.value = labelMap[filterType.value]
  showFilterDialog.value = false
  previewPage.value = 1
}

function clearFilter() {
  activeFilter.value = ''
  filterLabel.value = ''
  filterType.value = 'all'
  previewPage.value = 1
}

function goToConfirm() {
  currentStep.value = 3
}

async function confirmImport() {
  if (!uploadedFile.value) return

  try {
    importing.value = true
    const result = await api.confirmBookImport({
      file_id: uploadedFile.value.file_id,
      field_mappings: fieldMappings.value,
      row_updates: rowUpdates.value,
      skipped_rows: skippedRows.value
    })
    importResult.value = result
    currentStep.value = 4
    importing.value = false
  } catch (error) {
    console.error('导入失败:', error)
    importing.value = false
  }
}

function resetImport() {
  uploadedFile.value = null
  fieldMappings.value = []
  previewData.value = null
  previewRows.value = []
  rowUpdates.value = []
  skippedRows.value = []
  importResult.value = null
  currentStep.value = 0
  activeFilter.value = ''
}

function goBack() {
  router.back()
}

function goToHistory() {
  router.push('/books/import/history')
}

onMounted(() => {
  loadFields()
})
</script>

<style scoped>
.book-import-page {
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

.import-content {
  background: var(--bg-card);
  border-radius: 12px;
  padding: 24px;
}

.import-steps {
  margin-bottom: 32px;
}

.step-content {
  min-height: 400px;
}

.upload-area {
  max-width: 600px;
  margin: 0 auto 24px;
}

.upload-icon {
  font-size: 48px;
  color: var(--el-color-primary);
  margin-bottom: 16px;
}

.upload-text {
  font-size: 16px;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.upload-hint {
  font-size: 14px;
  color: var(--text-secondary);
}

.upload-tip {
  margin-top: 16px;
  text-align: left;
}

.upload-tip ul {
  margin: 8px 0 0 20px;
  padding: 0;
}

.upload-tip li {
  margin-bottom: 4px;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 24px;
  background: var(--bg-color);
  border-radius: 8px;
  max-width: 600px;
  margin: 0 auto 24px;
}

.file-name {
  flex: 1;
  font-weight: 500;
}

.file-size,
.file-rows {
  color: var(--text-secondary);
  font-size: 14px;
}

.step-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid var(--border-color);
}

.mapping-header {
  margin-bottom: 16px;
}

.mapping-header h3 {
  margin: 0 0 8px;
  font-size: 18px;
}

.mapping-header p {
  margin: 0;
  color: var(--text-secondary);
}

.mapping-table {
  margin-bottom: 16px;
}

.mapping-summary {
  margin-bottom: 16px;
}

.text-muted {
  color: var(--text-secondary);
}

.skipped-content {
  opacity: 0.6;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
  padding: 16px;
  background: var(--bg-color);
  border-radius: 8px;
}

.preview-stats {
  display: flex;
  gap: 32px;
}

.preview-actions {
  display: flex;
  gap: 8px;
}

.filter-info {
  margin-bottom: 12px;
}

.preview-table {
  margin-bottom: 16px;
}

.preview-table :deep(.row-error) {
  background-color: rgba(245, 108, 108, 0.1);
}

.preview-table :deep(.row-warning) {
  background-color: rgba(230, 162, 60, 0.1);
}

.preview-table :deep(.row-skipped) {
  background-color: rgba(144, 147, 153, 0.1);
}

.error-cell {
  color: var(--el-color-danger);
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 4px;
}

.error-icon {
  font-size: 12px;
}

.error-list,
.warning-list {
  font-size: 12px;
}

.error-item,
.warning-item {
  display: flex;
  align-items: flex-start;
  gap: 4px;
  margin-bottom: 4px;
}

.error-item {
  color: var(--el-color-danger);
}

.warning-item {
  color: var(--el-color-warning);
}

.preview-pagination {
  display: flex;
  justify-content: center;
  margin-bottom: 16px;
}

.confirm-summary {
  max-width: 800px;
  margin: 0 auto;
}

.confirm-summary h3 {
  margin: 0 0 16px;
  font-size: 18px;
}

.confirm-desc {
  margin-bottom: 16px;
}

.import-count {
  font-weight: 600;
  color: var(--el-color-success);
}

.skip-count {
  font-weight: 600;
  color: var(--el-color-info);
}

.error-count {
  font-weight: 600;
  color: var(--el-color-danger);
}

.step-complete {
  text-align: center;
  padding: 40px 20px;
}

.complete-content {
  max-width: 600px;
  margin: 0 auto;
}

.result-icon {
  margin-bottom: 16px;
}

.result-icon.success {
  color: var(--el-color-success);
}

.result-icon.error {
  color: var(--el-color-danger);
}

.complete-content h2 {
  margin: 0 0 8px;
  font-size: 24px;
}

.import-no {
  color: var(--text-secondary);
  margin-bottom: 24px;
}

.result-stats {
  margin-bottom: 24px;
}

.error-summary {
  margin-bottom: 24px;
  text-align: left;
}

.error-summary pre {
  margin: 0;
  white-space: pre-wrap;
  font-family: inherit;
  font-size: 13px;
}

.complete-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
}
</style>
