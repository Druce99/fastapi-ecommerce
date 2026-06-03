import { Link } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { getProducts, type Product } from '../api/products'

export default function HomePage() {
  const [featured, setFeatured] = useState<Product[]>([])

  useEffect(() => {
    getProducts(1, { in_stock: true }).then((data) => {
      setFeatured(data.items.slice(0, 4))
    })
  }, [])

  return (
    <div>
      {/* Hero */}
      <section className="h-screen bg-gray-100 flex items-center justify-center relative overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-gray-200 via-gray-100 to-gray-50" />
        <div className="relative text-center px-6">
          <p className="text-xs uppercase tracking-[0.4em] text-gray-400 mb-6">Streetwear из Европы</p>
          <h1 className="text-7xl md:text-9xl font-black tracking-tight uppercase leading-none mb-8">
            Drüce<br />Shop
          </h1>
          <p className="text-gray-400 text-sm tracking-widest uppercase mb-12 max-w-sm mx-auto">
            Доставка по всей России
          </p>
          <Link
            to="/products"
            className="inline-block bg-black text-white px-12 py-4 text-xs uppercase tracking-[0.3em] hover:bg-gray-900 transition-colors"
          >
            Смотреть каталог
          </Link>
        </div>
        <div className="absolute bottom-8 left-8 flex flex-col items-center gap-2 text-gray-300">
          <span className="text-xs uppercase tracking-widest" style={{ writingMode: 'vertical-rl' }}>Scroll</span>
          <div className="w-px h-8 bg-gray-300 animate-pulse" />
        </div>
      </section>

      {/* Новинки */}
      {featured.length > 0 && (
        <section className="max-w-6xl mx-auto px-6 py-24">
          <div className="flex items-end justify-between mb-12">
            <h2 className="text-2xl font-bold uppercase tracking-widest">Новинки</h2>
            <Link to="/products" className="text-xs uppercase tracking-widest text-gray-400 hover:text-black transition-colors border-b border-gray-300">
              Все товары
            </Link>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {featured.map((product) => (
              <Link key={product.id} to={`/products/${product.id}`} className="group block">
                <div className="bg-gray-50 aspect-square overflow-hidden mb-4">
                  {product.image_url ? (
                    <img
                      src={product.image_url}
                      alt={product.name}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-gray-200 text-xs">Нет фото</div>
                  )}
                </div>
                <p className="text-xs font-semibold uppercase tracking-widest mb-1">{product.name}</p>
                <p className="text-sm text-gray-400">{Number(product.price).toLocaleString('ru-RU')} ₽</p>
              </Link>
            ))}
          </div>
        </section>
      )}

      {/* Баннер */}
      <section className="bg-black text-white py-24 px-6 text-center">
        <p className="text-xs uppercase tracking-[0.4em] text-gray-500 mb-4">Доставка по всей России</p>
        <h2 className="text-4xl md:text-6xl font-black uppercase tracking-tight mb-8">
          No<br />Limits
        </h2>
        <Link
          to="/products"
          className="inline-block border border-white text-white px-12 py-4 text-xs uppercase tracking-[0.3em] hover:bg-white hover:text-black transition-colors"
        >
          Перейти в каталог
        </Link>
      </section>

      {/* Преимущества */}
      <section className="max-w-6xl mx-auto px-6 py-24 grid grid-cols-1 md:grid-cols-3 gap-12">
        {[
          { title: 'Привозим из Европы', desc: 'Оригинальный streetwear и кроссовки напрямую из Европы.' },
          { title: 'Быстрая доставка', desc: 'Отправляем в течение 24 часов.' },
          { title: 'Возврат 14 дней', desc: 'Не подошло — вернём деньги без лишних вопросов.' },
        ].map((item) => (
          <div key={item.title} className="border-t border-gray-200 pt-6">
            <h3 className="text-sm font-bold uppercase tracking-widest mb-3">{item.title}</h3>
            <p className="text-sm text-gray-400 leading-relaxed">{item.desc}</p>
          </div>
        ))}
      </section>
    </div>
  )
}
