---
name: monorepo-scaffolder
description: Scaffolds the Evolution-of-Todo monorepo using the Agentic Dev Stack (Claude Code + Spec-Kit Plus). Use when you must enforce the Phase 1–5 directory layout, governance docs, spec templates, Spec-Kit config, and uv workspace bootstrap before implementation work begins.
---

# Monorepo Scaffolder

## Overview

Use this skill to create (or re-baseline) the Evolution-of-Todo monorepo structure without touching code. It enforces phase isolation (`phases/phase-*`), centralized specs, Spec-Kit configuration, governance docs, and uv workspace wiring so that every feature starts from a consistent scaffold.

## Quick Start

1. **Confirm repo root**: Run commands from the intended monorepo root. Guardrails forbid modifying files outside the current repository.
2. **Execute the scaffold script**:
   ```bash
   bash .claude/skills/monorepo-scaffolder/scripts/scaffold_monorepo.sh $(pwd)
   ```
   - Optional: pass an explicit absolute path as the first argument.
3. **Review summary output** to ensure directories/files were created or left untouched if already compliant.

## What the Script Guarantees

1. **Directory Topology**
   - `specs/`
   - `phases/phase-1-console` through `phase-5-advanced-cloud`
   - `.spec-kit/`
2. **Governance Documents**
   - `CLAUDE.md` overwritten with `@AGENTS.md`
   - `AGENTS.md` rewritten with Evolution of Todo Constitution + mandatory rules
   - `README.md` reset with a high-level five-phase journey overview
3. **Spec Templates**
   - `specs/phase-1.md` … `specs/phase-5.md` created if missing, each with `Requirements / Tech Stack / Acceptance Criteria` headers only
4. **Spec-Kit Config**
   - `.spec-kit/config.yaml` maps every `phases/phase-*` directory to its matching `specs/phase-*.md`
5. **uv Workspace Bootstrap**
   - Creates a minimal `pyproject.toml` (if absent) with uv-compatible metadata and workspace members for all five phase directories.

All operations are idempotent: existing files are preserved unless governance docs need to be reset per requirements.

## Acceptance Checklist (Run After Script)

- [ ] `specs/` contains phase-1..phase-5 markdown templates with only the required headings
- [ ] `phases/` contains the five phase folders and no extra scaffolding
- [ ] `CLAUDE.md`, `AGENTS.md`, and `README.md` reflect the mandated content
- [ ] `.spec-kit/config.yaml` entries point to `specs/phase-x.md`
- [ ] `pyproject.toml` exists and lists all phase members under `[tool.uv.workspace]`

If any box is unchecked, rerun the script or patch manually—never start implementation without a clean scaffold (“No Task = No Code”).

## References

- `scripts/scaffold_monorepo.sh`: Primary automation entry point (read when auditing or patching behavior)
- `references/api_reference.md`: Operational notes, guardrails, and troubleshooting tips (load only when debugging edge cases)

This skill intentionally bundles no assets; scaffolding is handled entirely through shell commands for determinism.
