import axios from 'axios'
import type { Book, BookListResponse, BookCreate, LoginResponse, User, Promotion, PromotionListResponse, PromotionCreate, PromotionUpdate } from '@/types'
import { ElMessage } from 'element-plus'

const instance = axios.create({
    baseURL: '/api',
    timeout: 10000,
    headers: {
        'Content-Type': 'application/json'
    }
})

// 请求拦截器
instance.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('token')
        if (token) {
            config.headers.Authorization = `Bearer ${token}`
        }
        return config
    },
    (error) => {
        return Promise.reject(error)
    }
)

// 响应拦截器
instance.interceptors.response.use(
    (response) => response.data,
    (error) => {
        const message = error.response?.data?.detail || '请求失败，请稍后重试'
        ElMessage.error(message)
        return Promise.reject(error)
    }
)

export const api = {
    // 认证相关
    login: (username: string, password: string): Promise<LoginResponse> =>
        instance.post('/auth/login', { username, password }),

    register: (username: string, email: string, password: string): Promise<User> =>
        instance.post('/auth/register', { username, email, password }),

    getCurrentUser: (): Promise<User> =>
        instance.get('/auth/me'),

    // 图书相关
    getBooks: (params?: { page?: number; page_size?: number; search?: string; category?: string }): Promise<BookListResponse> =>
        instance.get('/books', { params }),

    getBook: (id: number): Promise<Book> =>
        instance.get(`/books/${id}`),

    createBook: (book: BookCreate): Promise<Book> =>
        instance.post('/books', book),

    updateBook: (id: number, book: Partial<BookCreate>): Promise<Book> =>
        instance.put(`/books/${id}`, book),

    deleteBook: (id: number): Promise<void> =>
        instance.delete(`/books/${id}`),

    getCategories: (): Promise<string[]> =>
        instance.get('/books/categories/list'),

    getPromotions: (params?: { page?: number; page_size?: number; status?: string; is_displayed?: boolean }): Promise<PromotionListResponse> =>
        instance.get('/promotions', { params }),

    getPromotion: (id: number): Promise<Promotion> =>
        instance.get(`/promotions/${id}`),

    createPromotion: (promotion: PromotionCreate): Promise<Promotion> =>
        instance.post('/promotions', promotion),

    updatePromotion: (id: number, promotion: PromotionUpdate): Promise<Promotion> =>
        instance.put(`/promotions/${id}`, promotion),

    deletePromotion: (id: number): Promise<void> =>
        instance.delete(`/promotions/${id}`),

    deductPromotionStock: (promotionId: number, promotionBookId: number, quantity: number): Promise<Promotion> =>
        instance.post(`/promotions/${promotionId}/deduct-stock`, { promotion_book_id: promotionBookId, quantity })
}
