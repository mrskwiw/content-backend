#!/usr/bin/env python3
"""Fix TypeScript syntax errors caused by literal newlines in strings."""

from pathlib import Path

def fix_files():
    """Fix both TypeScript files"""

    # Fix BriefImportSection.tsx
    brief_file = Path(r"C:\git\project\CONTENT MARKETING\30 Day Content Jumpstart\project\operator-dashboard\src\components\wizard\BriefImportSection.tsx")
    content = brief_file.read_text(encoding='utf-8')

    # Fix the join with literal newline (line 59)
    content = content.replace("].join('\n');", "].join('\n');")

    brief_file.write_text(content, encoding='utf-8')
    print(f"[OK] Fixed {brief_file.name}")

    # Fix Wizard.tsx
    wizard_file = Path(r"C:\git\project\CONTENT MARKETING\30 Day Content Jumpstart\project\operator-dashboard\src\pages\Wizard.tsx")
    content = wizard_file.read_text(encoding='utf-8')

    # Fix all template strings with literal newlines
    # Alert 1 (line 207-223)
    old1 = """        alert(
          'Company Name is required to create a client.

' +
          'This usually means:
' +
          '• Brief parsing failed (API authentication error)
' +
          '• Company name field was not filled in

' +
          'Please:
' +
          '• Enter the company name manually in the form above
' +
          '• Or re-upload the brief after fixing API credentials in Render'
        );"""

    new1 = """        alert(
          'Company Name is required to create a client.\n\n' +
          'This usually means:\n' +
          '• Brief parsing failed (API authentication error)\n' +
          '• Company name field was not filled in\n\n' +
          'Please:\n' +
          '• Enter the company name manually in the form above\n' +
          '• Or re-upload the brief after fixing API credentials in Render'
        );"""

    if old1 in content:
        content = content.replace(old1, new1)
        print("[OK] Fixed alert #1 (line 207-223)")

    # Fix remaining template strings with literal newlines
    replacements = [
        ("`Failed to create client: ${errorMsg}\n\nPlease check the console for details and try again.`",
         "`Failed to create client: ${errorMsg}\n\nPlease check the console for details and try again.`"),

        ("`Failed to update client: ${errorMsg}\n\nPlease check the console for details and try again.`",
         "`Failed to update client: ${errorMsg}\n\nPlease check the console for details and try again.`"),

        ("`Client saved successfully, but project creation failed: ${errorMsg}\n\nThe client has been saved. You can try creating the project again from the client detail page.`",
         "`Client saved successfully, but project creation failed: ${errorMsg}\n\nThe client has been saved. You can try creating the project again from the client detail page.`"),

        ("`An unexpected error occurred: ${errorMsg}\n\nPlease check the console for details.`",
         "`An unexpected error occurred: ${errorMsg}\n\nPlease check the console for details.`"),
    ]

    for i, (old, new) in enumerate(replacements, 2):
        if old in content:
            content = content.replace(old, new)
            print(f"[OK] Fixed alert #{i}")

    wizard_file.write_text(content, encoding='utf-8')
    print(f"[OK] Fixed {wizard_file.name}")

    print("\n[SUCCESS] All TypeScript syntax errors fixed!")
    print("\nNext steps:")
    print("  1. cd operator-dashboard && npm run typecheck")
    print("  2. docker-compose build")

if __name__ == '__main__':
    fix_files()
