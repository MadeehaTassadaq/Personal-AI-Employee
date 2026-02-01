# Quickstart: Stable Executive Dashboard

**Feature**: 001-stable-dashboard
**Date**: 2026-02-01

## Overview

This guide explains how to validate and test the Stable Executive Dashboard implementation.

---

## Prerequisites

- Python 3.13+ installed
- Virtual environment activated (`.venv`)
- Backend dependencies installed (`uv pip install -e .`)
- Access to `AI_Employee_Vault/` directory

---

## Quick Validation

### 1. Check Dashboard Exists

```bash
cat AI_Employee_Vault/Dashboard.md
```

Expected: Dashboard with 9 sections in correct order.

### 2. Trigger Manual Update

```python
# From project root
from backend.services.dashboard_updater import update_dashboard_now
update_dashboard_now()
```

### 3. Verify Section Order

The dashboard MUST have sections in this exact order:
1. `# Digital FTE Dashboard` (Header)
2. `## System Status`
3. `## Pending Approvals`
4. `## Active Tasks`
5. `## Signals / Inputs`
6. `## Recently Completed`
7. `## Metrics`
8. `## Weekly Summary` (in `<details>` tag)
9. `## Quick Actions`

### 4. Verify Item Limits

Each section with dynamic content should show max 10 items:
- Pending Approvals: ≤10 rows
- Active Tasks: ≤10 rows
- Signals / Inputs: ≤10 items
- Recently Completed: ≤10 items

---

## Acceptance Tests

### Test 1: Executive Readability (SC-001)

**Goal**: Verify dashboard can be scanned in <2 minutes

**Procedure**:
1. Open `Dashboard.md` in Obsidian or VS Code
2. Start timer
3. Answer these questions:
   - How many pending approvals?
   - Is the File Watcher active?
   - What was the last completed task?
   - How many tasks completed today?
4. Stop timer

**Pass Condition**: All questions answered correctly in <2 minutes

---

### Test 2: Update Stability (SC-002)

**Goal**: Verify dashboard survives 100 consecutive updates

**Procedure**:
```python
from backend.services.dashboard_updater import DashboardUpdater
from pathlib import Path
import os

vault_path = Path(os.getenv("VAULT_PATH", "AI_Employee_Vault"))
updater = DashboardUpdater(vault_path)

for i in range(100):
    updater.update_dashboard()
    # Validate structure
    content = (vault_path / "Dashboard.md").read_text()
    assert "# Digital FTE Dashboard" in content
    assert "## System Status" in content
    assert "## Pending Approvals" in content
    print(f"Update {i+1}/100 OK")

print("PASS: Dashboard stable after 100 updates")
```

**Pass Condition**: No exceptions; all assertions pass

---

### Test 3: Section Order Consistency (FR-009)

**Goal**: Verify section order never changes

**Procedure**:
```python
expected_order = [
    "# Digital FTE Dashboard",
    "## System Status",
    "## Pending Approvals",
    "## Active Tasks",
    "## Signals / Inputs",
    "## Recently Completed",
    "## Metrics",
    "## Weekly Summary",
    "## Quick Actions"
]

content = open("AI_Employee_Vault/Dashboard.md").read()
positions = [content.find(marker) for marker in expected_order]

# All markers present
assert all(p >= 0 for p in positions), "Missing section markers"

# Order is correct
assert positions == sorted(positions), "Sections out of order"

print("PASS: Section order is correct")
```

---

### Test 4: Overflow Handling (Edge Case)

**Goal**: Verify dashboard handles >50 items gracefully

**Procedure**:
1. Create 55 test files in `Pending_Approval/`
2. Trigger dashboard update
3. Verify only 10 items shown with overflow indicator

```bash
# Create test files
for i in {1..55}; do
  echo "---\ntitle: Test Task $i\n---" > AI_Employee_Vault/Pending_Approval/test-$i.md
done

# Update dashboard
python -c "from backend.services.dashboard_updater import update_dashboard_now; update_dashboard_now()"

# Check output
grep -c "test-" AI_Employee_Vault/Dashboard.md  # Should be ≤10
grep "View all" AI_Employee_Vault/Dashboard.md  # Should show overflow text

# Cleanup
rm AI_Employee_Vault/Pending_Approval/test-*.md
```

---

### Test 5: Recovery from Corruption (Edge Case)

**Goal**: Verify dashboard regenerates if corrupted

**Procedure**:
1. Corrupt `Dashboard.md` by removing sections
2. Trigger update
3. Verify dashboard is regenerated correctly

```bash
# Corrupt the file
echo "CORRUPTED" > AI_Employee_Vault/Dashboard.md

# Trigger regeneration
python -c "from backend.services.dashboard_updater import update_dashboard_now; update_dashboard_now()"

# Verify recovery
grep "# Digital FTE Dashboard" AI_Employee_Vault/Dashboard.md && echo "PASS: Recovered"
```

---

## Common Issues

### Issue: Dashboard not updating

**Cause**: Scheduler not running

**Solution**: Start backend with `./scripts/run_backend.sh`

---

### Issue: Empty sections

**Cause**: Vault folders empty or missing

**Solution**: Ensure folder structure exists:
```bash
mkdir -p AI_Employee_Vault/{Inbox,Needs_Action,Pending_Approval,Approved,Done,Logs}
```

---

### Issue: Timestamps incorrect

**Cause**: System timezone mismatch

**Solution**: Set `TZ` environment variable or use UTC

---

## Automated Test Results

Run the full test suite:

```bash
uv run pytest tests/test_dashboard_stability.py -v
```

**Latest Results (2026-02-01)**:

```
tests/test_dashboard_stability.py::TestDashboardStability::test_section_order_consistency PASSED
tests/test_dashboard_stability.py::TestDashboardStability::test_5_consecutive_updates PASSED
tests/test_dashboard_stability.py::TestDashboardStability::test_100_consecutive_updates PASSED
tests/test_dashboard_stability.py::TestDashboardStability::test_overflow_handling PASSED
tests/test_dashboard_stability.py::TestDashboardStability::test_recovery_from_corruption PASSED
tests/test_dashboard_stability.py::TestDashboardStability::test_empty_vault PASSED
tests/test_dashboard_stability.py::TestDashboardStability::test_validate_dashboard_content_detects_missing_sections PASSED
tests/test_dashboard_stability.py::TestDashboardStability::test_validate_dashboard_content_detects_wrong_order PASSED
tests/test_dashboard_stability.py::TestDashboardStability::test_weekly_summary_empty_week PASSED
tests/test_dashboard_stability.py::TestDashboardStability::test_metrics_section_format PASSED
tests/test_dashboard_stability.py::TestDashboardPerformance::test_update_performance PASSED

============================== 11 passed in 1.42s ==============================
```

**Success Criteria Validated**:
- SC-002: 100 consecutive updates - PASS
- Performance: <2 seconds - PASS (1.42s)

---

## Validation Checklist

- [x] Dashboard exists at `AI_Employee_Vault/Dashboard.md`
- [ ] All 9 sections present in correct order
- [ ] System Status shows all components
- [ ] Pending Approvals has approve/reject instructions
- [ ] Item limits enforced (max 10 per section)
- [ ] Metrics show Today and This Week columns
- [ ] Weekly Summary is collapsible
- [ ] Quick Actions are static and present
- [ ] No Mermaid diagrams (removed for simplicity)
- [ ] LLM can parse section markers reliably
