import re
with open('substrate-6070/src/lib.rs') as f:
    text = f.read()

# Remove second copy of everything after test block
index = text.find('// 5. ZK CIRCUIT SKELETON (Plonky2)')
if index != -1:
    text = text[:index]

with open('substrate-6070/src/lib.rs', 'w') as f:
    f.write(text)
