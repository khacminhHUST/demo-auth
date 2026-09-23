import axios from 'axios'

// Mặc định rỗng = gọi cùng origin với trang FE (đi qua proxy của Vite tới backend),
// để cookie refresh_token luôn là first-party thay vì bị trình duyệt chặn như
// third-party cookie khi FE/BE khác port (khác origin).
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''

let accessToken = null
let onAuthExpired = () => {}

export function setAccessToken(token) {
  accessToken = token
}

export function getAccessToken() {
  return accessToken
}

export function setOnAuthExpired(handler) {
  onAuthExpired = handler
}

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
})

apiClient.interceptors.request.use((config) => {
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`
  }
  return config
})

let refreshPromise = null

// Dùng chung 1 promise cho mọi lời gọi refresh xảy ra cùng lúc (React StrictMode
// double-invoke effect, nhiều tab, nhiều request 401 cùng lúc...). Refresh token bị
// rotate sau mỗi lần dùng, nên gọi /auth/refresh 2 lần song song bằng cùng 1 cookie
// sẽ khiến lần thứ 2 dùng phải token đã bị revoke -> bị hiểu nhầm là bị đánh cắp và
// server revoke toàn bộ session, tự động out người dùng.
export function refreshOnce() {
  if (!refreshPromise) {
    refreshPromise = axios
      .post(`${API_BASE_URL}/auth/refresh`, {}, { withCredentials: true })
      .finally(() => {
        refreshPromise = null
      })
  }
  return refreshPromise
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    const isRefreshCall = originalRequest?.url?.includes('/auth/refresh')
    if (error.response?.status === 401 && !originalRequest._retry && !isRefreshCall) {
      originalRequest._retry = true
      try {
        const { data } = await refreshOnce()
        setAccessToken(data.access_token)
        originalRequest.headers.Authorization = `Bearer ${data.access_token}`
        return apiClient(originalRequest)
      } catch (refreshError) {
        setAccessToken(null)
        onAuthExpired()
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  },
)
