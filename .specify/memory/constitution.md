<!--
SYNC IMPACT REPORT
==================
Version Change: N/A → 1.0.0 (Initial constitution)
Bump Type: MAJOR (Initial ratification)

Modified Principles: N/A (Initial creation)

Added Sections:
- I. Local-First
- II. Autonomy with Accountability
- III. File-as-API
- IV. Reproducibility
- V. Engineering over Prompting
- Scope Boundaries
- Success Criteria
- Definition of Done
- Governance

Removed Sections: N/A

Templates Status:
- .specify/templates/plan-template.md ✅ Compatible (Constitution Check section exists)
- .specify/templates/spec-template.md ✅ Compatible (requirements structure aligned)
- .specify/templates/tasks-template.md ✅ Compatible (phase-based approach aligned)

Deferred Items: None

Follow-up TODOs: None
==================
-->

# Digital FTE (Personal AI Employee) Constitution

## Vision

An AI-native, local-first autonomous agent system that functions as a full-time digital employee, managing personal and business workflows through continuous perception, reasoning, and action.

## Problem Statement

Existing automation tools are reactive, fragmented, and UI-dependent. Chatbots wait for prompts, and dashboards visualize data but do not act.

There is no unified system that behaves like a **human employee**—one that:
- Monitors continuously
- Reasons across domains
- Acts autonomously
- Escalates to humans only when required

## Core Principles

### I. Local-First

Sensitive data MUST remain on-device. The system operates as a local-first, agent-driven architecture with no mandatory cloud dependencies for core functionality.

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
- The approval workflow MUST be file-based through the `Pending_Approval/` → `Approved/` folder mechanism
- Auto-approved actions are limited to: reading vault files, moving files between lifecycle folders, updating the Dashboard, and creating drafts
- Every action MUST be logged with timestamp, action type, and outcome
- The system MUST NOT execute irreversible actions without approval

**Rationale:** Autonomy enables 24/7 operation, but human oversight ensures accountability and prevents unintended consequences.

### III. File-as-API

Markdown files in the Obsidian vault serve as the system's primary interface and contract.

**Non-Negotiable Rules:**
- The vault folder structure (`Inbox/`, `Needs_Action/`, `Pending_Approval/`, `Approved/`, `Done/`) defines the task lifecycle state machine
- Task state transitions MUST be accomplished by moving files between folders
- The `Dashboard.md` file MUST provide a real-time executive summary of system state
- All inter-component communication that persists state MUST go through the vault
- File formats MUST be human-readable Markdown with optional YAML frontmatter

**Rationale:** Files are inspectable, version-controllable, and tool-agnostic. This approach ensures transparency and enables integration with any Markdown-aware tooling.

### IV. Reproducibility

Every decision and action MUST be traceable through a complete audit trail.

**Non-Negotiable Rules:**
- All agent decisions MUST be logged in the `Logs/` folder with reasoning context
- Task files MUST include history of state transitions and actions taken
- The system MUST support replay and debugging of past decisions
- PHR (Prompt History Records) MUST be created for significant interactions
- ADRs (Architecture Decision Records) MUST document significant architectural choices

**Rationale:** Reproducibility enables debugging, compliance verification, and continuous improvement of agent behavior.

### V. Engineering over Prompting

The Digital FTE is an engineered agent system, not a chatbot wrapper.

**Non-Negotiable Rules:**
- The system MUST operate continuously without manual prompts (via watchers)
- Agent behavior MUST be defined through skills, not ad-hoc prompting
- The Ralph Wiggum Loop MUST guarantee task completion and prevent agent laziness
- MCP servers MUST be used for all external service integrations
- Failures MUST be handled gracefully with retry logic and escalation

**Rationale:** Production systems require deterministic behavior, fault tolerance, and maintainability—qualities achieved through software engineering, not prompt engineering.

## Scope Boundaries

### In Scope
- Personal and business workflow automation
- Continuous monitoring via watchers (filesystem, email, WhatsApp, LinkedIn)
- Multi-step reasoning and execution through Claude Code
- MCP-based external actions (Gmail, WhatsApp, LinkedIn, calendar)
- Human approval workflows for sensitive actions
- Executive dashboards and weekly briefings

### Out of Scope
- Fully graphical web dashboards (Markdown-native design is authoritative)
- Black-box SaaS automation without audit trails
- Irreversible autonomous actions without approval
- Real-time streaming interfaces (batch processing is acceptable)

## Success Criteria

- System operates continuously without manual prompts
- All sensitive actions require explicit human approval
- Dashboard is readable and actionable in under 2 minutes
- System recovers gracefully from failures without data loss
- Complete audit trail of all actions and decisions
- Weekly executive summary is generated autonomously

## Definition of Done

The Digital FTE is considered production-ready when:
- Dashboard UI is stable, readable, and collision-free
- Weekly executive summary is generated autonomously and accurately
- System runs unattended for 7+ days without critical failures
- No action occurs without traceable approval
- All five core principles are demonstrably enforced

## Governance

### Amendment Process
1. Proposed amendments MUST be documented with rationale
2. Amendments MUST be reviewed against existing principles for conflicts
3. Breaking changes to principles require MAJOR version bump
4. All amendments MUST update the `LAST_AMENDED_DATE`

### Version Policy
- **MAJOR**: Backward-incompatible principle changes or removals
- **MINOR**: New principles added or existing principles expanded
- **PATCH**: Clarifications, wording improvements, non-semantic changes

### Compliance
- All PRs and code reviews MUST verify compliance with this constitution
- The Constitution Check in `plan-template.md` MUST be passed before implementation
- Violations MUST be documented and resolved before merge

**Version**: 1.0.0 | **Ratified**: 2026-02-01 | **Last Amended**: 2026-02-01
