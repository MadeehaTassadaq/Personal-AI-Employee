# Advanced API Client Patterns

## Table of Contents
- [Request Interceptors](#request-interceptors)
- [Retry Logic](#retry-logic)
- [Refresh Token Flow](#refresh-token-flow)
- [Request Cancellation](#request-cancellation)
- [Error Types](#error-types)

---

## Request Interceptors

Add request/response interceptors for logging, analytics, or transformation.

```typescript
type RequestInterceptor = (config: RequestInit) => RequestInit;
type ResponseInterceptor = (response: Response) => Response | Promise<Response>;

class AuthenticatedApiClient {
  private requestInterceptors: RequestInterceptor[] = [];
  private responseInterceptors: ResponseInterceptor[] = [];

  addRequestInterceptor(fn: RequestInterceptor): void {
    this.requestInterceptors.push(fn);
  }

  addResponseInterceptor(fn: ResponseInterceptor): void {
    this.responseInterceptors.push(fn);
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    // Apply request interceptors
    let config = options;
    for (const interceptor of this.requestInterceptors) {
      config = interceptor(config);
    }

    let response = await fetch(`${API_BASE}${endpoint}`, config);

    // Apply response interceptors
    for (const interceptor of this.responseInterceptors) {
      response = await interceptor(response);
    }

    // ... rest of request handling
  }
}

// Usage
apiClient.addRequestInterceptor((config) => {
  console.log('Request:', config);
  return config;
});
```

---

## Retry Logic

Implement exponential backoff for transient failures.

```typescript
interface RetryConfig {
  maxRetries: number;
  baseDelay: number;
  retryableStatuses: number[];
}

const defaultRetryConfig: RetryConfig = {
  maxRetries: 3,
  baseDelay: 1000,
  retryableStatuses: [408, 429, 500, 502, 503, 504],
};

private async requestWithRetry<T>(
  endpoint: string,
  options: RequestInit,
  config: RetryConfig = defaultRetryConfig
): Promise<T> {
  let lastError: Error | null = null;

  for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
    try {
      const response = await fetch(`${API_BASE}${endpoint}`, options);

      if (config.retryableStatuses.includes(response.status) && attempt < config.maxRetries) {
        const delay = config.baseDelay * Math.pow(2, attempt);
        await new Promise(resolve => setTimeout(resolve, delay));
        continue;
      }

      return this.handleResponse<T>(response);
    } catch (error) {
      lastError = error as Error;
      if (attempt < config.maxRetries) {
        const delay = config.baseDelay * Math.pow(2, attempt);
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  }

  throw lastError || new Error('Request failed after retries');
}
```

---

## Refresh Token Flow

Handle token refresh transparently when access token expires.

```typescript
class AuthenticatedApiClient {
  private isRefreshing = false;
  private refreshSubscribers: ((token: string) => void)[] = [];

  private subscribeToRefresh(callback: (token: string) => void): void {
    this.refreshSubscribers.push(callback);
  }

  private notifySubscribers(token: string): void {
    this.refreshSubscribers.forEach(callback => callback(token));
    this.refreshSubscribers = [];
  }

  private async refreshToken(): Promise<string> {
    const refreshToken = localStorage.getItem('refreshToken');
    if (!refreshToken) throw new Error('No refresh token');

    const response = await fetch(`${API_BASE}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refreshToken }),
    });

    if (!response.ok) throw new Error('Refresh failed');

    const { accessToken, refreshToken: newRefreshToken } = await response.json();
    localStorage.setItem('token', accessToken);
    localStorage.setItem('refreshToken', newRefreshToken);

    return accessToken;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    // ... initial request setup

    const response = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });

    if (response.status === 401) {
      if (this.isRefreshing) {
        // Wait for ongoing refresh
        return new Promise<T>((resolve, reject) => {
          this.subscribeToRefresh(async (newToken) => {
            try {
              headers['Authorization'] = `Bearer ${newToken}`;
              const retryResponse = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });
              resolve(await retryResponse.json());
            } catch (error) {
              reject(error);
            }
          });
        });
      }

      this.isRefreshing = true;
      try {
        const newToken = await this.refreshToken();
        this.notifySubscribers(newToken);
        headers['Authorization'] = `Bearer ${newToken}`;
        const retryResponse = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });
        return retryResponse.json();
      } catch {
        localStorage.removeItem('token');
        localStorage.removeItem('refreshToken');
        window.location.href = '/login';
        throw new Error('Session expired');
      } finally {
        this.isRefreshing = false;
      }
    }

    // ... rest of handling
  }
}
```

---

## Request Cancellation

Use AbortController for cancellable requests.

```typescript
class AuthenticatedApiClient {
  private controllers = new Map<string, AbortController>();

  cancelRequest(requestId: string): void {
    const controller = this.controllers.get(requestId);
    if (controller) {
      controller.abort();
      this.controllers.delete(requestId);
    }
  }

  async requestCancellable<T>(
    endpoint: string,
    options: RequestInit = {},
    requestId?: string
  ): Promise<T> {
    const controller = new AbortController();
    const id = requestId || `${endpoint}-${Date.now()}`;

    // Cancel any existing request with same ID
    this.cancelRequest(id);
    this.controllers.set(id, controller);

    try {
      const response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        signal: controller.signal,
      });
      return await this.handleResponse<T>(response);
    } finally {
      this.controllers.delete(id);
    }
  }
}

// Usage - cancel on component unmount
useEffect(() => {
  apiClient.requestCancellable('/tasks', {}, 'tasks-list');
  return () => apiClient.cancelRequest('tasks-list');
}, []);
```

---

## Error Types

Typed error handling for better error management.

```typescript
class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public code?: string,
    public details?: unknown
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

class UnauthorizedError extends ApiError {
  constructor(message = 'Unauthorized') {
    super(message, 401, 'UNAUTHORIZED');
    this.name = 'UnauthorizedError';
  }
}

class ValidationError extends ApiError {
  constructor(message: string, public fields: Record<string, string[]>) {
    super(message, 422, 'VALIDATION_ERROR', fields);
    this.name = 'ValidationError';
  }
}

// In request handler
private async handleResponse<T>(response: Response): Promise<T> {
  if (response.status === 401) {
    throw new UnauthorizedError();
  }

  if (response.status === 422) {
    const body = await response.json();
    throw new ValidationError('Validation failed', body.errors);
  }

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new ApiError(
      body.message || response.statusText,
      response.status,
      body.code,
      body.details
    );
  }

  return response.json();
}

// Usage
try {
  await apiClient.post('/tasks', data);
} catch (error) {
  if (error instanceof ValidationError) {
    console.log('Field errors:', error.fields);
  } else if (error instanceof UnauthorizedError) {
    // Already redirecting in client
  } else if (error instanceof ApiError) {
    console.log(`API error ${error.status}: ${error.message}`);
  }
}
```
