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
