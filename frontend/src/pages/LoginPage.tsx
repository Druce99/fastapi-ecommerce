import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { login, decodeToken } from '../api/auth'
import { useAuthStore } from '../store/authStore'

export default function LoginPage() {
  const navigate = useNavigate()
  const setAuth = useAuthStore((s) => s.setAuth)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const tokens = await login(email, password)
      const user = decodeToken(tokens.access_token)
      setAuth(user, tokens.access_token, tokens.refresh_token)
      navigate('/')
    } catch {
      setError('Неверный email или пароль')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="w-full max-w-sm px-8 py-12 bg-white">
        <h1 className="text-2xl font-bold uppercase tracking-widest mb-10 text-center">Вход</h1>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="border border-gray-200 px-4 py-3 text-sm outline-none focus:border-black transition-colors"
          />
          <input
            type="password"
            placeholder="Пароль"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            className="border border-gray-200 px-4 py-3 text-sm outline-none focus:border-black transition-colors"
          />
          {error && <p className="text-red-500 text-xs">{error}</p>}
          <button
            type="submit"
            disabled={loading}
            className="bg-black text-white py-3 text-sm uppercase tracking-widest hover:bg-gray-800 transition-colors disabled:opacity-50 mt-2"
          >
            {loading ? 'Загрузка...' : 'Войти'}
          </button>
        </form>
        <p className="text-center text-sm text-gray-500 mt-6">
          Нет аккаунта?{' '}
          <Link to="/register" className="text-black underline">
            Зарегистрироваться
          </Link>
        </p>
      </div>
    </div>
  )
}
