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
                path: 'books/:bookId/reader/:chapterId?',
                name: 'BookReader',
                component: () => import('@/views/BookReader.vue'),
                meta: { title: '在线阅读' }
            },
            {
                path: 'promotions',
                name: 'Promotions',
                component: () => import('@/views/Promotions.vue'),
                meta: { title: '活动专题' }
            },
            {
                path: 'promotions/:id',
                name: 'PromotionDetail',
                component: () => import('@/views/PromotionDetail.vue'),
                meta: { title: '活动详情' }
            },
            {
                path: 'admin',
                name: 'Admin',
                component: () => import('@/views/Admin.vue'),
                meta: { title: '后台管理', requiresAdmin: true }
            },
            {
                path: 'feedback/submit',
                name: 'FeedbackSubmit',
                component: () => import('@/views/FeedbackSubmit.vue'),
                meta: { title: '提交反馈', requiresAuth: true }
            },
            {
                path: 'feedbacks',
                name: 'FeedbackList',
                component: () => import('@/views/FeedbackList.vue'),
                meta: { title: '我的反馈', requiresAuth: true }
            },
            {
                path: 'stock-taking/:id',
                name: 'StockTakingDetail',
                component: () => import('@/views/StockTakingDetail.vue'),
                meta: { title: '盘点详情', requiresAdmin: true }
            },
            {
                path: 'stock-taking-history',
                name: 'StockTakingHistory',
                component: () => import('@/views/StockTakingHistory.vue'),
                meta: { title: '盘点历史记录', requiresAdmin: true }
            },
            {
                path: 'purchase-order/:id',
                name: 'PurchaseOrderDetail',
                component: () => import('@/views/PurchaseOrderDetail.vue'),
                meta: { title: '采购单详情', requiresAdmin: true }
            },
            {
                path: 'addresses',
                name: 'AddressList',
                component: () => import('@/views/AddressList.vue'),
                meta: { title: '收货地址管理', requiresAuth: true }
            },
            {
                path: 'order-confirm',
                name: 'OrderConfirm',
                component: () => import('@/views/OrderConfirm.vue'),
                meta: { title: '确认订单', requiresAuth: true }
            },
            {
                path: 'books/compare',
                name: 'BookCompare',
                component: () => import('@/views/BookCompare.vue'),
                meta: { title: '图书对比' }
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
router.beforeEach((to, _from, next) => {
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
    }
    // 需要登录的页面
    else if (to.meta.requiresAuth) {
        if (!userStore.isLoggedIn) {
            next({ name: 'Login', query: { redirect: to.fullPath } })
        } else {
            next()
        }
    } else {
        next()
    }
})

export default router
