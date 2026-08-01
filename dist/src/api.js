// All requests go to /api/* which Vite proxies to the FastAPI backend.
const req = (path, opts = {}) =>
  fetch(path, { credentials: 'include', ...opts })

export async function getMe() {
  const r = await req('/api/me')
  return r.ok ? r.json() : null
}

export async function login(username, password) {
  const r = await req('/api/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  })
  if (!r.ok) throw new Error('Invalid credentials')
  return r.json()
}

export async function logout() {
  await req('/api/logout', { method: 'POST' })
}

export async function getOverview() {
  const r = await req('/api/admin/overview')
  if (r.status === 401) throw new Error('unauthorized')
  return r.json()
}

export async function getBenchmark() {
  const r = await req('/api/admin/benchmark')
  if (r.status === 401) throw new Error('unauthorized')
  return r.json()
}

export async function getLogs(filters = {}) {
  const q = new URLSearchParams()
  Object.entries(filters).forEach(([k, v]) => {
    if (v) q.set(k, v)
  })
  q.set('limit', '100')
  const r = await req('/api/admin/logs?' + q.toString())
  if (r.status === 401) throw new Error('unauthorized')
  return r.json()
}

export async function getActivationKeys() {
  const r = await req('/api/admin/activation-keys')
  if (r.status === 401) throw new Error('unauthorized')
  return r.json()
}
