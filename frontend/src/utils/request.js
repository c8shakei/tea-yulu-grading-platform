import axios from 'axios'
import { ElMessage } from 'element-plus'
import { getToken, removeToken } from './auth'
import { useUserStore } from '../stores/user'

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 30000,
})

request.interceptors.request.use(
  (config) => {
    const token = getToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

request.interceptors.response.use(
  (response) => {
    const data = response.data
    if (data && typeof data.code === 'number' && data.code !== 0) {
      ElMessage.error(data.message || '请求失败')
      if (data.code === 401) {
        removeToken()
        const userStore = useUserStore()
        userStore.logout()
      }
      return Promise.reject(new Error(data.message || '请求失败'))
    }
    return response
  },
  (error) => {
    const msg = error.response?.data?.message || error.message || '网络错误'
    ElMessage.error(msg)
    if (error.response?.status === 401) {
      removeToken()
      const userStore = useUserStore()
      userStore.logout()
    }
    return Promise.reject(error)
  }
)

export function unwrap(response) {
  return response.data?.data
}

export default request
