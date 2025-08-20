#!/usr/bin/env python3
"""Test runner script for the BFF application."""

import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd: list, description: str) -> bool:
    """Run a command and return success status."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with exit code {e.returncode}")
        return False


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="Run BFF application tests")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--contract", action="store_true", help="Run contract tests only")
    parser.add_argument("--load", action="store_true", help="Run load tests only")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--benchmark", action="store_true", help="Run benchmark tests")
    parser.add_argument("--parallel", "-n", type=int, help="Number of parallel workers")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--fast", action="store_true", help="Skip slow tests")
    
    args = parser.parse_args()
    
    # Base pytest command
    pytest_cmd = ["python", "-m", "pytest"]
    
    if args.verbose:
        pytest_cmd.append("-v")
    
    if args.parallel:
        pytest_cmd.extend(["-n", str(args.parallel)])
    
    if args.fast:
        pytest_cmd.extend(["-m", "not slow"])
    
    success = True
    
    # Run specific test types
    if args.unit:
        cmd = pytest_cmd + ["-m", "unit", "tests/"]
        success &= run_command(cmd, "Unit Tests")
    
    elif args.integration:
        cmd = pytest_cmd + ["-m", "integration", "tests/integration/"]
        success &= run_command(cmd, "Integration Tests")
    
    elif args.contract:
        cmd = pytest_cmd + ["-m", "contract", "tests/contract/"]
        success &= run_command(cmd, "Contract Tests")
    
    elif args.load:
        cmd = pytest_cmd + ["-m", "load", "tests/load/"]
        success &= run_command(cmd, "Load Tests")
    
    elif args.benchmark:
        cmd = pytest_cmd + ["-m", "benchmark", "--benchmark-only"]
        success &= run_command(cmd, "Benchmark Tests")
    
    else:
        # Run all tests in sequence
        test_suites = [
            (["tests/api/", "-m", "api"], "API Tests"),
            (["tests/services/", "-m", "service"], "Service Tests"),
            (["tests/integration/", "-m", "integration"], "Integration Tests"),
            (["tests/contract/", "-m", "contract"], "Contract Tests"),
        ]
        
        for test_args, description in test_suites:
            cmd = pytest_cmd + test_args
            success &= run_command(cmd, description)
    
    # Generate coverage report if requested
    if args.coverage:
        coverage_cmd = ["python", "-m", "coverage", "html"]
        run_command(coverage_cmd, "Coverage Report Generation")
        print(f"\n📊 Coverage report generated in htmlcov/index.html")
    
    # Run linting and type checking
    if not any([args.unit, args.integration, args.contract, args.load, args.benchmark]):
        print(f"\n{'='*60}")
        print("Running Code Quality Checks")
        print(f"{'='*60}")
        
        # Type checking
        mypy_cmd = ["python", "-m", "mypy", "app/"]
        run_command(mypy_cmd, "Type Checking (mypy)")
        
        # Linting
        ruff_cmd = ["python", "-m", "ruff", "check", "app/", "tests/"]
        run_command(ruff_cmd, "Linting (ruff)")
        
        # Security check
        bandit_cmd = ["python", "-m", "bandit", "-r", "app/"]
        run_command(bandit_cmd, "Security Check (bandit)")
    
    if success:
        print(f"\n🎉 All tests completed successfully!")
        sys.exit(0)
    else:
        print(f"\n💥 Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()