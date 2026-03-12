#!/usr/bin/env python3
"""
Batch fix PaginatedResponse structure in test files.
"""
import re
import glob

def fix_pagination_response(content):
    """Fix PaginatedResponse structure in test content."""

    # Pattern 1: Multi-line pagination with total, page, pageSize, totalPages
    pattern1 = r'\{\s*items:\s*(\[[^\]]*\])\s*,\s*total:\s*\d+\s*,\s*page:\s*\d+\s*,\s*pageSize:\s*(\d+)\s*,\s*totalPages:\s*\d+\s*\}'

    def replace1(match):
        items = match.group(1)
        page_size = match.group(2)
        return f"{{ items: {items}, metadata: {{ page_size: {page_size}, has_next: false, has_prev: false, strategy: 'offset' as const }} }}"

    content = re.sub(pattern1, replace1, content, flags=re.MULTILINE | re.DOTALL)

    return content

def fix_field_names(content):
    """Fix snake_case to camelCase field names."""
    replacements = [
        (r'client_id:', 'clientId:'),
        (r'project_id:', 'projectId:'),
        (r'run_id:', 'runId:'),
        (r'business_description:', 'businessDescription:'),
    ]

    for old, new in replacements:
        content = re.sub(old, new, content)

    return content

def process_file(filepath):
    """Process a single test file."""
    print(f"Processing {filepath}...")

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content
    content = fix_pagination_response(content)
    content = fix_field_names(content)

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  -> Fixed")
        return True
    return False

def main():
    patterns = [
        'src/api/__tests__/*.test.ts',
        'src/__tests__/integration/*.test.tsx',
    ]

    count = 0
    for pattern in patterns:
        for filepath in glob.glob(pattern):
            if process_file(filepath):
                count += 1

    print(f"\nFixed {count} files")

if __name__ == '__main__':
    main()
