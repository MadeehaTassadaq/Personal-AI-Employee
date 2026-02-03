# Next.js 16 Best Practices & Reference Guide

## App Router Features

### Layouts and Templates
```jsx
// app/layout.js
export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <header>Global Header</header>
        <main>{children}</main>
        <footer>Global Footer</footer>
      </body>
    </html>
  );
}
```

### Route Groups
```jsx
// Group routes without affecting the URL structure
// (dashboard)/analytics/page.js
// (dashboard)/settings/page.js
// Both are accessible as /analytics and /settings
```

### Parallel Routes
```jsx
// app/@analytics/page.js
// app/@settings/page.js
// app/page.js
export default function Page({
  children,
  analytics,
  settings,
}) {
  return (
    <>
      {children}
      {analytics}
      {settings}
    </>
  );
}
```

### Intercepted Routes
```jsx
// app/photos/[id]/page.js
// Intercepts from app/feed/page.js
import { InterceptingModal } from './InterceptingModal';

export default function PhotoPage({ params }) {
  return (
    <>
      <InterceptingModal>
        <Photo id={params.id} />
      </InterceptingModal>
    </>
  );
}
```

## Data Fetching Patterns

### Server Components
```jsx
// app/users/page.js
async function getUsers() {
  const res = await fetch('https://api.example.com/users');
  return res.json();
}

export default async function Page() {
  const users = await getUsers();
  return <UserList users={users} />;
}
```

### Streaming with Suspense
```jsx
// app/dashboard/page.js
import { Suspense } from 'react';
import { Analytics } from './analytics';
import { RecentOrders } from './recent-orders';

export default function Dashboard() {
  return (
    <div>
      <header>Dashboard</header>
      <Suspense fallback={<div>Loading analytics...</div>}>
        <Analytics />
      </Suspense>
      <Suspense fallback={<div>Loading orders...</div>}>
        <RecentOrders />
      </Suspense>
    </div>
  );
}
```

### Caching Strategies
```jsx
// Force dynamic data
import { unstable_noStore as noStore } from 'next/cache';

export async function DynamicComponent() {
  noStore();
  const data = await fetch('...');
  return <div>{data}</div>;
}

// Revalidate data
export async function RevalidatedComponent() {
  const res = await fetch('https://...', {
    next: { revalidate: 3600 } // Revalidate every hour
  });
  return <div>{res}</div>;
}
```

## React Best Practices

### Custom Hooks
```jsx
// hooks/useForm.js
import { useState, useCallback } from 'react';

export function useForm(initialValues, validationSchema) {
  const [values, setValues] = useState(initialValues);
  const [errors, setErrors] = useState({});

  const handleChange = useCallback((name, value) => {
    setValues(prev => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  }, [errors]);

  const validate = useCallback(() => {
    // Validation logic here
  }, [values, validationSchema]);

  return { values, errors, handleChange, validate };
}
```

### Performance Optimization
```jsx
// Use React.memo for components
import { memo } from 'react';

const ExpensiveComponent = memo(({ data, onUpdate }) => {
  return <div>{/* Expensive rendering */}</div>;
});

// Use useMemo for expensive calculations
import { useMemo } from 'react';

function Component({ items }) {
  const expensiveValue = useMemo(() => {
    return items.map(item => heavyComputation(item));
  }, [items]);

  return <div>{expensiveValue}</div>;
}
```

## TypeScript Integration

### Type Definitions
```typescript
// types/user.ts
export interface User {
  id: string;
  name: string;
  email: string;
  createdAt: Date;
}

// app/users/[id]/page.tsx
interface UserPageProps {
  params: { id: string };
}

export default async function UserPage({ params }: UserPageProps) {
  const user = await getUser(params.id);
  return <UserProfile user={user} />;
}
```

### Server Component Types
```typescript
// types/nextjs.ts
import { ReactNode } from 'react';

export interface LayoutProps {
  children: ReactNode;
  modal?: ReactNode;
}

export interface PageProps {
  params: Record<string, string>;
  searchParams: Record<string, string | string[]>;
}
```

## Performance Optimization

### Image Optimization
```jsx
import Image from 'next/image';

// Optimized image
export function OptimizedImage() {
  return (
    <Image
      src="/path/to/image.jpg"
      alt="Description"
      width={300}
      height={200}
      priority={true}
      placeholder="blur"
      blurDataURL="data:image/jpeg;base64,..."
    />
  );
}
```

### Dynamic Imports
```jsx
import dynamic from 'next/dynamic';

// Dynamically import heavy components
const HeavyChart = dynamic(() => import('./Chart'), {
  loading: () => <p>Loading chart...</p>,
  ssr: false // Only render on client
});

// With custom loading component
const InteractiveMap = dynamic(
  () => import('./Map'),
  {
    loading: () => <SkeletonLoader />,
    ssr: false
  }
);
```

## Accessibility Best Practices

### Semantic HTML
```jsx
// Use semantic elements
export function SemanticArticle({ title, content }) {
  return (
    <article>
      <header>
        <h1>{title}</h1>
      </header>
      <main>
        <p>{content}</p>
      </main>
      <footer>
        <time dateTime="2024-01-01">January 1, 2024</time>
      </footer>
    </article>
  );
}
```

### Focus Management
```jsx
// Custom focus hook
import { useEffect } from 'react';

export function useFocusOnMount(ref) {
  useEffect(() => {
    if (ref.current) {
      ref.current.focus();
    }
  }, [ref]);
}

// Focus trap for modals
import { useRef, useEffect } from 'react';

export function FocusTrap({ children, onClose }) {
  const wrapperRef = useRef(null);

  useEffect(() => {
    const focusableElements = wrapperRef.current.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    const handleKeyDown = (e) => {
      if (e.key === 'Tab') {
        if (e.shiftKey && document.activeElement === firstElement) {
          e.preventDefault();
          lastElement.focus();
        } else if (!e.shiftKey && document.activeElement === lastElement) {
          e.preventDefault();
          firstElement.focus();
        }
      }
    };

    firstElement.focus();
    document.addEventListener('keydown', handleKeyDown);

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, []);

  return <div ref={wrapperRef}>{children}</div>;
}
```

## Form Handling

### Client-Side Form with Validation
```jsx
'use client';

import { useForm } from '@/hooks/useForm';
import { userSchema } from '@/schemas/user';

export function UserForm() {
  const { values, errors, handleChange, validate } = useForm(
    { name: '', email: '' },
    userSchema
  );

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (validate()) {
      // Submit form
      await submitForm(values);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        name="name"
        value={values.name}
        onChange={(e) => handleChange('name', e.target.value)}
        aria-invalid={!!errors.name}
      />
      {errors.name && <span>{errors.name}</span>}

      <input
        name="email"
        type="email"
        value={values.email}
        onChange={(e) => handleChange('email', e.target.value)}
        aria-invalid={!!errors.email}
      />
      {errors.email && <span>{errors.email}</span>}

      <button type="submit">Submit</button>
    </form>
  );
}
```

## Error Handling

### Error Boundaries
```jsx
// app/error.js
'use client';

import { useEffect } from 'react';

export default function Error({ error, reset }) {
  useEffect(() => {
    // Log error to an error reporting service
    console.error(error);
  }, [error]);

  return (
    <div>
      <h2>Something went wrong!</h2>
      <button
        onClick={
          () => reset()
        }
      >
        Try again
      </button>
    </div>
  );
}
```

### Global Loading State
```jsx
// app/loading.js
export default function Loading() {
  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-gray-900"></div>
    </div>
  );
}
```

## Security Best Practices

### Input Sanitization
```jsx
import DOMPurify from 'isomorphic-dompurify';

// Sanitize user-generated content
export function SafeHTML({ html }) {
  const sanitizedHTML = DOMPurify.sanitize(html);
  return <div dangerouslySetInnerHTML={{ __html: sanitizedHTML }} />;
}
```

### Environment Variables
```jsx
// Use environment variables for sensitive data
const API_URL = process.env.NEXT_PUBLIC_API_URL;
const API_KEY = process.env.API_KEY; // Not exposed to client

// In API routes
export async function POST(request) {
  const secret = process.env.API_KEY; // Available on server
  // Use secret for API calls
}
```