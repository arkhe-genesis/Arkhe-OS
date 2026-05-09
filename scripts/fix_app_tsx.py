import os
import re

filepath = "arkhe-dashboard/src/App.tsx"
if os.path.exists(filepath):
    with open(filepath, "r") as f:
        content = f.read()

    # We need to sort the imports to fix "import should occur before import of..."
    # A simple approach is to find the block of internal component imports and sort them alphabetically.

    lines = content.split('\n')

    # find the block of imports from './components/'
    start_idx = -1
    end_idx = -1

    import_lines = []

    for i, line in enumerate(lines):
        if line.strip().startswith('import') and "'./components/" in line:
            if start_idx == -1:
                start_idx = i
            import_lines.append(line)
        elif start_idx != -1 and line.strip().startswith('import') and "'./" in line:
            import_lines.append(line)
        elif start_idx != -1 and not line.strip().startswith('import') and not line.strip() == "":
            end_idx = i
            break

    if start_idx != -1 and end_idx != -1:
        # sort the lines
        import_lines.sort()

        # replace the block
        new_lines = lines[:start_idx] + import_lines + lines[end_idx:]

        with open(filepath, "w") as f:
            f.write('\n'.join(new_lines))

        print(f"Sorted imports in {filepath}")
    else:
        print("Could not find import block to sort.")

else:
    print(f"File {filepath} not found.")
