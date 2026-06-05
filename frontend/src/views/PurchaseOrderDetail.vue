<template>
  <div class="purchase-order-detail" v-loading="loading">
    <div class="detail-header">
      <el-button @click="goBack" link>
        <el-icon><ArrowLeft /></el-icon>
        返回列表
      </el-button>
      <h1>采购单详情</h1>
      <div class="header-actions">
        <el-button
          v-if="order && (order.status === 'draft' || order.status === 'pending')"
          type="primary"
          @click="handleEdit"
        >
          <el-icon><Edit /></el-icon>
          编辑
        </el-button>
        <el-button
          v-if="order && order.status === 'draft'"
          type="success"
          @click="handleSubmit"
        >
          <el-icon><Check /></el-icon>
          提交待入库
        </el-button>
        <el-button
          v-if="order && order.status === 'pending'"
          type="success"
          @click="handleConfirm"
        >
          <el-icon><ShoppingCart /></el-icon>
          确认入库
        </el-button>
        <el-button
          v-if="order && order.status !== 'received' && order.status !== 'cancelled'"
          type="danger"
          @click="handleCancel"
        >
          <el-icon><Close /></el-icon>
          取消采购单
        </el-button>
      </div>
    </div>

    <div v-if="order" class="detail-content">
      <el-descriptions :column="2" border class="info-card">
        <el-descriptions-item label="采购单号">
          <span class="order-no">{{ order.order_no }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(order.status)" size="large">
            {{ getStatusText(order.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="供应商">
          <span>{{ order.supplier?.name || '-' }}</span>
          <span v-if="order.supplier?.contact_person" class="meta-text">
            ({{ order.supplier.contact_person }} - {{ order.supplier.phone || '' }})
          </span>
        </el-descriptions-item>
        <el-descriptions-item label="采购日期">
          {{ formatDate(order.purchase_date) }}
        </el-descriptions-item>
        <el-descriptions-item label="总金额">
          <span class="total-amount">¥{{ order.total_amount.toFixed(2) }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="创建人">
          {{ order.created_by_name || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="确认人" v-if="order.confirmed_by_name">
          {{ order.confirmed_by_name }}
        </el-descriptions-item>
        <el-descriptions-item label="确认时间" v-if="order.confirmed_at">
          {{ formatDate(order.confirmed_at) }}
        </el-descriptions-item>
        <el-descriptions-item label="创建时间" :span="2">
          {{ formatDate(order.created_at) }}
        </el-descriptions-item>
        <el-descriptions-item label="备注" :span="2" v-if="order.remark">
          {{ order.remark }}
        </el-descriptions-item>
      </el-descriptions>

      <el-card class="items-card">
        <template #header>
          <div class="card-header">
            <span class="card-title">采购明细</span>
            <span class="items-count">共 {{ order.items.length }} 项</span>
          </div>
        </template>
        <el-table :data="order.items" border stripe>
          <el-table-column label="序号" width="70" align="center">
            <template #default="{ $index }">
              {{ $index + 1 }}
            </template>
          </el-table-column>
          <el-table-column label="图书" min-width="200">
            <template #default="{ row }: { row: any }">
              <div class="book-info" v-if="row.book">
                <img
                  :src="row.book.cover_image || defaultCover"
                  :alt="row.book.title"
                  class="book-cover"
                  @error="handleImageError"
                />
                <div class="book-meta">
                  <div class="book-title">{{ row.book.title }}</div>
                  <div class="book-author">{{ row.book.author }}</div>
                </div>
              </div>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column label="采购数量" width="120" align="center">
            <template #default="{ row }: { row: any }">
              {{ row.quantity }}
            </template>
          </el-table-column>
          <el-table-column label="采购单价" width="120" align="center">
            <template #default="{ row }: { row: any }">
              ¥{{ row.unit_price.toFixed(2) }}
            </template>
          </el-table-column>
          <el-table-column label="小计" width="130" align="center">
            <template #default="{ row }: { row: any }">
              <span class="price">¥{{ row.subtotal.toFixed(2) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="已入库数量" width="120" align="center">
            <template #default="{ row }: { row: any }">
              <el-tag :type="row.received_quantity > 0 ? 'success' : 'info'" size="small">
                {{ row.received_quantity }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="预计到货时间" width="180" align="center">
            <template #default="{ row }: { row: any }">
              {{ row.expected_arrival_time ? formatDate(row.expected_arrival_time) : '-' }}
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <el-card v-if="order.stock_impact && order.stock_impact.length > 0" class="stock-impact-card">
        <template #header>
          <div class="card-header">
            <span class="card-title">
              <el-icon><TrendCharts /></el-icon>
              库存影响
            </span>
          </div>
        </template>
        <el-table :data="order.stock_impact" border stripe>
          <el-table-column label="图书" min-width="200">
            <template #default="{ row }: { row: any }">
              {{ row.book_title }}
            </template>
          </el-table-column>
          <el-table-column label="增加库存" width="120" align="center">
            <template #default="{ row }: { row: any }">
              <el-tag type="success" size="small">+{{ row.added_quantity }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="单位成本" width="120" align="center">
            <template #default="{ row }: { row: any }">
              ¥{{ row.unit_cost.toFixed(2) }}
            </template>
          </el-table-column>
          <el-table-column label="总成本" width="130" align="center">
            <template #default="{ row }: { row: any }">
              <span class="price">¥{{ row.total_cost.toFixed(2) }}</span>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <el-card v-if="stockChanges.length > 0" class="stock-changes-card">
        <template #header>
          <div class="card-header">
            <span class="card-title">
              <el-icon><Document /></el-icon>
              库存变动记录
            </span>
          </div>
        </template>
        <el-table :data="stockChanges" border stripe>
          <el-table-column label="图书" min-width="200">
            <template #default="{ row }: { row: any }">
              {{ row.book_title }}
            </template>
          </el-table-column>
          <el-table-column label="变动类型" width="120" align="center">
            <template #default="{ row }: { row: any }">
              <el-tag type="success" size="small">
                {{ row.change_type === 'purchase_in' ? '采购入库' : row.change_type }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="变动数量" width="120" align="center">
            <template #default="{ row }: { row: any }">
              <span class="change-quantity positive">+{{ row.change_quantity }}</span>
            </template>
          </el-table-column>
          <el-table-column label="变动前库存" width="120" align="center">
            <template #default="{ row }: { row: any }">
              {{ row.before_stock }}
            </template>
          </el-table-column>
          <el-table-column label="变动后库存" width="120" align="center">
            <template #default="{ row }: { row: any }">
              {{ row.after_stock }}
            </template>
          </el-table-column>
          <el-table-column label="单位成本" width="120" align="center">
            <template #default="{ row }: { row: any }">
              {{ row.unit_cost ? '¥' + row.unit_cost.toFixed(2) : '-' }}
            </template>
          </el-table-column>
          <el-table-column label="总成本" width="130" align="center">
            <template #default="{ row }: { row: any }">
              {{ row.total_cost ? '¥' + row.total_cost.toFixed(2) : '-' }}
            </template>
          </el-table-column>
          <el-table-column label="备注" min-width="150">
            <template #default="{ row }: { row: any }">
              {{ row.remark || '-' }}
            </template>
          </el-table-column>
          <el-table-column label="操作时间" width="180" align="center">
            <template #default="{ row }: { row: any }">
              {{ formatDate(row.created_at) }}
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>

    <el-empty v-if="!loading && !order" description="采购单不存在" />

    <el-dialog
      v-model="editDialogVisible"
      :title="'编辑采购单 - ' + (order?.order_no || '')"
      width="900px"
      destroy-on-close
      class="purchase-order-edit-dialog"
    >
      <el-form
        ref="editFormRef"
        :model="editForm"
        :rules="editRules"
        label-width="100px"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="供应商" prop="supplier_id">
              <el-select
                v-model="editForm.supplier_id"
                placeholder="请选择供应商"
                filterable
                style="width: 100%"
              >
                <el-option
                  v-for="supplier in supplierOptions"
                  :key="supplier.id"
                  :label="supplier.name"
                  :value="supplier.id"
                >
                  <span>{{ supplier.name }}</span>
                  <span v-if="supplier.contact_person" style="color: #999; margin-left: 8px;">
                    {{ supplier.contact_person }} - {{ supplier.phone || '' }}
                  </span>
                </el-option>
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="采购日期" prop="purchase_date">
              <el-date-picker
                v-model="editForm.purchase_date"
                type="datetime"
                placeholder="选择采购日期"
                style="width: 100%"
                value-format="YYYY-MM-DDTHH:mm:ss.sssZ"
              />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="备注" prop="remark">
          <el-input
            v-model="editForm.remark"
            type="textarea"
            :rows="2"
            placeholder="请输入备注信息"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
        
        <el-form-item label="采购明细">
          <div class="purchase-order-items">
            <div class="items-header">
              <span class="items-title">采购图书列表</span>
              <el-button type="primary" link @click="addEditItem">
                <el-icon><Plus /></el-icon>
                添加图书
              </el-button>
            </div>
            
            <el-table
              :data="editForm.items"
              border
              style="width: 100%"
            >
              <el-table-column label="图书" min-width="200">
                <template #default="{ row, $index }">
                  <el-select
                    v-model="row.book_id"
                    placeholder="选择图书"
                    filterable
                    style="width: 100%"
                    @change="handleEditItemBookChange($index)"
                  >
                    <el-option
                      v-for="book in allBooks"
                      :key="book.id"
                      :label="book.title"
                      :value="book.id"
                    >
                      <span>{{ book.title }}</span>
                      <span style="color: #999; margin-left: 8px;">作者: {{ book.author }}</span>
                    </el-option>
                  </el-select>
                </template>
              </el-table-column>
              <el-table-column label="采购数量" width="130">
                <template #default="{ row }">
                  <el-input-number
                    v-model="row.quantity"
                    :min="1"
                    :precision="0"
                    controls-position="right"
                    style="width: 100%"
                  />
                </template>
              </el-table-column>
              <el-table-column label="采购单价" width="130">
                <template #default="{ row }">
                  <el-input-number
                    v-model="row.unit_price"
                    :min="0.01"
                    :precision="2"
                    controls-position="right"
                    style="width: 100%"
                  />
                </template>
              </el-table-column>
              <el-table-column label="预计到货时间" width="180">
                <template #default="{ row }">
                  <el-date-picker
                    v-model="row.expected_arrival_time"
                    type="datetime"
                    placeholder="选择到货时间"
                    style="width: 100%"
                    value-format="YYYY-MM-DDTHH:mm:ss.sssZ"
                  />
                </template>
              </el-table-column>
              <el-table-column label="小计" width="120">
                <template #default="{ row }">
                  <span class="price">¥{{ (row.quantity * row.unit_price).toFixed(2) }}</span>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="80" align="center">
                <template #default="{ $index }">
                  <el-button
                    type="danger"
                    link
                    @click="removeEditItem($index)"
                  >
                    删除
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
            
            <div class="purchase-order-total">
              <span class="total-label">合计金额：</span>
              <span class="total-amount">¥{{ calculateEditTotal().toFixed(2) }}</span>
            </div>
          </div>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submittingEdit" @click="handleSubmitEdit">
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '@/api'
import type { PurchaseOrder, PurchaseOrderUpdate, PurchaseOrderItemCreate, StockChange, Book, SupplierOption } from '@/types'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { ArrowLeft, Edit, Check, ShoppingCart, Close, TrendCharts, Document, Plus } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()

const orderId = computed(() => Number(route.params.id))
const defaultCover = 'https://via.placeholder.com/60x80/6366f1/ffffff?text=Book'

const loading = ref(false)
const order = ref<PurchaseOrder | null>(null)
const stockChanges = ref<StockChange[]>([])
const allBooks = ref<Book[]>([])
const supplierOptions = ref<SupplierOption[]>([])

const editDialogVisible = ref(false)
const submittingEdit = ref(false)
const editFormRef = ref<FormInstance>()

const editForm = reactive<PurchaseOrderUpdate & { items: PurchaseOrderItemCreate[] }>({
  supplier_id: undefined,
  purchase_date: undefined,
  remark: '',
  items: []
})

const editRules: FormRules = {
  supplier_id: [{ required: true, message: '请选择供应商', trigger: 'change' }],
  purchase_date: [{ required: true, message: '请选择采购日期', trigger: 'change' }]
}

async function fetchOrder() {
  loading.value = true
  try {
    order.value = await api.getPurchaseOrder(orderId.value)
    if (order.value.status === 'received') {
      fetchStockChanges()
    }
  } catch (error) {
    console.error('获取采购单详情失败:', error)
  } finally {
    loading.value = false
  }
}

async function fetchStockChanges() {
  try {
    stockChanges.value = await api.getPurchaseOrderStockChanges(orderId.value)
  } catch (error) {
    console.error('获取库存变动记录失败:', error)
  }
}

async function fetchAllBooks() {
  try {
    const response = await api.getBooks({ page_size: 1000 })
    allBooks.value = response.items
  } catch (error) {
    console.error('获取图书列表失败:', error)
  }
}

async function fetchAllSuppliers() {
  try {
    supplierOptions.value = await api.getAllSuppliers()
  } catch (error) {
    console.error('获取供应商列表失败:', error)
  }
}

function getStatusType(status: string): 'success' | 'warning' | 'info' | 'danger' {
  switch (status) {
    case 'draft': return 'info'
    case 'pending': return 'warning'
    case 'received': return 'success'
    case 'cancelled': return 'danger'
    default: return 'info'
  }
}

function getStatusText(status: string): string {
  switch (status) {
    case 'draft': return '草稿'
    case 'pending': return '待入库'
    case 'received': return '已入库'
    case 'cancelled': return '已取消'
    default: return status
  }
}

function formatDate(date: string | Date): string {
  if (!date) return '-'
  const d = new Date(date)
  if (isNaN(d.getTime())) return '-'
  
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hours = String(d.getHours()).padStart(2, '0')
  const minutes = String(d.getMinutes()).padStart(2, '0')
  const seconds = String(d.getSeconds()).padStart(2, '0')
  
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
}

function handleImageError(e: Event) {
  const target = e.target as HTMLImageElement
  target.src = defaultCover
}

function goBack() {
  router.push('/admin')
}

function handleEdit() {
  if (!order.value) return
  
  if (supplierOptions.value.length === 0) {
    fetchAllSuppliers()
  }
  if (allBooks.value.length === 0) {
    fetchAllBooks()
  }
  
  editForm.supplier_id = order.value.supplier_id
  editForm.purchase_date = order.value.purchase_date
  editForm.remark = order.value.remark || ''
  editForm.items = order.value.items.map(item => ({
    book_id: item.book_id,
    quantity: item.quantity,
    unit_price: item.unit_price,
    expected_arrival_time: item.expected_arrival_time || undefined
  }))
  
  editDialogVisible.value = true
}

function addEditItem() {
  editForm.items.push({
    book_id: 0,
    quantity: 1,
    unit_price: 0,
    expected_arrival_time: undefined
  })
}

function removeEditItem(index: number) {
  editForm.items.splice(index, 1)
}

function handleEditItemBookChange(index: number) {
  const item = editForm.items[index]
  const book = allBooks.value.find(b => b.id === item.book_id)
  if (book && item.unit_price === 0) {
    item.unit_price = book.price
  }
}

function calculateEditTotal(): number {
  return editForm.items.reduce((sum, item) => sum + item.quantity * item.unit_price, 0)
}

async function handleSubmitEdit() {
  if (!editFormRef.value) return
  
  await editFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    if (editForm.items.length === 0) {
      ElMessage.warning('请至少添加一条采购明细')
      return
    }
    
    const invalidItems = editForm.items.filter(item => item.book_id === 0 || item.quantity <= 0 || item.unit_price <= 0)
    if (invalidItems.length > 0) {
      ElMessage.warning('请完善所有采购明细信息')
      return
    }
    
    submittingEdit.value = true
    try {
      await api.updatePurchaseOrder(orderId.value, {
        supplier_id: editForm.supplier_id,
        purchase_date: editForm.purchase_date,
        remark: editForm.remark,
        items: editForm.items
      })
      ElMessage.success('更新成功')
      editDialogVisible.value = false
      fetchOrder()
    } catch (error) {
      console.error('更新失败:', error)
    } finally {
      submittingEdit.value = false
    }
  })
}

async function handleSubmit() {
  try {
    await ElMessageBox.confirm(
      '确认提交该采购单吗？提交后状态将变为待入库。',
      '确认提交',
      { confirmButtonText: '确认提交', cancelButtonText: '返回', type: 'warning' }
    )
    await api.submitPurchaseOrder(orderId.value)
    ElMessage.success('采购单已提交，状态变为待入库')
    fetchOrder()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('提交失败:', error)
    }
  }
}

async function handleConfirm() {
  try {
    await ElMessageBox.confirm(
      '确认入库该采购单吗？确认后将增加库存、记录成本并生成库存变动记录，不可重复确认。',
      '确认入库',
      { confirmButtonText: '确认入库', cancelButtonText: '返回', type: 'success' }
    )
    await api.confirmPurchaseOrder(orderId.value)
    ElMessage.success('采购单已确认入库，库存已更新')
    fetchOrder()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('确认入库失败:', error)
    }
  }
}

async function handleCancel() {
  try {
    await ElMessageBox.confirm(
      '确认取消该采购单吗？取消后将不可恢复。',
      '确认取消',
      { confirmButtonText: '确认取消', cancelButtonText: '返回', type: 'error' }
    )
    await api.cancelPurchaseOrder(orderId.value)
    ElMessage.success('采购单已取消')
    fetchOrder()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('取消失败:', error)
    }
  }
}

onMounted(() => {
  fetchOrder()
  fetchAllBooks()
  fetchAllSuppliers()
})
</script>

<style scoped>
.purchase-order-detail {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.detail-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 8px;
}

.detail-header h1 {
  flex: 1;
  font-size: 24px;
  font-weight: 600;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.info-card {
  margin-bottom: 16px;
}

.order-no {
  font-family: monospace;
  font-size: 16px;
  font-weight: 600;
  color: var(--primary-color);
}

.meta-text {
  color: var(--text-secondary);
  font-size: 14px;
  margin-left: 8px;
}

.total-amount {
  font-size: 20px;
  font-weight: 700;
  color: var(--secondary-color);
}

.items-card,
.stock-impact-card,
.stock-changes-card {
  margin-bottom: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-weight: 600;
  font-size: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.items-count {
  color: var(--text-secondary);
  font-size: 14px;
}

.book-info {
  display: flex;
  gap: 12px;
  align-items: center;
}

.book-cover {
  width: 50px;
  height: 70px;
  object-fit: cover;
  border-radius: 4px;
}

.book-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.book-title {
  font-weight: 500;
}

.book-author {
  color: var(--text-secondary);
  font-size: 13px;
}

.price {
  color: var(--secondary-color);
  font-weight: 600;
}

.change-quantity.positive {
  color: var(--success-color);
  font-weight: 600;
}

.purchase-order-items {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 100%;
}

.items-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.items-title {
  font-weight: 500;
}

.purchase-order-total {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 8px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--border-color);
}

.total-label {
  font-size: 16px;
  color: var(--text-secondary);
}

.purchase-order-edit-dialog :deep(.el-dialog__body) {
  max-height: 70vh;
  overflow-y: auto;
}
</style>
