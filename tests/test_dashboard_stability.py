"""Integration tests for Dashboard stability (T019-T021, T032-T034).

Tests verify:
- Section order consistency across updates
- No corruption after consecutive updates
- Recovery from corrupted state
- Overflow handling with many items
"""

import os
import sys
import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timezone

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.services.dashboard_updater import (
    DashboardUpdater,
    SECTION_ORDER,
    MAX_ITEMS_PER_SECTION,
)


class TestDashboardStability:
    """Integration tests for dashboard stability (T019)."""

    @pytest.fixture
    def temp_vault(self, tmp_path):
        """Create a temporary vault with required folder structure."""
        vault_path = tmp_path / "test_vault"
        vault_path.mkdir()

        # Create required folders
        folders = ["Inbox", "Needs_Action", "Pending_Approval", "Approved", "Done", "Logs"]
        for folder in folders:
            (vault_path / folder).mkdir()

        return vault_path

    @pytest.fixture
    def updater(self, temp_vault):
        """Create a DashboardUpdater instance for testing."""
        return DashboardUpdater(temp_vault)

    @pytest.fixture
    def populated_vault(self, temp_vault):
        """Create a vault with sample task files."""
        # Add sample inbox tasks
        for i in range(3):
            task_file = temp_vault / "Inbox" / f"task-{i}.md"
            task_file.write_text(f"""---
title: Test Task {i}
created: 2026-02-01
---

# Test Task {i}

Sample task content.
""")

        # Add sample pending approval tasks
        for i in range(2):
            task_file = temp_vault / "Pending_Approval" / f"approval-{i}.md"
            task_file.write_text(f"""---
title: Approval Task {i}
type: email
created: 2026-02-01T10:00:00+00:00
---

# Approval Task {i}

Waiting for approval.
""")

        # Add sample done tasks
        for i in range(5):
            task_file = temp_vault / "Done" / f"done-{i}.md"
            day = 20 + i  # Valid days: 20, 21, 22, 23, 24
            task_file.write_text(f"""---
title: Completed Task {i}
type: social
created: 2026-01-{day:02d}T12:00:00+00:00
---

# Completed Task {i}

Task completed.
""")

        return temp_vault

    def test_section_order_consistency(self, updater, temp_vault):
        """Verify all 9 section markers appear in correct order (T020)."""
        # Generate dashboard
        updater.update_dashboard()

        # Read generated content
        dashboard_path = temp_vault / "Dashboard.md"
        assert dashboard_path.exists(), "Dashboard.md should be created"

        content = dashboard_path.read_text()

        # Verify all section markers are present in order
        last_pos = -1
        for marker in SECTION_ORDER:
            pos = content.find(marker)
            assert pos != -1, f"Section marker '{marker}' should be present"
            assert pos > last_pos, f"Section marker '{marker}' should appear after previous sections"
            last_pos = pos

    def test_5_consecutive_updates(self, updater, populated_vault):
        """Verify no corruption after 5 consecutive updates (T021)."""
        dashboard_path = populated_vault / "Dashboard.md"

        for i in range(5):
            # Update dashboard
            updater.update_dashboard()

            # Verify dashboard exists and is valid
            assert dashboard_path.exists(), f"Dashboard should exist after update {i+1}"

            content = dashboard_path.read_text()

            # Check all sections present
            for marker in SECTION_ORDER:
                assert marker in content, f"Marker '{marker}' missing after update {i+1}"

            # Verify sections are in order
            assert updater._validate_dashboard_content(content), f"Validation failed after update {i+1}"

    def test_100_consecutive_updates(self, updater, populated_vault):
        """Verify stability after 100 consecutive updates (T032, SC-002)."""
        dashboard_path = populated_vault / "Dashboard.md"

        for i in range(100):
            updater.update_dashboard()

            # Validate every 10th update
            if i % 10 == 0:
                content = dashboard_path.read_text()
                assert updater._validate_dashboard_content(content), f"Validation failed at update {i+1}"

        # Final validation
        content = dashboard_path.read_text()
        assert updater._validate_dashboard_content(content), "Final validation failed"

    def test_overflow_handling(self, temp_vault):
        """Verify item limits work with 55 test files (T033)."""
        # Create 55 inbox tasks
        inbox_path = temp_vault / "Inbox"
        for i in range(55):
            task_file = inbox_path / f"overflow-task-{i:03d}.md"
            task_file.write_text(f"""---
title: Overflow Task {i}
---

# Overflow Task {i}
""")

        updater = DashboardUpdater(temp_vault)
        updater.update_dashboard()

        content = (temp_vault / "Dashboard.md").read_text()

        # Check that overflow indicator is present
        assert "View all" in content or f"({55})" in content, "Overflow indicator should be present"

        # Count items in Signals/Inputs section
        signals_section = content.split("## Signals / Inputs")[1].split("---")[0]
        item_count = signals_section.count("[[Inbox/")

        assert item_count <= MAX_ITEMS_PER_SECTION, f"Should limit to {MAX_ITEMS_PER_SECTION} items, found {item_count}"

    def test_recovery_from_corruption(self, updater, temp_vault):
        """Verify dashboard recovers from corrupted state (T034)."""
        dashboard_path = temp_vault / "Dashboard.md"

        # First, create a valid dashboard
        updater.update_dashboard()
        assert dashboard_path.exists()

        # Corrupt the dashboard by writing invalid content
        dashboard_path.write_text("# Corrupted Dashboard\n\nThis is not valid.")

        # Read corrupted content
        corrupted_content = dashboard_path.read_text()
        assert not updater._validate_dashboard_content(corrupted_content), "Corrupted content should fail validation"

        # Update should recover
        updater.update_dashboard()

        # Read recovered content
        recovered_content = dashboard_path.read_text()
        assert updater._validate_dashboard_content(recovered_content), "Recovered content should be valid"

        # All sections should be present
        for marker in SECTION_ORDER:
            assert marker in recovered_content, f"Recovered dashboard missing '{marker}'"

    def test_empty_vault(self, updater, temp_vault):
        """Verify dashboard handles empty vault gracefully."""
        updater.update_dashboard()

        content = (temp_vault / "Dashboard.md").read_text()

        # Should still have all sections
        for marker in SECTION_ORDER:
            assert marker in content, f"Empty vault dashboard missing '{marker}'"

        # Should indicate no items
        assert "No pending approvals" in content or "0 items" in content
        assert "No tasks in progress" in content or "No tasks" in content

    def test_validate_dashboard_content_detects_missing_sections(self, updater):
        """Verify validation detects missing sections."""
        # Content missing several sections
        incomplete_content = """# Digital FTE Dashboard

## System Status

| Component | Status |
|-----------|--------|

## Quick Actions

- Add task
"""
        assert not updater._validate_dashboard_content(incomplete_content), "Should detect missing sections"

    def test_validate_dashboard_content_detects_wrong_order(self, updater):
        """Verify validation detects out-of-order sections."""
        # Sections in wrong order
        wrong_order = """# Digital FTE Dashboard

## Quick Actions

- Add task

## System Status

| Component | Status |
|-----------|--------|
"""
        assert not updater._validate_dashboard_content(wrong_order), "Should detect wrong section order"

    def test_weekly_summary_empty_week(self, temp_vault):
        """Verify weekly summary handles empty week correctly."""
        updater = DashboardUpdater(temp_vault)
        updater.update_dashboard()

        content = (temp_vault / "Dashboard.md").read_text()

        # Should have weekly summary section
        assert "## Weekly Summary" in content
        assert "No completed tasks this period" in content

    def test_metrics_section_format(self, updater, populated_vault):
        """Verify metrics section has correct Today/This Week format."""
        updater.update_dashboard()

        content = (populated_vault / "Dashboard.md").read_text()

        # Check metrics table format
        assert "| Metric | Today | This Week |" in content
        assert "Tasks Completed" in content
        assert "Pending Approvals" in content


class TestDashboardPerformance:
    """Performance tests for dashboard updates."""

    @pytest.fixture
    def large_vault(self, tmp_path):
        """Create a vault with many files for performance testing."""
        vault_path = tmp_path / "large_vault"
        vault_path.mkdir()

        folders = ["Inbox", "Needs_Action", "Pending_Approval", "Approved", "Done", "Logs"]
        for folder in folders:
            (vault_path / folder).mkdir()

        # Create 100 done tasks
        done_path = vault_path / "Done"
        for i in range(100):
            task_file = done_path / f"done-{i:03d}.md"
            day = (i % 28) + 1  # Valid days: 1-28
            task_file.write_text(f"""---
title: Done Task {i}
type: email
created: 2026-01-{day:02d}T12:00:00+00:00
---

# Done Task {i}
""")

        return vault_path

    def test_update_performance(self, large_vault):
        """Verify dashboard update completes in under 2 seconds (T037)."""
        import time

        updater = DashboardUpdater(large_vault)

        start = time.time()
        updater.update_dashboard()
        elapsed = time.time() - start

        assert elapsed < 2.0, f"Update took {elapsed:.2f}s, should be under 2s"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
