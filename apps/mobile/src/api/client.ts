import AsyncStorage from '@react-native-async-storage/async-storage';

const API_URL = process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:8000/api/v1';

const ACCESS_KEY = 'fashionxp.access';
const REFRESH_KEY = 'fashionxp.refresh';

export const tokenStore = {
  async getAccess() {
    return AsyncStorage.getItem(ACCESS_KEY);
  },
  async getRefresh() {
    return AsyncStorage.getItem(REFRESH_KEY);
  },
  async save(access: string, refresh: string) {
    await AsyncStorage.multiSet([
      [ACCESS_KEY, access],
      [REFRESH_KEY, refresh],
    ]);
  },
  async clear() {
    await AsyncStorage.multiRemove([ACCESS_KEY, REFRESH_KEY]);
  },
};

export class ApiError extends Error {
  code: string;
  status: number;
  details?: Record<string, unknown>;

  constructor(message: string, code: string, status: number, details?: Record<string, unknown>) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
    this.status = status;
    this.details = details;
  }
}

interface Envelope<T = unknown> {
  success: boolean;
  data?: T;
  error?: { code: string; message: string; details?: Record<string, unknown> };
}

let refreshing: Promise<boolean> | null = null;

async function tryRefresh(): Promise<boolean> {
  if (!refreshing) {
    refreshing = (async () => {
      const refresh = await tokenStore.getRefresh();
      if (!refresh) return false;
      try {
        const response = await fetch(`${API_URL}/auth/refresh`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh }),
        });
        if (!response.ok) return false;
        const body = (await response.json()) as { access: string; refresh?: string };
        await AsyncStorage.setItem(ACCESS_KEY, body.access);
        if (body.refresh) await AsyncStorage.setItem(REFRESH_KEY, body.refresh);
        return true;
      } catch {
        return false;
      } finally {
        setTimeout(() => (refreshing = null), 0);
      }
    })();
  }
  return refreshing;
}

async function request<T>(path: string, init: RequestInit & { retry?: boolean } = {}): Promise<T> {
  const access = await tokenStore.getAccess();
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      ...init,
      headers: {
        ...(init.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }),
        ...(access ? { Authorization: `Bearer ${access}` } : {}),
        ...init.headers,
      },
    });
  } catch {
    throw new ApiError('Network unavailable. Check your connection.', 'network_error', 0);
  }

  // Silent access-token refresh on expiry.
  if (response.status === 401 && !path.startsWith('/auth/') && init.retry !== false) {
    if (await tryRefresh()) {
      return request<T>(path, { ...init, retry: false });
    }
    await tokenStore.clear();
  }

  if (response.status === 204) return undefined as T;

  let body: Envelope<T>;
  try {
    body = (await response.json()) as Envelope<T>;
  } catch {
    throw new ApiError('Unexpected server response.', 'bad_response', response.status);
  }

  if (!response.ok || body.success === false) {
    throw new ApiError(
      body.error?.message ?? 'Request failed.',
      body.error?.code ?? 'error',
      response.status,
      body.error?.details,
    );
  }
  return body.data as T;
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, data?: unknown) =>
    request<T>(path, {
      method: 'POST',
      body: data instanceof FormData ? data : data != null ? JSON.stringify(data) : undefined,
    }),
  put: <T>(path: string, data?: unknown) =>
    request<T>(path, { method: 'PUT', body: data != null ? JSON.stringify(data) : undefined }),
  patch: <T>(path: string, data?: unknown) =>
    request<T>(path, { method: 'PATCH', body: data != null ? JSON.stringify(data) : undefined }),
  delete: <T>(path: string) => request<T>(path, { method: 'DELETE' }),
};
