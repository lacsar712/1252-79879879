import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/api'
import type { User } from '@/types'

export const useUserStore = defineStore('user', () => {
    const token = ref<string | null>(localStorage.getItem('token'))
    const user = ref<User | null>(null)

    const isLoggedIn = computed(() => !!token.value)
    const isAdmin = computed(() => user.value?.is_admin ?? false)

    async function login(username: string, password: string) {
        const response = await api.login(username, password)
        token.value = response.access_token
        localStorage.setItem('token', response.access_token)
        await fetchUser()
    }

    async function register(username: string, email: string, password: string) {
        await api.register(username, email, password)
    }

    async function fetchUser() {
        if (!token.value) return
        try {
            user.value = await api.getCurrentUser()
        } catch (error) {
            logout()
        }
    }

    function logout() {
        token.value = null
        user.value = null
        localStorage.removeItem('token')
    }

    // 初始化时获取用户信息
    if (token.value) {
        fetchUser()
    }

    return {
        token,
        user,
        isLoggedIn,
        isAdmin,
        login,
        register,
        fetchUser,
        logout
    }
})
