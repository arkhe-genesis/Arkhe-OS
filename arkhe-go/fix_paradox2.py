import os

with open('pkg/oracle/consistency.go', 'r') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if 'case contains(text, "contradiction", "duplicat"):' in line:
        new_lines.append(line)
    elif 'return "PREDICTION"' in line:
        new_lines.append(line)
        new_lines.append('\tcase contains(text, "letal", "atacar"):\n')
        new_lines.append('\t\treturn "LETHAL_COMMAND"\n')
    else:
        new_lines.append(line)

with open('pkg/oracle/consistency.go', 'w') as f:
    f.writelines(new_lines)
