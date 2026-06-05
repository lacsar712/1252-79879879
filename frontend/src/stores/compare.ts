import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import { api } from '@/api'
import { useUserStore } from './user'
import type { Book, BookCompareData } from '@/types'
import { ElMessage } from 'element-plus'

const MAX_COMPARE_BOOKS = 4
const LOCAL_STORAGE_KEY = 'book_compare_list'

export const useCompareStore = defineStore('compare', () => {
    const userStore = useUserStore()

    const compareBookIds = ref<number[]>([])
    const compareBooks = ref<Map<number, Book>>(new Map())
    const compareData = ref<BookCompareData[]>([])
    const isCollapsed = ref(false)
    const isLoading = ref(false)

    const compareCount = computed(() => compareBookIds.value.length)
    const canAddMore = computed(() => compareBookIds.value.length < MAX_COMPARE_BOOKS)
    const hasBooks = computed(() => compareBookIds.value.length > 0)
    const isFull = computed(() => compareBookIds.value.length >= MAX_COMPARE_BOOKS)

    function isInCompare(bookId: number): boolean {
        return compareBookIds.value.includes(bookId)
    }

    function addToCompare(book: Book): boolean {
        if (compareBookIds.value.includes(book.id)) {
            ElMessage.warning('该图书已在对比栏中')
            return false
        }
        if (compareBookIds.value.length >= MAX_COMPARE_BOOKS) {
            ElMessage.warning(`最多只能对比 ${MAX_COMPARE_BOOKS} 本图书`)
            return false
        }
        compareBookIds.value.push(book.id)
        compareBooks.value.set(book.id, book)
        saveToLocalStorage()
        ElMessage.success(`已添加《${book.title}》到对比栏`)
        return true
    }

    function removeFromCompare(bookId: number): void {
        const index = compareBookIds.value.indexOf(bookId)
        if (index > -1) {
            const book = compareBooks.value.get(bookId)
            compareBookIds.value.splice(index, 1)
            compareBooks.value.delete(bookId)
            saveToLocalStorage()
            if (book) {
                ElMessage.info(`已移除《${book.title}》`)
            }
        }
    }

    function clearCompare(): void {
        compareBookIds.value = []
        compareBooks.value.clear()
        compareData.value = []
        saveToLocalStorage()
        ElMessage.info('对比栏已清空')
    }

    function toggleCollapse(): void {
        isCollapsed.value = !isCollapsed.value
    }

    function saveToLocalStorage(): void {
        try {
            localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(compareBookIds.value))
        } catch (e) {
            console.error('保存对比列表到本地存储失败:', e)
        }
    }

    function loadFromLocalStorage(): void {
        try {
            const saved = localStorage.getItem(LOCAL_STORAGE_KEY)
            if (saved) {
                const ids = JSON.parse(saved) as number[]
                compareBookIds.value = ids.filter(id => typeof id === 'number')
            }
        } catch (e) {
            console.error('从本地存储加载对比列表失败:', e)
        }
    }

    async function syncWithServer(): Promise<void> {
        if (!userStore.isLoggedIn) return
        try {
            const response = await api.getSavedCompareList()
            if (response.book_ids && response.book_ids.length > 0) {
                const mergedIds = [...new Set([...compareBookIds.value, ...response.book_ids])]
                compareBookIds.value = mergedIds.slice(0, MAX_COMPARE_BOOKS)
                saveToLocalStorage()
            }
        } catch (e) {
            console.error('从服务器同步对比列表失败:', e)
        }
    }

    async function saveToServer(): Promise<void> {
        if (!userStore.isLoggedIn) {
            ElMessage.info('请先登录，以便同步对比数据')
            return
        }
        try {
            await api.saveCompareList(compareBookIds.value)
            ElMessage.success('对比列表已同步到服务器')
        } catch (e) {
            console.error('保存对比列表到服务器失败:', e)
        }
    }

    async function fetchCompareData(): Promise<BookCompareData[]> {
        if (compareBookIds.value.length === 0) {
            compareData.value = []
            return []
        }
        isLoading.value = true
        try {
            const response = await api.getBooksCompare(compareBookIds.value)
            compareData.value = response.items

            const invalidBooks = response.items.filter(item => !item.is_valid)
            if (invalidBooks.length > 0) {
                const invalidIds = invalidBooks.map(b => b.id)
                ElMessage.warning(`有 ${invalidIds.length} 本图书已失效，已自动移除`)
                invalidIds.forEach(id => removeFromCompare(id))
            }

            return response.items
        } catch (e) {
            console.error('获取对比数据失败:', e)
            throw e
        } finally {
            isLoading.value = false
        }
    }

    function hydrateBooks(books: Book[]): void {
        books.forEach(book => {
            if (compareBookIds.value.includes(book.id) && !compareBooks.value.has(book.id)) {
                compareBooks.value.set(book.id, book)
            }
        })
    }

    watch(
        () => userStore.isLoggedIn,
        (isLoggedIn) => {
            if (isLoggedIn) {
                syncWithServer()
            }
        },
        { immediate: true }
    )

    loadFromLocalStorage()

    return {
        compareBookIds,
        compareBooks,
        compareData,
        isCollapsed,
        isLoading,
        compareCount,
        canAddMore,
        hasBooks,
        isFull,
        MAX_COMPARE_BOOKS,
        isInCompare,
        addToCompare,
        removeFromCompare,
        clearCompare,
        toggleCollapse,
        fetchCompareData,
        saveToServer,
        syncWithServer,
        hydrateBooks
    }
})
