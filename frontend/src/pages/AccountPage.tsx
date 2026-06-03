import { useEffect, useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { useWishlistStore } from '../store/wishlistStore'
import api from '../api/client'
import { type Product } from '../api/products'

interface Order {
  id: number
  status: string
  total_amount: string
  created_at: string
  items: { quantity: number; product: { name: string; price: string } }[]
}

type Tab = 'orders' | 'wishlist' | 'settings'

const statusLabels: Record<string, string> = {
  pending: 'Ожидает',
  processing: 'В обработке',
  shipped: 'Отправлен',
  delivered: 'Доставлен',
  cancelled: 'Отменён',
}

const statusColors: Record<string, string> = {
  pending: 'text-yellow-500',
  processing: 'text-blue-500',
  shipped: 'text-purple-500',
  delivered: 'text-green-500',
  cancelled: 'text-red-500',
}

export default function AccountPage() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()
  const [tab, setTab] = useState<Tab>('orders')
  const [orders, setOrders] = useState<Order[]>([])
  const [wishlistProducts, setWishlistProducts] = useState<Product[]>([])
  const [ordersLoading, setOrdersLoading] = useState(true)
  const [notifications, setNotifications] = useState({ orders: true, promos: false })
  const { ids: wishlistIds, toggle } = useWishlistStore()

  useEffect(() => {
    if (!user) { navigate('/login'); return }
    api.get('/orders/').then((res) => {
      setOrders(res.data.items || [])
      setOrdersLoading(false)
    })
  }, [user])

  useEffect(() => {
    if (tab === 'wishlist' && wishlistIds.length > 0) {
      Promise.all(wishlistIds.map((id) => api.get(`/products/${id}`).then((r) => r.data)))
        .then(setWishlistProducts)
    }
  }, [tab, wishlistIds])

  if (!user) return null

  return (
    <div className="min-h-screen">
      {/* Шапка аккаунта */}
      <div className="bg-black text-white">
        <div className="max-w-6xl mx-auto px-6 py-12 flex flex-col md:flex-row items-start md:items-end justify-between gap-6">
          <div>
            <p className="text-xs uppercase tracking-widest text-gray-500 mb-2">Добро пожаловать</p>
            <h1 className="text-3xl font-bold tracking-tight">{user.email}</h1>
          </div>
          <button
            onClick={() => { logout(); navigate('/') }}
            className="text-xs uppercase tracking-widest text-gray-400 hover:text-white transition-colors border border-gray-700 px-5 py-2"
          >
            Выйти
          </button>
        </div>

        {/* Табы */}
        <div className="max-w-6xl mx-auto px-6 flex gap-0 border-t border-gray-800">
          {([['orders', 'Заказы'], ['wishlist', 'Избранное'], ['settings', 'Настройки']] as [Tab, string][]).map(([key, label]) => (
            <button
              key={key}
              onClick={() => setTab(key)}
              className={`px-6 py-4 text-xs font-semibold uppercase tracking-widest transition-colors border-b-2 ${
                tab === key ? 'border-white text-white' : 'border-transparent text-gray-500 hover:text-gray-300'
              }`}
            >
              {label}
              {key === 'wishlist' && wishlistIds.length > 0 && (
                <span className="ml-2 text-gray-500">{wishlistIds.length}</span>
              )}
            </button>
          ))}
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-6 py-10">

        {/* Вкладка: Заказы */}
        {tab === 'orders' && (
          ordersLoading ? (
            <p className="text-gray-400 text-sm">Загрузка...</p>
          ) : orders.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-24 gap-6">
              <p className="text-6xl font-black text-gray-100">0</p>
              <p className="text-gray-400 text-sm uppercase tracking-widest">Заказов пока нет</p>
              <Link to="/products"
                className="bg-black text-white px-10 py-3 text-xs font-semibold uppercase tracking-widest hover:bg-gray-900 transition-colors">
                Перейти в каталог
              </Link>
            </div>
          ) : (
            <div className="flex flex-col gap-3">
              {orders.map((order) => (
                <div key={order.id} className="border border-gray-100 p-6 hover:border-black transition-colors">
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <p className="text-sm font-bold uppercase tracking-wide">Заказ #{order.id}</p>
                      <p className="text-xs text-gray-400 mt-1">
                        {new Date(order.created_at).toLocaleDateString('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' })}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className={`text-xs font-semibold uppercase tracking-widest ${statusColors[order.status] ?? 'text-gray-400'}`}>
                        {statusLabels[order.status] ?? order.status}
                      </p>
                      <p className="text-base font-bold mt-1">{Number(order.total_amount).toLocaleString('ru-RU')} ₽</p>
                    </div>
                  </div>
                  {order.items?.length > 0 && (
                    <div className="border-t border-gray-100 pt-3 grid grid-cols-1 gap-1">
                      {order.items.map((item, i) => (
                        <div key={i} className="flex justify-between text-xs text-gray-400">
                          <span>{item.product.name} × {item.quantity}</span>
                          <span>{(parseFloat(item.product.price) * item.quantity).toLocaleString('ru-RU')} ₽</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )
        )}

        {/* Вкладка: Избранное */}
        {tab === 'wishlist' && (
          wishlistIds.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-24 gap-6">
              <svg width="48" height="48" fill="none" stroke="#d1d5db" strokeWidth="1.5" viewBox="0 0 24 24">
                <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
              </svg>
              <p className="text-gray-400 text-sm uppercase tracking-widest">Избранное пусто</p>
              <Link to="/products"
                className="bg-black text-white px-10 py-3 text-xs font-semibold uppercase tracking-widest hover:bg-gray-900 transition-colors">
                В каталог
              </Link>
            </div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-5">
              {wishlistProducts.map((product) => (
                <div key={product.id} className="group relative">
                  <Link to={`/products/${product.id}`} className="block">
                    <div className="bg-gray-50 aspect-square overflow-hidden mb-3">
                      {product.image_url
                        ? <img src={product.image_url} alt={product.name} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
                        : <div className="w-full h-full flex items-center justify-center text-gray-200 text-xs">Нет фото</div>}
                    </div>
                    <p className="text-xs font-bold uppercase tracking-widest mb-1">{product.name}</p>
                    <p className="text-sm text-gray-500">{Number(product.price).toLocaleString('ru-RU')} ₽</p>
                  </Link>
                  <button onClick={() => toggle(product.id)}
                    className="absolute top-2 right-2 w-7 h-7 bg-white flex items-center justify-center shadow-sm">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="#000" stroke="#000" strokeWidth="2">
                      <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
                    </svg>
                  </button>
                </div>
              ))}
            </div>
          )
        )}

        {/* Вкладка: Настройки */}
        {tab === 'settings' && (
          <div className="max-w-md flex flex-col gap-8">
            <div>
              <h2 className="text-xs font-bold uppercase tracking-widest mb-6 pb-3 border-b border-gray-100">
                Уведомления на email
              </h2>
              <div className="flex flex-col gap-5">
                {[
                  { key: 'orders', label: 'Статус заказов', desc: 'Когда заказ отправлен или доставлен' },
                  { key: 'promos', label: 'Акции и новинки', desc: 'Новые коллекции и специальные предложения' },
                ].map(({ key, label, desc }) => (
                  <div key={key} className="flex items-center justify-between gap-4">
                    <div>
                      <p className="text-sm font-semibold">{label}</p>
                      <p className="text-xs text-gray-400 mt-0.5">{desc}</p>
                    </div>
                    <button
                      onClick={() => setNotifications((n) => ({ ...n, [key]: !n[key as keyof typeof n] }))}
                      className={`relative w-11 h-6 rounded-full transition-colors duration-200 ${notifications[key as keyof typeof notifications] ? 'bg-black' : 'bg-gray-200'}`}
                    >
                      <span className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-transform duration-200 ${notifications[key as keyof typeof notifications] ? 'translate-x-6' : 'translate-x-1'}`} />
                    </button>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <h2 className="text-xs font-bold uppercase tracking-widest mb-6 pb-3 border-b border-gray-100">
                Аккаунт
              </h2>
              <div className="flex flex-col gap-3">
                <div className="flex justify-between items-center py-2">
                  <span className="text-xs text-gray-400 uppercase tracking-wider">Email</span>
                  <span className="text-sm font-medium">{user.email}</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
