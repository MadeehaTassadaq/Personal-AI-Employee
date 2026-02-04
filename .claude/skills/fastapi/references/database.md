# FastAPI Database Integration

## Table of Contents
- [SQLAlchemy Setup](#sqlalchemy-setup)
- [Database Models](#database-models)
- [Database Session Management](#database-session-management)
- [CRUD Operations](#crud-operations)
- [Async Database Operations](#async-database-operations)
- [Migrations with Alembic](#migrations-with-alembic)

## SQLAlchemy Setup

### Installation
```bash
pip install sqlalchemy psycopg2-binary alembic
```

### Database Configuration
```python
# app/core/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://user:password@localhost/dbname"
# For SQLite: "sqlite:///./test.db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
```

### Database Dependency
```python
from typing import Generator
from fastapi import Depends

def get_db() -> Generator:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Use in routes
@app.get("/items")
def read_items(db: Session = Depends(get_db)):
    return db.query(Item).all()
```

## Database Models

### Basic Model
```python
from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    price = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

### Relationships
```python
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    items = relationship("Item", back_populates="owner")

class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="items")
```

### Many-to-Many Relationships
```python
from sqlalchemy import Table

# Association table
item_tags = Table(
    "item_tags",
    Base.metadata,
    Column("item_id", Integer, ForeignKey("items.id")),
    Column("tag_id", Integer, ForeignKey("tags.id"))
)

class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    tags = relationship("Tag", secondary=item_tags, back_populates="items")

class Tag(Base):
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    items = relationship("Item", secondary=item_tags, back_populates="tags")
```

## Database Session Management

### Session Dependency with Type Annotation
```python
from typing import Annotated
from fastapi import Depends
from sqlalchemy.orm import Session

SessionDep = Annotated[Session, Depends(get_db)]

@app.get("/items")
def read_items(db: SessionDep):
    return db.query(Item).all()
```

### Yield Dependency Pattern
```python
from contextlib import contextmanager

@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
        db.commit()  # Auto-commit on success
    except Exception:
        db.rollback()  # Auto-rollback on error
        raise
    finally:
        db.close()
```

## CRUD Operations

### Create
```python
from fastapi import HTTPException
from sqlalchemy.orm import Session

def create_item(db: Session, item: ItemCreate) -> Item:
    """Create new item."""
    db_item = Item(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@app.post("/items", response_model=ItemResponse)
def create_item_endpoint(item: ItemCreate, db: SessionDep):
    return create_item(db, item)
```

### Read
```python
def get_item(db: Session, item_id: int) -> Item | None:
    """Get item by ID."""
    return db.query(Item).filter(Item.id == item_id).first()

def get_items(db: Session, skip: int = 0, limit: int = 100):
    """Get list of items."""
    return db.query(Item).offset(skip).limit(limit).all()

@app.get("/items/{item_id}")
def read_item(item_id: int, db: SessionDep):
    db_item = get_item(db, item_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item
```

### Update
```python
def update_item(db: Session, item_id: int, item: ItemUpdate) -> Item | None:
    """Update item."""
    db_item = db.query(Item).filter(Item.id == item_id).first()
    if db_item is None:
        return None

    # Update only provided fields
    update_data = item.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_item, field, value)

    db.commit()
    db.refresh(db_item)
    return db_item

@app.put("/items/{item_id}")
def update_item_endpoint(item_id: int, item: ItemUpdate, db: SessionDep):
    db_item = update_item(db, item_id, item)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item
```

### Delete
```python
def delete_item(db: Session, item_id: int) -> bool:
    """Delete item."""
    db_item = db.query(Item).filter(Item.id == item_id).first()
    if db_item is None:
        return False
    db.delete(db_item)
    db.commit()
    return True

@app.delete("/items/{item_id}", status_code=204)
def delete_item_endpoint(item_id: int, db: SessionDep):
    if not delete_item(db, item_id):
        raise HTTPException(status_code=404, detail="Item not found")
```

## Async Database Operations

### Async SQLAlchemy Setup
```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql+asyncpg://user:password@localhost/dbname"

engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_async_db():
    async with async_session() as session:
        yield session
```

### Async CRUD Operations
```python
from sqlalchemy import select

async def get_items_async(db: AsyncSession, skip: int = 0, limit: int = 100):
    """Get items asynchronously."""
    result = await db.execute(
        select(Item).offset(skip).limit(limit)
    )
    return result.scalars().all()

async def create_item_async(db: AsyncSession, item: ItemCreate):
    """Create item asynchronously."""
    db_item = Item(**item.dict())
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    return db_item

@app.get("/items")
async def read_items(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_async_db)):
    return await get_items_async(db, skip, limit)
```

## Migrations with Alembic

### Initialize Alembic
```bash
alembic init alembic
```

### Configure Alembic
```python
# alembic/env.py
from app.core.database import Base
from app.models import *  # Import all models

target_metadata = Base.metadata

# Update sqlalchemy.url in alembic.ini or:
config.set_main_option("sqlalchemy.url", DATABASE_URL)
```

### Create Migration
```bash
# Auto-generate migration from models
alembic revision --autogenerate -m "Create items table"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Manual Migration
```python
# alembic/versions/xxx_create_items.py
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        'items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_items_id'), 'items', ['id'])

def downgrade():
    op.drop_index(op.f('ix_items_id'), table_name='items')
    op.drop_table('items')
```

### Best Practices
- Always review auto-generated migrations
- Test migrations in development first
- Keep migrations small and focused
- Never edit applied migrations
- Use descriptive migration messages
- Backup database before production migrations
