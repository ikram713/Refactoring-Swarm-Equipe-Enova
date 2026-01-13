"""

Provides secure file operations within the sandbox directory.

Author: Toolsmith Team Member
"""

import os
import shutil
from pathlib import Path
from typing import List, Optional
from datetime import datetime


class SecurityError(Exception):
    """Raised when a security violation is detected (path escape attempt)."""
    pass


class FileOperationError(Exception):
    """Raised when a file operation fails."""
    pass


# Define the sandbox directory (absolute path)
SANDBOX_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "sandbox"))


def _validate_path(filepath: str) -> str:
    """
    Validate that a path is within the sandbox directory.
    
    This is a CRITICAL security function that prevents path traversal attacks.
    It ensures agents cannot access files outside the sandbox.
    
    Args:
        filepath: The path to validate (can be relative or absolute)
    
    Returns:
        str: The absolute, validated path within sandbox
    
    Raises:
        SecurityError: If the path attempts to escape the sandbox
        
    Examples:
        >>> _validate_path("test.py")  # OK
        '/path/to/sandbox/test.py'
        
        >>> _validate_path("../../../etc/passwd")  # BLOCKED
        SecurityError: Access denied
    """
    # Convert to absolute path
    if not os.path.isabs(filepath):
        # If relative, assume it's relative to sandbox
        abs_path = os.path.abspath(os.path.join(SANDBOX_DIR, filepath))
    else:
        abs_path = os.path.abspath(filepath)
    
    # Normalize the path 
    abs_path = os.path.normpath(abs_path)
    
    # Check if the path is within sandbox
    try:
        # Get the common path between sandbox and target
        common = os.path.commonpath([SANDBOX_DIR, abs_path])
        
     
        if common != SANDBOX_DIR:
            raise SecurityError(
                f"Security violation: Path '{filepath}' attempts to escape sandbox. "
                f"All operations must stay within: {SANDBOX_DIR}"
            )
    except ValueError:
        # Happens on Windows when paths are on different drives
        raise SecurityError(
            f"Security violation: Path '{filepath}' is on a different drive than sandbox"
        )
    
    return abs_path


def read_file(filepath: str) -> str:
    """
    Read the contents of a file from the sandbox.
    
    Args:
        filepath: Path to the file (relative to sandbox or absolute within sandbox)
    
    Returns:
        str: The complete file contents as a string
    
    Raises:
        SecurityError: If path escapes sandbox
        FileNotFoundError: If file doesn't exist
        FileOperationError: If file cannot be read (permissions, encoding issues)
        
    Example:
        >>> content = read_file("messy_code.py")
        >>> print(content)
        def foo():
            print("hello")
    """
    safe_path = _validate_path(filepath)
    
    if not os.path.exists(safe_path):
        raise FileNotFoundError(f"File not found: {filepath} (resolved to: {safe_path})")
    
    if not os.path.isfile(safe_path):
        raise FileOperationError(f"Path is not a file: {filepath}")
    
    try:
        with open(safe_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        # Try with different encoding if UTF-8 fails
        try:
            with open(safe_path, 'r', encoding='latin-1') as f:
                return f.read()
        except Exception as e:
            raise FileOperationError(f"Cannot read file {filepath}: {str(e)}")
    except Exception as e:
        raise FileOperationError(f"Error reading file {filepath}: {str(e)}")


def write_file(filepath: str, content: str, create_dirs: bool = True) -> bool:
    """
    Write content to a file in the sandbox.
    
    Args:
        filepath: Path to the file (relative to sandbox or absolute within sandbox)
        content: The content to write to the file
        create_dirs: If True, create parent directories if they don't exist
    
    Returns:
        bool: True if write was successful
    
    Raises:
        SecurityError: If path escapes sandbox
        FileOperationError: If write operation fails
        
    Example:
        >>> write_file("fixed_code.py", "def foo():\n    '''Documented!'''\n    pass")
        True
    """
    safe_path = _validate_path(filepath)
    
    # Create parent directories if needed
    if create_dirs:
        parent_dir = os.path.dirname(safe_path)
        if parent_dir and not os.path.exists(parent_dir):
            try:
                os.makedirs(parent_dir, exist_ok=True)
            except Exception as e:
                raise FileOperationError(f"Cannot create directories for {filepath}: {str(e)}")
    
    try:
        with open(safe_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        raise FileOperationError(f"Error writing to file {filepath}: {str(e)}")


def list_python_files(directory: str = "") -> List[str]:
    """
    List all Python (.py) files in a directory within the sandbox.
    
    Args:
        directory: Directory path relative to sandbox (empty string = sandbox root)
    
    Returns:
        List[str]: List of Python file paths relative to sandbox
    
    Raises:
        SecurityError: If path escapes sandbox
        FileOperationError: If directory doesn't exist or cannot be read
        
    Example:
        >>> files = list_python_files("dataset_01")
        >>> print(files)
        ['dataset_01/buggy_code.py', 'dataset_01/test_code.py']
    """
    if directory:
        safe_path = _validate_path(directory)
    else:
        safe_path = SANDBOX_DIR
    
    if not os.path.exists(safe_path):
        raise FileOperationError(f"Directory not found: {directory}")
    
    if not os.path.isdir(safe_path):
        raise FileOperationError(f"Path is not a directory: {directory}")
    
    python_files = []
    
    try:
        for root, dirs, files in os.walk(safe_path):
            for file in files:
                if file.endswith('.py'):
                  
                    full_path = os.path.join(root, file)
                    # Convert to relative path from sandbox
                    rel_path = os.path.relpath(full_path, SANDBOX_DIR)
                    python_files.append(rel_path)
    except Exception as e:
        raise FileOperationError(f"Error listing files in {directory}: {str(e)}")
    
    return sorted(python_files)


def backup_file(filepath: str, backup_suffix: Optional[str] = None) -> str:
    """
    Create a backup copy of a file before modification.
    
    Args:
        filepath: Path to the file to backup
        backup_suffix: Optional custom suffix (default: timestamp)
    
    Returns:
        str: Path to the backup file (relative to sandbox)
    
    Raises:
        SecurityError: If path escapes sandbox
        FileNotFoundError: If file doesn't exist
        FileOperationError: If backup operation fails
        
    Example:
        >>> backup_path = backup_file("code.py")
        >>> print(backup_path)
        'code.py.backup_20260107_143022'
    """
    safe_path = _validate_path(filepath)
    
    if not os.path.exists(safe_path):
        raise FileNotFoundError(f"Cannot backup non-existent file: {filepath}")
    
    # Generate backup filename
    if backup_suffix is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_suffix = f"backup_{timestamp}"
    
    backup_path = f"{safe_path}.{backup_suffix}"
    
    try:
        shutil.copy2(safe_path, backup_path)
        # Return relative path from sandbox
        rel_backup = os.path.relpath(backup_path, SANDBOX_DIR)
        return rel_backup
    except Exception as e:
        raise FileOperationError(f"Error creating backup of {filepath}: {str(e)}")


def file_exists(filepath: str) -> bool:
    """
    Check if a file exists in the sandbox.
    
    Args:
        filepath: Path to check
    
    Returns:
        bool: True if file exists, False otherwise
    
    Raises:
        SecurityError: If path escapes sandbox
    """
    try:
        safe_path = _validate_path(filepath)
        return os.path.isfile(safe_path)
    except SecurityError:
        raise
    except Exception:
        return False


def get_file_info(filepath: str) -> dict:
    """
    Get metadata about a file.
    
    Args:
        filepath: Path to the file
    
    Returns:
        dict: File information including size, modified time, etc.
    
    Raises:
        SecurityError: If path escapes sandbox
        FileNotFoundError: If file doesn't exist
        
    Example:
        >>> info = get_file_info("code.py")
        >>> print(info)
        {
            'size_bytes': 1024,
            'lines': 42,
            'modified': '2026-01-07 14:30:22',
            'extension': '.py'
        }
    """
    safe_path = _validate_path(filepath)
    
    if not os.path.exists(safe_path):
        raise FileNotFoundError(f"File not found: {filepath}")
    
    stat = os.stat(safe_path)
    
    # Count lines if it's a text file
    lines = 0
    try:
        with open(safe_path, 'r', encoding='utf-8') as f:
            lines = sum(1 for _ in f)
    except:
        lines = -1  # Indicate couldn't read as text
    
    return {
        'size_bytes': stat.st_size,
        'lines': lines,
        'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
        'extension': os.path.splitext(filepath)[1],
        'absolute_path': safe_path,
        'relative_path': os.path.relpath(safe_path, SANDBOX_DIR)
    }


def delete_file(filepath: str) -> bool:
    """
    Delete a file from the sandbox.
    
    Args:
        filepath: Path to the file to delete
    
    Returns:
        bool: True if deletion was successful
    
    Raises:
        SecurityError: If path escapes sandbox
        FileNotFoundError: If file doesn't exist
        FileOperationError: If deletion fails
        
    Warning:
        Use with caution! This permanently deletes files.
    """
    safe_path = _validate_path(filepath)
    
    if not os.path.exists(safe_path):
        raise FileNotFoundError(f"Cannot delete non-existent file: {filepath}")
    
    try:
        os.remove(safe_path)
        return True
    except Exception as e:
        raise FileOperationError(f"Error deleting file {filepath}: {str(e)}")


# Utility function to ensure sandbox exists
def ensure_sandbox_exists() -> str:
    """
    Ensure the sandbox directory exists. Create it if it doesn't.
    
    Returns:
        str: Absolute path to sandbox directory
    """
    if not os.path.exists(SANDBOX_DIR):
        os.makedirs(SANDBOX_DIR, exist_ok=True)
    return SANDBOX_DIR


if __name__ == "__main__":
    # Self-test when run directly
    print("=" * 60)
    print("FILE MANAGER SELF-TEST")
    print("=" * 60)
    
    # Ensure sandbox exists
    sandbox = ensure_sandbox_exists()
    print(f"✓ Sandbox directory: {sandbox}")
    
    # Test 1: Security validation
    print("\n[Test 1] Security Validation")
    try:
        _validate_path("../../../etc/passwd")
        print("✗ FAILED: Should have blocked path escape!")
    except SecurityError:
        print("✓ PASSED: Path escape blocked correctly")
    
    # Test 2: Write and read
    print("\n[Test 2] Write and Read")
    test_content = "# Test file\nprint('Hello from file manager!')\n"
    write_file("test_file.py", test_content)
    read_content = read_file("test_file.py")
    if read_content == test_content:
        print("✓ PASSED: Write and read work correctly")
    else:
        print("✗ FAILED: Content mismatch")
    
    # Test 3: Backup
    print("\n[Test 3] Backup")
    backup_path = backup_file("test_file.py")
    print(f"✓ PASSED: Backup created at {backup_path}")
    
    # Test 4: List files
    print("\n[Test 4] List Python files")
    files = list_python_files()
    print(f"✓ Found {len(files)} Python file(s): {files}")
    
    # Test 5: File info
    print("\n[Test 5] File Info")
    info = get_file_info("test_file.py")
    print(f"✓ File info: {info['lines']} lines, {info['size_bytes']} bytes")
    
    print("\n" + "=" * 60)
    print("All tests completed! File manager is ready.")
    print("=" * 60)