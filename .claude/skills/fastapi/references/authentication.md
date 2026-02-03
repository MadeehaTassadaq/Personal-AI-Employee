# FastAPI Authentication

## Table of Contents
- [JWT Authentication](#jwt-authentication)
- [OAuth2 with Password Flow](#oauth2-with-password-flow)
- [API Key Authentication](#api-key-authentication)
- [Session-Based Authentication](#session-based-authentication)
- [Security Best Practices](#security-best-practices)

## JWT Authentication

### Installation
```bash
pip install python-jose[cryptography] passlib[bcrypt] python-multipart
```

### Password Hashing
```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)
```

### JWT Token Creation
```python
from datetime import datetime, timedelta
from jose import JWTError, jwt

SECRET_KEY = "your-secret-key-here"  # Use environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
```

### Token Verification
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Validate token and return current user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Get user from database
    user = get_user(username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
):
    """Ensure user is active."""
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
```

## OAuth2 with Password Flow

### User Model
```python
from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None

class UserInDB(User):
    hashed_password: str
```

### Login Endpoint
```python
from fastapi.security import OAuth2PasswordRequestForm

@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """User login endpoint."""
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

def authenticate_user(username: str, password: str):
    """Authenticate user credentials."""
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user
```

### Protected Routes
```python
@app.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Get current user info."""
    return current_user

@app.get("/items")
async def read_own_items(current_user: User = Depends(get_current_active_user)):
    """Get current user's items."""
    return [{"item_id": "Foo", "owner": current_user.username}]
```

## API Key Authentication

### Header-Based API Key
```python
from fastapi import Security, HTTPException
from fastapi.security.api_key import APIKeyHeader

API_KEY = "your-api-key-here"
API_KEY_NAME = "X-API-Key"

api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(api_key: str = Security(api_key_header)):
    """Validate API key from header."""
    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate API Key"
        )
    return api_key

@app.get("/secure-data")
async def get_secure_data(api_key: str = Depends(get_api_key)):
    """Protected endpoint with API key."""
    return {"data": "This is secure data"}
```

### Query Parameter API Key
```python
from fastapi.security.api_key import APIKeyQuery

api_key_query = APIKeyQuery(name=API_KEY_NAME, auto_error=False)

async def get_api_key_query(api_key: str = Security(api_key_query)):
    """Validate API key from query parameter."""
    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate API Key"
        )
    return api_key
```

### Cookie-Based API Key
```python
from fastapi.security.api_key import APIKeyCookie

api_key_cookie = APIKeyCookie(name=API_KEY_NAME, auto_error=False)

async def get_api_key_cookie(api_key: str = Security(api_key_cookie)):
    """Validate API key from cookie."""
    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate API Key"
        )
    return api_key
```

## Session-Based Authentication

### Session Management
```python
from fastapi import Cookie, Response
import secrets

# In-memory session store (use Redis in production)
sessions = {}

def create_session(user_id: str) -> str:
    """Create new session."""
    session_id = secrets.token_urlsafe(32)
    sessions[session_id] = {"user_id": user_id}
    return session_id

def get_session(session_id: str) -> dict | None:
    """Get session data."""
    return sessions.get(session_id)

def delete_session(session_id: str):
    """Delete session."""
    if session_id in sessions:
        del sessions[session_id]
```

### Login/Logout with Sessions
```python
@app.post("/login")
async def login(response: Response, form_data: OAuth2PasswordRequestForm = Depends()):
    """Login and create session."""
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    session_id = create_session(user.username)
    response.set_cookie(key="session_id", value=session_id, httponly=True)
    return {"message": "Logged in successfully"}

@app.post("/logout")
async def logout(response: Response, session_id: str = Cookie(None)):
    """Logout and destroy session."""
    if session_id:
        delete_session(session_id)
    response.delete_cookie(key="session_id")
    return {"message": "Logged out successfully"}
```

### Session-Protected Routes
```python
async def get_current_user_session(session_id: str = Cookie(None)):
    """Get current user from session."""
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    session_data = get_session(session_id)
    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session"
        )

    user = get_user(session_data["user_id"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    return user

@app.get("/profile")
async def read_profile(current_user: User = Depends(get_current_user_session)):
    """Get user profile."""
    return current_user
```

## Security Best Practices

### 1. Environment Variables
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"

settings = Settings()
```

### 2. HTTPS Only
```python
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

# Redirect HTTP to HTTPS in production
if not DEBUG:
    app.add_middleware(HTTPSRedirectMiddleware)
```

### 3. CORS Configuration
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specific origins
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # Specific methods
    allow_headers=["Authorization", "Content-Type"],
)
```

### 4. Rate Limiting
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)

@app.post("/login")
@limiter.limit("5/minute")
async def login(request: Request):
    """Login with rate limiting."""
    pass
```

### 5. Password Requirements
```python
import re

def validate_password(password: str) -> bool:
    """Validate password strength."""
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False
    return True
```

### 6. Token Refresh
```python
def create_refresh_token(data: dict):
    """Create refresh token with longer expiry."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=7)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@app.post("/refresh")
async def refresh_token(refresh_token: str):
    """Refresh access token."""
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")

        username = payload.get("sub")
        new_access_token = create_access_token(data={"sub": username})
        return {"access_token": new_access_token, "token_type": "bearer"}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
```

### Security Checklist
- ✓ Use HTTPS in production
- ✓ Store secrets in environment variables
- ✓ Hash passwords with bcrypt
- ✓ Implement rate limiting
- ✓ Validate input thoroughly
- ✓ Use secure session storage (Redis)
- ✓ Set appropriate CORS policies
- ✓ Implement token refresh mechanism
- ✓ Log authentication attempts
- ✓ Use httponly cookies for sessions
- ✓ Implement account lockout after failed attempts
- ✓ Regular security audits
