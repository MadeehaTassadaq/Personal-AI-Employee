<!--
SYNC IMPACT REPORT
==================
Version Change: 1.0.0 → 2.0.0
Bump Type: MAJOR (Critical gaps identified, full rewrite for clarity)
Modified Principles: Expanded with "Critical Shortcomings" section
Added Sections:
- VI. Critical Shortcomings (NEW)
- VII. Tier Realities (NEW)
- VIII. Implementation Priorities (NEW)
Removed Sections: N/A
Templates Status: Pending (needs re-alignment)
Deferred Items:
- Add spec.md, plan.md, implement.md, tasks.md templates
- Re-align Silver Tier completion criteria
Follow-up TODOs:
- Create spec-driven development templates
- Implement critical fixes for Silver tier stability
==================
-->

# Digital FTE (Personal AI Employee) Constitution

> **Version:** 2.0.0
> **Ratified:** 2026-02-12
> **Last Amended:** 2026-02-12
> **Amendment Type:** MAJOR (Critical gaps identified, complete rewrite for Silver tier stability)

---

## Vision

An AI-native, local-first autonomous agent system that functions as a full-time digital employee, managing personal and business workflows through continuous perception, reasoning, and action.

## Problem Statement

Existing automation tools are reactive, fragmented, and UI-dependent. Chatbots wait for prompts, and dashboards visualize data but do not act.

There is no unified system that behaves like a **human employee**—one that:
- Monitors continuously (via watchers)
- Reasons across domains (personal + business)
- Acts autonomously (within approved boundaries)
- Escalates to humans only when required (approval needed)

---

## Core Principles

### I. Local-First

**Sensitive data MUST remain on-device. The system operates as a local-first, agent-driven architecture with no mandatory cloud dependencies for core functionality.**

**Non-Negotiable Rules:**
- All task state, memory, and audit logs MUST be stored in the local Obsidian vault
- External services are accessed only through controlled MCP servers
- No telemetry or data sharing without explicit user consent
- Credentials and secrets MUST be stored locally in environment files, never committed to version control

**Rationale:** Privacy and data sovereignty are fundamental. Users retain full control over their information and can operate the system in air-gapped environments if needed.

### II. Autonomy with Accountability

The AI agent acts autonomously within defined boundaries, but humans approve all risk-bearing actions.

**Non-Negotiable Rules:**
- Actions classified as sensitive (email sending, social media posting, financial transactions) MUST require explicit human approval
- The approval workflow MUST be file-based through `Pending_Approval/` → `Approved/` folder mechanism
- Auto-approved actions are limited to: reading vault files, moving files between lifecycle folders, updating `Dashboard.md`, and creating drafts
- Every action MUST be logged with timestamp, action type, platform, actor, and outcome

**Approval Matrix:**

| Action Category | Requires Approval | Rationale |
|----------------|-------------------|-----------|
| Financial (Odoo invoices/expenses) | **Yes** | Affects real money |
| Public Posting (social media) | **Yes** | Public, irreversible |
| Direct Messaging (WhatsApp/Email) | **Yes** | Represents user to contacts |
| Vault Operations (read/move) | **No** | Internal data organization |
| Dashboard Updates | **No** | System status tracking |
| Draft Creation | **No** | Creates files, doesn't execute actions |

**Rationale:** Autonomy enables 24/7 operation, but human oversight ensures accountability and prevents unintended consequences.

### III. File-as-API

Markdown files in the Obsidian vault serve as the system's primary interface and contract.

**Non-Negotiable Rules:**
- The vault folder structure (`Inbox/`, `Needs_Action/`, `Pending_Approval/`, `Approved/`, `Done/`) defines the task lifecycle state machine
- Task state transitions MUST be accomplished by moving files between folders
- The `Dashboard.md` file MUST provide a real-time executive summary of system state
- All inter-component communication that persists state MUST go through the vault
- File formats MUST be human-readable Markdown with optional YAML frontmatter

**Vault Structure:**

| Folder | Purpose | Lifecycle Stage |
|---------|-----------|----------------|
| `Inbox/` | New incoming tasks from watchers | New |
| `Needs_Action/` | Tasks being processed by Ralph | In Progress |
| `Pending_Approval/` | Actions awaiting human review | Awaiting Approval |
| `Approved/` | Approved actions ready to execute | Ready |
| `Done/` | Completed tasks (archive) | Complete |

**Key Files:**

| File | Purpose | Update Frequency |
|------|-----------|----------------|
| `Dashboard.md` | Real-time executive summary | Every 30 seconds |
| `Company_Handbook.md` | Operational rules, approval policies | Per user change |
| `Business_Goals.md` | KPIs, revenue targets, alert thresholds | Per user change |

**Rationale:** Files are inspectable, version-controllable, and tool-agnostic. This approach ensures transparency and enables integration with any Markdown-aware tooling.

### IV. Reproducibility

Every decision and action MUST be traceable through a complete audit trail.

**Non-Negotiable Rules:**
- All agent decisions MUST be logged in the `Logs/` folder with reasoning context
- Task files MUST include history of state transitions and actions taken
- The system MUST support replay and debugging of past decisions
- All external service calls (MCP servers) MUST include correlation IDs
- PHR (Prompt History Records) MUST be created for significant interactions

**Audit Trail Requirements:**

| Audit Type | Location | Retention | Content |
|-------------|-----------|----------|----------|
| Activity Log | `Logs/YYYY-MM-DD.json` | Daily rotation | All watcher events |
| System Audit | `Audit/YYYY-MM-DD.json` | Quarterly rotation | Correlation ID tracking |
| Task History | Task files | Permanent | Complete reasoning record |
| Correlation IDs | All requests | Per runtime | End-to-end tracing |

**Rationale:** Reproducibility enables debugging, compliance verification, and continuous improvement of agent behavior.

### V. Engineering Over Prompting

The Digital FTE is an engineered agent system, not a chatbot wrapper.

**Non-Negotiable Rules:**
- The system MUST operate continuously without manual prompts (via watchers)
- Agent behavior MUST be defined through skills and MCP servers, not ad-hoc prompting
- The Ralph Wiggum Loop MUST guarantee task completion and prevent agent laziness
- MCP servers MUST be used for all external service integrations
- Failures MUST be handled gracefully with retry logic and circuit breakers

**The Ralph Wiggum Mandate:**

> "The Ralph Wiggum Loop MUST guarantee task completion and prevent agent laziness."

**Implementation:**
- Stops Claude from exiting prematurely when task is incomplete
- Feeds prompts back with previous output context
- Enforces step limits (50 max) and timeouts (5 minutes per step)
- Maintains checkpoint every 10 steps for human approval
- Continues until task file is in `Done/` folder

**Rationale:** Production systems require deterministic behavior, fault tolerance, and maintainability—qualities achieved through software engineering, not prompt engineering.

---

## Scope Boundaries

### In Scope

**Personal and business workflow automation:**
- Continuous monitoring via watchers (filesystem, email, WhatsApp, LinkedIn)
- Multi-step reasoning and execution through Claude Code
- MCP-based external actions (Gmail, WhatsApp, LinkedIn, calendar)
- Human approval workflows for sensitive actions
- Executive dashboards and weekly briefings

**Out of Scope:**
- Fully graphical web dashboards (Markdown-native design is authoritative)
- Black-box SaaS automation without audit trails
- Irreversible autonomous actions without approval
- Real-time streaming interfaces (batch processing is acceptable)

---

## Success Criteria

The Digital FTE is considered production-ready when:
1. Dashboard UI is stable, readable, and loads without errors
2. Weekly executive summary is generated autonomously and accurately
3. System runs unattended for 7+ days without critical failures
4. No action occurs without traceable approval (when required)
5. Complete audit trail of all actions and decisions
6. All five core principles are demonstrably enforced

### Silver Tier Completion

- [ ] All watchers run without crashing for 24+ hours
- [ ] Tasks flow correctly: Inbox → Needs_Action → Pending_Approval → Approved → Done
- [ ] Ralph autonomously processes at least one task end-to-end per day
- [ ] Approval workflow UI functional with approve/reject capability
- [ ] Dashboard accurately reflects system state in real-time
- [ ] At least one MCP server sends real data (email or message)
- [ ] No console errors in dashboard or backend
- [ ] Complete audit trail of all system activities

### Gold Tier Completion

All Silver criteria plus:
- [ ] Odoo accounting workflow creates real invoices and expenses
- [ ] At least 3 social platforms auto-posting with engagement tracking
- [ ] CEO briefing generates weekly on schedule (Monday 9 AM)
- [ ] Error recovery handles all failure modes gracefully
- [ ] System operates 30+ days without manual intervention
- [ ] Complete documentation (README, API docs, architecture diagrams)
- [ ] Performance baseline established with monitoring

---

## Governance

### Amendment Process

1. Proposed amendments MUST be documented with rationale
2. Amendments MUST be reviewed against existing principles for conflicts
3. Breaking changes to principles require MAJOR version bump
4. All amendments MUST update the `LAST_AMENDED_DATE`
5. Technical disagreements resolved through code testing

### Version Policy

- **MAJOR**: Backward-incompatible principle changes or removals
- **MINOR**: New principles added or existing principles expanded
- **PATCH**: Clarifications, wording improvements, non-semantic changes

---

## VI. Critical Shortcomings

### Current Issues Preventing Gold Tier Achievement

Based on comprehensive codebase analysis, the following critical gaps must be addressed:

### 1. Task Flow Breakdown

**Issue:** Tasks are being completed in `Done/` folder but watchers are not consistently creating new tasks in `Inbox/`. The Ralph Wiggum loop may not be finding tasks in `Needs_Action/` to process.

**Symptoms:**
- Dashboard shows "Inbox is empty" despite system running
- `Done/` folder has 70+ completed tasks but few new tasks
- Ralph status shows "no tasks to process"

**Required Fixes:**
- Verify all watchers write to correct vault path (`VAULT_PATH` environment variable)
- Ensure Ralph scans `Needs_Action/` not a hardcoded path
- Add logging to show where Ralph is looking for tasks
- Test end-to-end: create task → verify it appears → Ralph processes → moves to Done

### 2. Dashboard UI Integration Issues

**Issue:** Dashboard components exist but may not be correctly displaying data from API endpoints.

**Symptoms:**
- Import paths fixed (`./components/` → `./components/` correct)
- Dashboard at http://localhost:5174 serves HTML shell
- WebSocket connection may not be established
- Real-time updates not reflecting

**Required Fixes:**
- Verify all API endpoints return correct data structures
- Ensure WebSocket at `/ws/activity` is connectable
- Add loading states for all async operations
- Handle error states gracefully in UI
- Verify `useApi` hook matches backend response formats

### 3. MCP Server Implementation Gaps

**Issue:** Most MCP servers are empty shells with only `__init__.py` and minimal code. They don't implement actual external service connections.

**Status by MCP Server:**

| MCP Server | Implementation Status | Required Action |
|-------------|-------------------|----------------|
| Gmail MCP | Partial | Complete `send_email` and `list_emails` tools |
| WhatsApp MCP | Complete | Verify session persistence works |
| LinkedIn MCP | Partial | Complete post creation |
| Facebook MCP | Partial | Complete page posting |
| Instagram MCP | Partial | Complete image/carousel posting |
| Twitter MCP | Partial | Complete tweet creation |
| Calendar MCP | Partial | Complete event management |
| Odoo MCP | Partial | Complete invoice/expense creation |
| Browser MCP | Complete | Already functional |

**Required Fix:** For each partially implemented MCP server, implement all required tools following the MCP stdio protocol.

### 4. Watcher Reliability Issues

**Issue:** Individual watchers may crash without proper error handling or auto-restart.

**Required Fixes:**
- Implement circuit breaker pattern in orchestrator
- Add health check endpoints for each watcher
- Implement exponential backoff for external API rate limits
- Add proper logging for all watcher failures
- Ensure graceful degradation when one watcher fails

### 5. Ralph Wiggum Integration

**Issue:** Ralph exists and is sophisticated but may not be properly integrated with watchers and approval workflow.

**Required Fixes:**
- Verify Ralph reads from correct `Needs_Action/` path
- Ensure Ralph creates approval files in `Pending_Approval/` correctly
- Test approval checkpoint mechanism every 10 steps
- Verify Ralph moves completed tasks to `Done/`
- Add visibility into Ralph's current task in dashboard

### 6. Missing Configuration Validation

**Issue:** System starts without validating that required configuration exists.

**Required Fixes:**
- Add startup validation for vault folder existence
- Verify `.env` file has all required variables
- Check MCP server availability before starting watchers
- Provide clear error messages for missing configuration
- Add setup wizard or configuration script

### 7. Testing and Documentation Gaps

**Issue:** No comprehensive integration tests verify end-to-end functionality.

**Required Fixes:**
- Create integration test suite covering full task lifecycle
- Test watcher → Ralph → approval → execution flow
- Test dashboard with mock backend
- Add performance tests for concurrent operations
- Create demo script showing all features
- Document troubleshooting steps for common issues

---

## VII. Tier Realities

### Actual Current State: Silver Tier (Mostly Complete)

**What Works:**
- Vault structure with all folders and key files
- File watcher, Gmail watcher, WhatsApp watcher operational
- Ralph Wiggum autonomous loop implemented
- Orchestrator service manages all components
- FastAPI backend with WebSocket support
- React dashboard with sidebar navigation
- Human-in-the-loop approval workflow (file-based)
- Multiple MCP servers with stdio protocol structure
- Audit logging to `Logs/` and `Audit/` folders

**What Doesn't Work:**
- Dashboard not displaying real vault data correctly
- Task flow broken (watchers → Ralph disconnect)
- Most MCP servers are empty shells
- Social media watchers (LinkedIn, Facebook, Instagram, Twitter) not operational
- No end-to-end testing of complete workflows
- Missing comprehensive documentation

**Gap Analysis:** The system has achieved approximately **70% of Silver tier** completion. The primary blockers are:
1. Dashboard integration with backend (data flow issues)
2. MCP server implementations (empty shells)
3. Missing end-to-end workflow verification
4. Configuration and setup documentation

---

## VIII. Implementation Priorities

### Immediate (Week 1)

**Priority: CRITICAL - Fix Dashboard Data Flow**

1. Fix API response format mismatches
2. Ensure all components render without errors
3. Verify WebSocket real-time updates work
4. Add proper error handling in useApi hook
5. Test all dashboard sections display correctly

**Priority: HIGH - Fix Task Flow**

1. Verify watchers write to correct `Inbox/` folder
2. Ensure Ralph reads from `Needs_Action/` correctly
3. Test complete task lifecycle end-to-end
4. Add visibility into task processing pipeline
5. Fix approval workflow display

### Short-term (Weeks 2-3)

**Priority: HIGH - Complete MCP Implementations**

1. Implement all tools in Gmail MCP (send_email, list_emails)
2. Complete LinkedIn MCP posting functionality
3. Complete Facebook MCP page posting
4. Complete Instagram MCP image/carousel posting
5. Complete Twitter MCP tweet creation
6. Complete Calendar MCP event management
7. Complete Odoo MCP invoice/expense workflow

**Priority: MEDIUM - Watcher Reliability**

1. Add health check endpoints
2. Implement circuit breaker pattern
3. Add exponential backoff for rate limits
4. Improve error handling and logging
5. Add watcher auto-restart on failure

### Medium-term (Weeks 4-6)

**Priority: MEDIUM - Testing and Documentation**

1. Create integration test suite
2. Add performance monitoring
3. Create setup wizard and configuration guide
4. Document all API endpoints
5. Create troubleshooting guide
6. Record demo video showing key features

---

## Compliance

All implementations MUST verify compliance with this constitution before merge. Violations MUST be documented and resolved.

---

**Version:** 2.0.0 | **Ratified:** 2026-02-12 | **Last Amended:** 2026-02-12

*This constitution is the authoritative source of truth for the Personal AI Employee project. All development decisions should reference this document.*
