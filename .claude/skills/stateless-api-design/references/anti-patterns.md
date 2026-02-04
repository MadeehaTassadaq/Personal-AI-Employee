# Stateless API Anti-Patterns

## Table of Contents

1. [Detection Strategies](#detection-strategies)
2. [Global State Anti-Patterns](#global-state-anti-patterns)
3. [Session Management Anti-Patterns](#session-management-anti-patterns)
4. [Caching Anti-Patterns](#caching-anti-patterns)
5. [Class-Level State Anti-Patterns](#class-level-state-anti-patterns)
6. [Framework-Specific Violations](#framework-specific-violations)
7. [Remediation Patterns](#remediation-patterns)

---

## Detection Strategies

### Code Scanning Patterns

Look for these patterns when reviewing code:

```python
# Pattern 1: Module-level dictionaries
users = {}          # ALERT: Potential stateful storage
sessions = {}       # ALERT: Potential session storage
cache = {}          # ALERT: Review caching strategy

# Pattern 2: Global collections
active_connections = []   # ALERT: Connection tracking
pending_requests = set()  # ALERT: Request queuing

# Pattern 3: Class attributes
class Service:
    current_user = None   # ALERT: Shared mutable state

# Pattern 4: Singleton state
_instance = None          # ALERT: Singleton with state
```

### Grep Patterns for Detection

```bash
# Find module-level dictionaries
grep -rn "^[a-z_]*\s*=\s*{}" --include="*.py"

# Find module-level lists
grep -rn "^[a-z_]*\s*=\s*\[\]" --include="*.py"

# Find class attributes
grep -rn "^\s*[a-z_]*\s*=\s*None\s*$" --include="*.py"

# Find global keyword usage
grep -rn "^\s*global\s+" --include="*.py"
```

---

## Global State Anti-Patterns

### Anti-Pattern 1: User Registry

```python
# VIOLATION
active_users = {}

@app.post("/login")
async def login(credentials: Credentials):
    user = authenticate(credentials)
    active_users[user.id] = {
        "logged_in_at": datetime.now(),
        "permissions": user.permissions
    }
    return {"user_id": user.id}

@app.get("/users/{user_id}/status")
async def get_status(user_id: str):
    if user_id not in active_users:  # Lost on restart!
        raise HTTPException(401, "Not logged in")
    return active_users[user_id]
```

**Why it fails:**
- Data lost on server restart
- Different servers have different views
- Memory grows unbounded with users

**Fix:**
```python
@app.post("/login")
async def login(credentials: Credentials, db: Session = Depends(get_db)):
    user = authenticate(credentials)
    session = UserSession(
        user_id=user.id,
        created_at=datetime.now(),
        expires_at=datetime.now() + timedelta(hours=24)
    )
    db.add(session)
    db.commit()
    return {"token": create_jwt(user.id)}
```

---

### Anti-Pattern 2: Rate Limiter in Memory

```python
# VIOLATION
request_counts = defaultdict(lambda: {"count": 0, "window_start": time.time()})

@app.middleware("http")
async def rate_limit(request: Request, call_next):
    client_ip = request.client.host
    now = time.time()

    if now - request_counts[client_ip]["window_start"] > 60:
        request_counts[client_ip] = {"count": 0, "window_start": now}

    request_counts[client_ip]["count"] += 1

    if request_counts[client_ip]["count"] > 100:
        raise HTTPException(429, "Too many requests")

    return await call_next(request)
```

**Why it fails:**
- Rate limits reset on restart
- Each server tracks separately (can 5x limits with 5 servers)
- Memory grows with unique IPs

**Fix:**
```python
# Use Redis for distributed rate limiting
import redis

redis_client = redis.Redis()

@app.middleware("http")
async def rate_limit(request: Request, call_next):
    client_ip = request.client.host
    key = f"rate_limit:{client_ip}"

    count = redis_client.incr(key)
    if count == 1:
        redis_client.expire(key, 60)

    if count > 100:
        raise HTTPException(429, "Too many requests")

    return await call_next(request)
```

---

### Anti-Pattern 3: Connection Pool Tracking

```python
# VIOLATION
websocket_connections = {}

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await websocket.accept()
    websocket_connections[user_id] = websocket  # Memory leak + lost on restart

    try:
        while True:
            data = await websocket.receive_text()
            await process_message(user_id, data)
    finally:
        del websocket_connections[user_id]
```

**Why it fails:**
- Connections tied to specific server
- Can't broadcast across servers
- Lost on server restart

**Fix:**
```python
# Use pub/sub for cross-server messaging
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str, redis=Depends(get_redis)):
    await websocket.accept()
    pubsub = redis.pubsub()
    await pubsub.subscribe(f"user:{user_id}")

    async def listen():
        async for message in pubsub.listen():
            if message["type"] == "message":
                await websocket.send_text(message["data"])

    listener = asyncio.create_task(listen())
    try:
        while True:
            data = await websocket.receive_text()
            await redis.publish(f"broadcast:{user_id}", data)
    finally:
        listener.cancel()
```

---

## Session Management Anti-Patterns

### Anti-Pattern 4: Server-Side Sessions

```python
# VIOLATION
sessions = {}

@app.post("/login")
async def login(username: str, password: str):
    user = verify_credentials(username, password)
    session_id = secrets.token_urlsafe(32)
    sessions[session_id] = {
        "user_id": user.id,
        "created_at": datetime.now()
    }
    response = JSONResponse({"message": "Logged in"})
    response.set_cookie("session_id", session_id)
    return response

@app.get("/me")
async def get_me(session_id: str = Cookie(None)):
    if session_id not in sessions:
        raise HTTPException(401)
    return sessions[session_id]
```

**Why it fails:**
- Session lost when server restarts
- User must re-login when routed to different server
- No horizontal scaling

**Fix:**
```python
# JWT-based stateless sessions
@app.post("/login")
async def login(username: str, password: str):
    user = verify_credentials(username, password)
    token = jwt.encode(
        {"sub": user.id, "exp": datetime.now() + timedelta(hours=24)},
        SECRET_KEY,
        algorithm="HS256"
    )
    return {"access_token": token, "token_type": "bearer"}

@app.get("/me")
async def get_me(token: str = Depends(oauth2_scheme)):
    payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    return {"user_id": payload["sub"]}
```

---

### Anti-Pattern 5: Shopping Cart in Memory

```python
# VIOLATION
shopping_carts = {}

@app.post("/cart/{user_id}/add")
async def add_to_cart(user_id: str, item: Item):
    if user_id not in shopping_carts:
        shopping_carts[user_id] = []
    shopping_carts[user_id].append(item)
    return {"cart": shopping_carts[user_id]}
```

**Why it fails:**
- Cart lost on restart
- Different servers see different carts
- User confusion during checkout

**Fix:**
```python
@app.post("/cart/add")
async def add_to_cart(
    item: Item,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    cart_item = CartItem(user_id=user.id, product_id=item.product_id, quantity=item.quantity)
    db.add(cart_item)
    db.commit()

    cart = db.query(CartItem).filter(CartItem.user_id == user.id).all()
    return {"cart": cart}
```

---

## Caching Anti-Patterns

### Anti-Pattern 6: Mutable Cache Without Persistence

```python
# VIOLATION
user_preferences_cache = {}

@app.put("/preferences")
async def update_preferences(user_id: str, preferences: dict):
    user_preferences_cache[user_id] = preferences  # Never persisted!
    return {"status": "updated"}

@app.get("/preferences/{user_id}")
async def get_preferences(user_id: str):
    return user_preferences_cache.get(user_id, {})  # Empty after restart
```

**Why it fails:**
- Updates never reach database
- Data lost on restart
- Inconsistent across servers

**Fix:**
```python
@app.put("/preferences")
async def update_preferences(
    preferences: dict,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user.preferences = preferences
    db.commit()
    return {"status": "updated"}
```

---

### Anti-Pattern 7: Cache as Source of Truth

```python
# VIOLATION
config_cache = {}

def load_config():
    # Only loaded once, never refreshed
    config_cache["settings"] = fetch_from_db()

@app.on_event("startup")
async def startup():
    load_config()

@app.get("/config")
async def get_config():
    return config_cache["settings"]  # Stale after DB update
```

**Why it fails:**
- Config changes require restart
- Different servers may have different configs
- No cache invalidation

**Fix:**
```python
@app.get("/config")
async def get_config(db: Session = Depends(get_db)):
    # Always fetch fresh, or use cache with TTL
    return db.query(Config).first()

# Or with TTL cache
from functools import lru_cache
import time

@lru_cache(maxsize=1)
def get_config_cached(timestamp_bucket):
    return fetch_from_db()

@app.get("/config")
async def get_config():
    # Cache for 60 seconds
    bucket = int(time.time() / 60)
    return get_config_cached(bucket)
```

---

## Class-Level State Anti-Patterns

### Anti-Pattern 8: Service Class with Instance State

```python
# VIOLATION
class OrderService:
    def __init__(self):
        self.pending_orders = []  # Shared across requests!
        self.current_user = None  # Race condition!

    def process_order(self, user_id: str, order: Order):
        self.current_user = user_id  # Overwritten by concurrent requests
        self.pending_orders.append(order)
        # Process...

# Created once, reused across requests
order_service = OrderService()
```

**Why it fails:**
- `current_user` is overwritten by concurrent requests
- `pending_orders` grows forever
- Race conditions cause data corruption

**Fix:**
```python
class OrderService:
    def __init__(self, db: Session):
        self.db = db  # Scoped to request

    def process_order(self, user_id: str, order: Order):
        db_order = OrderModel(user_id=user_id, **order.dict())
        self.db.add(db_order)
        self.db.commit()

@app.post("/orders")
async def create_order(
    order: Order,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = OrderService(db)  # New instance per request
    return service.process_order(user.id, order)
```

---

## Framework-Specific Violations

### FastAPI: Background Tasks with State

```python
# VIOLATION
processing_status = {}

@app.post("/process/{job_id}")
async def start_processing(job_id: str, background_tasks: BackgroundTasks):
    processing_status[job_id] = "started"
    background_tasks.add_task(process_job, job_id)
    return {"status": "processing"}

async def process_job(job_id: str):
    # Long running task
    processing_status[job_id] = "completed"  # Lost on restart

@app.get("/process/{job_id}/status")
async def get_status(job_id: str):
    return {"status": processing_status.get(job_id, "unknown")}
```

**Fix:**
```python
@app.post("/process/{job_id}")
async def start_processing(
    job_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    job = Job(id=job_id, status="started")
    db.add(job)
    db.commit()
    background_tasks.add_task(process_job, job_id)
    return {"status": "processing"}

async def process_job(job_id: str):
    async with get_async_session() as db:
        # Update status in database
        job = db.query(Job).get(job_id)
        job.status = "completed"
        db.commit()
```

---

## Remediation Patterns

### Quick Fix Checklist

1. **Global dict/list/set** → Database table or Redis
2. **Session storage** → JWT tokens
3. **Class instance state** → Request-scoped dependencies
4. **In-memory cache** → Redis with TTL
5. **Background task state** → Database job queue
6. **WebSocket connections** → Pub/sub (Redis/RabbitMQ)

### Migration Strategy

1. Identify all module-level mutable state
2. Create database schema for persistent storage
3. Replace in-memory access with database queries
4. Add cache layer (optional) with proper invalidation
5. Test with multiple server instances
6. Test with server restarts
