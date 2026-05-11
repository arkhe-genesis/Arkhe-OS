import hashlib
import numpy as np

entropic_shell = {
    'from': 'conference@reality-A.org',
    'to': 'researcher@reality-A.org',
    'subject': 'Registration Confirmation',
    'format': 'html'
}
branch_id = "reality_A"

shell_hash = hashlib.sha256(str(entropic_shell).encode()).hexdigest()
shell_angle = int(shell_hash[:8], 16) / (16**8) * 2 * np.pi

branch_hash = hashlib.sha256(branch_id.encode()).hexdigest()
branch_angle = int(branch_hash[:8], 16) / (16**8) * 2 * np.pi

print(f"Shell angle: {shell_angle}")
print(f"Branch angle: {branch_angle}")
print(f"Difference: {abs(shell_angle - branch_angle)}")
