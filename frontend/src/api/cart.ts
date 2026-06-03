import api from './client'
import type { Product } from './products'

export interface CartItem {
  id: number
  quantity: number
  product: Product
}

export interface Cart {
  user_id: number
  items: CartItem[]
  total_quantity: number
  total_price: string
}

export async function getCart(): Promise<Cart> {
  const res = await api.get('/cart/')
  return res.data
}

export async function addToCart(product_id: number, quantity = 1): Promise<CartItem> {
  const res = await api.post('/cart/items', { product_id, quantity })
  return res.data
}

export async function updateCartItem(product_id: number, quantity: number): Promise<CartItem> {
  const res = await api.put(`/cart/items/${product_id}`, { quantity })
  return res.data
}

export async function removeFromCart(product_id: number): Promise<void> {
  await api.delete(`/cart/items/${product_id}`)
}

export async function clearCart(): Promise<void> {
  await api.delete('/cart/')
}
