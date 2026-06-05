<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-header">
        <h1 class="text-gradient">登录</h1>
        <p>欢迎回来，请登录您的账户</p>
      </div>
      
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
        size="large"
        @submit.prevent="handleSubmit"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="form.username"
            placeholder="请输入用户名"
            prefix-icon="User"
          />
        </el-form-item>
        
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            prefix-icon="Lock"
            show-password
          />
        </el-form-item>
        
        <el-form-item>
          <el-button
            type="primary"
            native-type="submit"
            :loading="loading"
            class="submit-btn"
          >
            登录
          </el-button>
        </el-form-item>
      </el-form>
      
      <div class="login-footer">
        <span>还没有账户？</span>
        <router-link to="/register">立即注册</router-link>
      </div>
      
      <div class="demo-account">
        <el-divider>演示账号</el-divider>
        <div class="demo-list">
          <div class="demo-item" @click="fillDemo('admin', '123456')">
            <el-tag type="danger">管理员</el-tag>
            <span>admin / 123456</span>
          </div>
          <div class="demo-item" @click="fillDemo('user', '123456')">
            <el-tag>普通用户</el-tag>
            <span>user / 123456</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const formRef = ref<FormInstance>()
const loading = ref(false)

const form = reactive({
  username: '',
  password: ''
})

const rules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' }
  ]
}

async function handleSubmit() {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    loading.value = true
    try {
      await userStore.login(form.username, form.password)
      ElMessage.success('登录成功')
      
      const redirect = route.query.redirect as string
      router.push(redirect || '/')
    } catch (error) {
      // 错误已在 API 拦截器中处理
    } finally {
      loading.value = false
    }
  })
}

function fillDemo(username: string, password: string) {
  form.username = username
  form.password = password
}
</script>

<style scoped>
.login-page {
  min-height: calc(100vh - 64px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
}

.login-card {
  width: 100%;
  max-width: 420px;
  padding: 40px;
  background: var(--bg-secondary);
  border-radius: 20px;
  box-shadow: var(--shadow-lg);
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.login-header h1 {
  font-size: 32px;
  font-weight: 700;
  margin-bottom: 8px;
}

.login-header p {
  color: var(--text-secondary);
  font-size: 14px;
}

.submit-btn {
  width: 100%;
}

.login-footer {
  text-align: center;
  margin-top: 24px;
  color: var(--text-secondary);
  font-size: 14px;
}

.login-footer a {
  color: var(--primary-color);
  font-weight: 500;
  text-decoration: none;
  margin-left: 4px;
}

.login-footer a:hover {
  text-decoration: underline;
}

.demo-account {
  margin-top: 24px;
}

.demo-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.demo-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: #f8fafc;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.demo-item:hover {
  background: #f1f5f9;
}

.demo-item span {
  font-size: 13px;
  color: var(--text-secondary);
}
</style>
