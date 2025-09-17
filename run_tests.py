#!/usr/bin/env python3
"""
Test runner script for METAR Reader application.

This script provides different ways to run the test suite with various options
for coverage, output formats, and test selection.

Usage:
    python run_tests.py              # Run all tests
    python run_tests.py --coverage   # Run with coverage report
    python run_tests.py --unit       # Run only unit tests
    python run_tests.py --integration # Run only integration tests
    python run_tests.py --verbose    # Run with verbose output

Author: Claude Code
License: MIT
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_command(command, description=""):
    """
    Execute a shell command and handle the result.

    Args:
        command (list): Command and arguments to execute
        description (str): Description of what the command does

    Returns:
        bool: True if command succeeded, False otherwise
    """
    if description:
        print(f"\n[RUNNING] {description}")
        print("=" * 50)

    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("Warnings:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Command failed with exit code {e.returncode}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False
    except FileNotFoundError:
        print(f"[ERROR] Command not found: {command[0]}")
        print("Make sure all dependencies are installed.")
        return False


def check_dependencies():
    """Check if required testing dependencies are available."""
    print("[INFO] Checking test dependencies...")

    try:
        import pytest
        import pytest_cov
        print(f"[SUCCESS] pytest version: {pytest.__version__}")
        return True
    except ImportError as e:
        print(f"[ERROR] Missing dependency: {e}")
        print("Install testing dependencies with:")
        print("  uv add pytest pytest-cov pytest-mock")
        print("  OR pip install -r requirements.txt")
        return False


def run_unit_tests(verbose=False, coverage=False):
    """Run unit tests only."""
    command = ["uv", "run", "python", "-m", "pytest", "test_app.py::TestMetarDecoder", "test_app.py::TestFetchMetar"]

    if verbose:
        command.append("-v")

    if coverage:
        command.extend(["--cov=app", "--cov-report=term-missing"])

    return run_command(command, "Running unit tests")


def run_integration_tests(verbose=False):
    """Run integration tests only."""
    command = ["uv", "run", "python", "-m", "pytest", "test_app.py::TestIntegration", "test_app.py::TestFlaskRoutes"]

    if verbose:
        command.append("-v")

    return run_command(command, "Running integration tests")


def run_all_tests(verbose=False, coverage=False):
    """Run all tests."""
    command = ["uv", "run", "python", "-m", "pytest", "test_app.py"]

    if verbose:
        command.append("-v")

    if coverage:
        command.extend(["--cov=app", "--cov-report=term-missing", "--cov-report=html"])

    return run_command(command, "Running all tests")


def run_unittest_fallback():
    """Run tests using unittest as fallback if pytest is not available."""
    # Try uv first, then fall back to python
    command = ["uv", "run", "python", "test_app.py"]
    success = run_command(command, "Running tests with unittest (fallback via uv)")

    if not success:
        # If uv fails, try regular python
        command = ["python", "test_app.py"]
        success = run_command(command, "Running tests with unittest (direct python)")

    return success


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="METAR Reader Test Runner")
    parser.add_argument("--unit", action="store_true", help="Run only unit tests")
    parser.add_argument("--integration", action="store_true", help="Run only integration tests")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--fallback", action="store_true", help="Use unittest instead of pytest")

    args = parser.parse_args()

    print("METAR Reader Test Suite")
    print("=" * 30)

    # Check if we should use fallback
    if args.fallback or not check_dependencies():
        success = run_unittest_fallback()
    else:
        # Run specific test types
        if args.unit:
            success = run_unit_tests(args.verbose, args.coverage)
        elif args.integration:
            success = run_integration_tests(args.verbose)
        else:
            success = run_all_tests(args.verbose, args.coverage)

    # Print summary
    print("\n" + "=" * 50)
    if success:
        print("[SUCCESS] All tests passed!")
        if args.coverage:
            print("[INFO] Coverage report generated in htmlcov/index.html")
    else:
        print("[FAILED] Some tests failed!")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())