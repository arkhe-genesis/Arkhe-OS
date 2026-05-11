import subprocess
result = subprocess.run(['bash', 'tau_v1_1/3-validate-all.sh'], capture_output=True, text=True)
print(result.stdout)
print(result.stderr)
