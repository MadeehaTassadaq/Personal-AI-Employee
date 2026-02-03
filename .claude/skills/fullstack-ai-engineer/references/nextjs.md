# Next.js 16+ Reference

## Table of Contents
- [App Router Structure](#app-router-structure)
- [Page Components](#page-components)
- [Client Components](#client-components)
- [API Integration](#api-integration)
- [Middleware](#middleware)
- [Styling](#styling)

## App Router Structure

```
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx      # Root layout (providers, global styles)
│   │   ├── page.tsx        # Home page (/)
│   │   ├── login/
│   │   │   └── page.tsx    # Login page (/login)
│   │   ├── register/
│   │   │   └── page.tsx    # Register page (/register)
│   │   └── tasks/
│   │       └── page.tsx    # Tasks page (/tasks)
│   ├── components/
│   │   ├── Task.tsx
│   │   ├── CreateTask.tsx
│   │   └── ClientWrapper.tsx
│   ├── context/
│   │   └── AuthContext.tsx
│   ├── lib/
│   │   ├── api.ts          # API base URL config
│   │   └── api-client.ts   # Authenticated fetch
│   ├── services/
│   │   ├── auth.ts         # Auth API calls
│   │   └── tasks.ts        # Task API calls
│   └── types/
│       └── task.ts         # TypeScript types
├── middleware.ts           # Route protection
└── package.json
```

## Page Components

### Root Layout
```typescript
// app/layout.tsx
import { AuthProvider } from '@/context/AuthContext';
import './globals.css';

export const metadata = {
  title: 'Todo App',
  description: 'Task management application',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}
```

### Login Page
```typescript
// app/login/page.tsx
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import Link from 'next/link';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await login(email, password);
      router.push('/tasks');
    } catch (err: any) {
      setError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center">
      <form onSubmit={handleSubmit} className="w-full max-w-md p-8 space-y-4">
        <h1 className="text-2xl font-bold text-center">Login</h1>

        {error && (
          <div className="bg-red-100 text-red-700 p-3 rounded">{error}</div>
        )}

        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full p-3 border rounded"
          required
        />

        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full p-3 border rounded"
          required
        />

        <button
          type="submit"
          disabled={loading}
          className="w-full p-3 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
        >
          {loading ? 'Logging in...' : 'Login'}
        </button>

        <p className="text-center">
          Don't have an account? <Link href="/register" className="text-blue-500">Register</Link>
        </p>
      </form>
    </div>
  );
}
```

### Tasks Page
```typescript
// app/tasks/page.tsx
'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/context/AuthContext';
import { getTasks, createTask, deleteTask, updateTask } from '@/services/tasks';
import { Task as TaskType } from '@/types/task';
import Task from '@/components/Task';
import CreateTask from '@/components/CreateTask';

export default function TasksPage() {
  const [tasks, setTasks] = useState<TaskType[]>([]);
  const [loading, setLoading] = useState(true);
  const { isAuthenticated } = useAuth();

  useEffect(() => {
    if (isAuthenticated) {
      loadTasks();
    }
  }, [isAuthenticated]);

  const loadTasks = async () => {
    try {
      const data = await getTasks();
      setTasks(data);
    } catch (error) {
      console.error('Failed to load tasks:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (title: string, description?: string) => {
    const newTask = await createTask({ title, description });
    setTasks([...tasks, newTask]);
  };

  const handleDelete = async (id: string) => {
    await deleteTask(id);
    setTasks(tasks.filter(t => t.id !== id));
  };

  const handleUpdate = async (id: string, updates: Partial<TaskType>) => {
    const updated = await updateTask(id, updates);
    setTasks(tasks.map(t => t.id === id ? updated : t));
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">My Tasks</h1>
      <CreateTask onCreate={handleCreate} />
      <div className="space-y-4 mt-4">
        {tasks.map(task => (
          <Task
            key={task.id}
            task={task}
            onDelete={handleDelete}
            onUpdate={handleUpdate}
          />
        ))}
      </div>
    </div>
  );
}
```

## Client Components

### Task Component
```typescript
// components/Task.tsx
'use client';

import { Task as TaskType } from '@/types/task';

interface TaskProps {
  task: TaskType;
  onDelete: (id: string) => void;
  onUpdate: (id: string, updates: Partial<TaskType>) => void;
}

export default function Task({ task, onDelete, onUpdate }: TaskProps) {
  const toggleStatus = () => {
    const newStatus = task.status === 'completed' ? 'pending' : 'completed';
    onUpdate(task.id, { status: newStatus });
  };

  return (
    <div className="flex items-center justify-between p-4 border rounded">
      <div className="flex items-center gap-3">
        <input
          type="checkbox"
          checked={task.status === 'completed'}
          onChange={toggleStatus}
          className="w-5 h-5"
        />
        <div>
          <h3 className={`font-medium ${task.status === 'completed' ? 'line-through text-gray-500' : ''}`}>
            {task.title}
          </h3>
          {task.description && (
            <p className="text-sm text-gray-600">{task.description}</p>
          )}
        </div>
      </div>
      <button
        onClick={() => onDelete(task.id)}
        className="text-red-500 hover:text-red-700"
      >
        Delete
      </button>
    </div>
  );
}
```

### Create Task Component
```typescript
// components/CreateTask.tsx
'use client';

import { useState } from 'react';

interface CreateTaskProps {
  onCreate: (title: string, description?: string) => Promise<void>;
}

export default function CreateTask({ onCreate }: CreateTaskProps) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;

    setLoading(true);
    try {
      await onCreate(title, description || undefined);
      setTitle('');
      setDescription('');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <input
        type="text"
        placeholder="Task title"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        className="w-full p-2 border rounded"
        required
      />
      <input
        type="text"
        placeholder="Description (optional)"
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        className="w-full p-2 border rounded"
      />
      <button
        type="submit"
        disabled={loading}
        className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:opacity-50"
      >
        {loading ? 'Adding...' : 'Add Task'}
      </button>
    </form>
  );
}
```

## API Integration

### API Client
```typescript
// lib/api-client.ts
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const authFetch = async (
  endpoint: string,
  options: RequestInit = {}
): Promise<Response> => {
  const token = localStorage.getItem('token');

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` }),
      ...options.headers,
    },
  });

  if (response.status === 401) {
    localStorage.removeItem('token');
    window.location.href = '/login';
    throw new Error('Unauthorized');
  }

  return response;
};
```

### Task Service
```typescript
// services/tasks.ts
import { authFetch } from '@/lib/api-client';
import { Task, TaskCreate, TaskUpdate } from '@/types/task';

export const getTasks = async (): Promise<Task[]> => {
  const response = await authFetch('/api/tasks/');
  if (!response.ok) throw new Error('Failed to fetch tasks');
  return response.json();
};

export const createTask = async (task: TaskCreate): Promise<Task> => {
  const response = await authFetch('/api/tasks/', {
    method: 'POST',
    body: JSON.stringify(task),
  });
  if (!response.ok) throw new Error('Failed to create task');
  return response.json();
};

export const updateTask = async (id: string, updates: TaskUpdate): Promise<Task> => {
  const response = await authFetch(`/api/tasks/${id}`, {
    method: 'PUT',
    body: JSON.stringify(updates),
  });
  if (!response.ok) throw new Error('Failed to update task');
  return response.json();
};

export const deleteTask = async (id: string): Promise<void> => {
  const response = await authFetch(`/api/tasks/${id}`, { method: 'DELETE' });
  if (!response.ok) throw new Error('Failed to delete task');
};
```

## Middleware

```typescript
// middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

const publicPaths = ['/', '/login', '/register'];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Allow public paths
  if (publicPaths.includes(pathname)) {
    return NextResponse.next();
  }

  // Check for auth token (client-side check, server validates JWT)
  // Note: For proper SSR auth, use cookies instead of localStorage
  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
};
```

## Styling

### Tailwind CSS Setup
```javascript
// tailwind.config.js
module.exports = {
  content: [
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {},
  },
  plugins: [],
};
```

### Global Styles
```css
/* app/globals.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  @apply bg-gray-50 text-gray-900;
}
```

## TypeScript Types

```typescript
// types/task.ts
export interface Task {
  id: string;
  user_id: string;
  title: string;
  description?: string;
  status: 'pending' | 'in_progress' | 'completed';
  priority?: 'low' | 'medium' | 'high';
  due_date?: string;
  created_at: string;
  updated_at: string;
}

export interface TaskCreate {
  title: string;
  description?: string;
  priority?: string;
  due_date?: string;
}

export interface TaskUpdate {
  title?: string;
  description?: string;
  status?: string;
  priority?: string;
  due_date?: string;
}
```
