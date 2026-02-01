# Tasks: Stable Executive Dashboard

**Input**: Design documents from `/specs/001-stable-dashboard/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/dashboard-schema.md

**Tests**: Integration tests included per plan.md requirements for validation and hardening.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Backend services**: `backend/services/`
- **Tests**: `tests/integration/`
- **Vault output**: `AI_Employee_Vault/Dashboard.md`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Ensure project structure and existing codebase is ready for refactoring

- [x] T001 Verify vault folder structure exists with all required directories in `AI_Employee_Vault/` (Inbox, Needs_Action, Pending_Approval, Approved, Done, Logs)
- [x] T002 [P] Create backup of current `backend/services/dashboard_updater.py` to `backend/services/dashboard_updater.py.backup`
- [x] T003 [P] Create backup of current `AI_Employee_Vault/Dashboard.md` to `AI_Employee_Vault/Dashboard.md.backup`

**Checkpoint**: Backups created, ready for refactoring

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core refactoring of DashboardUpdater that all user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Define SECTION_ORDER constant with 9 section markers in `backend/services/dashboard_updater.py`
- [x] T005 Add MAX_ITEMS_PER_SECTION constant (10) in `backend/services/dashboard_updater.py`
- [x] T006 Create `_generate_header_section()` method returning header with Last Updated timestamp in `backend/services/dashboard_updater.py`
- [x] T007 Create `_generate_system_status_section()` method returning System Status table in `backend/services/dashboard_updater.py`
- [x] T008 Create `_generate_quick_actions_section()` method returning static Quick Actions list in `backend/services/dashboard_updater.py`
- [x] T009 Create `_validate_dashboard_content(content: str) -> bool` method that checks all 9 section markers in order in `backend/services/dashboard_updater.py`
- [x] T010 Update `update_dashboard()` to use section generator methods and validate before write in `backend/services/dashboard_updater.py`

**Checkpoint**: Foundation ready - DashboardUpdater has section-based architecture

---

## Phase 3: User Story 1 - Executive Reviews System Status (Priority: P1) 🎯 MVP

**Goal**: Dashboard displays clear visual hierarchy readable in <2 minutes

**Independent Test**: Open Dashboard.md, identify pending approvals count, active tasks, and system status within 2 minutes

### Implementation for User Story 1

- [x] T011 [US1] Create `_generate_pending_approvals_section()` method with item limit and overflow text in `backend/services/dashboard_updater.py`
- [x] T012 [US1] Create `_generate_active_tasks_section()` method with item limit and table format in `backend/services/dashboard_updater.py`
- [x] T013 [US1] Create `_generate_signals_inputs_section()` method with Obsidian wiki-links in `backend/services/dashboard_updater.py`
- [x] T014 [US1] Create `_generate_recently_completed_section()` method with date-prefixed list format in `backend/services/dashboard_updater.py`
- [x] T015 [US1] Create `_generate_metrics_section()` method with Today/This Week columns in `backend/services/dashboard_updater.py`
- [x] T016 [US1] Refactor `update_dashboard()` to assemble sections in canonical order defined in SECTION_ORDER in `backend/services/dashboard_updater.py`
- [x] T017 [US1] Remove Mermaid diagram and Python Watchers documentation sections from dashboard output in `backend/services/dashboard_updater.py`
- [x] T018 [US1] Run manual validation: trigger `update_dashboard_now()` and verify Dashboard.md has correct section order

**Checkpoint**: User Story 1 complete - Dashboard readable in <2 minutes with clear visual hierarchy

---

## Phase 4: User Story 2 - Dashboard Updates Without Corruption (Priority: P2)

**Goal**: Deterministic, collision-free updates with automatic recovery

**Independent Test**: Run 5 consecutive updates, verify file structure intact after each

### Tests for User Story 2

- [x] T019 [P] [US2] Create `tests/test_dashboard_stability.py` with test class and fixtures
- [x] T020 [P] [US2] Add `test_section_order_consistency()` verifying 9 markers in correct order in `tests/test_dashboard_stability.py`
- [x] T021 [P] [US2] Add `test_5_consecutive_updates()` verifying no corruption after 5 updates in `tests/test_dashboard_stability.py`

### Implementation for User Story 2

- [x] T022 [US2] Add `_recover_dashboard()` method that regenerates from vault state in `backend/services/dashboard_updater.py`
- [x] T023 [US2] Update `update_dashboard()` to call `_recover_dashboard()` if validation fails in `backend/services/dashboard_updater.py`
- [x] T024 [US2] Add logging for recovery events to `Logs/dashboard-recovery.json` in `backend/services/dashboard_updater.py`
- [x] T025 [US2] Run integration tests: `pytest tests/test_dashboard_stability.py -v`

**Checkpoint**: User Story 2 complete - Dashboard survives consecutive updates without corruption

---

## Phase 5: User Story 3 - Weekly Executive Summary Generation (Priority: P3)

**Goal**: Collapsible weekly summary with aggregated metrics

**Independent Test**: Verify weekly summary shows task counts, approval time, and action breakdown

### Implementation for User Story 3

- [x] T026 [US3] Add `_get_week_start_date() -> datetime` helper method in `backend/services/dashboard_updater.py`
- [x] T027 [US3] Add `_calculate_weekly_metrics() -> Dict` method aggregating from Done/ folder in `backend/services/dashboard_updater.py`
- [x] T028 [US3] Create `_generate_weekly_summary_section()` method with `<details>` collapsible tag in `backend/services/dashboard_updater.py`
- [x] T029 [US3] Update SECTION_ORDER to include Weekly Summary before Quick Actions in `backend/services/dashboard_updater.py`
- [x] T030 [US3] Handle empty week case: display "No completed tasks this period" message in `_generate_weekly_summary_section()`
- [x] T031 [US3] Run manual validation: verify Weekly Summary appears collapsed with correct metrics

**Checkpoint**: User Story 3 complete - Weekly summary shows aggregated performance

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final hardening, extended tests, and documentation

- [x] T032 [P] Add `test_100_consecutive_updates()` for SC-002 validation in `tests/test_dashboard_stability.py`
- [x] T033 [P] Add `test_overflow_handling()` with 55 test files in `tests/test_dashboard_stability.py`
- [x] T034 [P] Add `test_recovery_from_corruption()` simulating file corruption in `tests/test_dashboard_stability.py`
- [x] T035 Update `specs/001-stable-dashboard/quickstart.md` with actual test commands and results
- [x] T036 Run full test suite: `pytest tests/test_dashboard_stability.py -v` (11 passed)
- [x] T037 Measure dashboard update performance (target: <2 seconds) - PASSED: <1.42s
- [x] T038 Final manual validation: executive scan test (<2 minutes to identify key metrics) - PASSED in <30s

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational (Phase 2)
- **User Story 2 (Phase 4)**: Depends on Foundational (Phase 2) - Can run in parallel with US1
- **User Story 3 (Phase 5)**: Depends on Foundational (Phase 2) - Can run in parallel with US1/US2
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - MVP, highest priority
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Independent of US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Independent of US1/US2

### Within Each Phase

- Section generator methods can be developed in parallel [P]
- Tests marked [P] can run in parallel
- Integration tests depend on implementation being complete

### Parallel Opportunities

```bash
# Phase 2: These can run in parallel
Task T004: Define SECTION_ORDER constant
Task T005: Add MAX_ITEMS_PER_SECTION constant
Task T006: Create _generate_header_section()
Task T007: Create _generate_system_status_section()
Task T008: Create _generate_quick_actions_section()

# User Story 2 Tests: These can run in parallel
Task T019: Create test file
Task T020: Add test_section_order_consistency
Task T021: Add test_5_consecutive_updates

# Polish Phase: These can run in parallel
Task T032: Add test_100_consecutive_updates
Task T033: Add test_overflow_handling
Task T034: Add test_recovery_from_corruption
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: Foundational (T004-T010)
3. Complete Phase 3: User Story 1 (T011-T018)
4. **STOP and VALIDATE**: Open Dashboard.md, verify readability in <2 minutes
5. Demo-ready: MVP delivers executive-readable dashboard

### Incremental Delivery

1. Setup + Foundational → Section-based architecture ready
2. Add User Story 1 → Test independently → Demo (MVP!)
3. Add User Story 2 → Test independently → Stability proven
4. Add User Story 3 → Test independently → Weekly summary active
5. Polish → Full test coverage, documentation complete

### Task Counts

| Phase | Tasks | Parallel Opportunities |
|-------|-------|------------------------|
| Setup | 3 | 2 |
| Foundational | 7 | 5 |
| User Story 1 | 8 | 0 (sequential refactor) |
| User Story 2 | 7 | 3 (tests) |
| User Story 3 | 6 | 0 (sequential) |
| Polish | 7 | 3 (tests) |
| **Total** | **38** | **13** |

---

## Success Criteria Mapping

| Success Criterion | Validating Tasks |
|-------------------|------------------|
| SC-001: 2-minute readability | T018, T038 |
| SC-002: 100 update stability | T032 |
| SC-003: <1/1000 corruption | T025, T032 |
| SC-004: Above-the-fold content | T016, T017 |
| SC-005: Weekly accuracy | T027, T031 |
| SC-006: Judge comprehension | T035, T038 |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- All tasks modify `backend/services/dashboard_updater.py` (single file, sequential within phases)
- Tests in separate file can be developed in parallel
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
