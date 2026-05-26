import re

with open('test_substrates.py', 'r') as f:
    content = f.read()

# Fix test_substrato_841_web3_ontology_bridge
bad = 'assert data["Name"] == "CONSCIOUSNESS-SIMULATION-BRIDGE"'
good = 'assert data["Name"] == "WEB3-ONTOLOGY-BRIDGE"'
content = content.replace(bad, good)

# Remove the broken tests that the original repo had if we didn't add them
with open('test_substrates.py', 'w') as f:
    f.write(content)
