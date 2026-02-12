#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
Pre-Tool-Use Hook: Enforce uv package manager and security guardrails.

This hook intercepts tool calls before execution to:
1. Block pip/pip3 commands and suggest uv alternatives
2. Prevent dangerous file operations (.env access, rm -rf)
3. Log all tool usage for audit purposes

Exit codes:
- 0: Allow tool execution
- 2: Block tool execution (stderr message shown to Claude)
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path


def get_project_dir() -> Path:
    """Get the project directory from environment or current working directory."""
    return Path(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd()))


def log_tool_use(tool_name: str, tool_input: dict, action: str, reason: str = "") -> None:
    """Log tool usage to JSON file for audit trail."""
    log_dir = get_project_dir() / ".claude" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / "pre_tool_use.json"

    entry = {
        "timestamp": datetime.now().isoformat(),
        "tool_name": tool_name,
        "tool_input": tool_input,
        "action": action,
        "reason": reason,
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


def is_pip_command(command: str) -> tuple[bool, str]:
    """
    Check if command uses pip/pip3 instead of uv.

    Returns:
        Tuple of (is_pip, suggested_uv_command)
    """
    # Normalize command
    cmd = command.strip()

    # Patterns that indicate pip usage
    pip_patterns = [
        # Direct pip calls
        (r'^pip\s+install\s+(.+)$', 'uv pip install \\1'),
        (r'^pip3\s+install\s+(.+)$', 'uv pip install \\1'),
        (r'^pip\s+uninstall\s+(.+)$', 'uv pip uninstall \\1'),
        (r'^pip3\s+uninstall\s+(.+)$', 'uv pip uninstall \\1'),
        (r'^pip\s+freeze', 'uv pip freeze'),
        (r'^pip3\s+freeze', 'uv pip freeze'),
        (r'^pip\s+list', 'uv pip list'),
        (r'^pip3\s+list', 'uv pip list'),
        (r'^pip\s+show\s+(.+)$', 'uv pip show \\1'),
        (r'^pip3\s+show\s+(.+)$', 'uv pip show \\1'),

        # Python -m pip calls
        (r'^python3?\s+-m\s+pip\s+install\s+(.+)$', 'uv pip install \\1'),
        (r'^python3?\s+-m\s+pip\s+uninstall\s+(.+)$', 'uv pip uninstall \\1'),
        (r'^python3?\s+-m\s+pip\s+freeze', 'uv pip freeze'),
        (r'^python3?\s+-m\s+pip\s+list', 'uv pip list'),

        # Requirements file installation
        (r'^pip\s+install\s+-r\s+(.+)$', 'uv pip install -r \\1'),
        (r'^pip3\s+install\s+-r\s+(.+)$', 'uv pip install -r \\1'),

        # Virtual environment creation (suggest uv venv)
        (r'^python3?\s+-m\s+venv\s+(.+)$', 'uv venv \\1'),
        (r'^virtualenv\s+(.+)$', 'uv venv \\1'),
    ]

    for pattern, replacement in pip_patterns:
        match = re.match(pattern, cmd, re.IGNORECASE)
        if match:
            suggested = re.sub(pattern, replacement, cmd, flags=re.IGNORECASE)
            return True, suggested

    # Check for pip anywhere in a piped command
    if re.search(r'\bpip3?\s+(install|uninstall|freeze|list|show)\b', cmd, re.IGNORECASE):
        return True, "Use 'uv pip' instead of 'pip' for package management"

    return False, ""


def is_dangerous_command(command: str) -> tuple[bool, str]:
    """
    Check if command is dangerous and should be blocked.

    Returns:
        Tuple of (is_dangerous, reason)
    """
    cmd = command.strip().lower()

    # Dangerous patterns
    dangerous_patterns = [
        (r'rm\s+(-rf?|--recursive)\s+[/~]', "Recursive delete of root or home directory"),
        (r'rm\s+-rf?\s+\*', "Recursive delete with wildcard"),
        (r'>\s*/dev/sd[a-z]', "Direct write to block device"),
        (r'mkfs\.', "Filesystem formatting"),
        (r'dd\s+if=.*of=/dev/', "Direct disk write with dd"),
        (r'chmod\s+-R\s+777\s+/', "Recursive world-writable permissions on root"),
        (r':()\s*\{\s*:\|\:&\s*\};:', "Fork bomb"),
    ]

    for pattern, reason in dangerous_patterns:
        if re.search(pattern, cmd):
            return True, reason

    return False, ""


def is_env_file_access(tool_name: str, tool_input: dict) -> tuple[bool, str]:
    """
    Check if tool is trying to access .env files.

    Returns:
        Tuple of (is_env_access, reason)
    """
    # File path patterns that indicate .env access
    env_patterns = [
        r'\.env$',
        r'\.env\.',
        r'\.env\.local',
        r'\.env\.production',
        r'\.env\.development',
    ]

    # Check Read, Write, Edit tools
    if tool_name in ("Read", "Write", "Edit"):
        file_path = tool_input.get("file_path", "") or tool_input.get("path", "")
        for pattern in env_patterns:
            if re.search(pattern, file_path, re.IGNORECASE):
                return True, f"Access to sensitive file: {file_path}"

    # Check Bash commands
    if tool_name == "Bash":
        command = tool_input.get("command", "")
        # Check for cat, less, more, head, tail, vim, nano, etc. with .env
        if re.search(r'(cat|less|more|head|tail|vim|nano|code|edit)\s+.*\.env', command, re.IGNORECASE):
            return True, "Reading .env file via command"
        if re.search(r'>\s*\.env', command):
            return True, "Writing to .env file"

    return False, ""


def main():
    """Main hook entry point."""
    try:
        # Read input from stdin
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        # No valid input, allow execution
        sys.exit(0)

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    # Only check Bash commands for pip/dangerous patterns
    if tool_name == "Bash":
        command = tool_input.get("command", "")

        # Check for pip commands
        is_pip, suggestion = is_pip_command(command)
        if is_pip:
            log_tool_use(tool_name, tool_input, "BLOCKED", f"pip command detected")
            print(f"""BLOCKED: This project uses uv for package management, not pip.

❌ Your command: {command}
✅ Use instead: {suggestion}

Why uv?
- 10-100x faster than pip
- Deterministic dependency resolution
- Built-in virtual environment management
- Compatible with pip commands (just prefix with 'uv')

Quick reference:
  uv pip install <package>     # Install a package
  uv pip install -r req.txt    # Install from requirements
  uv pip freeze                 # List installed packages
  uv venv                       # Create virtual environment
  uv run script.py             # Run script with dependencies
""", file=sys.stderr)
            sys.exit(2)

        # Check for dangerous commands
        is_dangerous, reason = is_dangerous_command(command)
        if is_dangerous:
            log_tool_use(tool_name, tool_input, "BLOCKED", reason)
            print(f"BLOCKED: Dangerous command detected.\nReason: {reason}", file=sys.stderr)
            sys.exit(2)

    # Check for .env file access across all relevant tools
    is_env, reason = is_env_file_access(tool_name, tool_input)
    if is_env:
        log_tool_use(tool_name, tool_input, "BLOCKED", reason)
        print(f"""BLOCKED: Access to .env files is restricted for security.

Reason: {reason}

If you need to work with environment variables:
1. Use environment variable injection at runtime
2. Document required variables in README.md
3. Use .env.example for templates (without sensitive values)
""", file=sys.stderr)
        sys.exit(2)

    # Log allowed tool use
    log_tool_use(tool_name, tool_input, "ALLOWED")

    # Exit 0 = allow execution
    sys.exit(0)


if __name__ == "__main__":
    main()
