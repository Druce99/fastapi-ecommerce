import { useEffect } from 'react'
import { useCartStore } from '../store/cartStore'
import { useAuthStore } from '../store/authStore'
import { getCart, removeFromCart, updateCartItem } from '../api/cart'
import { useNavigate } from 'react-router-dom'

export default function CartDrawer() {
  const { cart, isOpen, closeCart, setCart } = useCartStore()
  const token = useAuthStore((s) => s.token)
  const navigate = useNavigate()

  useEffect(() => {
    if (isOpen && token) {
      getCart().then(setCart)
    }
  }, [isOpen, token])

  async function handleRemove(productId: number) {
    await removeFromCart(productId)
    const updated = await getCart()
    setCart(updated)
  }

  async function handleQuantity(productId: number, quantity: number) {
    if (quantity < 1) return
    await updateCartItem(productId, quantity)
    const updated = await getCart()
    setCart(updated)
  }

  function handleCheckout() {
    closeCart()
    navigate('/checkout')
  }

  return (
    <>
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/30 z-40"
          onClick={closeCart}
        />
      )}
      <div
        className={`fixed top-0 right-0 h-full w-full max-w-md bg-white z-50 flex flex-col transition-transform duration-300 ${
          isOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        <div className="flex items-center justify-between px-6 py-5 border-b border-gray-200">
          <h2 className="text-sm font-bold uppercase tracking-widest">Корзина</h2>
          <button onClick={closeCart} className="text-gray-400 hover:text-black text-xl">✕</button>
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-4">
          {!token ? (
            <div className="flex flex-col items-center justify-center h-full gap-4">
              <p className="text-gray-400 text-sm">Войдите чтобы увидеть корзину</p>
              <button
                onClick={() => { closeCart(); navigate('/login') }}
                className="bg-black text-white px-8 py-3 text-sm uppercase tracking-widest"
              >
                Войти
              </button>
            </div>
          ) : !cart || cart.items.length === 0 ? (
            <div className="flex items-center justify-center h-full">
              <p className="text-gray-400 text-sm">Корзина пуста</p>
            </div>
          ) : (
            <div className="flex flex-col gap-6">
              {cart.items.map((item) => (
                <div key={item.id} className="flex gap-4">
                  <div className="w-20 h-20 bg-gray-100 flex-shrink-0 overflow-hidden">
                    {item.product.image_url ? (
                      <img src={item.product.image_url} alt={item.product.name} className="w-full h-full object-cover" />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-gray-300 text-xs">Нет фото</div>
                    )}
                  </div>
                  <div className="flex-1 flex flex-col justify-between">
                    <p className="text-sm font-medium uppercase tracking-wide">{item.product.name}</p>
                    <p className="text-sm text-gray-500">{item.product.price} ₽</p>
                    <div className="flex items-center gap-3">
                      <button
                        onClick={() => handleQuantity(item.product.id, item.quantity - 1)}
                        className="w-6 h-6 border border-gray-200 flex items-center justify-center text-sm hover:border-black"
                      >−</button>
                      <span className="text-sm">{item.quantity}</span>
                      <button
                        onClick={() => handleQuantity(item.product.id, item.quantity + 1)}
                        className="w-6 h-6 border border-gray-200 flex items-center justify-center text-sm hover:border-black"
                      >+</button>
                    </div>
                  </div>
                  <button
                    onClick={() => handleRemove(item.product.id)}
                    className="text-gray-300 hover:text-black text-sm self-start"
                  >✕</button>
                </div>
              ))}
            </div>
          )}
        </div>

        {cart && cart.items.length > 0 && token && (
          <div className="px-6 py-6 border-t border-gray-200">
            <div className="flex justify-between text-sm mb-6">
              <span className="uppercase tracking-wider">Итого</span>
              <span className="font-medium">{cart.total_price} ₽</span>
            </div>
            <button
              onClick={handleCheckout}
              className="w-full bg-black text-white py-4 text-sm uppercase tracking-widest hover:bg-gray-800 transition-colors"
            >
              Оформить заказ
            </button>
          </div>
        )}
      </div>
    </>
  )
}
