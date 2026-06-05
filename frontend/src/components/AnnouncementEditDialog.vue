<template>
  <el-dialog
    v-model="visible"
    :title="isEdit ? '编辑公告' : '创建公告'"
    width="700px"
    :close-on-click-modal="false"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="100px"
      v-loading="loading"
    >
      <el-form-item label="公告标题" prop="title">
        <el-input
          v-model="form.title"
          placeholder="请输入公告标题"
          maxlength="200"
          show-word-limit
        />
      </el-form-item>

      <el-form-item label="公告内容" prop="content">
        <el-input
          v-model="form.content"
          type="textarea"
          :rows="5"
          placeholder="请输入公告内容"
          maxlength="2000"
          show-word-limit
        />
      </el-form-item>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="展示位置" prop="display_position">
            <el-select v-model="form.display_position" placeholder="请选择展示位置" style="width: 100%">
              <el-option
                v-for="pos in positionOptions"
                :key="pos.value"
                :label="pos.label"
                :value="pos.value"
              />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="展示类型" prop="display_type">
            <el-select v-model="form.display_type" placeholder="请选择展示类型" style="width: 100%">
              <el-option
                v-for="type in typeOptions"
                :key="type.value"
                :label="type.label"
                :value="type.value"
              />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="开始时间" prop="start_time">
            <el-date-picker
              v-model="form.start_time"
              type="datetime"
              placeholder="选择开始时间"
              value-format="YYYY-MM-DDTHH:mm:ss"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="结束时间" prop="end_time">
            <el-date-picker
              v-model="form.end_time"
              type="datetime"
              placeholder="选择结束时间"
              value-format="YYYY-MM-DDTHH:mm:ss"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="目标用户" prop="target_user_type">
            <el-select v-model="form.target_user_type" placeholder="请选择目标用户" style="width: 100%">
              <el-option
                v-for="type in targetUserOptions"
                :key="type.value"
                :label="type.label"
                :value="type.value"
              />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="优先级" prop="priority">
            <el-input-number
              v-model="form.priority"
              :min="0"
              :max="100"
              placeholder="数值越大越优先"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="置顶状态">
            <el-switch v-model="form.is_pinned" />
            <span class="form-tip">置顶公告会优先显示</span>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="启用状态">
            <el-switch v-model="form.is_enabled" />
            <span class="form-tip">停用后公告不会显示</span>
          </el-form-item>
        </el-col>
      </el-row>
    </el-form>

    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="handleSubmit">
        {{ isEdit ? '保存修改' : '创建公告' }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch, computed } from 'vue'
import { api } from '@/api'
import type { Announcement, AnnouncementCreate, AnnouncementUpdate } from '@/types'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'

const props = defineProps<{
  modelValue: boolean
  announcement?: Announcement | null
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  success: []
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const isEdit = computed(() => !!props.announcement)

const formRef = ref<FormInstance>()
const loading = ref(false)
const submitting = ref(false)

const positionOptions = ref<Array<{ value: string; label: string }>>([])
const typeOptions = ref<Array<{ value: string; label: string }>>([])
const targetUserOptions = ref<Array<{ value: string; label: string }>>([])

const form = reactive<AnnouncementCreate>({
  title: '',
  content: '',
  display_position: 'home',
  display_type: 'banner',
  start_time: '',
  end_time: '',
  is_pinned: false,
  priority: 0,
  target_user_type: 'all',
  is_enabled: true
})

const rules: FormRules = {
  title: [{ required: true, message: '请输入公告标题', trigger: 'blur' }],
  content: [{ required: true, message: '请输入公告内容', trigger: 'blur' }],
  display_position: [{ required: true, message: '请选择展示位置', trigger: 'change' }],
  display_type: [{ required: true, message: '请选择展示类型', trigger: 'change' }],
  start_time: [{ required: true, message: '请选择开始时间', trigger: 'change' }],
  end_time: [
    { required: true, message: '请选择结束时间', trigger: 'change' },
    {
      validator: (_rule, value, callback) => {
        if (value && form.start_time && new Date(value) <= new Date(form.start_time)) {
          callback(new Error('结束时间必须晚于开始时间'))
        } else {
          callback()
        }
      },
      trigger: 'change'
    }
  ],
  target_user_type: [{ required: true, message: '请选择目标用户', trigger: 'change' }],
  priority: [{ required: true, message: '请输入优先级', trigger: 'blur' }]
}

async function loadOptions() {
  try {
    const [positions, types, targets] = await Promise.all([
      api.getAnnouncementPositions(),
      api.getAnnouncementTypes(),
      api.getAnnouncementTargetUserTypes()
    ])
    positionOptions.value = positions
    typeOptions.value = types
    targetUserOptions.value = targets
  } catch (error) {
    console.error('加载选项失败:', error)
  }
}

function resetForm() {
  Object.assign(form, {
    title: '',
    content: '',
    display_position: 'home',
    display_type: 'banner',
    start_time: '',
    end_time: '',
    is_pinned: false,
    priority: 0,
    target_user_type: 'all',
    is_enabled: true
  })
  formRef.value?.resetFields()
}

function fillForm(announcement: Announcement) {
  Object.assign(form, {
    title: announcement.title,
    content: announcement.content,
    display_position: announcement.display_position,
    display_type: announcement.display_type,
    start_time: announcement.start_time,
    end_time: announcement.end_time,
    is_pinned: announcement.is_pinned,
    priority: announcement.priority,
    target_user_type: announcement.target_user_type,
    is_enabled: announcement.is_enabled
  })
}

async function handleSubmit() {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
  } catch {
    return
  }

  submitting.value = true
  try {
    if (isEdit.value && props.announcement) {
      const updateData: AnnouncementUpdate = { ...form }
      await api.updateAnnouncement(props.announcement.id, updateData)
      ElMessage.success('公告更新成功')
    } else {
      await api.createAnnouncement(form)
      ElMessage.success('公告创建成功')
    }
    emit('success')
    visible.value = false
  } catch (error) {
    console.error('提交失败:', error)
  } finally {
    submitting.value = false
  }
}

watch(visible, (val) => {
  if (val) {
    loadOptions()
    if (isEdit.value && props.announcement) {
      fillForm(props.announcement)
    } else {
      resetForm()
      const now = new Date()
      const tomorrow = new Date(now.getTime() + 24 * 60 * 60 * 1000)
      form.start_time = now.toISOString().slice(0, 19)
      form.end_time = tomorrow.toISOString().slice(0, 19)
    }
  }
})
</script>

<style scoped>
.form-tip {
  margin-left: 8px;
  font-size: 12px;
  color: var(--text-secondary);
}
</style>
