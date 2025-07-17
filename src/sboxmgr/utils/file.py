"""File utilities for SBoxMgr."""

import json
import logging
import os
import shutil
import tempfile


def handle_temp_file(content, target_path, validate_fn=None):
    """Write content to temporary file with validation and atomic move.

    Provides safe file operations by writing to a temporary location,
    optionally validating the content, then atomically moving to the
    target path. Ensures data integrity and prevents corruption.

    Args:
        content: Data to write (will be JSON-serialized).
        target_path: Final destination path for the file.
        validate_fn: Optional validation function that takes file path
                    and returns True if content is valid.

    Returns:
        True if operation completed successfully.

    Raises:
        ValueError: If validation fails.
        Exception: For file I/O errors or other failures.

    """
    temp_path = os.path.join(tempfile.gettempdir(), os.path.basename(target_path))
    try:
        with open(temp_path, "w") as f:
            f.write(json.dumps(content, indent=2))
        if validate_fn and not validate_fn(temp_path):
            logging.error(f"Validation failed for {temp_path}")
            raise ValueError(f"Validation failed for {temp_path}")
        shutil.move(temp_path, target_path)
        return True
    except Exception as e:
        logging.error(f"Failed to handle temporary file {temp_path}: {e}")
        raise


def atomic_write_json(data, path):
    """Atomically write JSON data to file with rollback on failure.

    Uses temporary file with atomic rename to ensure the target file
    is never left in a partially written state. Provides data integrity
    guarantees for configuration files and other critical data.

    Args:
        data: Python object to serialize as JSON.
        path: Target file path for the JSON data.

    Returns:
        True if write completed successfully.

    Raises:
        Exception: For JSON serialization errors or file I/O failures.

    Note:
        Temporary file is automatically cleaned up on failure.

    """
    temp_path = f"{path}.tmp"
    try:
        with open(temp_path, "w") as f:
            json.dump(data, f, indent=2)
        os.replace(temp_path, path)
        return True
    except Exception as e:
        logging.error(f"Failed to atomically write {path}: {e}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise


def atomic_remove(path):
    """Safely remove file with error handling and logging.

    Removes the specified file if it exists, with proper error handling
    and audit logging. Safe to call on non-existent files.

    Args:
        path: File path to remove.

    Raises:
        Exception: For file system errors preventing removal.

    Note:
        This function does not return a value. Check for exceptions
        to determine success or failure.

    """
    try:
        if os.path.exists(path):
            os.remove(path)
            logging.info(f"Removed file: {path}")
    except Exception as e:
        logging.error(f"Failed to remove {path}: {e}")
        raise


def file_exists(path):
    """Check if file exists at the specified path.

    Args:
        path: File path to check.

    Returns:
        True if file exists, False otherwise.

    """
    return os.path.exists(path)


def read_json(path):
    """Read and parse JSON data from file.

    Args:
        path: Path to JSON file to read.

    Returns:
        Parsed JSON data as Python object.

    Raises:
        FileNotFoundError: If file does not exist.
        json.JSONDecodeError: If file contains invalid JSON.

    """
    with open(path) as f:
        return json.load(f)


def write_json(data, path):
    """Write Python object to file as formatted JSON.

    Args:
        data: Python object to serialize as JSON.
        path: Target file path for JSON output.

    Raises:
        Exception: For file I/O errors or JSON serialization failures.

    Note:
        This function does not return a value and does not provide
        atomic write guarantees. Use atomic_write_json for safer operations.

    """
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
