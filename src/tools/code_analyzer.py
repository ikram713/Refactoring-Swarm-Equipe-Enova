"""
Code Analyzer Module for The Refactoring Swarm
===============================================
Provides interface to Pylint for static code analysis.

This module allows agents to analyze Python code quality,
detect issues, and get actionable feedback for refactoring.

"""

import subprocess
import json
import os
import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path

# Import our security validator
from .file_manager import _validate_path, SANDBOX_DIR


class AnalysisError(Exception):
    """Raised when code analysis fails."""
    pass


def run_pylint(filepath: str, output_format: str = "json") -> Dict:
    """
    Run Pylint static analysis on a Python file.
    
    Pylint checks for:
    - Code style violations (PEP 8)
    - Programming errors
    - Code smells
    - Missing docstrings
    - Unused variables
    - And much more!
    
    Args:
        filepath: Path to Python file (relative to sandbox or absolute within sandbox)
        output_format: Output format - "json" (structured) or "text" (human-readable)
    
    Returns:
        dict: Analysis results with structure:
            {
                "score": float,           # Quality score (0.0 to 10.0)
                "issues": [               # List of detected issues
                    {
                        "type": str,      # "convention", "warning", "error", "fatal"
                        "line": int,      # Line number
                        "column": int,    # Column number
                        "message": str,   # Human-readable description
                        "symbol": str,    # Issue code (e.g., "missing-docstring")
                        "message_id": str # Pylint message ID (e.g., "C0114")
                    }
                ],
                "statistics": {
                    "total_issues": int,
                    "by_type": {
                        "convention": int,
                        "warning": int,
                        "error": int,
                        "fatal": int
                    }
                },
                "raw_output": str        # Original Pylint output
            }
    
    Raises:
        AnalysisError: If Pylint is not installed or analysis fails
        SecurityError: If filepath escapes sandbox
    
    Example:
        >>> result = run_pylint("messy_code.py")
        >>> print(f"Code quality: {result['score']}/10")
        >>> print(f"Found {len(result['issues'])} issues")
    """
    # Validate path security
    safe_path = _validate_path(filepath)
    
    if not os.path.exists(safe_path):
        raise AnalysisError(f"File not found: {filepath}")
    
    if not safe_path.endswith('.py'):
        raise AnalysisError(f"File must be a Python file (.py): {filepath}")
    
    # Check if Pylint is installed
    if not _is_pylint_installed():
        raise AnalysisError(
            "Pylint is not installed. Please install it with: pip install pylint"
        )
    
    try:
        # Run Pylint with JSON output for structured parsing
        result = subprocess.run(
            [
                "pylint",
                safe_path,
                "--output-format=json",
                "--score=yes",
                # Disable some overly strict checks for student code
                "--disable=C0103",  # Invalid variable names (allow short names)
            ],
            capture_output=True,
            text=True,
            timeout=30  # Prevent hanging on very large files
        )
        
        # Pylint returns non-zero exit code even for warnings (it's normal)
        # Exit codes: 0=clean, 1=fatal, 2=error, 4=warning, 8=refactor, 16=convention
        
        raw_output = result.stdout
        
        # Parse JSON output
        try:
            issues = json.loads(raw_output) if raw_output.strip() else []
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            issues = []
        
        # Extract score from stderr (Pylint prints score there)
        score = _extract_score(result.stderr)
        
        # Parse issues into structured format
        parsed_issues = _parse_issues(issues)
        
        # Calculate statistics
        statistics = _calculate_statistics(parsed_issues)
        
        return {
            "score": score,
            "issues": parsed_issues,
            "statistics": statistics,
            "raw_output": raw_output if output_format == "json" else result.stderr
        }
        
    except subprocess.TimeoutExpired:
        raise AnalysisError(f"Pylint analysis timed out for {filepath}")
    except Exception as e:
        raise AnalysisError(f"Error running Pylint on {filepath}: {str(e)}")


def _is_pylint_installed() -> bool:
    """
    Check if Pylint is installed and accessible.
    
    Returns:
        bool: True if Pylint is available, False otherwise
    """
    try:
        result = subprocess.run(
            ["pylint", "--version"],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def _extract_score(stderr_output: str) -> float:
    """
    Extract Pylint score from stderr output.
    
    Pylint prints score like: "Your code has been rated at 7.50/10"
    
    Args:
        stderr_output: Pylint's stderr output
    
    Returns:
        float: Score from 0.0 to 10.0, or 0.0 if not found
    """
    # Pattern: "Your code has been rated at X.XX/10"
    pattern = r"rated at ([\d\.]+)/10"
    match = re.search(pattern, stderr_output)
    
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return 0.0
    
    return 0.0


def _parse_issues(raw_issues: List[Dict]) -> List[Dict]:
    """
    Parse Pylint JSON issues into our standardized format.
    
    Args:
        raw_issues: Raw issue list from Pylint JSON output
    
    Returns:
        List[Dict]: Parsed and standardized issues
    """
    parsed = []
    
    for issue in raw_issues:
        parsed.append({
            "type": issue.get("type", "unknown"),
            "line": issue.get("line", 0),
            "column": issue.get("column", 0),
            "message": issue.get("message", ""),
            "symbol": issue.get("symbol", ""),
            "message_id": issue.get("message-id", "")
        })
    
    return parsed


def _calculate_statistics(issues: List[Dict]) -> Dict:
    """
    Calculate statistics about detected issues.
    
    Args:
        issues: List of parsed issues
    
    Returns:
        dict: Statistics summary
    """
    by_type = {
        "convention": 0,
        "warning": 0,
        "error": 0,
        "fatal": 0,
        "refactor": 0
    }
    
    for issue in issues:
        issue_type = issue.get("type", "unknown")
        if issue_type in by_type:
            by_type[issue_type] += 1
    
    return {
        "total_issues": len(issues),
        "by_type": by_type
    }


def get_critical_issues(filepath: str) -> List[Dict]:
    """
    Get only critical issues (errors and fatal) from a file.
    
    This is useful for the Auditor agent to focus on the most important problems first.
    
    Args:
        filepath: Path to Python file
    
    Returns:
        List[Dict]: Only errors and fatal issues
    
    Example:
        >>> critical = get_critical_issues("buggy_code.py")
        >>> for issue in critical:
        ...     print(f"Line {issue['line']}: {issue['message']}")
    """
    result = run_pylint(filepath)
    
    critical = [
        issue for issue in result["issues"]
        if issue["type"] in ["error", "fatal"]
    ]
    
    return critical


def get_code_metrics(filepath: str) -> Dict:
    """
    Extract basic code metrics from a Python file.
    
    Metrics include:
    - Lines of code (total, blank, comments, code)
    - Number of functions
    - Number of classes
    - Cyclomatic complexity (if available)
    
    Args:
        filepath: Path to Python file
    
    Returns:
        dict: Code metrics
    
    Example:
        >>> metrics = get_code_metrics("my_code.py")
        >>> print(f"Functions: {metrics['functions']}")
        >>> print(f"Complexity: {metrics['avg_complexity']}")
    """
    safe_path = _validate_path(filepath)
    
    if not os.path.exists(safe_path):
        raise AnalysisError(f"File not found: {filepath}")
    
    metrics = {
        "total_lines": 0,
        "blank_lines": 0,
        "comment_lines": 0,
        "code_lines": 0,
        "functions": 0,
        "classes": 0,
        "avg_complexity": 0.0
    }
    
    try:
        with open(safe_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
            in_docstring = False
            docstring_char = None
            
            for line in lines:
                stripped = line.strip()
                metrics["total_lines"] += 1
                
                # Detect docstrings
                if '"""' in stripped or "'''" in stripped:
                    if not in_docstring:
                        in_docstring = True
                        docstring_char = '"""' if '"""' in stripped else "'''"
                    elif docstring_char in stripped:
                        in_docstring = False
                        metrics["comment_lines"] += 1
                        continue
                
                # Count line types
                if not stripped:
                    metrics["blank_lines"] += 1
                elif in_docstring:
                    metrics["comment_lines"] += 1
                elif stripped.startswith("#"):
                    metrics["comment_lines"] += 1
                else:
                    metrics["code_lines"] += 1
                    
                    # Count functions and classes
                    if stripped.startswith("def "):
                        metrics["functions"] += 1
                    elif stripped.startswith("class "):
                        metrics["classes"] += 1
        
        # Try to get complexity from Pylint (if available)
        try:
        
            metrics["avg_complexity"] = _estimate_complexity(safe_path)
        except:
            metrics["avg_complexity"] = 0.0
        
        return metrics
        
    except Exception as e:
        raise AnalysisError(f"Error extracting metrics from {filepath}: {str(e)}")


def _estimate_complexity(filepath: str) -> float:
    """
    Estimate cyclomatic complexity (simplified).
    
    Real implementation would use 'radon' library, but this is a basic estimate.
    
    Args:
        filepath: Path to Python file
    
    Returns:
        float: Estimated average complexity
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Count complexity-increasing keywords
    complexity_keywords = ['if', 'elif', 'for', 'while', 'and', 'or', 'except']
    complexity_count = sum(content.count(f" {keyword} ") for keyword in complexity_keywords)
    
    # Count functions
    function_count = content.count("def ")
    
    if function_count == 0:
        return 1.0
    
    # Average complexity per function (rough estimate)
    return round(1.0 + (complexity_count / function_count), 2)


def analyse_report(filepath: str) -> Dict:
    """
    Generate a structured analyse report.
    
    This function is designed to be used by the Auditor agent to create
    a prioritized list of improvements.
    
    Args:
        filepath: Path to Python file to analyze
    
    Returns:
        dict: Refactoring plan with structure:
            {
                "file": str,
                "current_score": float,
                "priority_issues": List[Dict],  # High-priority fixes
                "estimated_impact": str          # "high", "medium", "low"
            }
    
 
    """
    result = run_pylint(filepath)
    metrics = get_code_metrics(filepath)
    
    # Categorize issues by priority
    priority_issues = []
    for issue in result["issues"]:
        priority = _determine_priority(issue)
        if priority in ["critical", "high"]:
            priority_issues.append({
                **issue,
                "priority": priority
            })
    

    
    # Estimate impact
    impact = "high" if result["score"] < 5.0 else "medium" if result["score"] < 7.0 else "low"
    
    return {
        "file": filepath,
        "current_score": result["score"],
        "metrics": metrics,
        "priority_issues": sorted(priority_issues, key=lambda x: x["line"]),
        "estimated_impact": impact,
        "total_issues": result["statistics"]["total_issues"]
    }


def _determine_priority(issue: Dict) -> str:
    """
    Determine the priority level of an issue.
    
    Args:
        issue: Issue dictionary
    
    Returns:
        str: "critical", "high", "medium", or "low"
    """
    issue_type = issue.get("type", "")
    symbol = issue.get("symbol", "")
    
    # Critical: Fatal errors and syntax errors
    if issue_type == "fatal" or "syntax-error" in symbol:
        return "critical"
    
    # High: Runtime errors and important warnings
    if issue_type == "error":
        return "high"
    
    # Medium: Code quality warnings
    if issue_type == "warning":
        return "medium"
    
    # Low: Style conventions
    return "low"




if __name__ == "__main__":
    # Self-test when run directly
    print("=" * 60)
    print("CODE ANALYZER SELF-TEST")
    print("=" * 60)
    
    # Check if Pylint is installed
    print("\n[Test 1] Checking Pylint Installation")
    if _is_pylint_installed():
        print("✓ PASSED: Pylint is installed")
    else:
        print("✗ FAILED: Pylint is not installed. Run: pip install pylint")
        exit(1)
    
    # Create a test file with intentional issues
    from .file_manager import write_file, ensure_sandbox_exists
    
    ensure_sandbox_exists()
    
    test_code = '''# Test file with issues
def bad_function():
    x=1+2
    y = 3
    return x

class myClass:
    def method(self):
        pass
'''
    
    print("\n[Test 2] Creating Test File")
    write_file("test_analysis.py", test_code)
    print("✓ PASSED: Test file created")
    
    # Run analysis
    print("\n[Test 3] Running Pylint Analysis")
    try:
        result = run_pylint("test_analysis.py")
        print(f"✓ PASSED: Analysis completed")
        print(f"  Score: {result['score']}/10")
        print(f"  Issues found: {result['statistics']['total_issues']}")
    except Exception as e:
        print(f"✗ FAILED: {e}")
    
    # Get metrics
    print("\n[Test 4] Extracting Code Metrics")
    try:
        metrics = get_code_metrics("test_analysis.py")
        print(f"✓ PASSED: Metrics extracted")
        print(f"  Total lines: {metrics['total_lines']}")
        print(f"  Functions: {metrics['functions']}")
        print(f"  Classes: {metrics['classes']}")
    except Exception as e:
        print(f"✗ FAILED: {e}")
    
    
    print("\n[Test 5] Analyse report")
    try:
        plan = analyse_report("test_analysis.py")
        print(f"✓ PASSED: Analyse done {plan}")
        
    except Exception as e:
        print(f"✗ FAILED: {e}")
    
    print("\n" + "=" * 60)
    print("All tests completed! Code analyzer is ready.")
    print("=" * 60)
    #python -m src.tools.code_analyzer /pour run the file to test it