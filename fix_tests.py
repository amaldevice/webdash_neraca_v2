#!/usr/bin/env python3
"""
Script to fix test files by removing unnecessary 'with test_client as client:' wrappers
"""

import os
import re
from pathlib import Path

def fix_test_file(filepath):
    """Fix a single test file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Pattern to match: with test_client as client:
    # Followed by indented code, and replace client. with test_client.
    pattern = r'(\s+)with test_client as client:\n((?:\1    .*\n)+)'

    def replace_match(match):
        indent = match.group(1)
        code_block = match.group(2)

        # Remove the 'with' line and unindent the code block
        fixed_code = re.sub(rf'^{indent}    ', indent, code_block, flags=re.MULTILINE)

        # Replace 'client.' with 'test_client.'
        fixed_code = re.sub(r'\bclient\.', 'test_client.', fixed_code)

        return fixed_code

    # Apply the replacement
    fixed_content = re.sub(pattern, replace_match, content, flags=re.MULTILINE)

    # Write back if changed
    if fixed_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        print(f"Fixed {filepath}")
        return True
    return False

def main():
    """Fix all test files in bug_tests directory"""
    bug_tests_dir = Path('simple_tests/bug_tests')

    if not bug_tests_dir.exists():
        print("bug_tests directory not found")
        return

    test_files = [
        'test_validation.py',
        'test_error_handling.py',
        'test_security.py',
        'test_edge_cases.py',
        'test_concurrency.py'
    ]

    fixed_count = 0
    for test_file in test_files:
        filepath = bug_tests_dir / test_file
        if filepath.exists():
            if fix_test_file(filepath):
                fixed_count += 1

    print(f"Fixed {fixed_count} files")

if __name__ == '__main__':
    main()