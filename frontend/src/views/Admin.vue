<template>
  <div class="admin-page">
    <el-tabs v-model="activeTab" type="card" class="admin-tabs">
      <el-tab-pane label="图书管理" name="books">
        <div class="admin-header">
          <h1>图书管理</h1>
          <el-button type="primary" @click="handleAddBook">
            <el-icon><Plus /></el-icon>
            添加图书
          </el-button>
        </div>
        
        <div class="search-bar">
          <el-input
            v-model="searchQuery"
            placeholder="搜索图书..."
            clearable
            @keyup.enter="fetchBooks"
            style="max-width: 300px"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          <el-button @click="fetchBooks">搜索</el-button>
        </div>
        
        <el-table
          :data="books"
          v-loading="loadingBooks"
          stripe
          style="width: 100%"
        >
          <el-table-column prop="id" label="ID" width="70" />
          <el-table-column label="封面" width="80">
            <template #default="{ row }">
              <img
                :src="row.cover_image || defaultCover"
                :alt="row.title"
                class="book-thumbnail"
                @error="handleImageError"
              >
            </template>
          </el-table-column>
          <el-table-column prop="title" label="书名" min-width="150">
            <template #default="{ row }">
              <span class="book-title">{{ row.title }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="author" label="作者" width="120" />
          <el-table-column prop="publisher" label="出版社" width="140">
            <template #default="{ row }">
              <span>{{ row.publisher || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="category" label="分类" width="100">
            <template #default="{ row }">
              <el-tag v-if="row.category" size="small">{{ row.category }}</el-tag>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="price" label="价格" width="100">
            <template #default="{ row }">
              <span class="price">¥{{ row.price.toFixed(2) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="stock" label="库存" width="80">
            <template #default="{ row }">
              <el-tag :type="row.stock > 0 ? 'success' : 'danger'" size="small">
                {{ row.stock }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="handleEditBook(row)">
                编辑
              </el-button>
              <el-popconfirm
                title="确定要删除此图书吗？"
                @confirm="handleDeleteBook(row.id)"
              >
                <template #reference>
                  <el-button type="danger" link>删除</el-button>
                </template>
              </el-popconfirm>
            </template>
          </el-table-column>
        </el-table>
        
        <div class="pagination">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :total="totalBooks"
            layout="total, prev, pager, next"
            @current-change="fetchBooks"
          />
        </div>
      </el-tab-pane>

      <el-tab-pane label="活动管理" name="promotions">
        <div class="admin-header">
          <h1>活动管理</h1>
          <el-button type="primary" @click="handleAddPromotion">
            <el-icon><Plus /></el-icon>
            添加活动
          </el-button>
        </div>
        
        <div class="search-bar">
          <el-select
            v-model="promotionStatus"
            placeholder="活动状态"
            clearable
            @change="fetchPromotions"
            style="width: 150px"
          >
            <el-option label="未开始" value="pending" />
            <el-option label="进行中" value="active" />
            <el-option label="已结束" value="ended" />
          </el-select>
          <el-select
            v-model="promotionDisplayed"
            placeholder="展示状态"
            clearable
            @change="fetchPromotions"
            style="width: 150px"
          >
            <el-option label="展示" :value="true" />
            <el-option label="隐藏" :value="false" />
          </el-select>
          <el-button @click="fetchPromotions">搜索</el-button>
        </div>
        
        <el-table
          :data="promotions"
          v-loading="loadingPromotions"
          stripe
          style="width: 100%"
        >
          <el-table-column prop="id" label="ID" width="70" />
          <el-table-column label="封面" width="80">
            <template #default="{ row }">
              <img
                :src="row.cover_image || defaultCover"
                :alt="row.name"
                class="book-thumbnail"
                @error="handleImageError"
              >
            </template>
          </el-table-column>
          <el-table-column prop="name" label="活动名称" min-width="180">
            <template #default="{ row }">
              <span class="book-title">{{ row.name }}</span>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="getStatusType(row.status)" size="small">
                {{ getStatusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="start_time" label="开始时间" width="180">
            <template #default="{ row }">
              <span>{{ formatDate(row.start_time) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="end_time" label="结束时间" width="180">
            <template #default="{ row }">
              <span>{{ formatDate(row.end_time) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="参与图书" width="100">
            <template #default="{ row }">
              <span>{{ row.books.length }} 本</span>
            </template>
          </el-table-column>
          <el-table-column label="展示状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.is_displayed ? 'success' : 'info'" size="small">
                {{ row.is_displayed ? '展示' : '隐藏' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="180" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="handleEditPromotion(row)">
                编辑
              </el-button>
              <el-button link type="success" @click="router.push(`/promotions/${row.id}`)">
                查看
              </el-button>
              <el-popconfirm
                title="确定要删除此活动吗？"
                @confirm="handleDeletePromotion(row.id)"
              >
                <template #reference>
                  <el-button type="danger" link>删除</el-button>
                </template>
              </el-popconfirm>
            </template>
          </el-table-column>
        </el-table>
        
        <div class="pagination">
          <el-pagination
            v-model:current-page="promotionPage"
            v-model:page-size="promotionPageSize"
            :total="totalPromotions"
            layout="total, prev, pager, next"
            @current-change="fetchPromotions"
          />
        </div>
      </el-tab-pane>
    </el-tabs>

    <el-dialog
      v-model="bookDialogVisible"
      :title="isEditBook ? '编辑图书' : '添加图书'"
      width="600px"
      destroy-on-close
    >
      <el-form
        ref="bookFormRef"
        :model="bookForm"
        :rules="bookRules"
        label-width="80px"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="书名" prop="title">
              <el-input v-model="bookForm.title" placeholder="请输入书名" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="作者" prop="author">
              <el-input v-model="bookForm.author" placeholder="请输入作者" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="出版社" prop="publisher">
              <el-input v-model="bookForm.publisher" placeholder="请输入出版社" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="ISBN" prop="isbn">
              <el-input v-model="bookForm.isbn" placeholder="请输入ISBN" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="价格" prop="price">
              <el-input-number
                v-model="bookForm.price"
                :min="0.01"
                :precision="2"
                controls-position="right"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="库存" prop="stock">
              <el-input-number
                v-model="bookForm.stock"
                :min="0"
                controls-position="right"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="分类" prop="category">
          <el-input v-model="bookForm.category" placeholder="请输入分类" />
        </el-form-item>
        
        <el-form-item label="封面" prop="cover_image">
          <el-input v-model="bookForm.cover_image" placeholder="请输入封面图片URL" />
        </el-form-item>
        
        <el-form-item label="简介" prop="description">
          <el-input
            v-model="bookForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入图书简介"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="bookDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submittingBook" @click="handleSubmitBook">
          {{ isEditBook ? '保存' : '添加' }}
        </el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="promotionDialogVisible"
      :title="isEditPromotion ? '编辑活动' : '添加活动'"
      width="800px"
      destroy-on-close
      class="promotion-dialog"
    >
      <el-form
        ref="promotionFormRef"
        :model="promotionForm"
        :rules="promotionRules"
        label-width="100px"
      >
        <el-form-item label="活动名称" prop="name">
          <el-input v-model="promotionForm.name" placeholder="请输入活动名称" />
        </el-form-item>
        
        <el-form-item label="封面图片" prop="cover_image">
          <el-input v-model="promotionForm.cover_image" placeholder="请输入活动封面图片URL" />
        </el-form-item>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="开始时间" prop="start_time">
              <el-date-picker
                v-model="promotionForm.start_time"
                type="datetime"
                placeholder="选择开始时间"
                style="width: 100%"
                value-format="YYYY-MM-DDTHH:mm:ss.sssZ"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="结束时间" prop="end_time">
              <el-date-picker
                v-model="promotionForm.end_time"
                type="datetime"
                placeholder="选择结束时间"
                style="width: 100%"
                value-format="YYYY-MM-DDTHH:mm:ss.sssZ"
              />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="活动说明" prop="description">
          <el-input
            v-model="promotionForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入活动说明"
          />
        </el-form-item>
        
        <el-form-item label="展示状态" prop="is_displayed">
          <el-switch
            v-model="promotionForm.is_displayed"
            active-text="展示"
            inactive-text="隐藏"
          />
        </el-form-item>
        
        <el-form-item label="参与图书">
          <div class="promotion-books">
            <div
              v-for="(book, index) in promotionForm.books"
              :key="index"
              class="promotion-book-item"
            >
              <el-select
                v-model="book.book_id"
                placeholder="选择图书"
                filterable
                style="width: 200px"
                @change="handleBookChange(index)"
              >
                <el-option
                  v-for="b in allBooks"
                  :key="b.id"
                  :label="b.title"
                  :value="b.id"
                />
              </el-select>
              <el-input-number
                v-model="book.promotion_price"
                :min="0.01"
                :precision="2"
                placeholder="活动价"
                style="width: 120px"
              />
              <el-input-number
                v-model="book.promotion_stock"
                :min="0"
                placeholder="活动库存"
                style="width: 120px"
              />
              <el-input-number
                v-model="book.purchase_limit"
                :min="1"
                placeholder="限购"
                style="width: 100px"
              />
              <span v-if="getBookInfo(book.book_id)" class="book-price-info">
                原价: ¥{{ getBookInfo(book.book_id)?.price.toFixed(2) }}
              </span>
              <el-button type="danger" link @click="removePromotionBook(index)">
                删除
              </el-button>
            </div>
            <el-button type="primary" link @click="addPromotionBook">
              <el-icon><Plus /></el-icon>
              添加图书
            </el-button>
          </div>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="promotionDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submittingPromotion" @click="handleSubmitPromotion">
          {{ isEditPromotion ? '保存' : '添加' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/api'
import type { Book, BookCreate, Promotion, PromotionCreate } from '@/types'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'

const router = useRouter()

const activeTab = ref('books')
const defaultCover = 'https://via.placeholder.com/60x80/6366f1/ffffff?text=Book'

const loadingBooks = ref(false)
const submittingBook = ref(false)
const books = ref<Book[]>([])
const totalBooks = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const searchQuery = ref('')
const bookDialogVisible = ref(false)
const isEditBook = ref(false)
const editingBookId = ref<number | null>(null)
const bookFormRef = ref<FormInstance>()

const bookForm = reactive<BookCreate>({
  title: '',
  author: '',
  publisher: '',
  isbn: '',
  price: 0,
  stock: 0,
  description: '',
  cover_image: '',
  category: ''
})

const bookRules: FormRules = {
  title: [{ required: true, message: '请输入书名', trigger: 'blur' }],
  author: [{ required: true, message: '请输入作者', trigger: 'blur' }],
  price: [{ required: true, message: '请输入价格', trigger: 'blur' }]
}

const loadingPromotions = ref(false)
const submittingPromotion = ref(false)
const promotions = ref<Promotion[]>([])
const totalPromotions = ref(0)
const promotionPage = ref(1)
const promotionPageSize = ref(10)
const promotionStatus = ref('')
const promotionDisplayed = ref<boolean | undefined>(undefined)
const promotionDialogVisible = ref(false)
const isEditPromotion = ref(false)
const editingPromotionId = ref<number | null>(null)
const promotionFormRef = ref<FormInstance>()
const allBooks = ref<Book[]>([])

const promotionForm = reactive<PromotionCreate>({
  name: '',
  cover_image: '',
  start_time: '',
  end_time: '',
  description: '',
  is_displayed: true,
  books: []
})

const promotionRules: FormRules = {
  name: [{ required: true, message: '请输入活动名称', trigger: 'blur' }],
  start_time: [{ required: true, message: '请选择开始时间', trigger: 'change' }],
  end_time: [{ required: true, message: '请选择结束时间', trigger: 'change' }]
}

onMounted(async () => {
  await Promise.all([fetchBooks(), fetchAllBooks()])
})

watch(activeTab, (newTab) => {
  if (newTab === 'promotions' && promotions.value.length === 0) {
    fetchPromotions()
  }
})

async function fetchBooks() {
  loadingBooks.value = true
  try {
    const response = await api.getBooks({
      page: currentPage.value,
      page_size: pageSize.value,
      search: searchQuery.value || undefined
    })
    books.value = response.items
    totalBooks.value = response.total
  } catch (error) {
    console.error('获取图书列表失败:', error)
  } finally {
    loadingBooks.value = false
  }
}

async function fetchAllBooks() {
  try {
    const response = await api.getBooks({ page: 1, page_size: 1000 })
    allBooks.value = response.items
  } catch (error) {
    console.error('获取所有图书失败:', error)
  }
}

async function fetchPromotions() {
  loadingPromotions.value = true
  try {
    const response = await api.getPromotions({
      page: promotionPage.value,
      page_size: promotionPageSize.value,
      status: promotionStatus.value || undefined,
      is_displayed: promotionDisplayed.value
    })
    promotions.value = response.items
    totalPromotions.value = response.total
  } catch (error) {
    console.error('获取活动列表失败:', error)
  } finally {
    loadingPromotions.value = false
  }
}

function handleAddBook() {
  isEditBook.value = false
  editingBookId.value = null
  resetBookForm()
  bookDialogVisible.value = true
}

function handleEditBook(book: Book) {
  isEditBook.value = true
  editingBookId.value = book.id
  Object.assign(bookForm, {
    title: book.title,
    author: book.author,
    publisher: book.publisher || '',
    isbn: book.isbn || '',
    price: book.price,
    stock: book.stock,
    description: book.description || '',
    cover_image: book.cover_image || '',
    category: book.category || ''
  })
  bookDialogVisible.value = true
}

async function handleDeleteBook(id: number) {
  try {
    await api.deleteBook(id)
    ElMessage.success('删除成功')
    fetchBooks()
  } catch (error) {
    console.error('删除失败:', error)
  }
}

async function handleSubmitBook() {
  if (!bookFormRef.value) return
  
  await bookFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    submittingBook.value = true
    try {
      if (isEditBook.value && editingBookId.value) {
        await api.updateBook(editingBookId.value, bookForm)
        ElMessage.success('更新成功')
      } else {
        await api.createBook(bookForm)
        ElMessage.success('添加成功')
      }
      bookDialogVisible.value = false
      fetchBooks()
      fetchAllBooks()
    } catch (error) {
      console.error('操作失败:', error)
    } finally {
      submittingBook.value = false
    }
  })
}

function resetBookForm() {
  Object.assign(bookForm, {
    title: '',
    author: '',
    publisher: '',
    isbn: '',
    price: 0,
    stock: 0,
    description: '',
    cover_image: '',
    category: ''
  })
}

function handleAddPromotion() {
  isEditPromotion.value = false
  editingPromotionId.value = null
  resetPromotionForm()
  promotionDialogVisible.value = true
}

function handleEditPromotion(promotion: Promotion) {
  isEditPromotion.value = true
  editingPromotionId.value = promotion.id
  Object.assign(promotionForm, {
    name: promotion.name,
    cover_image: promotion.cover_image || '',
    start_time: promotion.start_time,
    end_time: promotion.end_time,
    description: promotion.description || '',
    is_displayed: promotion.is_displayed,
    books: promotion.books.map(b => ({
      book_id: b.book_id,
      promotion_price: b.promotion_price,
      promotion_stock: b.promotion_stock,
      purchase_limit: b.purchase_limit || undefined
    }))
  })
  promotionDialogVisible.value = true
}

async function handleDeletePromotion(id: number) {
  try {
    await api.deletePromotion(id)
    ElMessage.success('删除成功')
    fetchPromotions()
  } catch (error) {
    console.error('删除失败:', error)
  }
}

async function handleSubmitPromotion() {
  if (!promotionFormRef.value) return
  
  await promotionFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    if (promotionForm.books.length === 0) {
      ElMessage.warning('请至少添加一本参与图书')
      return
    }
    
    submittingPromotion.value = true
    try {
      if (isEditPromotion.value && editingPromotionId.value) {
        await api.updatePromotion(editingPromotionId.value, promotionForm)
        ElMessage.success('更新成功')
      } else {
        await api.createPromotion(promotionForm)
        ElMessage.success('添加成功')
      }
      promotionDialogVisible.value = false
      fetchPromotions()
    } catch (error) {
      console.error('操作失败:', error)
    } finally {
      submittingPromotion.value = false
    }
  })
}

function resetPromotionForm() {
  Object.assign(promotionForm, {
    name: '',
    cover_image: '',
    start_time: '',
    end_time: '',
    description: '',
    is_displayed: true,
    books: []
  })
}

function addPromotionBook() {
  promotionForm.books.push({
    book_id: 0,
    promotion_price: 0,
    promotion_stock: 0,
    purchase_limit: undefined
  })
}

function removePromotionBook(index: number) {
  promotionForm.books.splice(index, 1)
}

function handleBookChange(index: number) {
  const book = promotionForm.books[index]
  const bookInfo = getBookInfo(book.book_id)
  if (bookInfo && book.promotion_price === 0) {
    book.promotion_price = Number((bookInfo.price * 0.9).toFixed(2))
  }
}

function getBookInfo(bookId: number) {
  return allBooks.value.find(b => b.id === bookId)
}

function handleImageError(e: Event) {
  const img = e.target as HTMLImageElement
  img.src = defaultCover
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleString('zh-CN')
}

function getStatusType(status: string) {
  switch (status) {
    case 'pending': return 'warning'
    case 'active': return 'success'
    case 'ended': return 'info'
    default: return 'info'
  }
}

function getStatusText(status: string) {
  switch (status) {
    case 'pending': return '未开始'
    case 'active': return '进行中'
    case 'ended': return '已结束'
    default: return status
  }
}
</script>

<style scoped>
.admin-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.admin-tabs {
  margin-bottom: 16px;
}

.admin-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.admin-header h1 {
  font-size: 24px;
  font-weight: 600;
}

.search-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.book-thumbnail {
  width: 40px;
  height: 55px;
  object-fit: cover;
  border-radius: 4px;
}

.book-title {
  font-weight: 500;
}

.price {
  color: var(--secondary-color);
  font-weight: 600;
}

.pagination {
  display: flex;
  justify-content: center;
  margin-top: 16px;
}

.promotion-books {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 100%;
}

.promotion-book-item {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}

.book-price-info {
  color: var(--text-secondary);
  font-size: 14px;
}

.promotion-dialog :deep(.el-dialog__body) {
  max-height: 60vh;
  overflow-y: auto;
}
</style>
