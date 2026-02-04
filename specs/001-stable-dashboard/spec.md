# Feature Specification: Stable Executive Dashboard

**Feature Branch**: `001-stable-dashboard`
**Created**: 2026-02-01
**Status**: Draft
**Input**: Digital FTE Dashboard UI Stabilization — Autonomous Workflow System with deterministic, executive-readable Markdown dashboard

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Executive Reviews System Status (Priority: P1)

As a CEO or executive user, I want to open the Dashboard.md file and immediately understand the current state of my Digital FTE system within 2 minutes, so I can make informed decisions about pending approvals and system health.

**Why this priority**: The primary value proposition of the Digital FTE is replacing human operational labor. If the executive cannot quickly assess system status, the entire value proposition fails. This is the core use case.

**Independent Test**: Open Dashboard.md in Obsidian or any Markdown viewer. Within 2 minutes, the reviewer can correctly identify: (1) number of pending approvals, (2) active tasks, (3) completed actions today, and (4) any system component failures.

**Acceptance Scenarios**:

1. **Given** the dashboard file exists, **When** the user opens it, **Then** they see a clear visual hierarchy with sections for System Status, Pending Approvals, Active Tasks, and Completed Actions in a consistent order.
2. **Given** there are 3 pending approvals, **When** the user views the Pending Approvals section, **Then** each approval shows: item name, type, creation time, and clear approve/reject guidance.
3. **Given** a system component is down, **When** the user views System Status, **Then** the failed component is visually distinct (marked with status indicator) and includes troubleshooting guidance.

---

### User Story 2 - Dashboard Updates Without Corruption (Priority: P2)

As a system operator, I want dashboard updates to be deterministic and collision-free, so that concurrent agent operations do not corrupt the dashboard file or create conflicting content.

**Why this priority**: Dashboard corruption undermines trust in the system. If the file becomes unreadable due to write collisions, the executive cannot use it, making this a critical reliability requirement.

**Independent Test**: Run 5 consecutive dashboard update operations. Verify the file structure remains intact after each update, with no duplicate sections, no orphaned content, and consistent formatting.

**Acceptance Scenarios**:

1. **Given** the dashboard file exists, **When** an agent updates the Pending Approvals section, **Then** only that section changes while all other sections remain unchanged.
2. **Given** two update requests arrive within 1 second, **When** updates are processed, **Then** both updates are applied without data loss or file corruption.
3. **Given** an update fails mid-write, **When** the next update runs, **Then** the dashboard recovers to a valid state automatically.

---

### User Story 3 - Weekly Executive Summary Generation (Priority: P3)

As an executive, I want a weekly summary section that aggregates completed work, pending items, and system metrics, so I can review the week's operational performance in one glance.

**Why this priority**: While not required for day-to-day operation, the weekly summary demonstrates the labor-replacement value of the Digital FTE by showing cumulative work output.

**Independent Test**: After 7 days of operation with logged activities, trigger summary generation. Verify the summary accurately reflects: total tasks completed, approval turnaround time, and action breakdown by type.

**Acceptance Scenarios**:

1. **Given** 7 days of task history exists, **When** the weekly summary is generated, **Then** it displays: tasks completed count, average time-to-approval, and actions by category (email, social, file operations).
2. **Given** no tasks were completed in a week, **When** the summary is generated, **Then** it clearly indicates "No completed tasks this period" rather than showing empty tables.

---

### Edge Cases

- What happens when the vault folder structure is missing expected directories (Inbox, Needs_Action, etc.)?
  - Dashboard displays a clear error message indicating which directories are missing
- What happens when a task file has malformed frontmatter?
  - Dashboard skips the malformed file and logs a warning, continuing to display valid tasks
- What happens when the dashboard file is opened while an update is in progress?
  - User sees either the pre-update or post-update state, never a partial write
- What happens when there are more than 50 pending items?
  - Dashboard shows the 10 most recent items with a clear "View all (50)" link/reference

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Dashboard MUST display a System Status section showing the operational state of all components (Vault, Watchers, MCP servers) with status indicators (Active/Stopped/Error)
- **FR-002**: Dashboard MUST display a Pending Approvals section listing all items in the `Pending_Approval/` folder with: item name, type, creation timestamp, and approval guidance
- **FR-003**: Dashboard MUST display an Active Tasks section listing all items in the `Needs_Action/` folder with: task name and current status
- **FR-004**: Dashboard MUST display a Recently Completed section listing items from the `Done/` folder, limited to the most recent 10 items, with completion timestamp
- **FR-005**: Dashboard MUST display a Signals/Inputs section showing new items in the `Inbox/` folder awaiting triage
- **FR-006**: Dashboard MUST include a Metrics section showing daily and weekly counts for: tasks completed, actions pending, emails sent, messages sent, and social posts made
- **FR-007**: Dashboard updates MUST follow a section-based update pattern where only the modified section is rewritten, preserving other sections
- **FR-008**: Dashboard MUST include a Last Updated timestamp that refreshes with each update
- **FR-009**: Dashboard MUST maintain a consistent section order that does not change between updates
- **FR-010**: Dashboard MUST be readable in any standard Markdown viewer without requiring special plugins or rendering engines

### Key Entities

- **Dashboard Section**: A discrete, labeled block of content (e.g., System Status, Pending Approvals) with defined boundaries, update rules, and display format
- **Task Item**: A file in the vault representing work to be done, with frontmatter metadata (type, status, timestamps) and body content
- **System Component**: A monitored service (Vault, Watcher, MCP Server) with operational state (Active, Stopped, Error) and troubleshooting reference

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Executive users can identify system status, pending approvals count, and active tasks within 2 minutes of opening the dashboard
- **SC-002**: Dashboard file structure remains valid (parseable, correct section order) after 100 consecutive update operations
- **SC-003**: No more than 1 dashboard corruption incident per 1000 update operations
- **SC-004**: 95% of dashboard content is visible "above the fold" (first 50 lines) for the most critical information
- **SC-005**: Weekly summary accurately reflects actual task counts with less than 5% variance from source data
- **SC-006**: Hackathon judges can explain the Digital FTE workflow (Watcher → Reasoning → Action → Approval → Logging) after reviewing the dashboard and documentation for 10 minutes

## Assumptions

- The Obsidian vault folder structure (`Inbox/`, `Needs_Action/`, `Pending_Approval/`, `Approved/`, `Done/`, `Logs/`) exists and is maintained by the system
- Task files use YAML frontmatter for metadata (type, status, timestamps)
- Dashboard updates are triggered by a single orchestration process, not multiple concurrent writers
- Users view the dashboard in a Markdown-compatible viewer (Obsidian, VS Code, GitHub)
- The system has been running long enough to have task history for weekly summaries

## Constraints

- Dashboard format is Markdown only — no web UI, no frontend frameworks
- All state is file-based and must be auditable through version control
- Architecture remains local-first; no cloud dependencies for core dashboard functionality
- Changes must be completable within hackathon timeline (no speculative future features)
- Dashboard must remain LLM-readable for agent processing

## Out of Scope

- Graphical or web-based dashboard rendering
- Real-time live-updating dashboard (batch updates are acceptable)
- New agent capabilities beyond existing architecture
- SaaS or hosted platform features
- Vendor comparisons or market analysis
- Fully autonomous irreversible actions
