import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { type Product } from '../api/products'
import { addToCart, getCart } from '../api/cart'
import { useAuthStore } from '../store/authStore'
import { useCartStore } from '../store/cartStore'
import api from '../api/client'

export default function ProductPage() {
  const { id } = useParams()
  const [product, setProduct] = useState<Product | null>(null)
  const [loading, setLoading] = useState(true)
  const [adding, setAdding] = useState(false)
  const [added, setAdded] = useState(false)
  const token = useAuthStore((s) => s.token)
  const { setCart, openCart } = useCartStore()

  useEffect(() => {
    api.get(`/products/${id}`).then((res) => {
      setProduct(res.data)
      setLoading(false)
    })
  }, [id])

  async function handleAddToCart() {
    if (!token) {
      window.location.href = '/login'
      return
    }
    if (!product) return
    setAdding(true)
    try {
      await addToCart(product.id)
      const cart = await getCart()
      setCart(cart)
      setAdded(true)
      setTimeout(() => setAdded(false), 2000)
      openCart()
    } finally {
      setAdding(false)
    }
  }

  if (loading) return (
    <div className="max-w-6xl mx-auto px-6 py-12 text-gray-400 text-sm uppercase tracking-widest">
      Загрузка...
    </div>
  )

  if (!product) return (
    <div className="max-w-6xl mx-auto px-6 py-12 text-gray-400 text-sm">
      Товар не найден
    </div>
  )

  return (
    <div className="max-w-6xl mx-auto px-6 py-12">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
        <div className="bg-gray-100 aspect-square overflow-hidden">
          {product.image_url ? (
            <img
              src={product.image_url}
              alt={product.name}
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-gray-300">
              Нет фото
            </div>
          )}
        </div>

        <div className="flex flex-col justify-center">
          <p className="text-xs text-gray-400 uppercase tracking-widest mb-3">
            В наличии: {product.stock} шт.
          </p>
          <h1 className="text-3xl font-bold uppercase tracking-widest mb-4">
            {product.name}
          </h1>
          <p className="text-2xl mb-6">{product.price} ₽</p>
          <p className="text-gray-500 text-sm leading-relaxed mb-10">
            {product.description}
          </p>
          <button
            onClick={handleAddToCart}
            disabled={adding || product.stock === 0}
            className="bg-black text-white py-4 text-sm uppercase tracking-widest hover:bg-gray-800 transition-colors disabled:opacity-50"
          >
            {product.stock === 0
              ? 'Нет в наличии'
              : adding
              ? 'Добавляем...'
              : added
              ? 'Добавлено!'
              : 'В корзину'}
          </button>
        </div>
      </div>
    </div>
  )
}
