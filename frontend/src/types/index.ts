export interface User {
    id: number
    username: string
    email: string
    is_active: boolean
    is_admin: boolean
    created_at: string
}

export interface Book {
    id: number
    title: string
    author: string
    publisher: string | null
    isbn: string | null
    price: number
    stock: number
    description: string | null
    cover_image: string | null
    category: string | null
    created_at: string
    updated_at: string
}

export interface BookListResponse {
    total: number
    page: number
    page_size: number
    items: Book[]
}

export interface BookCreate {
    title: string
    author: string
    publisher?: string
    isbn?: string
    price: number
    stock?: number
    description?: string
    cover_image?: string
    category?: string
}

export interface LoginResponse {
    access_token: string
    token_type: string
}

export interface PromotionBook {
    id: number
    promotion_id: number
    book_id: number
    promotion_price: number
    promotion_stock: number
    sold_stock: number
    remaining_stock: number
    original_price: number
    purchase_limit: number | null
    book: Book
    created_at: string
    updated_at: string
}

export interface Promotion {
    id: number
    name: string
    cover_image: string | null
    start_time: string
    end_time: string
    description: string | null
    is_displayed: boolean
    status: 'pending' | 'active' | 'ended'
    remaining_seconds: number | null
    books: PromotionBook[]
    created_at: string
    updated_at: string
}

export interface PromotionListResponse {
    total: number
    page: number
    page_size: number
    items: Promotion[]
}

export interface PromotionBookCreate {
    book_id: number
    promotion_price: number
    promotion_stock: number
    purchase_limit?: number
}

export interface PromotionCreate {
    name: string
    cover_image?: string
    start_time: string
    end_time: string
    description?: string
    is_displayed: boolean
    books: PromotionBookCreate[]
}

export interface PromotionUpdate {
    name?: string
    cover_image?: string
    start_time?: string
    end_time?: string
    description?: string
    is_displayed?: boolean
    books?: PromotionBookCreate[]
}

export interface FeedbackAttachment {
    id: number
    feedback_id: number
    file_name: string
    file_path: string
    file_size: number | null
    file_type: string | null
    created_at: string
}

export interface FeedbackAttachmentCreate {
    file_name: string
    file_path: string
    file_size?: number
    file_type?: string
}

export interface FeedbackReply {
    id: number
    feedback_id: number
    replier_id: number
    replier_type: 'user' | 'admin'
    content: string
    is_internal: boolean
    status_change: string | null
    replier_name: string | null
    created_at: string
}

export interface Feedback {
    id: number
    user_id: number
    type: 'product' | 'order' | 'account' | 'payment' | 'other'
    title: string
    description: string
    contact_info: string | null
    related_order_id: string | null
    related_book_id: number | null
    status: 'pending' | 'processing' | 'replied' | 'closed'
    username: string | null
    related_book: Book | null
    attachments: FeedbackAttachment[]
    replies: FeedbackReply[]
    created_at: string
    updated_at: string
}

export interface FeedbackCreate {
    type: string
    title: string
    description: string
    contact_info?: string
    related_order_id?: string
    related_book_id?: number
    attachments: FeedbackAttachmentCreate[]
}

export interface FeedbackReplySubmit {
    content: string
    is_internal?: boolean
    status_change?: string
}

export interface FeedbackUpdate {
    status?: string
    title?: string
    description?: string
}

export interface FeedbackListResponse {
    total: number
    page: number
    page_size: number
    items: Feedback[]
}

export interface FeedbackTypeOption {
    value: string
    label: string
}

export interface FeedbackStatusOption {
    value: string
    label: string
}

export interface FeedbackUploadResponse {
    file_name: string
    file_path: string
    file_size: number
    file_type: string
}
