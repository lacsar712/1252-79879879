<template>
  <div class="main-layout">
    <!-- 顶部导航栏 -->
    <header class="header glass-effect">
      <div class="header-content">
        <div class="logo" @click="router.push('/')">
          <el-icon :size="28" color="#6366f1"><Reading /></el-icon>
          <span class="logo-text text-gradient">现代化在线书店</span>
        </div>
        
        <nav class="nav-menu">
          <router-link to="/" class="nav-link" exact-active-class="active">
            <el-icon><HomeFilled /></el-icon>
            <span>首页</span>
          </router-link>
          <router-link to="/books" class="nav-link" active-class="active">
            <el-icon><Collection /></el-icon>
            <span>图书列表</span>
          </router-link>
          <router-link to="/promotions" class="nav-link" active-class="active">
            <el-icon><Present /></el-icon>
            <span>活动专题</span>
          </router-link>
          <router-link v-if="userStore.isLoggedIn" to="/feedback/submit" class="nav-link" active-class="active">
            <el-icon><Service /></el-icon>
            <span>客服反馈</span>
          </router-link>
          <router-link v-if="userStore.isAdmin" to="/admin" class="nav-link" active-class="active">
            <el-icon><Setting /></el-icon>
            <span>后台管理</span>
          </router-link>
        </nav>
        
        <div class="header-actions">
          <template v-if="userStore.isLoggedIn">
            <el-dropdown trigger="click">
              <div class="user-info">
                <el-avatar :size="36" class="user-avatar">
                  {{ userStore.user?.username?.charAt(0).toUpperCase() }}
                </el-avatar>
                <span class="username">{{ userStore.user?.username }}</span>
                <el-icon><ArrowDown /></el-icon>
              </div>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item>
                    <el-icon><User /></el-icon>
                    {{ userStore.isAdmin ? '管理员' : '普通用户' }}
                  </el-dropdown-item>
                  <el-dropdown-item v-if="userStore.isAdmin" @click="router.push('/api-keys')">
                    <el-icon><Key /></el-icon>
                    API Key 管理
                  </el-dropdown-item>
                  <el-dropdown-item @click="router.push('/addresses')">
                    <el-icon><Location /></el-icon>
                    收货地址
                  </el-dropdown-item>
                  <el-dropdown-item @click="router.push('/feedbacks')">
                    <el-icon><ChatDotRound /></el-icon>
                    我的反馈
                  </el-dropdown-item>
                  <el-dropdown-item @click="router.push('/feedback/submit')">
                    <el-icon><Service /></el-icon>
                    提交反馈
                  </el-dropdown-item>
                  <el-dropdown-item divided @click="handleLogout">
                    <el-icon><SwitchButton /></el-icon>
                    退出登录
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
          <template v-else>
            <el-button type="primary" @click="router.push('/login')">登录</el-button>
            <el-button @click="router.push('/register')">注册</el-button>
          </template>
        </div>
      </div>
    </header>
    
    <!-- 主内容区 -->
    <main class="main-content">
      <router-view v-slot="{ Component }">
        <transition name="page-fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
    
    <!-- 对比栏 -->
    <CompareBar />
    
    <!-- 底部 -->
    <footer class="footer" :class="{ 'with-compare-bar': compareStore.hasBooks }">
      <p>© 2024 现代化在线书店 · 基于 Vue 3 + FastAPI 构建</p>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useCompareStore } from '@/stores/compare'
import { ElMessage } from 'element-plus'
import CompareBar from '@/components/CompareBar.vue'
import {
  Reading,
  HomeFilled,
  Collection,
  Present,
  Setting,
  ArrowDown,
  User,
  SwitchButton,
  Service,
  ChatDotRound,
  Location,
  Key
} from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useUserStore()
const compareStore = useCompareStore()

function handleLogout() {
  userStore.logout()
  ElMessage.success('已退出登录')
  router.push('/')
}
</script>

<style scoped>
.main-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  height: 64px;
  border-bottom: 1px solid var(--border-color);
}

.header-content {
  max-width: 1400px;
  margin: 0 auto;
  height: 100%;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  transition: opacity 0.2s;
}

.logo:hover {
  opacity: 0.8;
}

.logo-text {
  font-size: 20px;
  font-weight: 700;
}

.nav-menu {
  display: flex;
  gap: 8px;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 8px;
  color: var(--text-secondary);
  text-decoration: none;
  font-weight: 500;
  transition: all 0.2s;
}

.nav-link:hover {
  color: var(--primary-color);
  background: rgba(99, 102, 241, 0.1);
}

.nav-link.active {
  color: var(--primary-color);
  background: rgba(99, 102, 241, 0.15);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 12px 4px 4px;
  border-radius: 24px;
  cursor: pointer;
  transition: background 0.2s;
}

.user-info:hover {
  background: rgba(0, 0, 0, 0.05);
}

.user-avatar {
  background: var(--gradient-primary);
  color: #fff;
  font-weight: 600;
}

.username {
  font-weight: 500;
  color: var(--text-primary);
}

.main-content {
  flex: 1;
  margin-top: 64px;
  padding: 24px;
  max-width: 1400px;
  width: 100%;
  margin-left: auto;
  margin-right: auto;
}

.footer {
  padding: 24px;
  text-align: center;
  color: var(--text-secondary);
  font-size: 14px;
  border-top: 1px solid var(--border-color);
  transition: padding-bottom 0.3s ease;
}

.footer.with-compare-bar {
  padding-bottom: 180px;
}
</style>
