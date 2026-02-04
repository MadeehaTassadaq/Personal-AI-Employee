#!/usr/bin/env python3
"""
Stateless API Validator

Scans Python code for stateful anti-patterns that violate stateless API design principles.
Detects global state, in-memory sessions, mutable caches, and other violations.

Usage:
    python stateless_validator.py <path>           # Scan file or directory
    python stateless_validator.py <path> --json    # Output JSON report
    python stateless_validator.py <path> --strict  # Fail on warnings too

Exit codes:
    0 - No violations found
    1 - Violations found
    2 - Error (invalid path, etc.)
"""

import ast
import sys
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Generator


@dataclass
class Violation:
    """Represents a stateless design violation."""
    file: str
    line: int
    severity: str  # "error" | "warning"
    pattern: str
    message: str
    code_snippet: str
    fix_suggestion: str


class StatelessValidator(ast.NodeVisitor):
    """AST visitor that detects stateful anti-patterns."""

    # Module-level assignments that suggest stateful storage
    SUSPICIOUS_NAMES = {
        "sessions", "session", "users", "active_users", "logged_in_users",
        "connections", "websocket_connections", "active_connections",
        "cache", "user_cache", "data_cache", "request_cache",
        "state", "global_state", "app_state",
        "pending", "pending_requests", "pending_tasks",
        "conversations", "chat_history", "message_history",
        "shopping_carts", "carts", "baskets",
        "rate_limits", "request_counts"
    }

    def __init__(self, filepath: str, source_lines: list[str]):
        self.filepath = filepath
        self.source_lines = source_lines
        self.violations: list[Violation] = []
        self.in_class = False
        self.current_class = None

    def get_code_snippet(self, lineno: int) -> str:
        """Get the source code line for context."""
        if 1 <= lineno <= len(self.source_lines):
            return self.source_lines[lineno - 1].strip()
        return ""

    def add_violation(
        self,
        lineno: int,
        severity: str,
        pattern: str,
        message: str,
        fix_suggestion: str
    ):
        """Record a violation."""
        self.violations.append(Violation(
            file=self.filepath,
            line=lineno,
            severity=severity,
            pattern=pattern,
            message=message,
            code_snippet=self.get_code_snippet(lineno),
            fix_suggestion=fix_suggestion
        ))

    def visit_Assign(self, node: ast.Assign):
        """Check for module-level mutable assignments."""
        # Only check module-level (not inside functions/classes)
        if self.in_class:
            self.generic_visit(node)
            return

        for target in node.targets:
            if isinstance(target, ast.Name):
                name = target.id.lower()

                # Check for suspicious names
                if name in self.SUSPICIOUS_NAMES:
                    self.add_violation(
                        node.lineno,
                        "error",
                        "global_state",
                        f"Module-level variable '{target.id}' suggests stateful storage",
                        f"Move '{target.id}' to database or pass as dependency"
                    )

                # Check for empty dict/list/set initialization
                if isinstance(node.value, ast.Dict) and not node.value.keys:
                    self.add_violation(
                        node.lineno,
                        "warning",
                        "empty_dict",
                        f"Module-level empty dict '{target.id}' may be used for stateful storage",
                        "Ensure this dict is not used to store user/session data"
                    )
                elif isinstance(node.value, ast.List) and not node.value.elts:
                    self.add_violation(
                        node.lineno,
                        "warning",
                        "empty_list",
                        f"Module-level empty list '{target.id}' may be used for stateful storage",
                        "Ensure this list is not used to store request-scoped data"
                    )
                elif isinstance(node.value, ast.Set) and not node.value.elts:
                    self.add_violation(
                        node.lineno,
                        "warning",
                        "empty_set",
                        f"Module-level empty set '{target.id}' may be used for stateful storage",
                        "Ensure this set is not used to track user state"
                    )

                # Check for defaultdict
                if isinstance(node.value, ast.Call):
                    if isinstance(node.value.func, ast.Name):
                        if node.value.func.id == "defaultdict":
                            self.add_violation(
                                node.lineno,
                                "warning",
                                "defaultdict",
                                f"Module-level defaultdict '{target.id}' often indicates stateful storage",
                                "Consider database-backed storage instead"
                            )

        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        """Check for class-level mutable attributes."""
        old_in_class = self.in_class
        old_class = self.current_class
        self.in_class = True
        self.current_class = node.name

        # Check class body for mutable class attributes
        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        # Check for None assignments (often indicate shared state)
                        if isinstance(item.value, ast.Constant) and item.value.value is None:
                            name = target.id.lower()
                            if any(word in name for word in ["user", "session", "current", "state"]):
                                self.add_violation(
                                    item.lineno,
                                    "error",
                                    "class_state",
                                    f"Class attribute '{target.id}' = None in {node.name} may store cross-request state",
                                    f"Make '{target.id}' a method parameter instead of instance attribute"
                                )

                        # Check for mutable defaults
                        if isinstance(item.value, (ast.Dict, ast.List, ast.Set)):
                            self.add_violation(
                                item.lineno,
                                "error",
                                "mutable_class_attr",
                                f"Mutable class attribute '{target.id}' in {node.name} is shared across instances",
                                "Initialize mutable attributes in __init__ or use database"
                            )

        self.generic_visit(node)
        self.in_class = old_in_class
        self.current_class = old_class

    def visit_Global(self, node: ast.Global):
        """Flag use of global keyword."""
        for name in node.names:
            self.add_violation(
                node.lineno,
                "error",
                "global_keyword",
                f"Use of 'global {name}' suggests stateful design",
                "Pass state through function parameters or use database"
            )
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Check function bodies for stateful patterns."""
        # Check for modifications to module-level variables
        for stmt in ast.walk(node):
            if isinstance(stmt, ast.Subscript):
                if isinstance(stmt.ctx, ast.Store):
                    if isinstance(stmt.value, ast.Name):
                        name = stmt.value.id.lower()
                        if name in self.SUSPICIOUS_NAMES:
                            self.add_violation(
                                stmt.lineno,
                                "error",
                                "state_mutation",
                                f"Modifying module-level '{stmt.value.id}' creates stateful behavior",
                                "Store data in database instead of module-level dict/list"
                            )

        self.generic_visit(node)

    # Alias for async functions
    visit_AsyncFunctionDef = visit_FunctionDef


def validate_file(filepath: Path) -> list[Violation]:
    """Validate a single Python file for stateless violations."""
    try:
        source = filepath.read_text()
        tree = ast.parse(source)
        source_lines = source.splitlines()

        validator = StatelessValidator(str(filepath), source_lines)
        validator.visit(tree)

        return validator.violations
    except SyntaxError as e:
        return [Violation(
            file=str(filepath),
            line=e.lineno or 0,
            severity="error",
            pattern="syntax_error",
            message=f"Syntax error: {e.msg}",
            code_snippet="",
            fix_suggestion="Fix syntax error before validation"
        )]
    except Exception as e:
        return [Violation(
            file=str(filepath),
            line=0,
            severity="error",
            pattern="parse_error",
            message=f"Could not parse file: {e}",
            code_snippet="",
            fix_suggestion="Ensure file is valid Python"
        )]


def scan_path(path: Path) -> Generator[Violation, None, None]:
    """Scan a file or directory for violations."""
    if path.is_file():
        if path.suffix == ".py":
            yield from validate_file(path)
    elif path.is_dir():
        for py_file in path.rglob("*.py"):
            # Skip common non-source directories
            if any(part.startswith(".") or part in {"__pycache__", "venv", ".venv", "node_modules"}
                   for part in py_file.parts):
                continue
            yield from validate_file(py_file)


def format_violation(v: Violation) -> str:
    """Format a violation for terminal output."""
    severity_icon = "ERROR" if v.severity == "error" else "WARN"
    output = f"\n[{severity_icon}] {v.file}:{v.line} - {v.pattern}\n"
    output += f"  Message: {v.message}\n"
    if v.code_snippet:
        output += f"  Code: {v.code_snippet}\n"
    output += f"  Fix: {v.fix_suggestion}\n"
    return output


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)

    path = Path(sys.argv[1])
    json_output = "--json" in sys.argv
    strict = "--strict" in sys.argv

    if not path.exists():
        print(f"Error: Path does not exist: {path}")
        sys.exit(2)

    violations = list(scan_path(path))

    if json_output:
        print(json.dumps([asdict(v) for v in violations], indent=2))
    else:
        if not violations:
            print(f"No stateless violations found in {path}")
        else:
            errors = [v for v in violations if v.severity == "error"]
            warnings = [v for v in violations if v.severity == "warning"]

            print(f"\nStateless API Validation Report")
            print(f"{'=' * 40}")
            print(f"Path: {path}")
            print(f"Errors: {len(errors)}")
            print(f"Warnings: {len(warnings)}")

            for v in violations:
                print(format_violation(v))

            print(f"\n{'=' * 40}")
            if errors:
                print("FAILED: Fix errors before deployment")
            elif warnings and strict:
                print("FAILED (strict mode): Address warnings")
            elif warnings:
                print("PASSED with warnings: Review warnings")
            else:
                print("PASSED: No violations found")

    # Exit code
    errors = [v for v in violations if v.severity == "error"]
    warnings = [v for v in violations if v.severity == "warning"]

    if errors:
        sys.exit(1)
    if strict and warnings:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
