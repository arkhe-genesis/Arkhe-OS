import os

with open('pkg/oracle/consistency.go', 'r') as f:
    lines = f.readlines()

new_lines = []
skip = False
for line in lines:
    if 'case contains(text, "contradiction", "duplicat"):' in line:
        new_lines.append(line)
        new_lines.append('\t\treturn "PREDICTION"\n')
        skip = True
    elif skip and 'case contains(text, "entrop"):' in line:
        skip = False
        new_lines.append(line)
    elif not skip:
        new_lines.append(line)

with open('pkg/oracle/consistency.go', 'w') as f:
    f.writelines(new_lines)
