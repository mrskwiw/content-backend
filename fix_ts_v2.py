from pathlib import Path
import re

def fix_files():
    # Fix BriefImportSection.tsx
    brief_file = Path(r"C:\git\project\CONTENT MARKETING\30 Day Content Jumpstart\project\operator-dashboard\src\components\wizard\BriefImportSection.tsx")
    content = brief_file.read_text(encoding='utf-8')

    # The file has literal newlines in the string, we need to replace them
    # Pattern: ].join(' followed by newline(s) followed by ');
    content = re.sub(r"\]\.join\(['\"][\r\n]+['\"]\)", r"].join('\n')", content)

    brief_file.write_text(content, encoding='utf-8')
    print(f"Fixed {brief_file.name}")

    # Fix Wizard.tsx - replace all alert() blocks with literal newlines
    wizard_file = Path(r"C:\git\project\CONTENT MARKETING\30 Day Content Jumpstart\project\operator-dashboard\src\pages\Wizard.tsx")
    content = wizard_file.read_text(encoding='utf-8')

    # Find all template literals and string concatenations with literal newlines
    # Replace 'text\n' patterns (where \n is a literal newline)
    # This is tricky - we need to replace the actual newline characters within quoted strings

    # Strategy: Replace patterns like '...\n\n' + where \n is literal newline
    # with '...\n\n' +

    # Pattern 1: Single quotes with newlines followed by string concatenation
    # 'some text
    # ' +
    # Should become: 'some text\n' +

    lines = content.split('\n')
    fixed_lines = []

    for i, line in enumerate(lines):
        # Check if line contains a string that ends but has content continuing on next line
        if line.rstrip().endswith("' +") or line.rstrip().endswith("'"):
            # Check if this is inside an alert block
            # Look back to see if we're in an alert
            context = '\n'.join(lines[max(0, i-10):i+1])
            if 'alert(' in context or 'alert(`' in context:
                # This line is part of an alert
                # Check if the line ends with just a quote (which means the newline is in the string)
                stripped = line.rstrip()
                if stripped.endswith("'") and not stripped.endswith("\n'") and not stripped.endswith("' +"):
                    # This line ends with a quote but no explicit \n or + concat
                    # The newline is implied in the string
                    # Replace the closing quote
                    fixed_lines.append(line.replace("'", "\n'", 1) if line.count("'") > 0 else line)
                    continue

        fixed_lines.append(line)

    content = '\n'.join(fixed_lines)

    wizard_file.write_text(content, encoding='utf-8')
    print(f"Fixed {wizard_file.name}")
    print("\n[SUCCESS] Done!")

if __name__ == '__main__':
    fix_files()
