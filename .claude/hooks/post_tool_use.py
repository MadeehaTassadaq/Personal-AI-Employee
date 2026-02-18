#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "toml",
# ]
# ///

"""
Post-Tool-Use Hook: Handle uv package management operations and dependency updates.

This hook runs after tool execution to:
1. Monitor package installation/uninstallation
2. Update lock files when needed
3. Validate dependency consistency
4. Clean up temporary files
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def get_project_dir() -> Path:
    """Get the project directory from environment or current working directory."""
    return Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd()))


def get_hook_input() -> dict:
    """Get hook input from Claude Code's $ARGUMENTS environment variable."""
    args_json = os.environ.get("ARGUMENTS", "{}")
    try:
        return json.loads(args_json)
    except json.JSONDecodeError:
        return {}


def update_lock_file():
    """Update the uv lock file after dependency changes."""
    try:
        result = subprocess.run(
            ["uv", "lock"],
            cwd=get_project_dir(),
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            print("✓ Lock file updated successfully", file=sys.stdout)
        else:
            print(f"⚠ Lock file update failed: {result.stderr}", file=sys.stderr)
    except subprocess.TimeoutExpired:
        print("⚠ Lock file update timed out", file=sys.stderr)
    except Exception as e:
        print(f"⚠ Lock file update error: {str(e)}", file=sys.stderr)


def validate_dependencies():
    """Validate that dependencies are consistent."""
    try:
        result = subprocess.run(
            ["uv", "sync", "--locked"],
            cwd=get_project_dir(),
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode != 0:
            print(f"⚠ Dependency validation failed: {result.stderr}", file=sys.stderr)
            return False
        return True
    except Exception as e:
        print(f"⚠ Dependency validation error: {str(e)}", file=sys.stderr)
        return False


def log_post_tool_action(tool_name: str, tool_input: dict, action: str, details: str = "") -> None:
    """Log post-tool actions to JSON file for audit trail."""
    log_dir = get_project_dir() / ".claude" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / "post_tool_use.json"

    entry = {
        "timestamp": datetime.now().isoformat(),
        "tool_name": tool_name,
        "tool_input": tool_input,
        "action": action,
        "details": details,
    }

    # Append to log file
    logs = []
    if log_file.exists():
        try:
            content = log_file.read_text().strip()
            if content:
                logs = json.loads(content)
        except (json.JSONDecodeError, IOError):
            logs = []

    logs.append(entry)

    # Keep only last 1000 entries
    if len(logs) > 1000:
        logs = logs[-1000:]

    log_file.write_text(json.dumps(logs, indent=2))


def handle_package_management(tool_name: str, tool_input: dict):
    """Handle package management related post-processing."""
    if tool_name == "Bash":
        command = tool_input.get("command", "")

        # Check if this was a package management command
        if any(pkg_cmd in command.lower() for pkg_cmd in [
            "uv pip install", "uv pip uninstall", "uv sync",
            "uv add", "uv remove", "pip install", "pip uninstall"
        ]):
            print("📦 Detected package management operation, updating lock file...", file=sys.stdout)
            update_lock_file()

            if validate_dependencies():
                print("✅ Dependencies validated successfully", file=sys.stdout)
            else:
                print("⚠ Dependencies may need attention", file=sys.stderr)

            log_post_tool_action(tool_name, tool_input, "PACKAGE_UPDATE", "Lock file updated after package operation")


def main():
    """Main hook entry point."""
    # Get hook input from $ARGUMENTS environment variable
    input_data = get_hook_input()

    # Extract tool information
    tool_name = input_data.get("tool", "")
    tool_input = input_data.get("input", {})
    tool_result = input_data.get("result", {})

    # Handle package management operations
    handle_package_management(tool_name, tool_input)

    # Log the post-tool action
    log_post_tool_action(tool_name, tool_input, "PROCESSED")

    # Exit 0 = continue execution
    sys.exit(0)


if __name__ == "__main__":
    main()
