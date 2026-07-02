import axios from 'axios'
import { getAccessToken, getRefreshToken, saveTokens, clearTokens, isTokenExpired } from './auth.js'

// Настраиваем глобальный axios — все существующие импорты из 'axios' подхватят эти interceptors
const _setup = () => {
  // Request interceptor — добавляет Bearer к каждому запросу
  axios.interceptors.request.use(config => {
    const token = getAccessToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  })

  // Response interceptor — при 401 пробует refresh
  let refreshPromise = null

  axios.interceptors.response.use(
    response => response,
    async error => {
      const original = error.config

      if (
        !error.response ||
        error.response.status !== 401 ||
        original._retry ||
        !original.url?.startsWith('/api/') ||
        original.url?.includes('/auth/')
      ) {
        return Promise.reject(error)
      }

      original._retry = true

      if (!refreshPromise) {
        const refreshToken = getRefreshToken()
        if (!refreshToken || isTokenExpired(refreshToken)) {
          clearTokens()
          window.location.href = '/login'
          return Promise.reject(error)
        }

        refreshPromise = axios.post('/api/auth/refresh', { refresh_token: refreshToken })
          .then(res => {
            saveTokens(res.data.access_token, refreshToken)
            return res.data.access_token
          })
          .catch(() => {
            clearTokens()
            window.location.href = '/login'
            return null
          })
          .finally(() => {
            refreshPromise = null
          })
      }

      const newToken = await refreshPromise
      if (!newToken) return Promise.reject(error)

      original.headers.Authorization = `Bearer ${newToken}`
      return axios(original)
    }
  )
}

_setup()

export default axios
