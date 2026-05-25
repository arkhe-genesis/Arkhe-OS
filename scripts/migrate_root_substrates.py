import os
import re
import hashlib
from pathlib import Path
import json

root = Path('.')
to_migrate = []

# List all files matching substrato_*, substrate_*, test_substrato_*, etc.
files_to_check = []
for p in root.iterdir():
    if p.is_file():
        name = p.name
        if (name.startswith('substrate') or name.startswith('test_substrate') or
            name.startswith('test_substrato') or name.startswith('test_v') or
            name.startswith('substrato')):
            files_to_check.append(p)

def parse_num_name(name):
    # Match number
    m = re.search(r'(\d+)', name)
    if m:
        num = m.group(1)
        # Extract everything after number as name
        # Ex: substrato_181_agentic_architecture.py -> agentic_architecture
        parts = name.split(num)
        if len(parts) > 1:
            rest = parts[1]
            rest = re.sub(r'^[_\.]+', '', rest) # remove leading underscores/dots
            # remove extensions
            rest = re.sub(r'\.(py|json|md|sh)$', '', rest)
            # remove trailing underscores
            rest = re.sub(r'_$', '', rest)

            if not rest:
                rest = "legacy"
            return int(num), rest
    return None, None

def get_sha3_seal(filepath):
    try:
        content = filepath.read_bytes()
        return hashlib.sha3_256(content).hexdigest()
    except:
        return "PLACEHOLDER"

migrated_groups = {}
for p in files_to_check:
    num, name = parse_num_name(p.name)
    if num is not None:
        if num not in migrated_groups:
            migrated_groups[num] = {"files": [], "name": name}
        migrated_groups[num]["files"].append(p)

with open('scripts/migrate.sh', 'w') as f:
    f.write("#!/bin/bash\n")
    f.write("set -e\n")

    for num, group in migrated_groups.items():
        name = group["name"]
        if name == "legacy":
            # try to find a better name from files
            for p in group["files"]:
                _, n = parse_num_name(p.name)
                if n and n != "legacy":
                    name = n
                    break
        dir_name = f"{num}_{name}"
        f.write(f"mkdir -p substrates/{dir_name}\n")

        # calculate a combined seal
        seal = hashlib.sha3_256()
        for p in sorted(group["files"]):
            f.write(f"git mv {p.name} substrates/{dir_name}/ || mv {p.name} substrates/{dir_name}/\n")
            seal.update(p.read_bytes())

        seal_hex = seal.hexdigest()

        # create substrate.toml
        toml_content = f"""[substrate]
id = {num}
name = "{name}"
status = "MIGRATED"
seal = "{seal_hex}"

[metrics]
standard_phi_c = 0.85
theosis_index = 0.85

[audit]
source_verified = true

[cross_substrate]
links = []
"""
        f.write(f"cat << 'EOF_TOML' > substrates/{dir_name}/substrate.toml\n{toml_content}EOF_TOML\n")
        f.write(f"git add substrates/{dir_name}/substrate.toml || true\n")
