"""
Phase 1: Tool System Audit
Systematically analyze all 12 research tools for validation issues
"""

import re
from pathlib import Path
from typing import Dict, List, Set, Optional

# Tool list
TOOLS = [
    'voice_analysis',
    'seo_keyword_research',
    'competitive_analysis',
    'content_gap_analysis',
    'content_audit',
    'market_trends_research',
    'platform_strategy',
    'content_calendar_strategy',
    'audience_research',
    'icp_workshop',
    'story_mining',
    'brand_archetype',
    'determine_competitors',
    'business_report',
]

def extract_param_class_name(tool_name: str) -> str:
    """Convert tool name to parameter class name"""
    parts = tool_name.split('_')
    return ''.join(word.capitalize() for word in parts) + 'Params'

def analyze_schema_file():
    """Analyze research_schemas.py to extract field requirements"""
    schema_file = Path('backend/schemas/research_schemas.py')
    content = schema_file.read_text(encoding='utf-8')

    results = {}

    for tool in TOOLS:
        param_class = extract_param_class_name(tool)

        # Find class definition
        class_pattern = rf'class {param_class}\(BaseModel\):.*?(?=class |\Z)'
        match = re.search(class_pattern, content, re.DOTALL)

        if not match:
            results[tool] = {'error': f'Schema class {param_class} not found'}
            continue

        class_content = match.group(0)

        # Extract fields
        field_pattern = r'(\w+):\s*(?:Optional\[)?([^\]= ]+)\]?\s*=?\s*Field\((.*?)\)'
        fields = re.findall(field_pattern, class_content, re.DOTALL)

        tool_fields = {}

        for field_name, field_type, field_args in fields:
            is_optional = 'Optional[' in class_content
            description = ''
            desc_match = re.search(r'description=["\']([^"\']+)["\']', field_args)
            if desc_match:
                description = desc_match.group(1)

            tool_fields[field_name] = {
                'type': field_type,
                'optional': is_optional,
                'description': description
            }

        validators = re.findall(r'@field_validator\(["\']([^"\']+)["\']\)', class_content)

        results[tool] = {
            'param_class': param_class,
            'fields': tool_fields,
            'validators': validators,
            'field_count': len(tool_fields)
        }

    return results

def analyze_tool_implementation(tool_name: str) -> Dict:
    """Analyze tool implementation for data usage"""
    tool_file = Path(f'src/research/{tool_name}.py')

    if not tool_file.exists():
        return {'error': 'File not found'}

    content = tool_file.read_text(encoding='utf-8')

    # Find uses of client_context data
    client_context_fields = set()
    context_patterns = [
        r'client_context\.get\(["\']([^"\']+)["\']\)',
        r'self\.client_context\.get\(["\']([^"\']+)["\']\)',
    ]

    for pattern in context_patterns:
        matches = re.findall(pattern, content)
        client_context_fields.update(matches)

    has_error_handling = 'try:' in content and 'except' in content
    raises_errors = 'raise ValueError' in content

    return {
        'client_context_fields': sorted(client_context_fields),
        'has_error_handling': has_error_handling,
        'raises_errors': raises_errors
    }

# Run audit
print("=" * 80)
print("PHASE 1: TOOL SYSTEM AUDIT")
print("=" * 80)

schema_results = analyze_schema_file()

issues_found = []

for tool in TOOLS:
    print(f"\n{tool}")
    print("-" * 40)

    schema_info = schema_results.get(tool, {})
    if 'error' in schema_info:
        print(f"  ERROR: {schema_info['error']}")
        continue

    print(f"  Fields: {schema_info['field_count']}")

    for field_name, field_info in schema_info['fields'].items():
        opt = "Optional" if field_info['optional'] else "Required"
        print(f"    {field_name}: {field_info['type']} [{opt}]")

    impl_info = analyze_tool_implementation(tool)

    if impl_info['client_context_fields']:
        print(f"  Context fields: {', '.join(impl_info['client_context_fields'])}")

    print(f"  Error handling: {impl_info['has_error_handling']}")

print(f"\n\nTotal tools: {len(TOOLS)}")
