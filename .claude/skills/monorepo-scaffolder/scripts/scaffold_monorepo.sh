#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${1:-$(pwd)}"

echo "🛠️  Scaffolding Evolution-of-Todo monorepo under ${ROOT_DIR}" >&2

mkdir -p "${ROOT_DIR}/specs"
mkdir -p "${ROOT_DIR}/phases/phase-1-console"
mkdir -p "${ROOT_DIR}/phases/phase-2-webapp"
mkdir -p "${ROOT_DIR}/phases/phase-3-ai-agent"
mkdir -p "${ROOT_DIR}/phases/phase-4-local-k8s"
mkdir -p "${ROOT_DIR}/phases/phase-5-advanced-cloud"
mkdir -p "${ROOT_DIR}/.spec-kit"

cat <<'EOF' > "${ROOT_DIR}/CLAUDE.md"
@AGENTS.md
EOF

cat <<'EOF' > "${ROOT_DIR}/AGENTS.md"
# Evolution of Todo Constitution

- No Task = No Code
- Specify → Plan → Tasks → Implement
- Never modify architecture without updating speckit.plan
EOF

cat <<'EOF' > "${ROOT_DIR}/README.md"
# Evolution of Todo: Five-Phase Journey

This monorepo guides the product from a simple CLI into a cloud-native AI platform:

1. **Phase 1 – Console Todo**: Solidify CLI fundamentals, task modeling, and Spec → Plan → Tasks discipline.
2. **Phase 2 – Web App**: Introduce a modern UI, shared services, and browser-focused workflows.
3. **Phase 3 – AI Agent**: Layer intelligent assistance and agentic orchestration on top of core services.
4. **Phase 4 – Local K8s**: Validate containerized deployments, local clusters, and operations tooling.
5. **Phase 5 – Advanced Cloud**: Production-grade cloud rollout with automation, observability, and governance.

Each phase owns its implementation folder under `phases/` and central specifications live in `specs/phase-x.md`.
EOF

cat <<'EOF' > "${ROOT_DIR}/.spec-kit/config.yaml"
phases:
  phase-1-console:
    spec: specs/phase-1.md
  phase-2-webapp:
    spec: specs/phase-2.md
  phase-3-ai-agent:
    spec: specs/phase-3.md
  phase-4-local-k8s:
    spec: specs/phase-4.md
  phase-5-advanced-cloud:
    spec: specs/phase-5.md
EOF

create_spec_template() {
  local phase_label="$1"
  local file_name="$2"
  local spec_path="${ROOT_DIR}/specs/${file_name}"

  if [[ -f "${spec_path}" ]]; then
    echo "• ${file_name} already exists; leaving in place" >&2
    return
  fi

  cat <<EOF > "${spec_path}"
# ${phase_label}

## Requirements

## Tech Stack

## Acceptance Criteria
EOF
}

create_spec_template "Phase 1 – Console" "phase-1.md"
create_spec_template "Phase 2 – Web App" "phase-2.md"
create_spec_template "Phase 3 – AI Agent" "phase-3.md"
create_spec_template "Phase 4 – Local K8s" "phase-4.md"
create_spec_template "Phase 5 – Advanced Cloud" "phase-5.md"

PYPROJECT_PATH="${ROOT_DIR}/pyproject.toml"
if [[ ! -f "${PYPROJECT_PATH}" ]]; then
  cat <<'EOF' > "${PYPROJECT_PATH}"
[project]
name = "evolution-of-todo"
version = "0.1.0"
description = "Evolution of Todo monorepo scaffold"
requires-python = ">=3.11"
dependencies = []

[tool.uv.workspace]
members = [
  "phases/phase-1-console",
  "phases/phase-2-webapp",
  "phases/phase-3-ai-agent",
  "phases/phase-4-local-k8s",
  "phases/phase-5-advanced-cloud",
]
EOF
  echo "• Created root pyproject.toml for uv workspace" >&2
else
  echo "• pyproject.toml already present; verify uv config manually" >&2
fi

cat <<'EOF'
✅ Evolution-of-Todo scaffold ensured.
- specs/phase-*.md templates present
- phases/* directories prepared
- Governance docs (CLAUDE.md, AGENTS.md, README.md) reset
- .spec-kit/config.yaml linked to specs
- Root pyproject.toml created when missing with uv workspace members
EOF
