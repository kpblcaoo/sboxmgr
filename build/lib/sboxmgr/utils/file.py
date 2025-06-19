import os
import json
import tempfile
import shutil
from logging import error

def handle_temp_file(content, target_path, validate_fn=None):
    """Write content to a temporary file, validate, and move to target path."""
    temp_path = os.path.join(tempfile.gettempdir(), os.path.basename(target_path))
    try:
        with open(temp_path, "w") as f:
            f.write(json.dumps(content, indent=2))
        if validate_fn and not validate_fn(temp_path):
            error(f"Validation failed for {temp_path}")
            raise ValueError(f"Validation failed for {temp_path}")
        shutil.move(temp_path, target_path)
        return True
    except Exception as e:
        error(f"Failed to handle temporary file {temp_path}: {e}")
        raise