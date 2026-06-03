import api from './client'

export interface User {
  id: number
  email: string
  role: string
  is_active: boolean
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export async function login(email: string, password: string): Promise<TokenResponse> {
  const form = new URLSearchParams()
  form.append('username', email)
  form.append('password', password)
  const res = await api.post('/users/token', form, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
  return res.data
}

export async function register(email: string, password: string): Promise<User> {
  const res = await api.post('/users/', { email, password, role: 'buyer' })
  return res.data
}

export function decodeToken(token: string): User {
  const payload = JSON.parse(atob(token.split('.')[1]))
  return { id: payload.id, email: payload.sub, role: payload.role, is_active: true }
}
