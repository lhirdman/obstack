#!/usr/bin/env python3
"""
Test runner script for auth API tests.
This script ensures proper database setup before running the auth tests.
"""

import subprocess
import sys
import os

def main():
    """Run auth API tests with proper setup."""
    # Change to backend directory
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(backend_dir)
    
    print("Running auth API tests with database setup...")
    
    # Set up environment variables
    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    env["JWT_SECRET_KEY"] = "testsecret"
    env["ENVIRONMENT"] = "development"  # Ensure development mode for consistent behavior
    
    print(f"Running tests with JWT_SECRET_KEY={env.get('JWT_SECRET_KEY')}")
    
    # Run the specific auth tests
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/api/test_auth_api.py",
        "-v",
        "--tb=short"
    ]
    
    try:
        result = subprocess.run(cmd, env=env, check=True)
        print("✅ All auth tests passed!")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"❌ Tests failed with exit code {e.returncode}")
        return e.returncode

if __name__ == "__main__":
    sys.exit(main())