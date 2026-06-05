import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes: RouteRecordRaw[] = [
    {
        path: '/',
        component: () => import('@/layouts/MainLayout.vue'),
        children: [
            {
                path: '',
                name: 'Home',
                component: () => import('@/views/Home.vue'),
                meta: { title: '首页' }
            },
            {
                path: 'books',
                name: 'Books',
                component: () => import('@/views/Books.vue'),
                meta: { title: '图书列表' }
            },
            {
                path: 'books/:id',
                name: 'BookDetail',
                component: () => import('@/views/BookDetail.vue'),
                meta: { title: '图书详情' }
            },
            {
                path: 'admin',
                name: 'Admin',
                component: () => import('@/views/Admin.vue'),
                meta: { title: '后台管理', requiresAdmin: true }
            }
        ]
    },
    {
        path: '/login',
        name: 'Login',
        component: () => import('@/views/Login.vue'),
        meta: { title: '登录' }
    },
    {
        path: '/register',
        name: 'Register',
        component: () => import('@/views/Register.vue'),
        meta: { title: '注册' }
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
    // 更新页面标题
    document.title = `${to.meta.title || '在线书店'} - 现代化在线书店`

    const userStore = useUserStore()

    // 需要管理员权限的页面
    if (to.meta.requiresAdmin) {
        if (!userStore.isLoggedIn) {
            next({ name: 'Login', query: { redirect: to.fullPath } })
        } else if (!userStore.isAdmin) {
            next({ name: 'Home' })
        } else {
            next()
        }
    } else {
        next()
    }
})

export default router
