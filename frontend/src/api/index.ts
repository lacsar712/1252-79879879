import { get, post, put, del, patch } from '@/utils/request'
import { buildPaginationParams } from '@/utils/pagination'
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
    UserAddressDeleteResponse, UserAddressReassignDefaultRequest, AddressTagOption,
    BookCompareResponse,
    APIKey, APIKeyListResponse, APIKeyCreate, APIKeyUpdate,
    APIKeyCreateResponse, APIKeyRotateResponse,
    APIKeyCallLogListResponse,
    APIKeyAccessScopeOption, APIKeyRatePeriodOption, APIKeyStatusOption,
    Announcement, AnnouncementListResponse, AnnouncementCreate, AnnouncementUpdate,
    AnnouncementDisplayPositionOption, AnnouncementDisplayTypeOption,
    AnnouncementTargetUserTypeOption, AnnouncementStatusOption,
    BookImportUploadResponse, BookImportPreviewResponse, BookImportPreviewRequest,
    BookImportConfirmRequest, BookImportProgressResponse,
    BookImportRecordListResponse, BookImportRecordDetail,
    BookImportFieldOption, BookImportStatusOption
} from '@/types'

export const api = {
    login: (username: string, password: string): Promise<LoginResponse> =>
        post('/auth/login', { username, password }),

    register: (username: string, email: string, password: string): Promise<User> =>
        post('/auth/register', { username, email, password }),

    getCurrentUser: (): Promise<User> =>
        get('/auth/me'),

    getBooks: (params?: { page?: number; page_size?: number; search?: string; category?: string }): Promise<BookListResponse> =>
        get('/books', {
            params: buildPaginationParams(
                params?.page ?? 1,
                params?.page_size ?? 10,
                {
                    search: params?.search,
                    category: params?.category
                }
            )
        }),

    getBook: (id: number): Promise<Book> =>
        get(`/books/${id}`),

    createBook: (book: BookCreate): Promise<Book> =>
        post('/books', book),

    updateBook: (id: number, book: Partial<BookCreate>): Promise<Book> =>
        put(`/books/${id}`, book),

    deleteBook: (id: number): Promise<void> =>
        del(`/books/${id}`),

    getCategories: (): Promise<string[]> =>
        get('/books/categories/list'),

    getPromotions: (params?: { page?: number; page_size?: number; status?: string; is_displayed?: boolean }): Promise<PromotionListResponse> =>
        get('/promotions', {
            params: buildPaginationParams(
                params?.page ?? 1,
                params?.page_size ?? 10,
                {
                    status: params?.status,
                    is_displayed: params?.is_displayed
                }
            )
        }),

    getPromotion: (id: number): Promise<Promotion> =>
        get(`/promotions/${id}`),

    createPromotion: (promotion: PromotionCreate): Promise<Promotion> =>
        post('/promotions', promotion),

    updatePromotion: (id: number, promotion: PromotionUpdate): Promise<Promotion> =>
        put(`/promotions/${id}`, promotion),

    deletePromotion: (id: number): Promise<void> =>
        del(`/promotions/${id}`),

    deductPromotionStock: (promotionId: number, promotionBookId: number, quantity: number): Promise<Promotion> =>
        post(`/promotions/${promotionId}/deduct-stock`, { promotion_book_id: promotionBookId, quantity }),

    uploadFeedbackAttachment: (file: File): Promise<FeedbackUploadResponse> => {
        const formData = new FormData()
        formData.append('file', file)
        return post('/feedbacks/upload', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        })
    },

    createFeedback: (feedback: FeedbackCreate): Promise<Feedback> =>
        post('/feedbacks', feedback),

    getMyFeedbacks: (params?: {
        page?: number
        page_size?: number
        status?: string
        type?: string
        start_date?: string
        end_date?: string
    }): Promise<FeedbackListResponse> =>
        get('/feedbacks/my', {
            params: buildPaginationParams(
                params?.page ?? 1,
                params?.page_size ?? 10,
                {
                    status: params?.status,
                    type: params?.type,
                    start_date: params?.start_date,
                    end_date: params?.end_date
                }
            )
        }),

    getFeedback: (id: number): Promise<Feedback> =>
        get(`/feedbacks/${id}`),

    replyFeedback: (id: number, content: string): Promise<FeedbackReply> =>
        post(`/feedbacks/${id}/reply`, { content }),

    getAllFeedbacks: (params?: {
        page?: number
        page_size?: number
        status?: string
        type?: string
        start_date?: string
        end_date?: string
        keyword?: string
    }): Promise<FeedbackListResponse> =>
        get('/feedbacks', {
            params: buildPaginationParams(
                params?.page ?? 1,
                params?.page_size ?? 10,
                {
                    status: params?.status,
                    type: params?.type,
                    start_date: params?.start_date,
                    end_date: params?.end_date,
                    keyword: params?.keyword
                }
            )
        }),

    adminReplyFeedback: (id: number, reply: FeedbackReplySubmit): Promise<FeedbackReply> =>
        post(`/feedbacks/${id}/admin-reply`, reply),

    updateFeedbackStatus: (id: number, status: string): Promise<Feedback> =>
        put(`/feedbacks/${id}/status`, { status }),

    getFeedbackTypes: (): Promise<FeedbackTypeOption[]> =>
        get('/feedbacks/types/list'),

    getFeedbackStatuses: (): Promise<FeedbackStatusOption[]> =>
        get('/feedbacks/statuses/list'),

    getPublicChapters: (bookId: number): Promise<BookChapterPublicListResponse> =>
        get(`/chapters/public/${bookId}`),

    getPublicChapter: (bookId: number, chapterId: number): Promise<BookChapterPublic> =>
        get(`/chapters/public/${bookId}/${chapterId}`),

    getAdminChapters: (bookId: number): Promise<BookChapterListResponse> =>
        get(`/chapters/admin/${bookId}`),

    getAdminChapter: (bookId: number, chapterId: number): Promise<BookChapter> =>
        get(`/chapters/admin/${bookId}/${chapterId}`),

    createChapter: (chapter: BookChapterCreate): Promise<BookChapter> =>
        post('/chapters', chapter),

    updateChapter: (chapterId: number, chapter: BookChapterUpdate): Promise<BookChapter> =>
        put(`/chapters/${chapterId}`, chapter),

    toggleChapterPublic: (chapterId: number): Promise<BookChapter> =>
        patch(`/chapters/${chapterId}/toggle-public`),

    updateChapterSort: (chapterId: number, sortOrder: number): Promise<BookChapter> =>
        patch(`/chapters/${chapterId}/sort`, null, { params: { sort_order: sortOrder } }),

    deleteChapter: (chapterId: number): Promise<void> =>
        del(`/chapters/${chapterId}`),

    previewChapter: (chapterId: number): Promise<BookChapter> =>
        get(`/chapters/preview/${chapterId}`),

    getStockTakings: (params?: {
        page?: number
        page_size?: number
        status?: string
        keyword?: string
    }): Promise<StockTakingListResponse> =>
        get('/stock-takings', {
            params: buildPaginationParams(
                params?.page ?? 1,
                params?.page_size ?? 10,
                {
                    status: params?.status,
                    keyword: params?.keyword
                }
            )
        }),

    getStockTakingHistory: (params?: {
        page?: number
        page_size?: number
        keyword?: string
        start_date?: string
        end_date?: string
    }): Promise<StockTakingListResponse> =>
        get('/stock-takings/history', {
            params: buildPaginationParams(
                params?.page ?? 1,
                params?.page_size ?? 10,
                {
                    keyword: params?.keyword,
                    start_date: params?.start_date,
                    end_date: params?.end_date
                }
            )
        }),

    getStockTaking: (id: number): Promise<StockTaking> =>
        get(`/stock-takings/${id}`),

    createStockTaking: (data: StockTakingCreate): Promise<StockTaking> =>
        post('/stock-takings', data),

    updateStockTaking: (id: number, data: StockTakingUpdate): Promise<StockTaking> =>
        put(`/stock-takings/${id}`, data),

    startStockTaking: (id: number): Promise<StockTaking> =>
        post(`/stock-takings/${id}/start`),

    batchEntryStock: (id: number, data: StockTakingBatchEntryRequest): Promise<StockTaking> =>
        post(`/stock-takings/${id}/entry`, data),

    confirmStockTaking: (id: number): Promise<StockTaking> =>
        post(`/stock-takings/${id}/confirm`),

    cancelStockTaking: (id: number): Promise<StockTaking> =>
        post(`/stock-takings/${id}/cancel`),

    getStockTakingScopes: (): Promise<StockTakingScopeOption[]> =>
        get('/stock-takings/scopes/list'),

    getSuppliers: (params?: {
        page?: number
        page_size?: number
        keyword?: string
    }): Promise<SupplierListResponse> =>
        get('/purchase-orders/suppliers', {
            params: buildPaginationParams(
                params?.page ?? 1,
                params?.page_size ?? 10,
                {
                    keyword: params?.keyword
                }
            )
        }),

    getAllSuppliers: (): Promise<SupplierOption[]> =>
        get('/purchase-orders/suppliers/all'),

    getSupplier: (id: number): Promise<Supplier> =>
        get(`/purchase-orders/suppliers/${id}`),

    createSupplier: (supplier: SupplierCreate): Promise<Supplier> =>
        post('/purchase-orders/suppliers', supplier),

    updateSupplier: (id: number, supplier: SupplierUpdate): Promise<Supplier> =>
        put(`/purchase-orders/suppliers/${id}`, supplier),

    deleteSupplier: (id: number): Promise<void> =>
        del(`/purchase-orders/suppliers/${id}`),

    getPurchaseOrders: (params?: {
        page?: number
        page_size?: number
        status?: string
        supplier_id?: number
        keyword?: string
        start_date?: string
        end_date?: string
    }): Promise<PurchaseOrderListResponse> =>
        get('/purchase-orders', {
            params: buildPaginationParams(
                params?.page ?? 1,
                params?.page_size ?? 10,
                {
                    status: params?.status,
                    supplier_id: params?.supplier_id,
                    keyword: params?.keyword,
                    start_date: params?.start_date,
                    end_date: params?.end_date
                }
            )
        }),

    getPurchaseOrder: (id: number): Promise<PurchaseOrder> =>
        get(`/purchase-orders/${id}`),

    createPurchaseOrder: (order: PurchaseOrderCreate): Promise<PurchaseOrder> =>
        post('/purchase-orders', order),

    updatePurchaseOrder: (id: number, order: PurchaseOrderUpdate): Promise<PurchaseOrder> =>
        put(`/purchase-orders/${id}`, order),

    submitPurchaseOrder: (id: number): Promise<PurchaseOrder> =>
        post(`/purchase-orders/${id}/submit`),

    confirmPurchaseOrder: (id: number): Promise<PurchaseOrder> =>
        post(`/purchase-orders/${id}/confirm`),

    cancelPurchaseOrder: (id: number): Promise<PurchaseOrder> =>
        post(`/purchase-orders/${id}/cancel`),

    getPurchaseOrderStatuses: (): Promise<PurchaseOrderStatusOption[]> =>
        get('/purchase-orders/statuses/list'),

    getPurchaseOrderStockChanges: (id: number): Promise<StockChange[]> =>
        get(`/purchase-orders/${id}/stock-changes`),

    getAddresses: (): Promise<UserAddressListResponse> =>
        get('/addresses'),

    getDefaultAddress: (): Promise<UserAddress> =>
        get('/addresses/default'),

    getAddress: (id: number): Promise<UserAddress> =>
        get(`/addresses/${id}`),

    createAddress: (address: UserAddressCreate): Promise<UserAddress> =>
        post('/addresses', address),

    updateAddress: (id: number, address: UserAddressUpdate): Promise<UserAddress> =>
        put(`/addresses/${id}`, address),

    setDefaultAddress: (id: number): Promise<UserAddress> =>
        patch(`/addresses/${id}/set-default`),

    deleteAddress: (id: number): Promise<UserAddressDeleteResponse> =>
        del(`/addresses/${id}`),

    reassignDefaultAddress: (data: UserAddressReassignDefaultRequest): Promise<UserAddress> =>
        post('/addresses/reassign-default', data),

    getAddressTags: (): Promise<AddressTagOption[]> =>
        Promise.resolve([
            { value: '家', label: '家', type: 'success' },
            { value: '公司', label: '公司', type: 'primary' },
            { value: '学校', label: '学校', type: 'warning' },
            { value: '其他', label: '其他', type: 'info' }
        ]),

    getBooksCompare: (bookIds: number[]): Promise<BookCompareResponse> =>
        post('/books/compare', { book_ids: bookIds }),

    saveCompareList: (bookIds: number[]): Promise<{ message: string }> =>
        post('/books/compare/save', { book_ids: bookIds }),

    getSavedCompareList: (): Promise<{ book_ids: number[] }> =>
        get('/books/compare/saved'),

    getAPIKeys: (params?: {
        page?: number
        page_size?: number
        search?: string
        is_enabled?: boolean
        risk_status?: string
    }): Promise<APIKeyListResponse> =>
        get('/api-keys', {
            params: buildPaginationParams(
                params?.page ?? 1,
                params?.page_size ?? 10,
                {
                    search: params?.search,
                    is_enabled: params?.is_enabled,
                    risk_status: params?.risk_status
                }
            )
        }),

    getAPIKey: (id: number): Promise<APIKey> =>
        get(`/api-keys/${id}`),

    createAPIKey: (data: APIKeyCreate): Promise<APIKeyCreateResponse> =>
        post('/api-keys', data),

    updateAPIKey: (id: number, data: APIKeyUpdate): Promise<APIKey> =>
        put(`/api-keys/${id}`, data),

    deleteAPIKey: (id: number): Promise<void> =>
        del(`/api-keys/${id}`),

    toggleAPIKey: (id: number): Promise<APIKey> =>
        post(`/api-keys/${id}/toggle`),

    rotateAPIKey: (id: number): Promise<APIKeyRotateResponse> =>
        post(`/api-keys/${id}/rotate`),

    getAPIKeyLogs: (id: number, params?: {
        page?: number
        page_size?: number
        status?: string
        start_date?: string
        end_date?: string
    }): Promise<APIKeyCallLogListResponse> =>
        get(`/api-keys/${id}/logs`, {
            params: buildPaginationParams(
                params?.page ?? 1,
                params?.page_size ?? 10,
                {
                    status: params?.status,
                    start_date: params?.start_date,
                    end_date: params?.end_date
                }
            )
        }),

    getAPIAccessScopes: (): Promise<APIKeyAccessScopeOption[]> =>
        get('/api-keys/scopes/list'),

    getAPIRatePeriods: (): Promise<APIKeyRatePeriodOption[]> =>
        get('/api-keys/rate-periods/list'),

    getAPIKeyStatuses: (): Promise<APIKeyStatusOption[]> =>
        get('/api-keys/statuses/list'),

    testOpenAPI: (apiKey: string, params?: {
        page?: number
        page_size?: number
        search?: string
        category?: string
    }): Promise<any> =>
        get('/open/books', {
            params: buildPaginationParams(
                params?.page ?? 1,
                params?.page_size ?? 10,
                {
                    search: params?.search,
                    category: params?.category
                }
            ),
            headers: { 'X-API-Key': apiKey }
        }),

    getDisplayAnnouncements: (position: string): Promise<Announcement[]> =>
        get('/announcements/display', { params: { position } }),

    closeAnnouncement: (id: number): Promise<void> =>
        post(`/announcements/${id}/close`),

    getAnnouncements: (params?: {
        page?: number
        page_size?: number
        status?: string
        position?: string
        keyword?: string
    }): Promise<AnnouncementListResponse> =>
        get('/announcements', {
            params: buildPaginationParams(
                params?.page ?? 1,
                params?.page_size ?? 10,
                {
                    status: params?.status,
                    position: params?.position,
                    keyword: params?.keyword
                }
            )
        }),

    getAnnouncement: (id: number): Promise<Announcement> =>
        get(`/announcements/${id}`),

    createAnnouncement: (data: AnnouncementCreate): Promise<Announcement> =>
        post('/announcements', data),

    updateAnnouncement: (id: number, data: AnnouncementUpdate): Promise<Announcement> =>
        put(`/announcements/${id}`, data),

    deleteAnnouncement: (id: number): Promise<void> =>
        del(`/announcements/${id}`),

    toggleAnnouncement: (id: number): Promise<Announcement> =>
        post(`/announcements/${id}/toggle`),

    getAnnouncementPositions: (): Promise<AnnouncementDisplayPositionOption[]> =>
        get('/announcements/positions/list'),

    getAnnouncementTypes: (): Promise<AnnouncementDisplayTypeOption[]> =>
        get('/announcements/types/list'),

    getAnnouncementTargetUserTypes: (): Promise<AnnouncementTargetUserTypeOption[]> =>
        get('/announcements/target-user-types/list'),

    getAnnouncementStatuses: (): Promise<AnnouncementStatusOption[]> =>
        get('/announcements/statuses/list'),

    uploadBookImportFile: (file: File): Promise<BookImportUploadResponse> => {
        const formData = new FormData()
        formData.append('file', file)
        return post('/books/import/upload', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        })
    },

    getBookImportFields: (): Promise<BookImportFieldOption[]> =>
        get('/books/import/fields'),

    previewBookImport: (data: BookImportPreviewRequest): Promise<BookImportPreviewResponse> =>
        post('/books/import/preview', data),

    confirmBookImport: (data: BookImportConfirmRequest): Promise<BookImportProgressResponse> =>
        post('/books/import/confirm', data),

    getBookImportProgress: (importRecordId: number): Promise<BookImportProgressResponse> =>
        get(`/books/import/progress/${importRecordId}`),

    getBookImportRecords: (params?: {
        page?: number
        page_size?: number
        status?: string
        keyword?: string
    }): Promise<BookImportRecordListResponse> =>
        get('/books/import/records', {
            params: buildPaginationParams(
                params?.page ?? 1,
                params?.page_size ?? 10,
                {
                    status: params?.status,
                    keyword: params?.keyword
                }
            )
        }),

    getBookImportRecordDetail: (importRecordId: number, params?: {
        status_filter?: string
    }): Promise<BookImportRecordDetail> =>
        get(`/books/import/records/${importRecordId}`, {
            params: params?.status_filter ? { status_filter: params.status_filter } : undefined
        }),

    getBookImportStatuses: (): Promise<BookImportStatusOption[]> =>
        Promise.resolve([
            { value: 'pending', label: '待处理', type: 'info' },
            { value: 'processing', label: '处理中', type: 'primary' },
            { value: 'completed', label: '已完成', type: 'success' },
            { value: 'failed', label: '失败', type: 'danger' }
        ])
}
