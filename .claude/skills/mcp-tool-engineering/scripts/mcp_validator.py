#!/usr/bin/env python3
"""
MCP Tool Validator

Validates MCP tools for compliance with statelessness,
determinism, and other requirements.
"""

import json
import sys
import ast
from typing import Dict, List, Tuple, Any
from pathlib import Path


class MCPTValidator:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def validate_tool_spec(self, tool_spec: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
        """Validate an MCP tool specification against required criteria."""
        self.errors = []
        self.warnings = []

        # Validate required fields
        self._validate_required_fields(tool_spec)

        # Validate statelessness
        self._validate_statelessness(tool_spec)

        # Validate input/output schemas
        self._validate_schemas(tool_spec)

        # Validate error handling
        self._validate_error_handling(tool_spec)

        # Validate idempotency
        self._validate_idempotency(tool_spec)

        success = len(self.errors) == 0
        return success, self.errors, self.warnings

    def _validate_required_fields(self, tool_spec: Dict[str, Any]):
        """Check for required fields in the tool specification."""
        required_fields = ['name', 'description', 'input_schema', 'output_schema']

        for field in required_fields:
            if field not in tool_spec:
                self.errors.append(f"Missing required field: {field}")

    def _validate_statelessness(self, tool_spec: Dict[str, Any]):
        """Validate that the tool is stateless."""
        # Check for problematic patterns in implementation
        implementation = tool_spec.get('implementation', '')

        # Look for stateful patterns
        stateful_patterns = [
            'session', 'cache', 'memory', 'global',
            'persistent', 'stored_between_calls'
        ]

        for pattern in stateful_patterns:
            if pattern.lower() in implementation.lower():
                self.errors.append(f"Potential stateful pattern detected: {pattern}")

        # Check parameters for user identification
        input_schema = tool_spec.get('input_schema', {})
        properties = input_schema.get('properties', {})

        user_identifiers = ['user_id', 'session_id', 'auth_token']
        has_user_id = any(uid in properties for uid in user_identifiers)

        if not has_user_id and tool_spec.get('needs_authentication', True):
            self.errors.append("Tool requires user identification but lacks user_id parameter")

    def _validate_schemas(self, tool_spec: Dict[str, Any]):
        """Validate input and output schemas."""
        input_schema = tool_spec.get('input_schema', {})
        output_schema = tool_spec.get('output_schema', {})

        # Validate schema structure
        if not isinstance(input_schema, dict):
            self.errors.append("Input schema must be a dictionary/object")

        if not isinstance(output_schema, dict):
            self.errors.append("Output schema must be a dictionary/object")

        # Check for required schema properties
        if 'properties' not in input_schema:
            self.errors.append("Input schema must have 'properties' field")

        # Validate output schema has success indicator
        output_props = output_schema.get('properties', {})
        if 'success' not in output_props and output_schema.get('type') != 'boolean':
            self.warnings.append("Output schema should include 'success' field for error indication")

    def _validate_error_handling(self, tool_spec: Dict[str, Any]):
        """Validate error handling patterns."""
        output_schema = tool_spec.get('output_schema', {})
        output_props = output_schema.get('properties', {})

        # Check for error fields in output schema
        error_fields = ['error_code', 'error_message', 'recoverable']
        has_error_handling = any(field in output_props for field in error_fields)

        if not has_error_handling:
            self.warnings.append("Output schema should include error handling fields (error_code, error_message)")

    def _validate_idempotency(self, tool_spec: Dict[str, Any]):
        """Validate idempotency considerations."""
        tool_name = tool_spec.get('name', '').lower()

        # Read operations should be idempotent
        read_operations = ['get_', 'list_', 'fetch_', 'read_']
        is_read_op = any(op in tool_name for op in read_operations)

        # Write operations may need special consideration
        write_operations = ['create_', 'update_', 'delete_', 'modify_']
        is_write_op = any(op in tool_name for op in write_operations)

        if is_read_op:
            # Read operations should naturally be idempotent
            pass  # No specific validation needed
        elif is_write_op:
            # Check if tool handles duplicates or has operation IDs
            input_schema = tool_spec.get('input_schema', {})
            props = input_schema.get('properties', {})

            has_operation_id = 'operation_id' in props or 'request_id' in props
            if not has_operation_id and is_write_op:
                self.warnings.append("Write operations should consider idempotency (suggest operation_id parameter)")


def validate_mcp_tools_from_file(file_path: str) -> bool:
    """Validate MCP tools from a JSON file."""
    validator = MCPTValidator()

    try:
        with open(file_path, 'r') as f:
            tool_specs = json.load(f)

        # Handle both single tool and array of tools
        if isinstance(tool_specs, dict):
            tool_specs = [tool_specs]

        all_valid = True

        for i, tool_spec in enumerate(tool_specs):
            print(f"\nValidating tool {i+1}: {tool_spec.get('name', 'unnamed')}")
            print("-" * 50)

            success, errors, warnings = validator.validate_tool_spec(tool_spec)

            if errors:
                print("❌ ERRORS:")
                for error in errors:
                    print(f"  - {error}")

            if warnings:
                print("⚠️  WARNINGS:")
                for warning in warnings:
                    print(f"  - {warning}")

            if success:
                print("✅ VALID")
            else:
                print("❌ INVALID")
                all_valid = False

        return all_valid

    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in file: {e}")
        return False
    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
        return False


def validate_single_tool(tool_spec: Dict[str, Any]) -> bool:
    """Validate a single MCP tool specification."""
    validator = MCPTValidator()
    success, errors, warnings = validator.validate_tool_spec(tool_spec)

    if errors:
        print("❌ ERRORS:")
        for error in errors:
            print(f"  - {error}")

    if warnings:
        print("⚠️  WARNINGS:")
        for warning in warnings:
            print(f"  - {warning}")

    if success:
        print("✅ VALID")
    else:
        print("❌ INVALID")

    return success


def main():
    if len(sys.argv) != 2:
        print("Usage: python mcp_validator.py <tool_spec_file.json>")
        sys.exit(1)

    file_path = sys.argv[1]
    is_valid = validate_mcp_tools_from_file(file_path)

    if is_valid:
        print("\n🎉 All MCP tools are valid!")
        sys.exit(0)
    else:
        print("\n❌ Some MCP tools have validation errors!")
        sys.exit(1)


if __name__ == "__main__":
    main()