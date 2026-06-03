import { Link } from 'react-router-dom'

export default function NotFoundPage() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-6">
      <p className="text-8xl font-black text-gray-100 mb-4">404</p>
      <h1 className="text-2xl font-bold uppercase tracking-widest mb-3">Страница не найдена</h1>
      <p className="text-gray-400 text-sm mb-10">Такой страницы не существует</p>
      <Link
        to="/"
        className="bg-black text-white px-10 py-3 text-xs uppercase tracking-widest hover:bg-gray-800 transition-colors"
      >
        На главную
      </Link>
    </div>
  )
}
