import { useEffect, useState, useCallback, useRef } from 'react'
import { Link } from 'react-router-dom'
import { getProducts, type Product } from '../api/products'
import { useWishlistStore } from '../store/wishlistStore'

type SortOption = 'default' | 'price_asc' | 'price_desc'

const sortLabels: Record<SortOption, string> = {
  default: 'По умолчанию',
  price_asc: 'Сначала дешевле',
  price_desc: 'Сначала дороже',
}

function SortDropdown({ value, onChange }: { value: SortOption; onChange: (v: SortOption) => void }) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex items-center gap-3 border-b border-gray-300 py-1 text-sm bg-transparent w-44 text-left focus:border-black transition-colors"
      >
        <span className="flex-1">{sortLabels[value]}</span>
        <svg width="10" height="6" viewBox="0 0 10 6" fill="none" className={`transition-transform duration-200 ${open ? 'rotate-180' : ''}`}>
          <path d="M1 1l4 4 4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
        </svg>
      </button>
      {open && (
        <div className="absolute top-full left-0 mt-1 w-44 bg-white border border-gray-100 shadow-lg z-20">
          {(Object.keys(sortLabels) as SortOption[]).map((key) => (
            <button
              key={key}
              type="button"
              onClick={() => { onChange(key); setOpen(false) }}
              className={`w-full text-left px-4 py-2.5 text-xs uppercase tracking-wider transition-colors ${
                value === key ? 'bg-black text-white' : 'hover:bg-gray-50 text-gray-700'
              }`}
            >
              {sortLabels[key]}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

function useDebounce<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay)
    return () => clearTimeout(timer)
  }, [value, delay])
  return debounced
}

function pluralize(n: number, one: string, few: string, many: string): string {
  const mod10 = n % 10
  const mod100 = n % 100
  if (mod100 >= 11 && mod100 <= 19) return `${n} ${many}`
  if (mod10 === 1) return `${n} ${one}`
  if (mod10 >= 2 && mod10 <= 4) return `${n} ${few}`
  return `${n} ${many}`
}

export default function ProductsPage() {
  const [products, setProducts] = useState<Product[]>([])
  const [fetching, setFetching] = useState(true)
  const [total, setTotal] = useState(0)

  const [searchInput, setSearchInput] = useState('')
  const [search, setSearch] = useState('')
  const [minPrice, setMinPrice] = useState('')
  const [maxPrice, setMaxPrice] = useState('')
  const [sort, setSort] = useState<SortOption>('default')
  const [inStock, setInStock] = useState(false)
  const [filtersOpen, setFiltersOpen] = useState(false)

  const searchRef = useRef<HTMLInputElement>(null)
  const { toggle, has } = useWishlistStore()

  const debouncedMin = useDebounce(minPrice, 600)
  const debouncedMax = useDebounce(maxPrice, 600)

  const fetchProducts = useCallback(async () => {
    setFetching(true)
    const params: Record<string, string | boolean> = {}
    if (search) params.search = search
    if (debouncedMin) params.min_price = debouncedMin
    if (debouncedMax) params.max_price = debouncedMax
    if (inStock) params.in_stock = true

    const data = await getProducts(1, params)
    let items = [...data.items]
    if (sort === 'price_asc') items.sort((a, b) => parseFloat(a.price) - parseFloat(b.price))
    if (sort === 'price_desc') items.sort((a, b) => parseFloat(b.price) - parseFloat(a.price))
    setProducts(items)
    setTotal(data.total)
    setFetching(false)
  }, [search, debouncedMin, debouncedMax, sort, inStock])

  useEffect(() => { fetchProducts() }, [fetchProducts])

  function handleSearch(e: React.FormEvent) {
    e.preventDefault()
    setSearch(searchInput)
  }

  const hasFilters = search || minPrice || maxPrice || inStock || sort !== 'default'

  function clearFilters() {
    setSearchInput('')
    setSearch('')
    setMinPrice('')
    setMaxPrice('')
    setInStock(false)
    setSort('default')
  }

  return (
    <div className="min-h-screen">

      {/* Шапка страницы */}
      <div className="border-b border-gray-100">
        <div className="max-w-6xl mx-auto px-6 py-10 flex flex-col md:flex-row md:items-end justify-between gap-6">
          <div>
            <h1 className="text-4xl font-bold tracking-tight">Каталог</h1>
            {!fetching && (
              <p className="text-gray-400 text-sm mt-1">
                {pluralize(total, 'товар', 'товара', 'товаров')}
              </p>
            )}
          </div>

          {/* Поиск */}
          <form onSubmit={handleSearch} className="flex items-center gap-0 border-b-2 border-black pb-1 w-full md:w-72">
            <input
              ref={searchRef}
              type="text"
              placeholder="Поиск..."
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              className="flex-1 text-sm outline-none bg-transparent placeholder-gray-400"
            />
            {searchInput && (
              <button type="button" onClick={() => { setSearchInput(''); setSearch('') }} className="text-gray-300 hover:text-black mr-2 text-xs">✕</button>
            )}
            <button type="submit" className="text-black hover:text-gray-500 transition-colors">
              <svg width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <circle cx="11" cy="11" r="8" />
                <path d="m21 21-4.35-4.35" />
              </svg>
            </button>
          </form>
        </div>
      </div>

      {/* Фильтры — выпадающие */}
      <div className="border-b border-gray-100 bg-white sticky top-16 z-30">
        <div className="max-w-6xl mx-auto px-6">
          <div className="flex items-center gap-6 py-3">
            <button
              onClick={() => setFiltersOpen(!filtersOpen)}
              className={`flex items-center gap-2 text-xs font-semibold uppercase tracking-widest transition-colors ${filtersOpen ? 'text-black' : 'text-gray-400 hover:text-black'}`}
            >
              <svg width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <line x1="4" y1="6" x2="20" y2="6" />
                <line x1="8" y1="12" x2="20" y2="12" />
                <line x1="12" y1="18" x2="20" y2="18" />
              </svg>
              Фильтры
              {hasFilters && <span className="w-1.5 h-1.5 rounded-full bg-black" />}
            </button>

            {/* Быстрые теги активных фильтров */}
            <div className="flex items-center gap-2 flex-wrap">
              {search && (
                <span className="bg-black text-white text-xs px-3 py-1 flex items-center gap-2">
                  «{search}»
                  <button onClick={() => { setSearch(''); setSearchInput('') }} className="hover:opacity-70">✕</button>
                </span>
              )}
              {(minPrice || maxPrice) && (
                <span className="bg-black text-white text-xs px-3 py-1 flex items-center gap-2">
                  {minPrice && `от ${minPrice} ₽`}{minPrice && maxPrice && ' '}{maxPrice && `до ${maxPrice} ₽`}
                  <button onClick={() => { setMinPrice(''); setMaxPrice('') }} className="hover:opacity-70">✕</button>
                </span>
              )}
              {inStock && (
                <span className="bg-black text-white text-xs px-3 py-1 flex items-center gap-2">
                  В наличии
                  <button onClick={() => setInStock(false)} className="hover:opacity-70">✕</button>
                </span>
              )}
              {sort !== 'default' && (
                <span className="bg-black text-white text-xs px-3 py-1 flex items-center gap-2">
                  {sort === 'price_asc' ? 'Дешевле' : 'Дороже'}
                  <button onClick={() => setSort('default')} className="hover:opacity-70">✕</button>
                </span>
              )}
              {hasFilters && (
                <button onClick={clearFilters} className="text-xs text-gray-400 hover:text-black underline underline-offset-2 transition-colors">
                  Сбросить всё
                </button>
              )}
            </div>
          </div>

          {/* Выпадающая панель фильтров */}
          <div className={`transition-all duration-300 ${filtersOpen ? 'max-h-60 pb-5 overflow-visible' : 'max-h-0 overflow-hidden'}`}>
            <div className="flex flex-wrap gap-6 pt-3 border-t border-gray-100">
              <div className="flex flex-col gap-1">
                <label className="text-xs font-semibold uppercase tracking-widest text-gray-400">Цена</label>
                <div className="flex items-center gap-2">
                  <input type="number" placeholder="от" value={minPrice} onChange={(e) => setMinPrice(e.target.value)}
                    className="w-24 border-b border-gray-300 py-1 text-sm outline-none focus:border-black bg-transparent" />
                  <span className="text-gray-300">—</span>
                  <input type="number" placeholder="до" value={maxPrice} onChange={(e) => setMaxPrice(e.target.value)}
                    className="w-24 border-b border-gray-300 py-1 text-sm outline-none focus:border-black bg-transparent" />
                </div>
              </div>

              <div className="flex flex-col gap-1 relative">
                <label className="text-xs font-semibold uppercase tracking-widest text-gray-400">Сортировка</label>
                <div className="relative">
                  <SortDropdown value={sort} onChange={setSort} />
                </div>
              </div>

              <div className="flex flex-col gap-1">
                <label className="text-xs font-semibold uppercase tracking-widest text-gray-400">Наличие</label>
                <label className="flex items-center gap-2 text-sm cursor-pointer mt-1">
                  <input type="checkbox" checked={inStock} onChange={(e) => setInStock(e.target.checked)} className="accent-black w-4 h-4" />
                  Только в наличии
                </label>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Сетка товаров */}
      <div className="max-w-6xl mx-auto px-6 py-10">
        <div className={`transition-opacity duration-200 ${fetching ? 'opacity-30 pointer-events-none' : 'opacity-100'}`}>
          {products.length === 0 && !fetching ? (
            <div className="flex flex-col items-center justify-center py-32 gap-6">
              <p className="text-7xl font-black text-gray-100">∅</p>
              <p className="text-gray-400 text-sm uppercase tracking-widest">Ничего не найдено</p>
              <button onClick={clearFilters} className="text-xs font-semibold uppercase tracking-widest border-b-2 border-black pb-0.5 hover:text-gray-500 transition-colors">
                Сбросить фильтры
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-x-5 gap-y-12">
              {products.map((product) => (
                <div key={product.id} className="group">
                  <Link to={`/products/${product.id}`} className="block relative bg-gray-50 aspect-square overflow-hidden mb-4">
                    {product.image_url ? (
                      <img src={product.image_url} alt={product.name}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-gray-200 text-xs uppercase tracking-widest">
                        Нет фото
                      </div>
                    )}
                    {product.stock === 0 && (
                      <div className="absolute inset-0 bg-white/80 flex items-center justify-center">
                        <span className="text-xs uppercase tracking-widest text-gray-400 font-semibold">Нет в наличии</span>
                      </div>
                    )}
                    {/* Hover оверлей */}
                    <div className="absolute inset-x-0 bottom-0 bg-black text-white text-center py-3 text-xs font-semibold uppercase tracking-widest translate-y-full group-hover:translate-y-0 transition-transform duration-300">
                      Смотреть
                    </div>
                    {/* Избранное */}
                    <button
                      onClick={(e) => { e.preventDefault(); toggle(product.id) }}
                      className="absolute top-3 right-3 w-8 h-8 bg-white flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity shadow-sm"
                    >
                      <svg width="14" height="14" viewBox="0 0 24 24" fill={has(product.id) ? '#000' : 'none'} stroke="#000" strokeWidth="2">
                        <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
                      </svg>
                    </button>
                  </Link>
                  <p className="text-xs font-bold uppercase tracking-widest mb-1 group-hover:text-gray-500 transition-colors leading-tight">
                    {product.name}
                  </p>
                  <p className="text-sm text-gray-500 font-medium">{Number(product.price).toLocaleString('ru-RU')} ₽</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
