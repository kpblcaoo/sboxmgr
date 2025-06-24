import os
import json
import tempfile
import shutil
import logging
from logging import error

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
    """Atomically write JSON data to a file."""
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
    """Atomically remove a file if it exists."""
    try:
        if os.path.exists(path):
            os.remove(path)
            logging.info(f"Removed file: {path}")
    except Exception as e:
        logging.error(f"Failed to remove {path}: {e}")
        raise

def file_exists(path):
    return os.path.exists(path)

def read_json(path):
    with open(path, "r") as f:
        return json.load(f)

def write_json(data, path):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)