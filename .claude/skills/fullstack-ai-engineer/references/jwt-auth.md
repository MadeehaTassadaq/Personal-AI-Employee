# JWT Authentication Reference

## Table of Contents
- [Password Hashing](#password-hashing)
- [Token Generation](#token-generation)
- [Auth Middleware](#auth-middleware)
- [Protected Routes](#protected-routes)
- [Frontend Integration](#frontend-integration)

## Password Hashing

```python
import bcrypt

def hash_password(password: str) -> str:
    """Hash password using bcrypt with auto-generated salt."""
    return bcrypt.hashpw(
        password.encode('utf-8'),
        bcrypt.gensalt()
    ).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against stored hash."""
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )
```

## Token Generation

```python
from jose import jwt, JWTError
from datetime import datetime, timedelta
import os

SECRET_KEY = os.getenv("BETTER_AUTH_SECRET")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(user_id: str, email: str) -> str:
    """Create JWT access token with user claims."""
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "sub": email,
        "user_id": user_id,
        "exp": expire
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    """Decode and validate JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
```

## Auth Middleware

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session
from jose import jwt, JWTError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session)
) -> User:
    """Extract and validate current user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = session.get(User, UUID(user_id))
    if user is None:
        raise credentials_exception

    return user
```

## Protected Routes

```python
from fastapi import APIRouter, Depends
from ..middleware.auth import get_current_user
from ..models.user import User

router = APIRouter()

@router.get("/protected")
def protected_route(current_user: User = Depends(get_current_user)):
    """Route that requires authentication."""
    return {"user_id": str(current_user.id), "email": current_user.email}

@router.get("/tasks")
def get_user_tasks(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get tasks for authenticated user only."""
    tasks = session.query(Task).filter(Task.user_id == current_user.id).all()
    return tasks
```

## Frontend Integration

### Token Storage
```typescript
// After successful login
const login = async (email: string, password: string) => {
  const response = await fetch(`${API_URL}/api/auth/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({ username: email, password }),
  });

  if (!response.ok) throw new Error('Login failed');

  const data = await response.json();
  localStorage.setItem('token', data.access_token);
  localStorage.setItem('user_id', data.user_id);
  return data;
};
```

### Authenticated Requests
```typescript
const authFetch = async (url: string, options: RequestInit = {}) => {
  const token = localStorage.getItem('token');

  if (!token) {
    window.location.href = '/login';
    throw new Error('No token');
  }

  const response = await fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });

  if (response.status === 401) {
    localStorage.removeItem('token');
    window.location.href = '/login';
  }

  return response;
};
```

### Auth Context
```typescript
// context/AuthContext.tsx
import { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface AuthContextType {
  token: string | null;
  userId: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [token, setToken] = useState<string | null>(null);
  const [userId, setUserId] = useState<string | null>(null);

  useEffect(() => {
    const storedToken = localStorage.getItem('token');
    const storedUserId = localStorage.getItem('user_id');
    if (storedToken) setToken(storedToken);
    if (storedUserId) setUserId(storedUserId);
  }, []);

  const login = async (email: string, password: string) => {
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/auth/token`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ username: email, password }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Login failed');
    }

    const data = await response.json();
    localStorage.setItem('token', data.access_token);
    localStorage.setItem('user_id', data.user_id);
    setToken(data.access_token);
    setUserId(data.user_id);
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user_id');
    setToken(null);
    setUserId(null);
  };

  return (
    <AuthContext.Provider value={{
      token,
      userId,
      login,
      logout,
      isAuthenticated: !!token
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
};
```

## Security Best Practices

1. **Token Expiry**: Keep access tokens short-lived (15-30 minutes)
2. **HTTPS Only**: Never transmit tokens over HTTP
3. **Secure Storage**: Use HttpOnly cookies for production (localStorage for dev)
4. **Secret Rotation**: Rotate JWT secrets periodically
5. **Token Invalidation**: Implement token blacklist for logout
