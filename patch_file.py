with open(".github/workflows/arkhe-ma-s2-check.yml", "r") as f:
    lines = f.readlines()

new_lines = []
for i, line in enumerate(lines):
    if line.strip() == "upload-artifact:":
        pass
    elif i >= 1 and lines[i-1].strip() == "upload-artifact:":
        pass
    elif i >= 2 and lines[i-2].strip() == "upload-artifact:":
        pass
    elif i >= 3 and lines[i-3].strip() == "upload-artifact:":
        pass
    elif i >= 4 and lines[i-4].strip() == "upload-artifact:":
        pass
    elif line.strip() == "# Upload como artifact":
        new_lines.append("    - name: Upload Compliance Report\n")
        new_lines.append("      uses: actions/upload-artifact@v4\n")
        new_lines.append("      if: always()\n")
        new_lines.append("      with:\n")
        new_lines.append("        name: ma-s2-compliance-report\n")
        new_lines.append("        path: MA_S2_Compliance_Report.md\n")
    else:
        new_lines.append(line)

with open(".github/workflows/arkhe-ma-s2-check.yml", "w") as f:
    f.writelines(new_lines)
