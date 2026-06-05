<template>
  <div class="admin-page">
    <div class="admin-header">
      <h1>图书管理</h1>
      <el-button type="primary" @click="handleAdd">
        <el-icon><Plus /></el-icon>
        添加图书
      </el-button>
    </div>
    
    <!-- 搜索栏 -->
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
    
    <!-- 图书表格 -->
    <el-table
      :data="books"
      v-loading="loading"
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
          <el-button link type="primary" @click="handleEdit(row)">
            编辑
          </el-button>
          <el-popconfirm
            title="确定要删除此图书吗？"
            @confirm="handleDelete(row.id)"
          >
            <template #reference>
              <el-button type="danger" link>删除</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>
    
    <!-- 分页 -->
    <div class="pagination">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next"
        @current-change="fetchBooks"
      />
    </div>
    
    <!-- 添加/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑图书' : '添加图书'"
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
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">
          {{ isEdit ? '保存' : '添加' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { api } from '@/api'
import type { Book, BookCreate } from '@/types'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'

const loading = ref(false)
const submitting = ref(false)
const books = ref<Book[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const searchQuery = ref('')
const dialogVisible = ref(false)
const isEdit = ref(false)
const editingId = ref<number | null>(null)
const bookFormRef = ref<FormInstance>()
const defaultCover = 'https://via.placeholder.com/60x80/6366f1/ffffff?text=Book'

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

onMounted(() => {
  fetchBooks()
})

async function fetchBooks() {
  loading.value = true
  try {
    const response = await api.getBooks({
      page: currentPage.value,
      page_size: pageSize.value,
      search: searchQuery.value || undefined
    })
    books.value = response.items
    total.value = response.total
  } catch (error) {
    console.error('获取图书列表失败:', error)
  } finally {
    loading.value = false
  }
}

function handleAdd() {
  isEdit.value = false
  editingId.value = null
  resetForm()
  dialogVisible.value = true
}

function handleEdit(book: Book) {
  isEdit.value = true
  editingId.value = book.id
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
  dialogVisible.value = true
}

async function handleDelete(id: number) {
  try {
    await api.deleteBook(id)
    ElMessage.success('删除成功')
    fetchBooks()
  } catch (error) {
    console.error('删除失败:', error)
  }
}

async function handleSubmit() {
  if (!bookFormRef.value) return
  
  await bookFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    submitting.value = true
    try {
      if (isEdit.value && editingId.value) {
        await api.updateBook(editingId.value, bookForm)
        ElMessage.success('更新成功')
      } else {
        await api.createBook(bookForm)
        ElMessage.success('添加成功')
      }
      dialogVisible.value = false
      fetchBooks()
    } catch (error) {
      console.error('操作失败:', error)
    } finally {
      submitting.value = false
    }
  })
}

function resetForm() {
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

function handleImageError(e: Event) {
  const img = e.target as HTMLImageElement
  img.src = defaultCover
}
</script>

<style scoped>
.admin-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.admin-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.admin-header h1 {
  font-size: 24px;
  font-weight: 600;
}

.search-bar {
  display: flex;
  gap: 12px;
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
}
</style>
