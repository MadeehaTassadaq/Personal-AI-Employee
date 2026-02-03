# PostgreSQL + SQLModel Reference

## Table of Contents
- [Connection Setup](#connection-setup)
- [Model Definitions](#model-definitions)
- [CRUD Operations](#crud-operations)
- [Relationships](#relationships)
- [Migrations](#migrations)
- [Neon PostgreSQL](#neon-postgresql)

## Connection Setup

```python
# database.py
from sqlmodel import SQLModel, create_engine, Session
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    echo=True,  # SQL logging (disable in production)
    pool_pre_ping=True,  # Verify connections
    pool_size=5,
    max_overflow=10
)

def create_db_and_tables():
    """Create all tables defined in SQLModel models."""
    SQLModel.metadata.create_all(engine)

def get_session():
    """Dependency for FastAPI route injection."""
    with Session(engine) as session:
        yield session
```

## Model Definitions

### User Model
```python
# models/user.py
from sqlmodel import Field, SQLModel
from uuid import UUID, uuid4
from datetime import datetime

class User(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(unique=True, index=True)
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

### Task Model
```python
# models/task.py
from sqlmodel import Field, SQLModel
from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional

class Task(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)
    title: str = Field(max_length=255)
    description: Optional[str] = None
    status: str = Field(default="pending")  # pending, in_progress, completed
    priority: Optional[str] = None  # low, medium, high
    due_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

### Pydantic Schemas (Request/Response)
```python
# schemas/task.py
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[datetime] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[datetime] = None

class TaskResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    description: Optional[str]
    status: str
    priority: Optional[str]
    due_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

## CRUD Operations

```python
# api/tasks.py
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from uuid import UUID
from datetime import datetime

router = APIRouter()

@router.post("/", response_model=TaskResponse)
def create_task(
    task: TaskCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    db_task = Task(
        **task.model_dump(),
        user_id=current_user.id
    )
    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    return db_task

@router.get("/", response_model=list[TaskResponse])
def get_tasks(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    statement = select(Task).where(Task.user_id == current_user.id)
    return session.exec(statement).all()

@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    task = session.get(Task, task_id)
    if not task or task.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.put("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: UUID,
    task_update: TaskUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    task = session.get(Task, task_id)
    if not task or task.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Task not found")

    update_data = task_update.model_dump(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()

    for key, value in update_data.items():
        setattr(task, key, value)

    session.add(task)
    session.commit()
    session.refresh(task)
    return task

@router.delete("/{task_id}")
def delete_task(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    task = session.get(Task, task_id)
    if not task or task.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Task not found")

    session.delete(task)
    session.commit()
    return {"message": "Task deleted"}
```

## Relationships

```python
from sqlmodel import Relationship, Field, SQLModel
from typing import List, Optional

class User(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(unique=True, index=True)
    password_hash: str

    # Relationship to tasks
    tasks: List["Task"] = Relationship(back_populates="user")

class Task(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id")
    title: str

    # Relationship to user
    user: Optional["User"] = Relationship(back_populates="tasks")
```

## Migrations

Using Alembic for database migrations:

```bash
# Install alembic
pip install alembic

# Initialize
alembic init alembic

# Edit alembic.ini - set sqlalchemy.url
# Edit alembic/env.py - import your models

# Generate migration
alembic revision --autogenerate -m "Add tasks table"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

**alembic/env.py configuration:**
```python
from app.models import *  # Import all models
from app.database import DATABASE_URL

config.set_main_option("sqlalchemy.url", DATABASE_URL)
target_metadata = SQLModel.metadata
```

## Neon PostgreSQL

### Connection String Format
```
postgresql://user:password@ep-xxx.region.aws.neon.tech/dbname?sslmode=require
```

### Environment Setup
```bash
# .env
DATABASE_URL=postgresql://user:pass@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require
```

### Connection with SSL
```python
engine = create_engine(
    DATABASE_URL,
    connect_args={"sslmode": "require"}
)
```

### Neon Features
- **Autoscaling**: Compute scales to zero when idle
- **Branching**: Create database branches for dev/test
- **Connection Pooling**: Use pooler endpoint for serverless

```bash
# Pooler connection (for serverless/high connections)
DATABASE_URL=postgresql://user:pass@ep-xxx-pooler.region.aws.neon.tech/neondb?sslmode=require
```
