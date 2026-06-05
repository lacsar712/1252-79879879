import axios from 'axios'
import type { 
    Book, BookListResponse, BookCreate, LoginResponse, User, 
    Promotion, PromotionListResponse, PromotionCreate, PromotionUpdate,
    Feedback, FeedbackListResponse, FeedbackCreate, FeedbackReplySubmit,
    FeedbackTypeOption, FeedbackStatusOption, FeedbackUploadResponse,
    FeedbackReply,
    BookChapter, BookChapterPublic, BookChapterCreate, BookChapterUpdate,
    BookChapterListResponse, BookChapterPublicListResponse,
    StockTaking, StockTakingListResponse, StockTakingCreate, StockTakingUpdate,
    StockTakingBatchEntryRequest, StockTakingScopeOption,
    Supplier, SupplierListResponse, SupplierCreate, SupplierUpdate, SupplierOption,
    PurchaseOrder, PurchaseOrderListResponse, PurchaseOrderCreate, PurchaseOrderUpdate,
    PurchaseOrderStatusOption, StockChange,
    UserAddress, UserAddressListResponse, UserAddressCreate, UserAddressUpdate,
    UserAddressDeleteResponse, UserAddressReassignDefaultRequest, AddressTagOption
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
        instance.get(`/chapters/preview/${chapterId}`),

    // 库存盘点相关
    getStockTakings: (params?: {
        page?: number
        page_size?: number
        status?: string
        keyword?: string
    }): Promise<StockTakingListResponse> =>
        instance.get('/stock-takings', { params }),

    getStockTakingHistory: (params?: {
        page?: number
        page_size?: number
        keyword?: string
        start_date?: string
        end_date?: string
    }): Promise<StockTakingListResponse> =>
        instance.get('/stock-takings/history', { params }),

    getStockTaking: (id: number): Promise<StockTaking> =>
        instance.get(`/stock-takings/${id}`),

    createStockTaking: (data: StockTakingCreate): Promise<StockTaking> =>
        instance.post('/stock-takings', data),

    updateStockTaking: (id: number, data: StockTakingUpdate): Promise<StockTaking> =>
        instance.put(`/stock-takings/${id}`, data),

    startStockTaking: (id: number): Promise<StockTaking> =>
        instance.post(`/stock-takings/${id}/start`),

    batchEntryStock: (id: number, data: StockTakingBatchEntryRequest): Promise<StockTaking> =>
        instance.post(`/stock-takings/${id}/entry`, data),

    confirmStockTaking: (id: number): Promise<StockTaking> =>
        instance.post(`/stock-takings/${id}/confirm`),

    cancelStockTaking: (id: number): Promise<StockTaking> =>
        instance.post(`/stock-takings/${id}/cancel`),

    getStockTakingScopes: (): Promise<StockTakingScopeOption[]> =>
        instance.get('/stock-takings/scopes/list'),

    // 供应商相关
    getSuppliers: (params?: {
        page?: number
        page_size?: number
        keyword?: string
    }): Promise<SupplierListResponse> =>
        instance.get('/purchase-orders/suppliers', { params }),

    getAllSuppliers: (): Promise<SupplierOption[]> =>
        instance.get('/purchase-orders/suppliers/all'),

    getSupplier: (id: number): Promise<Supplier> =>
        instance.get(`/purchase-orders/suppliers/${id}`),

    createSupplier: (supplier: SupplierCreate): Promise<Supplier> =>
        instance.post('/purchase-orders/suppliers', supplier),

    updateSupplier: (id: number, supplier: SupplierUpdate): Promise<Supplier> =>
        instance.put(`/purchase-orders/suppliers/${id}`, supplier),

    deleteSupplier: (id: number): Promise<void> =>
        instance.delete(`/purchase-orders/suppliers/${id}`),

    // 采购单相关
    getPurchaseOrders: (params?: {
        page?: number
        page_size?: number
        status?: string
        supplier_id?: number
        keyword?: string
        start_date?: string
        end_date?: string
    }): Promise<PurchaseOrderListResponse> =>
        instance.get('/purchase-orders', { params }),

    getPurchaseOrder: (id: number): Promise<PurchaseOrder> =>
        instance.get(`/purchase-orders/${id}`),

    createPurchaseOrder: (order: PurchaseOrderCreate): Promise<PurchaseOrder> =>
        instance.post('/purchase-orders', order),

    updatePurchaseOrder: (id: number, order: PurchaseOrderUpdate): Promise<PurchaseOrder> =>
        instance.put(`/purchase-orders/${id}`, order),

    submitPurchaseOrder: (id: number): Promise<PurchaseOrder> =>
        instance.post(`/purchase-orders/${id}/submit`),

    confirmPurchaseOrder: (id: number): Promise<PurchaseOrder> =>
        instance.post(`/purchase-orders/${id}/confirm`),

    cancelPurchaseOrder: (id: number): Promise<PurchaseOrder> =>
        instance.post(`/purchase-orders/${id}/cancel`),

    getPurchaseOrderStatuses: (): Promise<PurchaseOrderStatusOption[]> =>
        instance.get('/purchase-orders/statuses/list'),

    getPurchaseOrderStockChanges: (id: number): Promise<StockChange[]> =>
        instance.get(`/purchase-orders/${id}/stock-changes`),

    getAddresses: (): Promise<UserAddressListResponse> =>
        instance.get('/addresses'),

    getDefaultAddress: (): Promise<UserAddress> =>
        instance.get('/addresses/default'),

    getAddress: (id: number): Promise<UserAddress> =>
        instance.get(`/addresses/${id}`),

    createAddress: (address: UserAddressCreate): Promise<UserAddress> =>
        instance.post('/addresses', address),

    updateAddress: (id: number, address: UserAddressUpdate): Promise<UserAddress> =>
        instance.put(`/addresses/${id}`, address),

    setDefaultAddress: (id: number): Promise<UserAddress> =>
        instance.patch(`/addresses/${id}/set-default`),

    deleteAddress: (id: number): Promise<UserAddressDeleteResponse> =>
        instance.delete(`/addresses/${id}`),

    reassignDefaultAddress: (data: UserAddressReassignDefaultRequest): Promise<UserAddress> =>
        instance.post('/addresses/reassign-default', data),

    getAddressTags: (): Promise<AddressTagOption[]> =>
        Promise.resolve([
            { value: '家', label: '家', type: 'success' },
            { value: '公司', label: '公司', type: 'primary' },
            { value: '学校', label: '学校', type: 'warning' },
            { value: '其他', label: '其他', type: 'info' }
        ])
}
