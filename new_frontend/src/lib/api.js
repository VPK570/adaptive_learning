const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

async function request(path, options = {}) {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded', ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const detail = (await res.json().catch(() => ({}))).detail || `Request failed (${res.status})`;
    throw new Error(detail);
  }
  return res.json();
}

export async function login(email, password) {
  const body = new URLSearchParams({ username: email, password });
  return request('/auth/login', {
    method: 'POST',
    body: body.toString(),
  });
}

export async function register(email, password, role = 'student') {
  return request('/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password, role }),
  });
}
