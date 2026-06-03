import api from "./client";

export interface Product {
  id: number;
  name: string;
  description: string;
  price: string;
  stock: number;
  image_url: string | null;
  category_id: number;
}

export interface ProductList {
  items: Product[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export async function getProducts(
  page = 1,
  filters: Record<string, string | boolean> = {}
): Promise<ProductList> {
  const response = await api.get('/products/', {
    params: { page, page_size: 20, ...filters },
  })
  return response.data
}
