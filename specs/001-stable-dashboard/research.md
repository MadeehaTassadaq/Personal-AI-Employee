# Research: Stable Executive Dashboard

**Feature**: 001-stable-dashboard
**Date**: 2026-02-01

## Research Questions

### Q1: How does the current dashboard update mechanism work?

**Finding**: The dashboard is updated by a single `DashboardUpdater` class in `backend/services/dashboard_updater.py`. Updates are triggered every 60 seconds by the `Scheduler` service. The system uses a "smart write" pattern—only writing to the file if content has changed.

**Decision**: Maintain single-writer pattern
**Rationale**: Eliminates write collision risk entirely; already implemented and working
**Alternatives Considered**: Section-based partial updates (rejected: adds complexity without benefit)

---

### Q2: What causes dashboard UI clutter and inconsistency?

**Finding**: Current issues identified:
1. Mermaid workflow diagram takes ~20 lines of vertical space
2. Section order prioritizes informational content over actionable items
3. No item limits—all tasks displayed regardless of count
4. Metrics section lacks weekly aggregation
5. No visual distinction between critical and reference sections

**Decision**: Reorder sections to prioritize actionable items (Pending Approvals first)
**Rationale**: Executives need to see what requires their action immediately
**Alternatives Considered**: Keep current order with visual markers (rejected: doesn't solve scan time issue)

---

### Q3: What is the optimal section order for executive readability?

**Finding**: Based on executive dashboard best practices and the spec's 2-minute readability requirement:
1. Header + timestamp (orientation)
2. System Status (health check)
3. Pending Approvals (action required)
4. Active Tasks (awareness)
5. Signals/Inputs (incoming work)
6. Recently Completed (audit)
7. Metrics (performance)
8. Quick Actions (reference)
9. Weekly Summary (collapsed/optional)

**Decision**: Implement fixed section order as listed above
**Rationale**: Action-required items above the fold; reference content at bottom
**Alternatives Considered**: Customizable section order (rejected: adds complexity; one user)

---

### Q4: How should overflow (>10 items) be handled?

**Finding**: Current implementation shows all items, making the dashboard unwieldy when many tasks exist.

**Decision**: Limit each section to 10 items with overflow indicator
**Rationale**: Keeps dashboard concise; full list available in vault folders
**Alternatives Considered**: Pagination (rejected: not appropriate for Markdown); infinite scroll (rejected: web-only)

---

### Q5: Should raw logs appear in the dashboard?

**Finding**: Current dashboard includes Python watcher documentation and Mermaid diagrams, which are reference material rather than operational status.

**Decision**: Display aggregated metrics only; remove raw logs and static documentation
**Rationale**: Executives need summaries; developers can access Logs/ folder directly
**Alternatives Considered**: Expandable log sections (rejected: clutters executive view)

---

### Q6: How should dashboard corruption be handled?

**Finding**: The vault folders (Inbox/, Done/, etc.) are the source of truth. Dashboard.md is a derived view that can be regenerated.

**Decision**: Regenerate from scratch if validation fails
**Rationale**: Simple recovery; vault state is always authoritative
**Alternatives Considered**: Incremental repair (rejected: complex; regeneration is fast)

---

## Technology Decisions

| Component | Decision | Rationale |
|-----------|----------|-----------|
| Dashboard Writer | `DashboardUpdater` class | Single-writer pattern already works |
| Update Frequency | 60 seconds (Scheduler) | Balances freshness and performance |
| Data Source | Vault folders + YAML frontmatter | Constitution-compliant |
| Output Format | Markdown tables and lists | Obsidian-compatible; LLM-readable |
| Validation | Section marker presence check | Lightweight; enables recovery |
| Weekly Summary | Generated from Done/ folder | Already has timestamp data |

---

## Unresolved Items

None. All research questions have been resolved with clear decisions.
