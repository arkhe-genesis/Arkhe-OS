# The issue is that the job exits with code 1 despite `|| echo ...`.
# Wait, let me check the yaml.
# `winget install Arkhe.ArkheCLI --accept-package-agreements --accept-source-agreements || echo "ArkheCLI not found, mocking installation"`
# In powershell (the default shell on windows-latest), `||` does not work like bash. In newer PowerShell 7 it might, but it is better to use `ContinueOnError` or ignore errors in PS properly, or specify `shell: bash`.
