---
id: 001
title: Initial Constitution Ratification
stage: constitution
date: 2026-02-01
surface: agent
model: claude-opus-4-5-20251101
feature: none
branch: master
user: madeeha
command: /sp.constitution
labels: ["constitution", "governance", "principles", "initial-setup"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .specify/memory/constitution.md
tests:
  - N/A (governance document)
---

## Prompt

# /sp.constitution

## Project
**Digital FTE (Personal AI Employee)**
An AI-native, local-first autonomous agent system that functions as a full-time digital employee, managing personal and business workflows through continuous perception, reasoning, and action.

---

## Problem Statement
Existing automation tools are reactive, fragmented, and UI-dependent.
Chatbots wait for prompts, and dashboards visualize data but do not act.

There is no unified system that behaves like a **human employee**—one that:
- Monitors continuously
- Reasons across domains
- Acts autonomously
- Escalates to humans only when required

---

## Solution Overview
The Digital FTE is a **local-first, agent-driven system** composed of:

- **Claude Code** — reasoning and planning engine
- **Obsidian (Markdown)** — system of record, memory, and audit layer
- **Watchers (Python)** — continuous perception (email, WhatsApp, files, finance)
- **MCP Servers** — controlled action execution layer
- **Human-in-the-Loop (HITL)** — file-based approvals for sensitive actions
- **Ralph Wiggum Loop** — guarantees task completion and prevents agent laziness

The system runs continuously, converts signals into tasks, plans actions, requests approval when required, executes safely, and logs all decisions.

---

## Current Implementation Status
### Implemented
- Watcher → Vault → Claude Code → MCP → Approval → Action loop
- File-based HITL approval mechanism
- Obsidian vault as canonical state and audit log
- Multi-step autonomous task execution

### Known Limitation
- The **Dashboard UI (`Dashboard.md`)** is functional but **visually cluttered and inconsistent**, reducing clarity.

This is a **UI/UX refinement issue**, not a core architectural problem.

---

## Improvement Focus (Active Work)
Current development is focused on **stabilizing and improving the dashboard UI**, not expanding scope.

Planned improvements:
- Enforce single-writer rule for `Dashboard.md`
- Separate sections for:
  - Signals
  - Active Tasks
  - Pending Approvals
  - Completed Actions
- Deterministic layout to prevent agent write collisions
- Clear visual hierarchy for executive-level review
- Maintain Markdown-native design for locality and auditability

---

## Core Principles
- **Local-First** — sensitive data remains on-device
- **Autonomy with Accountability** — AI acts, humans approve risk
- **File-as-API** — Markdown files are the system contract
- **Reproducibility** — every decision is traceable
- **Engineering over Prompting** — agent systems, not chatbots

---

## Scope Boundaries
### In Scope
- Personal and business workflow automation
- Continuous monitoring via watchers
- Multi-step reasoning and execution
- MCP-based external actions
- Human approval workflows

### Out of Scope
- Fully graphical web dashboards
- Black-box SaaS automation
- Irreversible autonomous actions without approval

---

## Success Criteria
- System operates continuously without manual prompts
- All sensitive actions require explicit human approval
- Dashboard is readable in under 2 minutes
- System recovers gracefully from failures
- Complete audit trail of actions and decisions

---

## Definition of Done
The Digital FTE is considered production-ready when:
- Dashboard UI is stable, readable, and collision-free
- Weekly executive summary is generated autonomously
- System runs unattended for 7+ days
- No action occurs without traceable approval

---

## Why This Project Matters
This project reframes AI from a **tool** into a **unit of labor**.

A Digital FTE:
- Operates 24/7 (~8,760 hours/year)
- Costs a fraction of a human FTE
- Scales instantly
- Acts with predictable, auditable behavior

This is not a chatbot.
This is **AI-native software engineering**.

## Response snapshot

Created and ratified the initial Digital FTE constitution at `.specify/memory/constitution.md` version 1.0.0.

The constitution includes:
- **5 Core Principles**: Local-First, Autonomy with Accountability, File-as-API, Reproducibility, Engineering over Prompting
- **Scope Boundaries**: Clear in-scope and out-of-scope definitions
- **Success Criteria**: Measurable outcomes for production readiness
- **Definition of Done**: Specific conditions for considering the system production-ready
- **Governance**: Amendment process, version policy, and compliance requirements

All templates verified as compatible. No follow-up actions required.

## Outcome

- Impact: Initial constitution established; governance framework in place for all future development
- Tests: N/A (governance document)
- Files: .specify/memory/constitution.md (created)
- Next prompts: Consider /sp.adr for significant architectural decisions; use constitution as reference for all implementation planning
- Reflection: Constitution successfully derived from detailed user input; all 5 principles mapped with non-negotiable rules and rationale

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Monitor constitution compliance during feature development
