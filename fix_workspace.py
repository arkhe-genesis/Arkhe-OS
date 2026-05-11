with open("Cargo.toml", "r") as f:
    content = f.read()

import re
# check if substrate-9002 is in workspace.members
if "substrate-9002" not in content:
    members_regex = r"members\s*=\s*\[(.*?)\]"
    match = re.search(members_regex, content, flags=re.DOTALL)
    if match:
        old_members = match.group(1)
        new_members = old_members.rstrip() + ',\n    "substrate-9002",\n'
        content = content.replace(old_members, new_members)
        with open("Cargo.toml", "w") as f:
            f.write(content)
