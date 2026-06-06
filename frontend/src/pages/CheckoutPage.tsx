import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { useCartStore } from '../store/cartStore'
import api from '../api/client'

export default function CheckoutPage() {
  const navigate = useNavigate()
  const user = useAuthStore((s) => s.user)
  const { cart, setCart } = useCartStore()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  if (!user) {
    navigate('/login')
    return null
  }

  if (!cart || cart.items.length === 0) {
    navigate('/products')
    return null
  }

  async function handleOrder() {
    setError('')
    setLoading(true)
    try {
      const response = await api.post('/orders/checkout')
      const confirmationUrl: string | null = response.data?.confirmation_url ?? null
      setCart({ ...cart!, items: [], total_quantity: 0, total_price: '0' })
      if (confirmationUrl) {
        window.location.href = confirmationUrl
      } else {
        navigate('/account')
      }
    } catch {
      setError('Ошибка при оформлении заказа. Попробуйте снова.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-3xl mx-auto px-6 py-12">
      <h1 className="text-2xl font-bold uppercase tracking-widest mb-10">Оформление заказа</h1>

      <div className="flex flex-col gap-4 mb-10">
        {cart.items.map((item) => (
          <div key={item.id} className="flex items-center gap-4 border-b border-gray-100 pb-4">
            <div className="w-16 h-16 bg-gray-100 flex-shrink-0 overflow-hidden">
              {item.product.image_url ? (
                <img src={item.product.image_url} alt={item.product.name} className="w-full h-full object-cover" />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-gray-300 text-xs">Нет фото</div>
              )}
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium uppercase tracking-wide">{item.product.name}</p>
              <p className="text-xs text-gray-400 mt-1">Кол-во: {item.quantity}</p>
            </div>
            <p className="text-sm font-medium">
              {(parseFloat(item.product.price) * item.quantity).toFixed(2)} ₽
            </p>
          </div>
        ))}
      </div>

      <div className="flex justify-between text-sm mb-8 font-medium">
        <span className="uppercase tracking-wider">Итого</span>
        <span>{cart.total_price} ₽</span>
      </div>

      {error && <p className="text-red-500 text-xs mb-4">{error}</p>}

      <button
        onClick={handleOrder}
        disabled={loading}
        className="w-full bg-black text-white py-4 text-sm uppercase tracking-widest hover:bg-gray-800 transition-colors disabled:opacity-50"
      >
        {loading ? 'Оформляем...' : 'Подтвердить заказ'}
      </button>

      <p className="text-center text-xs text-gray-400 mt-4">
        После подтверждения вы получите уведомление на {user.email}
      </p>
    </div>
  )
}
