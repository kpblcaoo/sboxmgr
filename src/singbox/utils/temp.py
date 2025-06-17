import json
import os
import tempfile
import shutil

def handle_temp_file(content, target_path, validate_fn):
    """Handle temporary file creation and validation."""
    temp_path = os.path.join(tempfile.gettempdir(), os.path.basename(target_path))
    with open(temp_path, 'w') as f:
        f.write(json.dumps(content, indent=2))
    if validate_fn(temp_path):
        shutil.move(temp_path, target_path)
    else:
        raise ValueError(f"Validation failed for {temp_path}") 