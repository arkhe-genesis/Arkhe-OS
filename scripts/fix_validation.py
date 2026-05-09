import re
with open('scripts/arkhe_ising_v325/validate_architectural_decisions.py', 'r') as f:
    content = f.read()

content = content.replace("shattering_ratio > 0.2", "0.2 < shattering_ratio < 0.5")

with open('scripts/arkhe_ising_v325/validate_architectural_decisions.py', 'w') as f:
    f.write(content)
