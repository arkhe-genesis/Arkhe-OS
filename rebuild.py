import base64
import os
import re

# rebuilding 863
with open('substrates/t/863_secops_guardian_bridge/repo_integrity_daemon.py', 'r') as f:
    repo_data = f.read()
b64_repo = base64.b64encode(repo_data.encode()).decode()

with open('substrates/t/863_secops_guardian_bridge/substrato_863_secops_guardian_bridge.py', 'r') as f:
    sub_863 = f.read()
# We replace the base64 string directly
sub_863 = re.sub(r'("repo_integrity_daemon":\s*")[^"]*(")', r'\g<1>' + b64_repo + r'\g<2>', sub_863)
with open('substrates/t/863_secops_guardian_bridge/substrato_863_secops_guardian_bridge.py', 'w') as f:
    f.write(sub_863)

# rebuilding 870
with open('substrates/t/870_blockchain_z_glm/blockchain_z_glm.py', 'r') as f:
    bc_data = f.read()
b64_bc = base64.b64encode(bc_data.encode()).decode()

with open('substrates/t/870_blockchain_z_glm/substrato_870_blockchain_z_glm.py', 'r') as f:
    sub_870 = f.read()
sub_870 = re.sub(r'("blockchain_z_glm":\s*")[^"]*(")', r'\g<1>' + b64_bc + r'\g<2>', sub_870)
with open('substrates/t/870_blockchain_z_glm/substrato_870_blockchain_z_glm.py', 'w') as f:
    f.write(sub_870)
