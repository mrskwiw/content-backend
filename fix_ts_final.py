from pathlib import Path

# Fix BriefImportSection.tsx
brief_file = Path(r"C:\git\project\CONTENT MARKETING\30 Day Content Jumpstart\project\operator-dashboard\src\components\wizard\BriefImportSection.tsx")
content = brief_file.read_text(encoding='utf-8')

# Read the file and find the problematic join
lines = content.splitlines(keepends=True)
output = []

i = 0
while i < len(lines):
    line = lines[i]

    # Fix the join pattern - look for ].join(' followed by next line being ');
    if "].join('" in line and i + 1 < len(lines):
        next_line = lines[i + 1]
        if next_line.strip() == "');":
            # This is the problematic pattern - replace both lines
            # Extract indentation
            indent = line[:len(line) - len(line.lstrip())]
            output.append(indent + "].join('\n');\n")
            i += 2  # Skip the next line
            continue

    output.append(line)
    i += 1

brief_file.write_text(''.join(output), encoding='utf-8')
print(f"Fixed BriefImportSection.tsx")

# Fix Wizard.tsx
wizard_file = Path(r"C:\git\project\CONTENT MARKETING\30 Day Content Jumpstart\project\operator-dashboard\src\pages\Wizard.tsx")
content = wizard_file.read_text(encoding='utf-8')
lines = content.splitlines(keepends=True)
output = []

i = 0
in_alert = False
alert_lines = []

while i < len(lines):
    line = lines[i]

    # Detect start of alert
    if 'alert(' in line and "'" in line:
        in_alert = True
        alert_lines = [line]
        i += 1
        continue

    # Collect alert lines
    if in_alert:
        alert_lines.append(line)

        # Check if alert ends
        if ');' in line and not line.strip().startswith('//'):
            # Process collected alert
            alert_text = ''.join(alert_lines)

            # Fix literal newlines in strings
            # Replace string patterns like 'text\n' + (where \n is literal newline)
            if "'\n" not in alert_text and "\n' +" in alert_text:
                # This has literal newlines, fix them
                fixed_alert = []
                for aline in alert_lines:
                    # If line ends with just ' or ' + and contains a newline before the quote
                    if ("' +" in aline or aline.rstrip().endswith("'")) and "\n" not in aline:
                        # Insert \n before the closing quote
                        fixed_line = aline.rstrip()
                        if fixed_line.endswith("' +"):
                            fixed_line = fixed_line[:-3] + "\n' +"
                        elif fixed_line.endswith("'"):
                            fixed_line = fixed_line[:-1] + "\n'"
                        fixed_alert.append(fixed_line + '\n')
                    else:
                        fixed_alert.append(aline)
                output.extend(fixed_alert)
            else:
                output.extend(alert_lines)

            in_alert = False
            alert_lines = []
            i += 1
            continue

        i += 1
        continue

    output.append(line)
    i += 1

wizard_file.write_text(''.join(output), encoding='utf-8')
print(f"Fixed Wizard.tsx")
print("\n[SUCCESS] All files fixed!")
