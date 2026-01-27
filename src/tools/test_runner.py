"""
Test Runner Module for The Refactoring Swarm
=============================================
Provides interface to Pytest for running unit tests.

This module allows agents to execute tests, parse results,
and generate test templates for untested code.
"""

import subprocess
import json
import os
import re
from typing import Dict, List, Optional
from pathlib import Path

# Import our security validator
from .file_manager import _validate_path, SANDBOX_DIR


class TestError(Exception):
    """Raised when test execution fails."""
    pass

# for auditor/judge  agent to use it
def run_pytest(
    test_path: str,
    verbose: bool = True,
    stop_on_first_fail: bool = False,
    timeout: int = 60
) -> Dict:
    """
    Execute pytest on a test file or directory.
    
    This function runs pytest and parses the results into a structured format
    that agents can easily understand and act upon.
    
    Args:
        test_path: Path to test file or directory (relative to sandbox)
        verbose: If True, capture detailed output
        stop_on_first_fail: If True, stop at first failure (-x flag)
        timeout: Maximum execution time in seconds
    
    Returns:
        dict: Test results with structure:
            {
                "passed": int,           # Number of passed tests
                "failed": int,           # Number of failed tests
                "errors": int,           # Number of errors
                "skipped": int,          # Number of skipped tests
                "total": int,            # Total tests run
                "duration": float,       # Execution time in seconds
                "success": bool,         # True if all tests passed
                "details": [             # Individual test details
                    {
                        "test_name": str,     # Test function name
                        "outcome": str,       # "passed", "failed", "error", "skipped"
                        "message": str,       # Error message if failed
                        "duration": float,    # Test execution time
                        "location": str       # File:line where test is defined
                    }
                ],
                "summary": str,          # Human-readable summary
                "raw_output": str        # Complete pytest output
            }
    
    Raises:
        TestError: If pytest is not installed or execution fails
        SecurityError: If test_path escapes sandbox
    

    """
    safe_path = _validate_path(test_path)
    
    if not os.path.exists(safe_path):
        raise TestError(f"Test path not found: {test_path}")
    
  
    if not _is_pytest_installed():
        raise TestError(
            "Pytest is not installed. Please install it with: pip install pytest"
        )
    
    # Build pytest command
    cmd = ["pytest", safe_path]
    
    # Add flags
    if verbose:
        cmd.append("-v")  # Verbose output
    
    if stop_on_first_fail:
        cmd.append("-x")  # Stop at first failure
    
    # Add output format flags
    cmd.extend([
        "--tb=short",  # Short traceback format
        "-ra"          # Show summary of all test outcomes
    ])
    
    try:
        # Run pytest
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=SANDBOX_DIR  # Run from sandbox directory
        )
        
        # Parse output because pytest contrairement a pylint doesn't return the result parsed
        parsed = _parse_pytest_output(result.stdout, result.stderr)
        
        # Add raw output
        parsed["raw_output"] = result.stdout + "\n" + result.stderr
        
        return parsed
        
    except subprocess.TimeoutExpired:
        raise TestError(f"Test execution timed out after {timeout} seconds")
    except Exception as e:
        raise TestError(f"Error running pytest: {str(e)}")


def _is_pytest_installed() -> bool:

    try:
        result = subprocess.run(
            ["pytest", "--version"],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def _parse_pytest_output(stdout: str, stderr: str) -> Dict:
    """
    Parse pytest output into structured format.
    
    Pytest output format example:
        test_file.py::test_function PASSED                          [ 50%]
        test_file.py::test_another FAILED                           [100%]
        
        ======================== short test summary info =========================
        FAILED test_file.py::test_another - assert False
        ==================== 1 failed, 1 passed in 0.05s ====================
    
    Args:
        stdout: Pytest standard output
        stderr: Pytest standard error
    
    Returns:
        dict: Parsed test results
    """
    output = stdout + "\n" + stderr
    
    # Initialize 
    result = {
        "passed": 0,
        "failed": 0,
        "errors": 0,
        "skipped": 0,
        "total": 0,
        "duration": 0.0,
        "success": False,
        "details": [],
        "summary": ""
    }
    
    # Extract summary line (
    summary_pattern = r"(\d+)\s+failed.*?(\d+)\s+passed.*?in\s+([\d\.]+)s"
    summary_match = re.search(summary_pattern, output)
    
    if summary_match:
        result["failed"] = int(summary_match.group(1))
        result["passed"] = int(summary_match.group(2))
        result["duration"] = float(summary_match.group(3))
    else:
        # Try alternative patterns
        passed_match = re.search(r"(\d+)\s+passed.*?in\s+([\d\.]+)s", output)
        if passed_match:
            result["passed"] = int(passed_match.group(1))
            result["duration"] = float(passed_match.group(2))
        
        failed_match = re.search(r"(\d+)\s+failed", output)
        if failed_match:
            result["failed"] = int(failed_match.group(1))
    
    # Count other outcomes
    result["errors"] = len(re.findall(r"ERROR", output))
    result["skipped"] = len(re.findall(r"SKIPPED", output))
    
    # Calculate total
    result["total"] = (
        result["passed"] + 
        result["failed"] + 
        result["errors"] + 
        result["skipped"]
    )
    
    # Determine success
    result["success"] = (result["failed"] == 0 and result["errors"] == 0)
    
    # Parse individual test details
    result["details"] = _parse_test_details(output)
    
    # Generate summary
    if result["success"]:
        result["summary"] = f" All {result['passed']} tests passed in {result['duration']:.2f}s"
    else:
        result["summary"] = (
            f" {result['failed']} failed, "
            f"{result['passed']} passed, "
            f"{result['errors']} errors in {result['duration']:.2f}s"
        )
    
    return result


def _parse_test_details(output: str) -> List[Dict]:
    """
    Parse individual test results from pytest output.
    
    Args:
        output: Pytest output text
    
    Returns:
        List[Dict]: List of test details
    """
    details = []
    
    # Pattern for test lines: test_file.py::test_name PASSED/FAILED [percentage]
    test_pattern = r"([\w/\.]+\.py)::([\w_]+)\s+(PASSED|FAILED|ERROR|SKIPPED)"
    
    for match in re.finditer(test_pattern, output):
        file_path = match.group(1)
        test_name = match.group(2)
        outcome = match.group(3).lower()
        
        message = ""
        if outcome == "failed" or outcome == "error":
            # Look for error message after this test
            error_pattern = rf"{test_name}.*?-\s+(.*?)(?:\n|$)"
            error_match = re.search(error_pattern, output)
            if error_match:
                message = error_match.group(1).strip()
        
        details.append({
            "test_name": test_name,
            "outcome": outcome,
            "message": message,
            "duration": 0.0,  # Pytest doesn't always show individual durations
            "location": file_path
        })
    
    return details

#for judge agent to use 
def generate_test_template(source_file: str, output_file: Optional[str] = None) -> str:
    """
    Generate a pytest template for a source file.
    
    This function analyzes a Python source file and generates a basic
    test template with test stubs for all functions and classes.
    
    Args:
        source_file: Path to source Python file
        output_file: Where to save the test file (optional)
    
    Returns:
        str: Generated test code
    
    Raises:
        TestError: If source file cannot be read
        SecurityError: If paths escape sandbox
    
    Example:
        >>> template = generate_test_template("calculator.py", "test_calculator.py")
        >>> print("Test template created!")
    """
    from .file_manager import read_file, write_file
    
    safe_path = _validate_path(source_file)
    
    if not os.path.exists(safe_path):
        raise TestError(f"Source file not found: {source_file}")
    
    # Read source code
    try:
        source_code = read_file(source_file)
    except Exception as e:
        raise TestError(f"Cannot read source file: {str(e)}")
    
    # Extract functions and classes
    functions = _extract_functions(source_code)
    classes = _extract_classes(source_code)
    
    # Generate test code
    test_code = _generate_test_code(
        source_file=source_file,
        functions=functions,
        classes=classes
    )
    
    # Save if output file specified
    if output_file:
        try:
            write_file(output_file, test_code)
        except Exception as e:
            raise TestError(f"Cannot write test file: {str(e)}")
    
    return test_code


def _extract_functions(source_code: str) -> List[str]:
    """
    Extract function names from source code.
    
    Args:
        source_code: Python source code
    
    Returns:
        List[str]: Function names
    """
    functions = []
    
    # Pattern: def function_name(
    pattern = r"^def\s+([\w_]+)\s*\("
    
    for line in source_code.split("\n"):
        match = re.match(pattern, line.strip())
        if match:
            func_name = match.group(1)
            # Skip private functions (starting with _) and magic methods
            if not func_name.startswith("_"):
                functions.append(func_name)
    
    return functions


def _extract_classes(source_code: str) -> List[str]:
    """
    Extract class names from source code.
    
    Args:
        source_code: Python source code
    
    Returns:
        List[str]: Class names
    """
    classes = []
    
    # Pattern: class ClassName:
    pattern = r"^class\s+([\w_]+)"
    
    for line in source_code.split("\n"):
        match = re.match(pattern, line.strip())
        if match:
            class_name = match.group(1)
            # Skip private classes
            if not class_name.startswith("_"):
                classes.append(class_name)
    
    return classes


def _generate_test_code(
    source_file: str,
    functions: List[str],
    classes: List[str]
) -> str:
    # LLM Fills In The Tests 
    """
    Generate pytest test code template.
    
    Args:
        source_file: Name of source file
        functions: List of function names
        classes: List of class names
    
    Returns:
        str: Generated test code
    """
    module_name = os.path.splitext(os.path.basename(source_file))[0]
    
    test_code = f'''"""
Unit Tests for {source_file}
{'=' * 60}
Auto-generated test template.

TODO: Implement test logic for each function.
"""

import pytest
from {module_name} import (
'''
    
    # Add imports
    if functions:
        for func in functions:
            test_code += f"    {func},\n"
    if classes:
        for cls in classes:
            test_code += f"    {cls},\n"
    
    test_code += ")\n\n"
    
    # Generate test functions
    if functions:
        test_code += "\n# ============================================================\n"
        test_code += "# Function Tests\n"
        test_code += "# ============================================================\n\n"
        
        for func in functions:
            test_code += f'''
def test_{func}():
    """
    Test {func}() function.
    
    TODO: Implement test logic
    - Test with valid inputs
    - Test with edge cases
    - Test with invalid inputs
    """
    # Arrange
    # TODO: Set up test data
    
    # Act
    # TODO: Call the function
    # result = {func}(...)
    
    # Assert
    # TODO: Verify the result
    # assert result == expected
    
    pytest.skip("Test not implemented yet")

'''
    
    # Generate class tests
    if classes:
        test_code += "\n# ============================================================\n"
        test_code += "# Class Tests\n"
        test_code += "# ============================================================\n\n"
        
        for cls in classes:
            test_code += f'''
class Test{cls}:
    """
    Test suite for {cls} class.
    """
    
    def test_initialization(self):
        """Test {cls} initialization."""
        # TODO: Test object creation
        # obj = {cls}(...)
        # assert obj is not None
        pytest.skip("Test not implemented yet")
    
    def test_methods(self):
        """Test {cls} methods."""
        # TODO: Test class methods
        pytest.skip("Test not implemented yet")

'''
    
    # Add footer
    test_code += '''
# ============================================================
# Run tests: pytest {test_file} -v
# ============================================================
'''
    
    return test_code


def check_test_coverage(source_file: str, test_file: str) -> Dict:
    """
    Check if all functions in source file have corresponding tests.
    
    Args:
        source_file: Path to source Python file
        test_file: Path to test file
    
    Returns:
        dict: Coverage information:
            {
                "total_functions": int,
                "tested_functions": int,
                "untested_functions": List[str],
                "coverage_percent": float
            }
    
    Example:
        >>> coverage = check_test_coverage("calculator.py", "test_calculator.py")
        >>> print(f"Coverage: {coverage['coverage_percent']:.1f}%")
    """
    from .file_manager import read_file
    
    # Read both files
    source_code = read_file(source_file)
    test_code = read_file(test_file)
    
    # Extract functions from source
    source_functions = _extract_functions(source_code)
    
    # Find which functions have tests
    tested_functions = []
    untested_functions = []
    
    for func in source_functions:
        # Check if test_function_name exists in test file
        test_pattern = f"test_{func}"
        if test_pattern in test_code:
            tested_functions.append(func)
        else:
            untested_functions.append(func)
    
    # Calculate coverage
    total = len(source_functions)
    coverage = (len(tested_functions) / total * 100) if total > 0 else 100.0
    
    return {
        "total_functions": total,
        "tested_functions": len(tested_functions),
        "untested_functions": untested_functions,
        "coverage_percent": coverage
    }


if __name__ == "__main__":
    # Self-test when run directly
    print("=" * 60)
    print("TEST RUNNER SELF-TEST")
    print("=" * 60)
    
    from .file_manager import write_file, ensure_sandbox_exists
    
    ensure_sandbox_exists()
    
    # Test 1: Check pytest installation
    print("\n[Test 1] Checking Pytest Installation")
    if _is_pytest_installed():
        print("✓ PASSED: Pytest is installed")
    else:
        print("✗ FAILED: Pytest is not installed. Run: pip install pytest")
        exit(1)
    
    # Test 2: Create sample code
    print("\n[Test 2] Creating Sample Code")
    sample_code = '''def add(a, b):
    """Add two numbers."""
    return a + b

def subtract(a, b):
    """Subtract b from a."""
    return a - b

class Calculator:
    """Simple calculator class."""
    
    def multiply(self, a, b):
        """Multiply two numbers."""
        return a * b
'''
    write_file("sample_calculator.py", sample_code)
    print("✓ PASSED: Sample code created")
    
    # Test 3: Generate test template
    print("\n[Test 3] Generating Test Template")
    try:
        template = generate_test_template(
            "sample_calculator.py",
            "test_sample_calculator.py"
        )
        print("✓ PASSED: Test template generated")
        print(f"  Generated {len(template.split('def test_'))} test stubs")
    except Exception as e:
        print(f"✗ FAILED: {e}")
    
    # Test 4: Create actual tests
    print("\n[Test 4] Creating Real Tests")
    real_tests = '''import pytest
from sample_calculator import add, subtract, Calculator

def test_add():
    assert add(2, 3) == 5
    assert add(-1, 1) == 0
    assert add(0, 0) == 0

def test_subtract():
    assert subtract(5, 3) == 2
    assert subtract(0, 0) == 0
    assert subtract(-1, -1) == 0

class TestCalculator:
    def test_multiply(self):
        calc = Calculator()
        assert calc.multiply(2, 3) == 6
        assert calc.multiply(0, 5) == 0
'''
    write_file("test_sample_calculator.py", real_tests)
    print("✓ PASSED: Real tests created")
    
    # Test 5: Run tests
    print("\n[Test 5] Running Tests")
    try:
        result = run_pytest("test_sample_calculator.py")
        print(f"✓ PASSED: Tests executed")
        print(f"  {result['summary']}")
        print(f"  Passed: {result['passed']}, Failed: {result['failed']}")
    except Exception as e:
        print(f"✗ FAILED: {e}")
    
    # Test 6: Check coverage
    print("\n[Test 6] Checking Test Coverage")
    try:
        coverage = check_test_coverage(
            "sample_calculator.py",
            "test_sample_calculator.py"
        )
        print(f"✓ PASSED: Coverage calculated")
        print(f"  Coverage: {coverage['coverage_percent']:.1f}%")
        print(f"  Tested: {coverage['tested_functions']}/{coverage['total_functions']} functions")
        if coverage['untested_functions']:
            print(f"  Untested: {', '.join(coverage['untested_functions'])}")
    except Exception as e:
        print(f"✗ FAILED: {e}")
    
    print("\n" + "=" * 60)
    print("All tests completed! Test runner is ready.")
    print("=" * 60)