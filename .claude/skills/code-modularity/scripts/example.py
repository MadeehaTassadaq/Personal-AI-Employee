#!/usr/bin/env python3
"""
Code Modularity Analyzer

This script analyzes Python code files to identify potential modularity improvements,
such as circular dependencies, overly complex modules, and violations of separation
of concerns principles.
"""

import ast
import os
import sys
from typing import List, Dict, Set


class ModularityAnalyzer:
    def __init__(self):
        self.imports = {}
        self.dependencies = {}
        self.functions = {}
        self.classes = {}

    def analyze_file(self, file_path: str) -> Dict:
        """Analyze a single Python file for modularity issues."""
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                tree = ast.parse(f.read())
            except SyntaxError:
                print(f"Syntax error in {file_path}")
                return {}

        imports = []
        functions = []
        classes = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
            elif isinstance(node, ast.FunctionDef):
                functions.append({
                    'name': node.name,
                    'line': node.lineno,
                    'args': len(node.args.args)
                })
            elif isinstance(node, ast.AsyncFunctionDef):
                functions.append({
                    'name': node.name,
                    'line': node.lineno,
                    'args': len(node.args.args)
                })
            elif isinstance(node, ast.ClassDef):
                classes.append({
                    'name': node.name,
                    'line': node.lineno,
                    'methods': len([n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))])
                })

        self.imports[file_path] = imports
        self.functions[file_path] = functions
        self.classes[file_path] = classes

        return {
            'imports': imports,
            'functions': functions,
            'classes': classes
        }

    def find_circular_dependencies(self) -> List[tuple]:
        """Find circular dependencies between modules."""
        # This is a simplified version - in a real implementation,
        # we would build a proper dependency graph
        circular_deps = []

        # For now, just look for obvious circular imports
        for file, imports in self.imports.items():
            for imported in imports:
                # Check if the imported module imports back
                imported_file = self._find_file_for_module(imported)
                if imported_file and imported_file in self.imports:
                    if file in self.imports[imported_file]:
                        circular_deps.append((file, imported_file))

        return circular_deps

    def _find_file_for_module(self, module_name: str) -> str:
        """Find the file path for a given module name."""
        # Simplified implementation - would need to handle package structure properly
        potential_paths = [
            f"{module_name}.py",
            f"{module_name}/__init__.py",
            f"{module_name.replace('.', '/')}.py"
        ]

        for path in potential_paths:
            if os.path.exists(path):
                return path
        return None

    def check_module_complexity(self, file_path: str, max_functions: int = 10) -> List[str]:
        """Check if a module has too many functions or classes."""
        issues = []

        if file_path in self.functions:
            functions = self.functions[file_path]
            if len(functions) > max_functions:
                issues.append(f"Module {file_path} has {len(functions)} functions (max {max_functions})")

            # Check for overly complex functions (too many parameters)
            for func in functions:
                if func['args'] > 5:  # More than 5 params is often too complex
                    issues.append(f"Function {func['name']} in {file_path} has {func['args']} parameters")

        return issues


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 example.py <directory_path>")
        print("Analyzes Python files in the given directory for modularity issues")
        return

    directory_path = sys.argv[1]
    if not os.path.isdir(directory_path):
        print(f"Directory {directory_path} does not exist")
        return

    analyzer = ModularityAnalyzer()

    # Find all Python files in the directory
    python_files = []
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))

    print(f"Analyzing {len(python_files)} Python files for modularity issues...\n")

    # Analyze each file
    for file_path in python_files:
        print(f"Analyzing {file_path}")
        result = analyzer.analyze_file(file_path)

        # Check for complexity issues
        issues = analyzer.check_module_complexity(file_path)
        for issue in issues:
            print(f"  ⚠️  {issue}")

    # Check for circular dependencies
    print("\nChecking for circular dependencies...")
    circular_deps = analyzer.find_circular_dependencies()
    if circular_deps:
        print("⚠️  Circular dependencies found:")
        for dep1, dep2 in circular_deps:
            print(f"  {dep1} <-> {dep2}")
    else:
        print("✅ No circular dependencies found")

    print("\nModularity analysis complete!")


if __name__ == "__main__":
    main()
