---
name: fullstack-todo-architect
description: |
  Full-Stack ToDo App Architect for spec-driven development. Design, fix, and implement production-ready ToDo web applications using Next.js 16+ (App Router), FastAPI, SQLModel, Neon PostgreSQL, and Better Auth. Use when: (1) Building a new ToDo web application, (2) Fixing auth/UI issues in ToDo apps, (3) Debugging task list not showing, (4) Modernizing dated UI, (5) Implementing CRUD task APIs, (6) Setting up Better Auth with consistent signup/login fields. Triggers: "task list not showing", "UI not modern", "signup/login mismatch", "build todo app", "fix auth", "implement task API".
---

# Full-Stack ToDo App Architect

Expert engineering skill for designing, fixing, and implementing production-ready ToDo web applications using strict Spec-Driven Development (SDD).

## Core Principles

1. **Spec-First:** Everything follows Spec → Plan → Tasks → Implementation
2. **Modular Architecture:** Frontend/Backend separation with clear boundaries
3. **Modern UX:** Professional SaaS-quality UI, mobile-first responsive design
4. **Consistent Auth:** Signup/login fields must match exactly
5. **Testable Features:** All functionality verifiable via UI

## Tech Stack (Strict)

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 16+ (App Router), Tailwind CSS |
| Backend | Python FastAPI, SQLModel ORM |
| Database | Neon Serverless PostgreSQL |
| Auth | Better Auth (JWT) |
| Specs | Claude Code, Spec-Kit Plus |

See [references/tech-stack.md](references/tech-stack.md) for implementation details.

## Task API Contracts

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/{user_id}/tasks` | List all tasks |
| POST | `/api/{user_id}/tasks` | Create task |
| GET | `/api/{user_id}/tasks/{id}` | Get single task |
| PUT | `/api/{user_id}/tasks/{id}` | Update task |
| DELETE | `/api/{user_id}/tasks/{id}` | Delete task |
| PATCH | `/api/{user_id}/tasks/{id}/complete` | Toggle completion |

See [references/api-contracts.md](references/api-contracts.md) for request/response schemas.

## Authentication Rules

### Signup (ALL fields required)
- `username`
- `email`
- `password`

### Login (identifier can be username OR email)
- `identifier`
- `password`

**Critical:** If signup/login fields mismatch, STOP, diagnose, and fix both frontend and backend together.

## Project Structure

See [references/project-structure.md](references/project-structure.md) for complete layout.

```
/specs/phase-{1-5}/     # Spec, plan, tasks per phase
/frontend/              # Next.js app
/backend/               # FastAPI app
/history/prompts/       # PHR records
```

## Phase-Based Execution

### Phase 1 - Core Task API
- FastAPI setup with SQLModel
- CRUD endpoints for tasks
- Neon PostgreSQL connection

### Phase 2 - Auth Integration
- User model and auth routes
- Better Auth with JWT
- Consistent signup/login fields

### Phase 3 - Frontend Task UI
- Task list component (MUST be visible after login)
- Create/Update/Delete task forms
- Toggle completion

### Phase 4 - UX & Responsiveness
- Loading, error, empty states
- Mobile-first responsive layout
- Modern UI components

### Phase 5 - Bug Fixes & Polish
- Edge case handling
- Form validation
- Accessibility improvements

## Error Handling Workflow

When user reports issues:

1. **Diagnose** root cause
2. **Explain** clearly
3. **Fix spec** if needed
4. **Update plan**
5. **Update tasks**
6. **Implement fix**
7. **Verify** with checklist

See [references/troubleshooting.md](references/troubleshooting.md) for common issues.

## Output Format

Always structure responses as:

```markdown
## 1. Problem Diagnosis
[What's wrong and why]

## 2. Spec Update
[Changes to spec.md if needed]

## 3. Plan
[Implementation approach]

## 4. Tasks Breakdown
[Specific actionable tasks]

## 5. Implementation
[Code changes with file paths]

## 6. Verification Checklist
- [ ] Task list visible after login
- [ ] Create/Update/Delete working
- [ ] Auth fields consistent
- [ ] Mobile responsive
- [ ] Loading/error states present
```

## Frontend UI Requirements

- Task list MUST be visible after login
- Empty state when no tasks
- Loading spinner during fetch
- Error message on failure
- Mobile-first responsive layout
- Modern SaaS-quality design (no console-style UI)

### Modern UI Patterns

```tsx
// Card component pattern
<div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 hover:shadow-md transition-shadow">
  <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
  <p className="text-gray-600 mt-2">{description}</p>
</div>

// Button pattern
<button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors font-medium">
  Add Task
</button>
```

## Quick Fixes

### Task List Not Showing
1. Check API call fires after login
2. Verify user ID passed correctly
3. Ensure component state updates
4. Add useEffect with user dependency

### Auth Field Mismatch
1. Align signup: `username`, `email`, `password`
2. Align login: `identifier`, `password`
3. Backend checks identifier against both fields

### UI Not Modern
1. Apply consistent spacing (`space-y-4`, `p-6`)
2. Add shadows (`shadow-sm`, `shadow-md`)
3. Round corners (`rounded-lg`, `rounded-xl`)
4. Add hover transitions
