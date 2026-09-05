/**
 * AssessIQ API Client
 */

const API_BASE = (import.meta as any).env?.VITE_API_BASE_URL
  ? `${(import.meta as any).env.VITE_API_BASE_URL}/api/v1`
  : '/api/v1';


export class ApiError extends Error {
  status: number;
  details?: any;

  constructor(message: string, status: number, details?: any) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.details = details;
  }
}

export async function apiRequest<T = any>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = localStorage.getItem('assessiq_access_token');
  const headers = new Headers(options.headers || {});

  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;

  let response = await fetch(url, {
    ...options,
    headers,
  });

  // Handle Token Refresh on 401
  if (response.status === 401 && !endpoint.includes('/auth/login') && !endpoint.includes('/auth/refresh')) {
    const refreshToken = localStorage.getItem('assessiq_refresh_token');
    if (refreshToken) {
      try {
        const refreshRes = await fetch(`${API_BASE}/auth/refresh`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: refreshToken }),
        });

        if (refreshRes.ok) {
          const newTokens = await refreshRes.json();
          localStorage.setItem('assessiq_access_token', newTokens.access_token);
          localStorage.setItem('assessiq_refresh_token', newTokens.refresh_token);

          // Retry original request with new token
          headers.set('Authorization', `Bearer ${newTokens.access_token}`);
          response = await fetch(url, { ...options, headers });
        } else {
          // Token expired completely
          localStorage.removeItem('assessiq_access_token');
          localStorage.removeItem('assessiq_refresh_token');
        }
      } catch (err) {
        localStorage.removeItem('assessiq_access_token');
        localStorage.removeItem('assessiq_refresh_token');
      }
    }
  }

  if (!response.ok) {
    let errorMsg = `Request failed (${response.status})`;
    let details;
    try {
      const errData = await response.json();
      errorMsg = errData.detail || errData.error?.message || errData.message || errorMsg;
      details = errData.error?.details || errData;
    } catch (_) {}
    throw new ApiError(errorMsg, response.status, details);
  }

  if (response.status === 204) {
    return null as T;
  }

  return response.json();
}
