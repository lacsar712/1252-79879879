import axios from 'axios'
import type { 
    Book, BookListResponse, BookCreate, LoginResponse, User, 
    Promotion, PromotionListResponse, PromotionCreate, PromotionUpdate,
    Feedback, FeedbackListResponse, FeedbackCreate, FeedbackReplySubmit,
    FeedbackTypeOption, FeedbackStatusOption, FeedbackUploadResponse,
    FeedbackReply,
    BookChapter, BookChapterPublic, BookChapterCreate, BookChapterUpdate,
    BookChapterListResponse, BookChapterPublicListResponse
} from '@/types'
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
        instance.post(`/promotions/${promotionId}/deduct-stock`, { promotion_book_id: promotionBookId, quantity }),

    // 反馈相关
    uploadFeedbackAttachment: (file: File): Promise<FeedbackUploadResponse> => {
        const formData = new FormData()
        formData.append('file', file)
        return instance.post('/feedbacks/upload', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        })
    },

    createFeedback: (feedback: FeedbackCreate): Promise<Feedback> =>
        instance.post('/feedbacks', feedback),

    getMyFeedbacks: (params?: {
        page?: number
        page_size?: number
        status?: string
        type?: string
        start_date?: string
        end_date?: string
    }): Promise<FeedbackListResponse> =>
        instance.get('/feedbacks/my', { params }),

    getFeedback: (id: number): Promise<Feedback> =>
        instance.get(`/feedbacks/${id}`),

    replyFeedback: (id: number, content: string): Promise<FeedbackReply> =>
        instance.post(`/feedbacks/${id}/reply`, { content }),

    getAllFeedbacks: (params?: {
        page?: number
        page_size?: number
        status?: string
        type?: string
        start_date?: string
        end_date?: string
        keyword?: string
    }): Promise<FeedbackListResponse> =>
        instance.get('/feedbacks', { params }),

    adminReplyFeedback: (id: number, reply: FeedbackReplySubmit): Promise<FeedbackReply> =>
        instance.post(`/feedbacks/${id}/admin-reply`, reply),

    updateFeedbackStatus: (id: number, status: string): Promise<Feedback> =>
        instance.put(`/feedbacks/${id}/status`, { status }),

    getFeedbackTypes: (): Promise<FeedbackTypeOption[]> =>
        instance.get('/feedbacks/types/list'),

    getFeedbackStatuses: (): Promise<FeedbackStatusOption[]> =>
        instance.get('/feedbacks/statuses/list'),

    // 试读章节相关 - 公开接口
    getPublicChapters: (bookId: number): Promise<BookChapterPublicListResponse> =>
        instance.get(`/chapters/public/${bookId}`),

    getPublicChapter: (bookId: number, chapterId: number): Promise<BookChapterPublic> =>
        instance.get(`/chapters/public/${bookId}/${chapterId}`),

    // 试读章节相关 - 管理接口
    getAdminChapters: (bookId: number): Promise<BookChapterListResponse> =>
        instance.get(`/chapters/admin/${bookId}`),

    getAdminChapter: (bookId: number, chapterId: number): Promise<BookChapter> =>
        instance.get(`/chapters/admin/${bookId}/${chapterId}`),

    createChapter: (chapter: BookChapterCreate): Promise<BookChapter> =>
        instance.post('/chapters', chapter),

    updateChapter: (chapterId: number, chapter: BookChapterUpdate): Promise<BookChapter> =>
        instance.put(`/chapters/${chapterId}`, chapter),

    toggleChapterPublic: (chapterId: number): Promise<BookChapter> =>
        instance.patch(`/chapters/${chapterId}/toggle-public`),

    updateChapterSort: (chapterId: number, sortOrder: number): Promise<BookChapter> =>
        instance.patch(`/chapters/${chapterId}/sort`, null, { params: { sort_order: sortOrder } }),

    deleteChapter: (chapterId: number): Promise<void> =>
        instance.delete(`/chapters/${chapterId}`),

    previewChapter: (chapterId: number): Promise<BookChapter> =>
        instance.get(`/chapters/preview/${chapterId}`)
}
