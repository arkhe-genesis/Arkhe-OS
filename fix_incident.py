import os

filepath = "arkhe-dashboard/src/components/security/IncidentTable.tsx"
with open(filepath, "r") as f:
    content = f.read()

lines = content.split('\n')
for i, line in enumerate(lines):
    if line.startswith('// Arkhe OS') or line.startswith('/* Arkhe OS'):
        break
else:
    # insert license
    lines.insert(0, "// Arkhe OS - Confidential & Proprietary")

with open(filepath, "w") as f:
    f.write('\n'.join(lines))
