import { Link } from 'react-router-dom'

export default function Footer() {
  return (
    <footer className="bg-black text-white mt-24">
      <div className="max-w-6xl mx-auto px-6 py-16 grid grid-cols-1 md:grid-cols-3 gap-12">
        <div>
          <h2 className="text-xl font-bold tracking-widest uppercase mb-4">DrüceShop</h2>
          <p className="text-gray-400 text-sm leading-relaxed">
            Streetwear и кроссовки из Европы. Доставка по всей России.
          </p>
        </div>
        <div>
          <h3 className="text-xs uppercase tracking-widest text-gray-400 mb-4">Навигация</h3>
          <ul className="flex flex-col gap-3 text-sm">
            <li><Link to="/" className="hover:text-gray-300 transition-colors">Главная</Link></li>
            <li><Link to="/products" className="hover:text-gray-300 transition-colors">Каталог</Link></li>
            <li><Link to="/account" className="hover:text-gray-300 transition-colors">Аккаунт</Link></li>
          </ul>
        </div>
        <div>
          <h3 className="text-xs uppercase tracking-widest text-gray-400 mb-4">Информация</h3>
          <ul className="flex flex-col gap-3 text-sm text-gray-400">
            <li>Доставка: 3–7 дней</li>
            <li>Возврат: 14 дней</li>
            <li>Поддержка: support@druceshop.ru</li>
          </ul>
        </div>
      </div>
      <div className="border-t border-gray-800 py-6 text-center text-xs text-gray-600 tracking-widest uppercase">
        © 2026 DrüceShop. Все права защищены.
      </div>
    </footer>
  )
}
