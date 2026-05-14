# The error was Node.js 20 actions are deprecated for checkout@v4, and the job exited.
# But wait, looking at the logs:
# `winget install Arkhe.ArkheCLI --accept-package-agreements --accept-source-agreements`
# Output:
# `No package found matching input criteria.`
# `Process completed with exit code 1.`

# Oh, the issue is that Arkhe.ArkheCLI does not exist in the public msstore.
# How to install it?
# Let's check other workflows.
