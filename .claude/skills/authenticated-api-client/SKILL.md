---
name: authenticated-api-client
description: "Inject auth headers automatically into API requests, handle 401 globally, and reduce code duplication. Use when creating or refactoring frontend API clients that need (1) automatic Authorization header injection from localStorage, (2) global 401 handling with redirect to login, (3) typed fetch wrapper reducing boilerplate. Triggers include requests for authenticated fetch, API client setup, token-based auth, or handling expired sessions."
---

# Authenticated API Client

Create a typed, reusable API client that automatically handles authentication headers and 401 responses.

## Quick Start

```typescript
// src/services/api-client.ts
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class AuthenticatedApiClient {
  private getToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('token');
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const token = this.getToken();

    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers,
    });

    if (response.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
      throw new Error('Unauthorized');
    }

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return response.json();
  }

  get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET' });
  }

  post<T>(endpoint: string, data: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  put<T>(endpoint: string, data: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }
}

export const apiClient = new AuthenticatedApiClient();
```

## Usage Pattern

```typescript
// src/services/tasks.ts
import { apiClient } from './api-client';

interface Task {
  id: string;
  title: string;
  completed: boolean;
}

export const taskService = {
  getAll: () => apiClient.get<Task[]>('/tasks'),
  create: (data: Omit<Task, 'id'>) => apiClient.post<Task>('/tasks', data),
  update: (id: string, data: Partial<Task>) => apiClient.put<Task>(`/tasks/${id}`, data),
  delete: (id: string) => apiClient.delete<void>(`/tasks/${id}`),
};
```

## Key Features

| Feature | Implementation |
|---------|---------------|
| Token storage | `localStorage.getItem('token')` |
| Header injection | `Authorization: Bearer ${token}` |
| 401 handling | Clear token + redirect to `/login` |
| Type safety | Generic `<T>` return types |

## Customization Points

- **Token key**: Change `'token'` to match your storage key
- **Login route**: Change `'/login'` to your auth route
- **Base URL**: Configure via environment variable
- **Error handling**: Extend for custom error types

## References

For advanced patterns (interceptors, retry logic, refresh tokens), see [references/advanced-patterns.md](references/advanced-patterns.md).
