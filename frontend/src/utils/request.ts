import axios, { type AxiosInstance, type AxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus'
import type { Ref } from 'vue'

export interface RequestConfig extends AxiosRequestConfig {
  showSuccess?: boolean
  successMessage?: string
  showError?: boolean
  errorMessage?: string
  loadingRef?: Ref<boolean>
}

export interface RequestOptions {
  baseURL?: string
  timeout?: number
}

function createRequestInstance(options: RequestOptions = {}): AxiosInstance {
  const instance = axios.create({
    baseURL: options.baseURL || '/api',
    timeout: options.timeout || 10000,
    headers: {
      'Content-Type': 'application/json'
    }
  })

  instance.interceptors.request.use(
    (config) => {
      const token = localStorage.getItem('token')
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
      return config
    },
    (error) => Promise.reject(error)
  )

  instance.interceptors.response.use(
    (response) => response.data,
    (error) => {
      const message = error.response?.data?.detail || '请求失败，请稍后重试'
      ElMessage.error(message)
      return Promise.reject(error)
    }
  )

  return instance
}

export const requestInstance = createRequestInstance()

function extractRequestConfig(config: RequestConfig) {
  const {
    showSuccess,
    successMessage,
    showError,
    errorMessage,
    loadingRef,
    ...axiosConfig
  } = config
  return {
    showSuccess,
    successMessage,
    showError,
    errorMessage,
    loadingRef,
    axiosConfig
  }
}

async function handleLoadingStart(loadingRef?: Ref<boolean>) {
  if (loadingRef) {
    loadingRef.value = true
  }
}

async function handleLoadingEnd(loadingRef?: Ref<boolean>) {
  if (loadingRef) {
    loadingRef.value = false
  }
}

function handleSuccess(showSuccess?: boolean, successMessage?: string) {
  if (showSuccess && successMessage) {
    ElMessage.success(successMessage)
  }
}

function handleError(
  error: any,
  showError?: boolean,
  errorMessage?: string
): never {
  if (showError && errorMessage) {
    ElMessage.error(errorMessage)
  }
  throw error
}

export async function request<T = any>(config: RequestConfig): Promise<T> {
  const { showSuccess, successMessage, showError, errorMessage, loadingRef, axiosConfig } = extractRequestConfig(config)

  handleLoadingStart(loadingRef)

  try {
    const response = await requestInstance.request<T, T>(axiosConfig)
    handleSuccess(showSuccess, successMessage)
    return response
  } catch (error) {
    handleError(error, showError, errorMessage)
  } finally {
    handleLoadingEnd(loadingRef)
  }
}

export async function get<T = any>(url: string, config: RequestConfig = {}): Promise<T> {
  return request<T>({ ...config, method: 'GET', url })
}

export async function post<T = any>(url: string, data?: any, config: RequestConfig = {}): Promise<T> {
  return request<T>({ ...config, method: 'POST', url, data })
}

export async function put<T = any>(url: string, data?: any, config: RequestConfig = {}): Promise<T> {
  return request<T>({ ...config, method: 'PUT', url, data })
}

export async function del<T = any>(url: string, config: RequestConfig = {}): Promise<T> {
  return request<T>({ ...config, method: 'DELETE', url })
}

export async function patch<T = any>(url: string, data?: any, config: RequestConfig = {}): Promise<T> {
  return request<T>({ ...config, method: 'PATCH', url, data })
}

export function withSuccess<T>(
  fn: () => Promise<T>,
  message: string
): () => Promise<T> {
  return async () => {
    const result = await fn()
    ElMessage.success(message)
    return result
  }
}

export function withLoading<T>(
  fn: () => Promise<T>,
  loadingRef: Ref<boolean>
): () => Promise<T> {
  return async () => {
    loadingRef.value = true
    try {
      return await fn()
    } finally {
      loadingRef.value = false
    }
  }
}
