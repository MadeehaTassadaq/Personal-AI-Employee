# Project Structure Reference

## Mandatory Directory Layout

```
/project-root
├── specs/
│   ├── phase-1/
│   │   ├── spec.md
│   │   ├── plan.md
│   │   └── tasks.md
│   ├── phase-2/
│   ├── phase-3/
│   ├── phase-4/
│   └── phase-5/
│
├── frontend/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   ├── globals.css
│   │   ├── (auth)/
│   │   │   ├── login/page.tsx
│   │   │   └── signup/page.tsx
│   │   └── dashboard/
│   │       └── page.tsx
│   ├── components/
│   │   ├── ui/
│   │   │   ├── button.tsx
│   │   │   ├── input.tsx
│   │   │   └── card.tsx
│   │   ├── forms/
│   │   │   ├── task-form.tsx
│   │   │   └── login-form.tsx
│   │   └── features/
│   │       ├── task-list.tsx
│   │       └── task-item.tsx
│   ├── services/
│   │   ├── api.ts
│   │   └── tasks.ts
│   ├── auth/
│   │   └── auth-provider.tsx
│   ├── lib/
│   │   └── utils.ts
│   └── types/
│       └── index.ts
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   └── main.py
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── tasks.py
│   │   └── auth.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── task.py
│   │   └── user.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── task_service.py
│   │   └── auth_service.py
│   ├── auth/
│   │   ├── __init__.py
│   │   └── dependencies.py
│   └── database.py
│
└── history/
    └── prompts/
```

## Phase Breakdown

### Phase 1 - Core Task API
**Focus:** Backend API foundation

**Deliverables:**
- FastAPI app setup
- SQLModel Task model
- CRUD endpoints for tasks
- Database connection to Neon

**Files:**
- `backend/app/main.py`
- `backend/models/task.py`
- `backend/routers/tasks.py`
- `backend/database.py`

### Phase 2 - Auth Integration
**Focus:** Authentication system

**Deliverables:**
- User model
- Signup endpoint
- Login endpoint
- JWT token generation
- Auth middleware

**Files:**
- `backend/models/user.py`
- `backend/routers/auth.py`
- `backend/services/auth_service.py`
- `backend/auth/dependencies.py`

### Phase 3 - Frontend Task UI
**Focus:** Core frontend functionality

**Deliverables:**
- Task list component
- Create task form
- Update task modal
- Delete confirmation
- Toggle completion

**Files:**
- `frontend/components/features/task-list.tsx`
- `frontend/components/features/task-item.tsx`
- `frontend/components/forms/task-form.tsx`
- `frontend/services/tasks.ts`

### Phase 4 - UX & Responsiveness
**Focus:** Polish and mobile support

**Deliverables:**
- Loading states
- Error states
- Empty states
- Mobile-first layout
- Modern UI components

**Files:**
- `frontend/components/ui/*`
- `frontend/app/globals.css`

### Phase 5 - Bug Fixes & Polish
**Focus:** Edge cases and refinement

**Deliverables:**
- Error boundary
- Form validation
- Optimistic updates
- Accessibility improvements

## File Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| React Components | PascalCase | `TaskList.tsx` |
| React Files | kebab-case | `task-list.tsx` |
| Python Modules | snake_case | `task_service.py` |
| CSS/Config | kebab-case | `tailwind.config.js` |
| Specs | kebab-case | `spec.md`, `plan.md` |
