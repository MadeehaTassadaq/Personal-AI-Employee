# Implementation Plan: Stable Executive Dashboard

**Branch**: `001-stable-dashboard` | **Date**: 2026-02-01 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-stable-dashboard/spec.md`

## Summary

Stabilize the Digital FTE Dashboard.md to provide a deterministic, executive-readable Markdown interface that displays system status, pending approvals, active tasks, and completed actions within a 2-minute scan time. The implementation focuses on refactoring the existing `DashboardUpdater` service to enforce section-based updates, improve visual hierarchy, and ensure collision-free writes.

## Technical Context

**Language/Version**: Python 3.13
**Primary Dependencies**: FastAPI, pydantic, PyYAML, python-frontmatter
**Storage**: File-based (Obsidian vault with YAML frontmatter Markdown files)
**Testing**: pytest with manual validation scripts
**Target Platform**: Linux (local-first, no cloud dependencies)
**Project Type**: Single project with backend services
**Performance Goals**: Dashboard update completes in <2 seconds; file readable in <2 minutes
**Constraints**: Markdown-only output, no web UI changes, LLM-readable format
**Scale/Scope**: Single user (CEO), ~50 tasks per category, ~100 daily operations

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Requirement | Status | Notes |
|-----------|-------------|--------|-------|
| **I. Local-First** | All data in local vault | ✅ PASS | Dashboard.md stored in `AI_Employee_Vault/` |
| **II. Autonomy with Accountability** | Approval workflow intact | ✅ PASS | Dashboard reads from `Pending_Approval/`; no action execution |
| **III. File-as-API** | Markdown with YAML frontmatter | ✅ PASS | Dashboard follows vault conventions |
| **IV. Reproducibility** | Audit trail preserved | ✅ PASS | Metrics derived from `Logs/` folder |
| **V. Engineering over Prompting** | Deterministic behavior | ✅ PASS | Section-based update pattern enforced |

**Gate Status**: PASSED — No violations detected.

## Project Structure

### Documentation (this feature)

```text
specs/001-stable-dashboard/
├── plan.md              # This file
├── research.md          # Phase 0 output (architecture decisions)
├── data-model.md        # Phase 1 output (dashboard schema)
├── quickstart.md        # Phase 1 output (validation guide)
├── contracts/           # Phase 1 output (dashboard section contracts)
│   └── dashboard-schema.md
├── checklists/
│   └── requirements.md  # Spec validation checklist
└── tasks.md             # Phase 2 output (/sp.tasks command)
```

### Source Code (repository root)

```text
backend/
├── services/
│   ├── dashboard_updater.py    # PRIMARY: Refactored dashboard generator
│   └── scheduler.py            # Triggers dashboard updates (60s interval)
└── api/
    └── status.py               # Dashboard read endpoint (no writes)

AI_Employee_Vault/
├── Dashboard.md                # OUTPUT: Executive dashboard file
├── Inbox/                      # Source: New tasks
├── Needs_Action/               # Source: Active tasks
├── Pending_Approval/           # Source: Awaiting approval
├── Approved/                   # Source: Ready for execution
├── Done/                       # Source: Completed tasks
└── Logs/                       # Source: Metrics aggregation

tests/
└── integration/
    └── test_dashboard_stability.py  # Dashboard corruption tests
```

**Structure Decision**: Leverage existing `backend/services/dashboard_updater.py` as the single writer. No new modules required — refactor existing code to enforce section-based update pattern and improve visual hierarchy.

## Complexity Tracking

> **No violations to track** — Implementation uses existing architecture without adding complexity.

---

## Architecture Overview

### Current State (Baseline)

```
┌────────────────────────────────────────────────────────────────┐
│                    DASHBOARD UPDATE FLOW                        │
└────────────────────────────────────────────────────────────────┘

Scheduler (60s interval)
        │
        ▼
DashboardUpdater.update_dashboard()
        │
        ├── count_files() for each vault folder
        ├── get_recent_done_tasks(limit=5)
        ├── get_pending_approval_tasks()
        ├── get_needs_action_tasks()
        ├── get_inbox_tasks()
        ├── get_social_metrics() from Logs/*.json
        │
        ▼
Generate complete Dashboard.md content
        │
        ▼
Smart write: only if content changed
        │
        ▼
Dashboard.md (single file, single writer)
```

**Key Insight**: The existing architecture already uses a **single-writer pattern** via the `DashboardUpdater` class. The scheduler ensures writes are serialized. The only issue is the dashboard layout and visual hierarchy, not write collisions.

### Target State (After Implementation)

```
┌────────────────────────────────────────────────────────────────┐
│              STABLE DASHBOARD UPDATE FLOW                       │
└────────────────────────────────────────────────────────────────┘

Scheduler (60s interval)
        │
        ▼
DashboardUpdater.update_dashboard()
        │
        ├── Section 1: Header + Last Updated
        ├── Section 2: System Status (table)
        ├── Section 3: Pending Approvals (table, max 10)
        ├── Section 4: Active Tasks (table, max 10)
        ├── Section 5: Signals/Inputs (list, max 10)
        ├── Section 6: Recently Completed (list, max 10)
        ├── Section 7: Metrics Summary (table)
        ├── Section 8: Weekly Summary (generated on demand)
        ├── Section 9: Quick Actions Reference
        │
        ▼
Validate section order (deterministic)
        │
        ▼
Smart write: only if content changed
        │
        ▼
Dashboard.md (executive-readable in <2 minutes)
```

---

## Architectural Decisions

### ADR-001: Single-Writer Dashboard Pattern (Confirmed)

**Decision**: Maintain `DashboardUpdater` as the exclusive writer to `Dashboard.md`.

**Rationale**:
- Eliminates write collision risk entirely
- Simplifies debugging (single code path)
- Scheduler serializes updates (60-second interval)

**Alternatives Considered**:
- Section-based partial updates (rejected: complexity without benefit given single writer)
- Real-time WebSocket updates (rejected: violates Markdown-native constraint)

**Status**: Confirmed — existing pattern is correct.

---

### ADR-002: Section Order and Visual Hierarchy

**Decision**: Implement fixed section order with clear visual separators.

**Proposed Section Order** (optimized for executive scan):

1. **Header** — Title + Last Updated timestamp
2. **System Status** — Component health table (above the fold)
3. **Pending Approvals** — Items requiring action (critical for HITL)
4. **Active Tasks** — Work in progress
5. **Signals/Inputs** — New items in Inbox
6. **Recently Completed** — Audit trail (last 10)
7. **Metrics** — Daily/weekly counts
8. **Quick Actions** — How to interact
9. **Weekly Summary** — Aggregated performance (collapsed by default)

**Rationale**:
- Pending Approvals at top ensures executive sees actionable items first
- System Status provides immediate health check
- Metrics and weekly summary are reference content, not primary

---

### ADR-003: Item Limits and Overflow Handling

**Decision**: Limit each section to 10 items with clear overflow indication.

**Implementation**:
- Pending Approvals: Show 10, indicate "View all (N) in Pending_Approval/"
- Active Tasks: Show 10, indicate total count
- Completed: Show 10 most recent
- Inbox: Show 10, indicate total count

**Rationale**:
- Prevents dashboard from becoming unmanageably long
- Keeps critical content above the fold (first 50 lines)
- SC-004 requires 95% of critical content visible early

---

### ADR-004: Log Summarization vs Raw Output

**Decision**: Display aggregated metrics only; no raw logs in dashboard.

**Implementation**:
- Metrics section shows counts (emails sent, tasks completed, etc.)
- Raw logs remain in `Logs/` folder for debugging
- Weekly summary aggregates from `Done/` folder frontmatter

**Rationale**:
- Executives need summaries, not raw data
- Raw logs would clutter the dashboard
- Logs folder provides full detail when needed

---

### ADR-005: Dashboard Recovery on Corruption

**Decision**: Implement validation check before write; regenerate from scratch if invalid.

**Implementation**:
- Before final write, validate section markers are present
- If validation fails, regenerate entire dashboard from vault state
- Log recovery event to `Logs/`

**Rationale**:
- Vault folders are source of truth, not the dashboard
- Dashboard can always be regenerated from vault state
- Simple approach: regenerate rather than partial repair

---

## Phase 0: Research Findings

### Existing Architecture Analysis

**Current `DashboardUpdater` Capabilities**:
- ✅ Reads all vault folders (Inbox, Needs_Action, Pending_Approval, Done)
- ✅ Parses YAML frontmatter for task metadata
- ✅ Aggregates metrics from `Logs/*.json`
- ✅ Smart write (only if content changed)
- ❌ No section validation
- ❌ No item limits (displays all items)
- ❌ Inconsistent visual hierarchy
- ❌ Weekly summary not implemented

**Current Dashboard Layout Issues** (from spec analysis):
1. Mermaid diagram takes significant vertical space
2. Section order not optimized for executive scan
3. No overflow handling for large item counts
4. Metrics section incomplete (missing weekly aggregation)

### Technology Choices Confirmed

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Dashboard Writer | `DashboardUpdater` class | Already single-writer; minimize changes |
| Update Trigger | Scheduler (60s) | Prevents rapid-fire updates; already working |
| Data Source | Vault folders + frontmatter | Constitution-compliant; already implemented |
| Output Format | Markdown with tables | Obsidian-compatible; LLM-readable |
| Validation | Section marker check | Lightweight; enables recovery |

---

## Phase 1: Design Artifacts

### Data Model: Dashboard Sections

Each section has a defined structure:

```yaml
# Dashboard Section Contract
sections:
  - name: "System Status"
    marker: "## System Status"
    format: table
    columns: [Component, Status, Notes]
    max_items: null  # Show all components

  - name: "Pending Approvals"
    marker: "## Pending Approvals"
    format: table
    columns: [Item, Type, Created, Action]
    max_items: 10
    overflow_text: "View all ({count}) in `Pending_Approval/`"

  - name: "Active Tasks"
    marker: "## Active Tasks"
    format: table
    columns: [Task, Status, Started]
    max_items: 10
    overflow_text: "View all ({count}) in `Needs_Action/`"

  - name: "Signals / Inputs"
    marker: "## Signals / Inputs"
    format: list
    max_items: 10
    overflow_text: "{count} new items in `Inbox/`"

  - name: "Recently Completed"
    marker: "## Recently Completed"
    format: list
    max_items: 10

  - name: "Metrics"
    marker: "## Metrics"
    format: table
    columns: [Metric, Today, This Week]

  - name: "Weekly Summary"
    marker: "## Weekly Summary"
    format: prose
    collapsed: true  # Use <details> tag

  - name: "Quick Actions"
    marker: "## Quick Actions"
    format: list
```

### Dashboard Template (Target Output)

```markdown
# Digital FTE Dashboard

> Last Updated: 2026-02-01 15:48:33

---

## System Status

| Component | Status | Notes |
|-----------|--------|-------|
| Vault | Active | AI_Employee_Vault |
| File Watcher | Active | Monitoring Inbox/ |
| Gmail MCP | Configured | Ready |
| WhatsApp MCP | Not Configured | QR scan required |

**Mode:** `DRY_RUN=false` (Live mode)

---

## Pending Approvals

> **{count} items awaiting your decision**

| Item | Type | Created | Action |
|------|------|---------|--------|
| instagram-post-2026-02-01 | Social Media | 2026-02-01 12:00 | Move to `Approved/` or `Done/` |

**To approve:** Move file from `Pending_Approval/` to `Approved/`
**To reject:** Move file to `Done/` with rejection note

---

## Active Tasks

| Task | Status | Started |
|------|--------|---------|
| _No tasks in progress_ | — | — |

---

## Signals / Inputs

> **{count} new items in Inbox/**

- [[Inbox/prepare-report|Prepare Report]]
- [[Inbox/test-task|Test Task]]

---

## Recently Completed

> Last 10 completed tasks

- [2026-02-01] facebook-ai-healthcare
- [2026-01-31] instagram-ai-healthcare
- [2026-01-30] email-meeting-notification

---

## Metrics

| Metric | Today | This Week |
|--------|-------|-----------|
| Tasks Completed | 2 | 15 |
| Pending Approvals | 1 | — |
| Emails Sent | 0 | 3 |
| Social Posts | 1 | 8 |

---

<details>
<summary>## Weekly Summary (Week of 2026-01-27)</summary>

- **Total Tasks Completed**: 15
- **Avg Time to Approval**: 4.2 hours
- **Actions by Type**: Email (3), Social (8), Other (4)
- **System Uptime**: 99.8%

</details>

---

## Quick Actions

- **Add task:** Create `.md` file in `Inbox/`
- **Approve action:** Move file from `Pending_Approval/` to `Approved/`
- **View logs:** Check `Logs/` folder
- **Reject action:** Move file from `Pending_Approval/` to `Done/`
```

---

## Implementation Phases

### Phase 1: System Mapping (Documentation)

**Deliverables**:
- ✅ Architecture diagram (included above)
- ✅ Current component analysis (research phase)
- ✅ Known UI pain points documented
- ✅ Dashboard ownership confirmed (single-writer)

### Phase 2: Dashboard Foundation

**Tasks**:
1. Refactor `DashboardUpdater.update_dashboard()` method
2. Implement section-based generation with fixed order
3. Add item limits with overflow indicators
4. Improve table formatting and visual hierarchy
5. Add weekly summary generation (from Done/ folder)
6. Add section validation before write

**Files Modified**:
- `backend/services/dashboard_updater.py` — Main refactor

### Phase 3: Agent Integration

**Tasks**:
1. Verify vault-reader skill works with new dashboard format
2. Ensure dashboard remains LLM-readable
3. Test Human-in-the-Loop flow end-to-end
4. Validate metrics accuracy

**Validation**:
- Run file watcher with test tasks
- Trigger approval workflow
- Verify dashboard updates correctly

### Phase 4: Validation & Hardening

**Tasks**:
1. Create integration test for dashboard stability
2. Run 100 consecutive update operations
3. Verify section order consistency
4. Test recovery from simulated corruption
5. Measure executive scan time (<2 minutes)

**Test Script**:
```python
# tests/integration/test_dashboard_stability.py
def test_100_consecutive_updates():
    """SC-002: Dashboard remains valid after 100 updates"""

def test_section_order_consistency():
    """FR-009: Section order does not change"""

def test_overflow_handling():
    """Edge case: >50 pending items"""

def test_recovery_from_corruption():
    """Dashboard regenerates from vault state"""
```

---

## Validation Checklist

| Success Criterion | Test Method | Pass Condition |
|-------------------|-------------|----------------|
| SC-001: 2-minute readability | Manual review | Executive identifies key metrics in <2 min |
| SC-002: 100 update stability | Automated test | No file corruption after 100 updates |
| SC-003: <1/1000 corruption | Extended run | Zero corruption in 1000 updates |
| SC-004: Above-the-fold content | Line count | Critical sections in first 50 lines |
| SC-005: Weekly accuracy | Metrics validation | <5% variance from source data |
| SC-006: Judge comprehension | Hackathon demo | Judge explains workflow after 10 min |

---

## Risk Analysis

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Dashboard update slow (>2s) | Low | Medium | Profile and optimize vault reads |
| Section validation false positive | Low | Low | Simple marker check; log warnings |
| Weekly summary calculation errors | Medium | Low | Unit test aggregation logic |
| Obsidian rendering differences | Low | Low | Test in multiple viewers |

---

## Next Steps

1. Run `/sp.tasks` to generate implementation tasks
2. Implement Phase 2 (Dashboard Foundation) first
3. Validate with manual testing before Phase 4
4. Create PHR after implementation

---

**Plan Status**: READY FOR IMPLEMENTATION

📋 **Architectural decisions detected**:
- ADR-001: Single-Writer Dashboard Pattern
- ADR-002: Section Order and Visual Hierarchy
- ADR-003: Item Limits and Overflow Handling

Document reasoning and tradeoffs? Run `/sp.adr dashboard-update-pattern`
