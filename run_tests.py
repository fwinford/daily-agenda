#!/usr/bin/env python3
"""
Test Runner for Daily Agenda

This script runs all the unit tests for the daily agenda application.
It's designed for developers who want to verify that their code changes
don't break existing functionality.

The tests include:
- Calendar parsing and event fetching
- Notion API integration
- Email sending functionality
- HTML rendering
- Configuration loading

Usage: python run_tests.py

Note: This uses mock data and doesn't require real API tokens.
For testing with your actual data, use: python main.py
"""
import subprocess
import sys
import os

def run_tests():
    """
    Run all unit tests and display results.
    
    This function executes the Python unittest discovery to find and run
    all test files in the tests/ directory. Tests are run with verbose
    output to show individual test results.
    
    Returns:
        int: Exit code (0 for success, 1 for failures)
    """
    print("running daily agenda unit tests")
    print("=" * 50)
    
    # Change to project directory to ensure proper imports
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Run unittest discovery with verbose output
    # This finds all test_*.py files in the tests/ directory
    result = subprocess.run([
        sys.executable, "-m", "unittest", "discover", 
        "-s", "tests", "-p", "test_*.py", "-v"
    ], capture_output=False)
    
    # Display final result with appropriate symbol
    if result.returncode == 0:
        print("\nall tests passed!")
    else:
        print("\nsome tests failed!")
        
    return result.returncode

def run_tests_with_coverage():
    """Run tests with coverage report"""
    print("running tests with coverage")
    print("=" * 50)
    
    # Change to project directory  
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Run with pytest and coverage
    result = subprocess.run([
        sys.executable, "-m", "pytest", "tests/", 
        "--cov=app", "--cov=main", "--cov-report=term-missing", "-v"
    ], capture_output=False)
    
    return result.returncode

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--coverage":
        exit_code = run_tests_with_coverage()
    else:
        exit_code = run_tests()
    
    sys.exit(exit_code)
