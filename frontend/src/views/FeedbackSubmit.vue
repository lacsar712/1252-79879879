<template>
  <div class="feedback-submit-page">
    <div class="page-header">
      <h1>提交客服反馈</h1>
      <p class="page-desc">我们非常重视您的反馈，客服团队会尽快处理您的问题</p>
    </div>

    <el-card class="form-card">
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
        class="feedback-form"
      >
        <el-row :gutter="24">
          <el-col :span="12">
            <el-form-item label="问题类型" prop="type">
              <el-select v-model="form.type" placeholder="请选择问题类型" style="width: 100%">
                <el-option
                  v-for="item in feedbackTypes"
                  :key="item.value"
                  :label="item.label"
                  :value="item.value"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="联系方式" prop="contact_info">
              <el-input
                v-model="form.contact_info"
                placeholder="手机号或邮箱，方便我们联系您"
                maxlength="200"
                show-word-limit
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="标题" prop="title">
          <el-input
            v-model="form.title"
            placeholder="请简要描述您遇到的问题"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>

        <el-row :gutter="24">
          <el-col :span="12">
            <el-form-item label="关联订单">
              <el-input
                v-model="form.related_order_id"
                placeholder="请输入订单号（如有）"
                maxlength="100"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="关联图书">
              <el-select
                v-model="form.related_book_id"
                placeholder="选择关联图书（如有）"
                filterable
                clearable
                style="width: 100%"
              >
                <el-option
                  v-for="book in books"
                  :key="book.id"
                  :label="book.title"
                  :value="book.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="问题描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="6"
            placeholder="请详细描述您遇到的问题，包括问题发生的时间、具体现象等信息"
            maxlength="2000"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="上传图片">
          <el-upload
            :auto-upload="false"
            :multiple="true"
            :limit="5"
            :on-change="handleFileChange"
            :on-remove="handleFileRemove"
            :file-list="fileList"
            list-type="picture-card"
            accept="image/*"
            class="image-uploader"
          >
            <el-icon><Plus /></el-icon>
            <template #tip>
              <div class="el-upload__tip">
                支持 JPG、PNG、GIF、WEBP 格式，单张不超过 10MB，最多上传 5 张
              </div>
            </template>
          </el-upload>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="submitting" @click="handleSubmit" size="large">
            <el-icon><CircleCheck /></el-icon>
            提交反馈
          </el-button>
          <el-button @click="handleReset" size="large">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-image-viewer
      v-if="previewVisible"
      :url-list="[previewImage]"
      :initial-index="0"
      @close="previewVisible = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/api'
import type { Book, FeedbackAttachmentCreate, FeedbackTypeOption, FeedbackCreate } from '@/types'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules, type UploadFile, type UploadProps } from 'element-plus'
import { Plus, CircleCheck, Refresh } from '@element-plus/icons-vue'

const router = useRouter()
const formRef = ref<FormInstance>()
const submitting = ref(false)
const uploading = ref(false)
const books = ref<Book[]>([])
const feedbackTypes = ref<FeedbackTypeOption[]>([])
const fileList = ref<UploadFile[]>([])
const previewVisible = ref(false)
const previewImage = ref('')

const form = reactive<FeedbackCreate>({
  type: '',
  title: '',
  description: '',
  contact_info: '',
  related_order_id: '',
  related_book_id: undefined,
  attachments: []
})

const rules: FormRules = {
  type: [{ required: true, message: '请选择问题类型', trigger: 'change' }],
  title: [
    { required: true, message: '请输入反馈标题', trigger: 'blur' },
    { min: 5, max: 200, message: '标题长度在 5 到 200 个字符', trigger: 'blur' }
  ],
  description: [
    { required: true, message: '请输入问题描述', trigger: 'blur' },
    { min: 10, max: 2000, message: '描述长度在 10 到 2000 个字符', trigger: 'blur' }
  ],
  contact_info: [
    {
      validator: (_rule, value, callback) => {
        if (value && value.length > 200) {
          callback(new Error('联系方式不能超过 200 个字符'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

onMounted(async () => {
  await Promise.all([fetchBooks(), fetchFeedbackTypes()])
})

async function fetchBooks() {
  try {
    const response = await api.getBooks({ page: 1, page_size: 1000 })
    books.value = response.items
  } catch (error) {
    console.error('获取图书列表失败:', error)
  }
}

async function fetchFeedbackTypes() {
  try {
    feedbackTypes.value = await api.getFeedbackTypes()
  } catch (error) {
    console.error('获取反馈类型失败:', error)
  }
}

const handleFileChange: UploadProps['onChange'] = async (file, uploadFiles) => {
  if (file.raw) {
    const maxSize = 10 * 1024 * 1024
    if (file.raw.size > maxSize) {
      ElMessage.error('文件大小不能超过 10MB')
      uploadFiles.pop()
      return
    }

    const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/jpg']
    if (!allowedTypes.includes(file.raw.type)) {
      ElMessage.error('只支持上传图片文件')
      uploadFiles.pop()
      return
    }
  }

  fileList.value = uploadFiles
}

const handleFileRemove: UploadProps['onRemove'] = (_file, uploadFiles) => {
  fileList.value = uploadFiles
}

async function uploadFiles(): Promise<FeedbackAttachmentCreate[]> {
  const attachments: FeedbackAttachmentCreate[] = []

  for (const file of fileList.value) {
    if (file.raw) {
      try {
        const result = await api.uploadFeedbackAttachment(file.raw)
        attachments.push({
          file_name: result.file_name,
          file_path: result.file_path,
          file_size: result.file_size,
          file_type: result.file_type
        })
      } catch (error) {
        console.error('上传文件失败:', error)
        throw new Error(`文件 ${file.name} 上传失败`)
      }
    }
  }

  return attachments
}

async function handleSubmit() {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    try {
      await ElMessageBox.confirm(
        '确认提交反馈吗？提交后我们会尽快处理您的问题。',
        '确认提交',
        {
          confirmButtonText: '确认提交',
          cancelButtonText: '取消',
          type: 'info'
        }
      )
    } catch {
      return
    }

    submitting.value = true
    try {
      let attachments: FeedbackAttachmentCreate[] = []
      if (fileList.value.length > 0) {
        uploading.value = true
        attachments = await uploadFiles()
      }

      const feedbackData: FeedbackCreate = {
        type: form.type,
        title: form.title,
        description: form.description,
        contact_info: form.contact_info || undefined,
        related_order_id: form.related_order_id || undefined,
        related_book_id: form.related_book_id,
        attachments
      }

      await api.createFeedback(feedbackData)
      ElMessage.success('反馈提交成功！我们会尽快处理您的问题')
      router.push('/feedbacks')
    } catch (error) {
      console.error('提交反馈失败:', error)
      ElMessage.error('提交失败，请稍后重试')
    } finally {
      submitting.value = false
      uploading.value = false
    }
  })
}

function handleReset() {
  formRef.value?.resetFields()
  form.type = ''
  form.title = ''
  form.description = ''
  form.contact_info = ''
  form.related_order_id = ''
  form.related_book_id = undefined
  form.attachments = []
  fileList.value = []
}
</script>

<style scoped>
.feedback-submit-page {
  max-width: 900px;
  margin: 0 auto;
}

.page-header {
  text-align: center;
  margin-bottom: 32px;
}

.page-header h1 {
  font-size: 32px;
  font-weight: 700;
  margin-bottom: 8px;
  background: var(--gradient-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.page-desc {
  color: var(--text-secondary);
  font-size: 16px;
}

.form-card {
  padding: 24px;
}

.feedback-form {
  padding: 16px 0;
}

.image-uploader {
  width: 100%;
}

.image-uploader :deep(.el-upload--picture-card) {
  width: 120px;
  height: 120px;
  line-height: 120px;
}

.image-uploader :deep(.el-upload-list--picture-card .el-upload-list__item) {
  width: 120px;
  height: 120px;
}

.image-item {
  position: relative;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.2s;
}

.image-item:hover {
  transform: scale(1.02);
}

.image-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.image-mask {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  opacity: 0;
  transition: opacity 0.2s;
}

.image-item:hover .image-mask {
  opacity: 1;
}

.mask-btn {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-primary);
  transition: all 0.2s;
}

.mask-btn:hover {
  background: #fff;
  color: var(--primary-color);
}

.mask-btn.danger:hover {
  color: var(--error-color);
}

.attachment-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: var(--bg-secondary);
  border-radius: 8px;
  margin-bottom: 8px;
}

.attachment-icon {
  font-size: 32px;
  color: var(--primary-color);
}

.attachment-info {
  flex: 1;
  min-width: 0;
}

.attachment-name {
  font-weight: 500;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.attachment-size {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 2px;
}
</style>
