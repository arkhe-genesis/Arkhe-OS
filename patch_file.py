with open("substrato_255.py", "r") as f:
    lines = f.readlines()

new_lines = []
skip = False
for i, line in enumerate(lines):
    # Fix security-scan
    if "  security-scan:" in line:
        new_lines.append(line)
        new_lines.append(lines[i+1])
        new_lines.append(lines[i+2])
        new_lines.append("    strategy:\n")
        new_lines.append("      matrix:\n")
        new_lines.append("        arch: [arm64, amd64, riscv64]\n")
        continue

    # Remove the old hardcoded arch stuff
    if "    steps:" in lines[i-1] and "security-scan:" in lines[i-4]:
        # we are at `- uses: actions/download-artifact@v4` inside security-scan
        pass

    new_lines.append(line)

