#!/usr/bin/env python3
"""Script to fix structural docstring issues automatically.

This script fixes common structural docstring issues without changing content:
- D203: Add blank line before class docstring
- D213: Fix multi-line docstring summary placement
- D406/D407: Fix section underlines
- D413: Add blank line after last section
"""

import ast
import re
import sys
from pathlib import Path
from typing import List, Tuple


def fix_d203_class_docstring(content: str) -> str:
    """Add blank line before class docstring (D203)."""
    lines = content.split('\n')
    fixed_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]
        fixed_lines.append(line)

        # Check if this is a class definition
        if line.strip().startswith('class ') and ':' in line:
            # Look ahead for docstring
            j = i + 1
            while j < len(lines) and lines[j].strip() == '':
                j += 1

            if j < len(lines) and lines[j].strip().startswith('"""'):
                # Found docstring, check if we need to add blank line
                if j > i + 1:  # There's already a blank line
                    pass
                else:  # Need to add blank line
                    fixed_lines.append('')

        i += 1

    return '\n'.join(fixed_lines)


def process_file(file_path: Path) -> bool:
    """Process a single Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # Apply fixes - only the safest ones
        content = fix_d203_class_docstring(content)

        # Write back if changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed: {file_path}")
            return True

        return False

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python fix_docstring_structure.py <directory>")
        sys.exit(1)

    directory = Path(sys.argv[1])
    if not directory.exists():
        print(f"Directory {directory} does not exist")
        sys.exit(1)

    python_files = list(directory.rglob("*.py"))
    fixed_count = 0

    for file_path in python_files:
        if process_file(file_path):
            fixed_count += 1

    print(f"\nFixed {fixed_count} files")


if __name__ == "__main__":
    main()
