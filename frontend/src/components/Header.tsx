import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { useCartStore } from '../store/cartStore'

export default function Header() {
  const user = useAuthStore((s) => s.user)
  const { openCart, totalItems } = useCartStore()
  const navigate = useNavigate()
  const location = useLocation()
  const cartCount = totalItems()

  const navLink = (to: string, label: string) => (
    <Link
      to={to}
      className={`text-xs font-semibold uppercase tracking-widest transition-colors ${
        location.pathname.startsWith(to) && to !== '/'
          ? 'text-black'
          : 'text-gray-400 hover:text-black'
      }`}
    >
      {label}
    </Link>
  )

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-white border-b border-gray-100">
      <div className="max-w-6xl mx-auto px-4 md:px-6 h-14 md:h-16 flex items-center justify-between gap-4">
        <Link to="/" className="text-base md:text-lg font-black tracking-tight uppercase shrink-0">
          DrüceShop
        </Link>

        <nav className="flex items-center gap-4 md:gap-8">
          {navLink('/products', 'Каталог')}

          <button
            onClick={openCart}
            className="relative text-xs font-semibold uppercase tracking-widest text-gray-400 hover:text-black transition-colors"
          >
            Корзина
            {cartCount > 0 && (
              <span className="absolute -top-2 -right-4 bg-black text-white text-[10px] w-4 h-4 rounded-full flex items-center justify-center font-bold">
                {cartCount}
              </span>
            )}
          </button>

          {user ? (
            navLink('/account', 'Аккаунт')
          ) : (
            <button
              onClick={() => navigate('/login')}
              className="text-xs font-semibold uppercase tracking-widest text-gray-400 hover:text-black transition-colors"
            >
              Войти
            </button>
          )}
        </nav>
      </div>
    </header>
  )
}
