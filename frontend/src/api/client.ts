import axios from 'axios'

const api = axios.create({
  baseURL: 'https://druceshop.ru',
})

api.interceptors.request.use((config) => {
  try {
    const raw = localStorage.getItem('auth')
    if (raw) {
      const token = JSON.parse(raw)?.state?.token
      if (token) {
        config.headers['Authorization'] = `Bearer ${token}`
      }
    }
  } catch {}
  return config
})

let isRefreshing = false
let queue: ((token: string) => void)[] = []

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config

    if (error.response?.status !== 401 || original._retry) {
      return Promise.reject(error)
    }

    original._retry = true

    const raw = localStorage.getItem('auth')
    const refreshToken = raw ? JSON.parse(raw)?.state?.refreshToken : null

    if (!refreshToken) {
      localStorage.removeItem('auth')
      window.location.href = '/login'
      return Promise.reject(error)
    }

    if (isRefreshing) {
      return new Promise((resolve) => {
        queue.push((token) => {
          original.headers['Authorization'] = `Bearer ${token}`
          resolve(api(original))
        })
      })
    }

    isRefreshing = true

    try {
      const res = await axios.post('https://druceshop.ru/users/access-token', {
        refresh_token: refreshToken,
      })
      const newToken = res.data.access_token

      const authRaw = localStorage.getItem('auth')
      if (authRaw) {
        const parsed = JSON.parse(authRaw)
        parsed.state.token = newToken
        localStorage.setItem('auth', JSON.stringify(parsed))
      }

      queue.forEach((cb) => cb(newToken))
      queue = []

      original.headers['Authorization'] = `Bearer ${newToken}`
      return api(original)
    } catch {
      localStorage.removeItem('auth')
      window.location.href = '/login'
      return Promise.reject(error)
    } finally {
      isRefreshing = false
    }
  }
)

export default api
