# Troubleshooting Guide

## Common Issues and Fixes

### Auth Field Mismatch

**Symptom:** Login fails even with correct credentials

**Root Cause:** Signup and login forms use different field names

**Diagnosis:**
```
Signup form: { username, email, password }
Login form: { email, password }  ← WRONG: missing username option
```

**Fix:**
1. Ensure signup collects: `username`, `email`, `password`
2. Ensure login accepts: `identifier` (username OR email), `password`
3. Backend must check identifier against both username and email fields

```python
# Correct backend login
def authenticate(identifier: str, password: str):
    user = session.exec(
        select(User).where(
            (User.username == identifier) | (User.email == identifier)
        )
    ).first()
    if user and verify_password(password, user.hashed_password):
        return user
    return None
```

### Task List Not Showing

**Symptom:** After login, no tasks visible even when they exist

**Possible Causes:**
1. API not called after login
2. User ID not passed to API
3. Component not rendering data
4. Auth token not included in request

**Diagnosis Checklist:**
- [ ] Check network tab for API call
- [ ] Verify user ID is correct
- [ ] Check response data structure
- [ ] Verify component state updates

**Fix Pattern:**
```typescript
// Ensure tasks are fetched on mount
useEffect(() => {
  if (user?.id) {
    fetchTasks(user.id);
  }
}, [user?.id]);
```

### API Works but UI Broken

**Symptom:** API returns correct data, UI doesn't display it

**Common Causes:**
1. State not updated after fetch
2. Wrong property access in render
3. Missing loading/error handling
4. Component not re-rendering

**Fix Pattern:**
```typescript
const [tasks, setTasks] = useState<Task[]>([]);
const [loading, setLoading] = useState(true);
const [error, setError] = useState<string | null>(null);

useEffect(() => {
  async function load() {
    try {
      const data = await fetchTasks(userId);
      setTasks(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }
  load();
}, [userId]);

if (loading) return <LoadingSpinner />;
if (error) return <ErrorMessage error={error} />;
if (tasks.length === 0) return <EmptyState />;
return <TaskList tasks={tasks} />;
```

### UI Not Modern

**Symptom:** Application looks dated or unprofessional

**Indicators:**
- Default browser form styling
- No spacing/padding consistency
- Missing hover/focus states
- No visual hierarchy

**Fix Approach:**
1. Apply consistent spacing scale (Tailwind: `space-y-4`, `p-6`)
2. Add hover states (`hover:bg-gray-100`)
3. Use shadow for depth (`shadow-sm`, `shadow-md`)
4. Apply border radius (`rounded-lg`)
5. Use proper typography scale

**Modern Card Pattern:**
```tsx
<div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 hover:shadow-md transition-shadow">
  <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
  <p className="text-gray-600 mt-2">{description}</p>
</div>
```

### CORS Errors

**Symptom:** Frontend can't reach backend API

**Fix:**
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Database Connection Failed

**Symptom:** API returns 500, logs show connection error

**Checklist:**
- [ ] `DATABASE_URL` environment variable set
- [ ] SSL mode included (`?sslmode=require`)
- [ ] Neon database is active (not suspended)
- [ ] IP not blocked by firewall

### Token Expired

**Symptom:** Requests fail after some time with 401

**Fix:**
1. Implement token refresh logic
2. Handle 401 in API client
3. Redirect to login on refresh failure

```typescript
// API client with token refresh
async function fetchWithAuth(url: string, options: RequestInit = {}) {
  let response = await fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      Authorization: `Bearer ${getToken()}`,
    },
  });

  if (response.status === 401) {
    const refreshed = await refreshToken();
    if (refreshed) {
      response = await fetch(url, {
        ...options,
        headers: {
          ...options.headers,
          Authorization: `Bearer ${getToken()}`,
        },
      });
    } else {
      redirectToLogin();
    }
  }

  return response;
}
```
