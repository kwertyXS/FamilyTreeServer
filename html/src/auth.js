const ACCESS_KEY = 'access_token'
const REFRESH_KEY = 'refresh_token'

function decodeToken(token) {
  try {
    const payload = token.split('.')[1]
    return JSON.parse(atob(payload))
  } catch {
    return null
  }
}

export function saveTokens(access, refresh) {
  localStorage.setItem(ACCESS_KEY, access)
  localStorage.setItem(REFRESH_KEY, refresh)
}

export function getAccessToken() {
  return localStorage.getItem(ACCESS_KEY)
}

export function getRefreshToken() {
  return localStorage.getItem(REFRESH_KEY)
}

export function clearTokens() {
  localStorage.removeItem(ACCESS_KEY)
  localStorage.removeItem(REFRESH_KEY)
}

export function isTokenExpired(token) {
  const data = decodeToken(token)
  if (!data || !data.exp) return true
  return Date.now() >= data.exp * 1000
}

export function isAuthenticated() {
  return !!getAccessToken()
}

export function isAdmin() {
  const token = getAccessToken()
  if (!token) return false
  const data = decodeToken(token)
  return data?.is_admin === true
}
