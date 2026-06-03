import { create } from 'zustand'
import type { Cart } from '../api/cart'

interface CartState {
  cart: Cart | null
  isOpen: boolean
  setCart: (cart: Cart) => void
  openCart: () => void
  closeCart: () => void
  totalItems: () => number
}

export const useCartStore = create<CartState>()((set, get) => ({
  cart: null,
  isOpen: false,
  setCart: (cart) => set({ cart }),
  openCart: () => set({ isOpen: true }),
  closeCart: () => set({ isOpen: false }),
  totalItems: () => get().cart?.total_quantity ?? 0,
}))
