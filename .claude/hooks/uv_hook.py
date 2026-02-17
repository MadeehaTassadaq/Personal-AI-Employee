#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "toml",
# ]
# ///

"""
UV-Specific Hook: Advanced uv package manager operations and optimizations.

This hook handles advanced uv-specific operations:
1. Automatic environment synchronization
2. Dependency optimization
3. Cache management
4. Security scanning
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


def sync_environment():
    """Synchronize the virtual environment with the lock file."""
    try:
        result = subprocess.run(
            ["uv", "sync", "--locked"],
            cwd=get_project_dir(),
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            print("✓ Environment synchronized successfully", file=sys.stdout)
            return True
        else:
            print(f"⚠ Environment sync failed: {result.stderr}", file=sys.stderr)
            return False
    except subprocess.TimeoutExpired:
        print("⚠ Environment sync timed out", file=sys.stderr)
        return False
    except Exception as e:
        print(f"⚠ Environment sync error: {str(e)}", file=sys.stderr)
        return False


def check_security():
    """Run security audit on dependencies."""
    try:
        # Install and run safety check
        result = subprocess.run(
            ["uv", "pip", "install", "safety"],
            cwd=get_project_dir(),
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            audit_result = subprocess.run(
                ["uv", "run", "safety", "check", "-r", "requirements.txt"],
                cwd=get_project_dir(),
                capture_output=True,
                text=True,
                timeout=60
            )

            if audit_result.returncode == 0:
                print("✓ Security audit passed", file=sys.stdout)
            else:
                print(f"⚠ Security issues found:\n{audit_result.stdout}", file=sys.stderr)
        else:
            print("⚠ Could not install safety for security audit", file=sys.stderr)
    except Exception as e:
        print(f"⚠ Security check error: {str(e)}", file=sys.stderr)


def optimize_dependencies():
    """Optimize dependency resolution."""
    try:
        result = subprocess.run(
            ["uv", "lock", "--upgrade"],
            cwd=get_project_dir(),
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            print("✓ Dependencies optimized", file=sys.stdout)
        else:
            print(f"⚠ Dependency optimization failed: {result.stderr}", file=sys.stderr)
    except Exception as e:
        print(f"⚠ Dependency optimization error: {str(e)}", file=sys.stderr)


def cleanup_cache():
    """Clean up uv cache to save space."""
    try:
        result = subprocess.run(
            ["uv", "cache", "clean"],
            cwd=get_project_dir(),
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            print("✓ Cache cleaned successfully", file=sys.stdout)
        else:
            print(f"⚠ Cache cleanup failed: {result.stderr}", file=sys.stderr)
    except Exception as e:
        print(f"⚠ Cache cleanup error: {str(e)}", file=sys.stderr)


def log_uv_action(action: str, details: str = "") -> None:
    """Log uv-specific actions to JSON file for audit trail."""
    log_dir = get_project_dir() / ".claude" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / "uv_operations.json"

    entry = {
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "details": details,
        "project_dir": str(get_project_dir()),
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


def main():
    """Main hook entry point."""
    try:
        # Read input from stdin
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        # No valid input, exit gracefully
        sys.exit(0)

    # Get the action to perform from the input
    action = input_data.get("action", "")
    project_dir = input_data.get("project_dir", str(get_project_dir()))

    # Set the working directory
    os.chdir(project_dir)

    success = False

    if action == "sync":
        success = sync_environment()
    elif action == "security_check":
        check_security()
        success = True
    elif action == "optimize":
        optimize_dependencies()
        success = True
    elif action == "cleanup":
        cleanup_cache()
        success = True
    elif action == "full_sync":
        print("🔄 Running full uv sync operation...", file=sys.stdout)
        success = sync_environment()
        if success:
            optimize_dependencies()
            check_security()
            cleanup_cache()
    else:
        # Default action: sync environment
        success = sync_environment()
        if success:
            check_security()

    # Log the operation
    log_uv_action(action, f"Success: {success}")

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()