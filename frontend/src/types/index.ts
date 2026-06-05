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

export interface BookChapter {
    id: number
    book_id: number
    title: string
    content: string
    sort_order: number
    is_public: boolean
    created_at: string
    updated_at: string
}

export interface BookChapterPublic {
    id: number
    book_id: number
    title: string
    content: string
    sort_order: number
    created_at: string
    updated_at: string
}

export interface BookChapterCreate {
    book_id: number
    title: string
    content: string
    sort_order?: number
    is_public?: boolean
}

export interface BookChapterUpdate {
    title?: string
    content?: string
    sort_order?: number
    is_public?: boolean
}

export interface BookChapterListResponse {
    total: number
    items: BookChapter[]
}

export interface BookChapterPublicListResponse {
    total: number
    items: BookChapterPublic[]
}

export interface StockTakingItem {
    id: number
    stock_taking_id: number
    book_id: number
    expected_stock: number
    actual_stock: number | null
    difference: number | null
    book: Book | null
    created_at: string
    updated_at: string
}

export interface StockTaking {
    id: number
    task_no: string
    name: string
    scope: string
    person_in_charge: string | null
    remark: string | null
    status: 'draft' | 'in_progress' | 'confirmed' | 'cancelled'
    created_by: number
    confirmed_by: number | null
    created_by_name: string | null
    confirmed_by_name: string | null
    items: StockTakingItem[]
    total_books: number
    completed_count: number
    difference_count: number
    created_at: string
    updated_at: string
    confirmed_at: string | null
}

export interface StockTakingListResponse {
    total: number
    page: number
    page_size: number
    items: StockTaking[]
}

export interface StockTakingCreate {
    name: string
    scope: string
    person_in_charge?: string
    remark?: string
    book_ids: number[]
}

export interface StockTakingUpdate {
    name?: string
    scope?: string
    person_in_charge?: string
    remark?: string
    book_ids?: number[]
}

export interface StockTakingItemUpdate {
    item_id: number
    actual_stock: number
}

export interface StockTakingBatchEntryRequest {
    items: StockTakingItemUpdate[]
}

export interface StockTakingScopeOption {
    value: string
    label: string
}

export interface Supplier {
    id: number
    name: string
    contact_person: string | null
    phone: string | null
    email: string | null
    address: string | null
    remark: string | null
    created_at: string
    updated_at: string
}

export interface SupplierListResponse {
    total: number
    page: number
    page_size: number
    items: Supplier[]
}

export interface SupplierCreate {
    name: string
    contact_person?: string
    phone?: string
    email?: string
    address?: string
    remark?: string
}

export interface SupplierUpdate {
    name?: string
    contact_person?: string
    phone?: string
    email?: string
    address?: string
    remark?: string
}

export interface SupplierOption {
    id: number
    name: string
    contact_person: string | null
    phone: string | null
}

export interface PurchaseOrderItem {
    id: number
    purchase_order_id: number
    book_id: number
    quantity: number
    unit_price: number
    expected_arrival_time: string | null
    received_quantity: number
    book: Book | null
    subtotal: number
    created_at: string
    updated_at: string
}

export interface PurchaseOrderItemCreate {
    book_id: number
    quantity: number
    unit_price: number
    expected_arrival_time?: string
}

export interface PurchaseOrder {
    id: number
    order_no: string
    supplier_id: number
    purchase_date: string
    total_amount: number
    remark: string | null
    status: 'draft' | 'pending' | 'received' | 'cancelled'
    created_by: number
    confirmed_by: number | null
    created_by_name: string | null
    confirmed_by_name: string | null
    supplier: Supplier | null
    items: PurchaseOrderItem[]
    stock_impact: Array<{
        book_id: number
        book_title: string
        added_quantity: number
        unit_cost: number
        total_cost: number
    }> | null
    created_at: string
    updated_at: string
    confirmed_at: string | null
}

export interface PurchaseOrderListResponse {
    total: number
    page: number
    page_size: number
    items: PurchaseOrder[]
}

export interface PurchaseOrderCreate {
    supplier_id: number
    purchase_date: string
    remark?: string
    items: PurchaseOrderItemCreate[]
}

export interface PurchaseOrderUpdate {
    supplier_id?: number
    purchase_date?: string
    remark?: string
    items?: PurchaseOrderItemCreate[]
}

export interface PurchaseOrderStatusOption {
    value: string
    label: string
    type: string
}

export interface StockChange {
    id: number
    book_id: number
    book_title: string
    change_type: string
    change_quantity: number
    before_stock: number
    after_stock: number
    unit_cost: number | null
    total_cost: number | null
    remark: string | null
    created_at: string
}

export interface UserAddress {
    id: number
    user_id: number
    contact_name: string
    phone: string
    province: string
    city: string
    district: string
    detail_address: string
    address_tag: string | null
    is_default: boolean
    full_address: string
    created_at: string
    updated_at: string
}

export interface UserAddressListResponse {
    total: number
    items: UserAddress[]
}

export interface UserAddressCreate {
    contact_name: string
    phone: string
    province: string
    city: string
    district: string
    detail_address: string
    address_tag?: string | null
    is_default: boolean
}

export interface UserAddressUpdate {
    contact_name?: string
    phone?: string
    province?: string
    city?: string
    district?: string
    detail_address?: string
    address_tag?: string | null
    is_default?: boolean
}

export interface UserAddressDeleteResponse {
    message: string
    need_reassign_default: boolean
    remaining_addresses?: Array<{
        id: number
        contact_name: string
        phone: string
        full_address: string
    }>
}

export interface UserAddressReassignDefaultRequest {
    new_default_address_id: number
}

export interface AddressTagOption {
    value: string
    label: string
    type: '' | 'success' | 'warning' | 'info' | 'danger' | 'primary'
}

export interface BookRating {
    book_id: number
    rating: number
    review_count: number
}

export interface BookTag {
    book_id: number
    tags: string[]
}

export interface BookCompareData {
    id: number
    title: string
    author: string
    publisher: string | null
    category: string | null
    price: number
    stock: number
    description: string | null
    cover_image: string | null
    isbn: string | null
    rating: number | null
    review_count: number
    tags: string[]
    is_valid: boolean
    invalid_reason?: string
}

export interface BookCompareResponse {
    items: BookCompareData[]
    invalid_ids: number[]
}
