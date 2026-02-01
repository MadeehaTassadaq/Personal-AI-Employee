"""Test runner for Digital FTE API tests."""

import subprocess
import sys
import os


def run_tests():
    """Run all tests using pytest."""
    # Change to the project root directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)

    print("Running Digital FTE API tests...")
    print("=" * 50)

    # Run pytest with verbose output
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-v",           # Verbose output
        "--tb=short"    # Short traceback
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)

        print("STDOUT:")
        print(result.stdout)

        if result.stderr:
            print("STDERR:")
            print(result.stderr)

        print(f"Return code: {result.returncode}")

        return result.returncode

    except FileNotFoundError:
        print("pytest not found. Installing...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "pytest", "pytest-asyncio"], check=True)
            print("pytest installed successfully.")

            # Retry running tests
            result = subprocess.run(cmd, capture_output=True, text=True)

            print("STDOUT:")
            print(result.stdout)

            if result.stderr:
                print("STDERR:")
                print(result.stderr)

            print(f"Return code: {result.returncode}")
            return result.returncode

        except subprocess.CalledProcessError as e:
            print(f"Failed to install pytest: {e}")
            return 1


if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)