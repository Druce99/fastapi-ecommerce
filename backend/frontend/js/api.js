const BASE_URL = 'http://localhost:8000';

// ─── Token helpers ───────────────────────────────────────────────────────────

const Auth = {
  getAccess: () => localStorage.getItem('access_token'),
  getRefresh: () => localStorage.getItem('refresh_token'),
  set: (access, refresh) => {
    localStorage.setItem('access_token', access);
    if (refresh) localStorage.setItem('refresh_token', refresh);
  },
  clear: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
  },
  isLoggedIn: () => !!localStorage.getItem('access_token'),
  getUser: () => JSON.parse(localStorage.getItem('user') || 'null'),
  setUser: (u) => localStorage.setItem('user', JSON.stringify(u)),
};

// ─── Core fetch ──────────────────────────────────────────────────────────────

async function request(path, options = {}, retry = true) {
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
  const token = Auth.getAccess();
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers });

  if (res.status === 401 && retry) {
    const refreshed = await tryRefresh();
    if (refreshed) return request(path, options, false);
    Auth.clear();
    window.location.href = '/frontend/auth.html';
    return;
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(err.detail || 'Request failed');
  }

  if (res.status === 204) return null;
  return res.json();
}

async function tryRefresh() {
  const refresh = Auth.getRefresh();
  if (!refresh) return false;
  try {
    const res = await fetch(`${BASE_URL}/users/access-token`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refresh }),
    });
    if (!res.ok) return false;
    const data = await res.json();
    Auth.set(data.access_token, null);
    return true;
  } catch {
    return false;
  }
}

// ─── Auth ─────────────────────────────────────────────────────────────────────

const api = {
  auth: {
    async login(email, password) {
      const form = new URLSearchParams({ username: email, password });
      const res = await fetch(`${BASE_URL}/users/token`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: form,
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'Login failed');
      }
      const data = await res.json();
      Auth.set(data.access_token, data.refresh_token);
      return data;
    },

    async register(email, password) {
      return request('/users/', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      });
    },

    logout() {
      Auth.clear();
      window.location.href = '/frontend/auth.html';
    },
  },

  // ─── Products ───────────────────────────────────────────────────────────────

  products: {
    getAll(params = {}) {
      const q = new URLSearchParams(params).toString();
      return request(`/products/?${q}`);
    },
    getById(id) {
      return request(`/products/${id}`);
    },
    getByCategory(categoryId) {
      return request(`/products/category/${categoryId}`);
    },
  },

  // ─── Categories ─────────────────────────────────────────────────────────────

  categories: {
    getAll() {
      return request('/categories/');
    },
  },

  // ─── Cart ───────────────────────────────────────────────────────────────────

  cart: {
    get() {
      return request('/cart/');
    },
    addItem(product_id, quantity = 1) {
      return request('/cart/items', {
        method: 'POST',
        body: JSON.stringify({ product_id, quantity }),
      });
    },
    updateItem(product_id, quantity) {
      return request(`/cart/items/${product_id}`, {
        method: 'PUT',
        body: JSON.stringify({ quantity }),
      });
    },
    removeItem(product_id) {
      return request(`/cart/items/${product_id}`, { method: 'DELETE' });
    },
    clear() {
      return request('/cart/', { method: 'DELETE' });
    },
  },

  // ─── Orders ─────────────────────────────────────────────────────────────────

  orders: {
    checkout() {
      return request('/orders/checkout', { method: 'POST' });
    },
    getAll(page = 1, page_size = 10) {
      return request(`/orders/?page=${page}&page_size=${page_size}`);
    },
    getById(id) {
      return request(`/orders/${id}`);
    },
  },

  // ─── Reviews ────────────────────────────────────────────────────────────────

  reviews: {
    getByProduct(productId) {
      return request(`/products/${productId}/reviews`);
    },
  },
};

// ─── UI helpers ──────────────────────────────────────────────────────────────

function imageUrl(path) {
  if (!path) return null;
  if (path.startsWith('http')) return path;
  return `${BASE_URL}${path}`;
}

function formatPrice(price) {
  return `£${Number(price).toFixed(2)}`;
}

function showToast(msg, type = 'success') {
  const existing = document.getElementById('druce-toast');
  if (existing) existing.remove();

  const toast = document.createElement('div');
  toast.id = 'druce-toast';
  toast.textContent = msg;
  toast.style.cssText = `
    position: fixed; bottom: 2rem; right: 2rem; z-index: 9999;
    padding: 1rem 1.5rem; font-family: inherit; font-size: .875rem;
    font-weight: 700; letter-spacing: .05em; text-transform: uppercase;
    background: ${type === 'error' ? '#FF0000' : '#fff'};
    color: ${type === 'error' ? '#fff' : '#0a0a0a'};
    border: 2px solid ${type === 'error' ? '#FF0000' : '#fff'};
    animation: fadeIn .2s ease;
  `;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 3000);
}

function updateCartBadge() {
  if (!Auth.isLoggedIn()) return;
  api.cart.get().then(cart => {
    const badge = document.getElementById('cart-badge');
    if (badge) {
      badge.textContent = cart.total_quantity || 0;
      badge.style.display = cart.total_quantity > 0 ? 'flex' : 'none';
    }
  }).catch(() => {});
}
