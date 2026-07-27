const API_URL = '';  // Use Next.js proxy (relative URLs)

export async function apiFetch(path: string, options: RequestInit = {}) {
  const token = getToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> || {}),
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_URL}${path}`, { ...options, headers });

  if (res.status === 401) {
    // Try refresh
    const refreshToken = getRefreshToken();
    if (refreshToken) {
      const refreshRes = await fetch(`${API_URL}/api/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (refreshRes.ok) {
        const data = await refreshRes.json();
        setToken(data.access_token);
        setRefreshToken(data.refresh_token);
        // Retry original request
        headers['Authorization'] = `Bearer ${data.access_token}`;
        return fetch(`${API_URL}${path}`, { ...options, headers });
      }
    }
    // Refresh failed — clear tokens
    clearTokens();
    window.location.href = '/login';
    throw new Error('Unauthorized');
  }

  return res;
}

export function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('auth_token');
}

export function getRefreshToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('refresh_token');
}

export function setToken(token: string) {
  localStorage.setItem('auth_token', token);
}

export function setRefreshToken(token: string) {
  localStorage.setItem('refresh_token', token);
}

export function clearTokens() {
  localStorage.removeItem('auth_token');
  localStorage.removeItem('refresh_token');
}

export function isLoggedIn(): boolean {
  return !!getToken();
}
