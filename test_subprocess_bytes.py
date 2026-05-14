import sys
import os
sys.path.insert(0, "substrates/9015_arkhe_stdlib")
os.environ["ARKHE_STDLIB_ENABLED"] = "1"
import arkhe_stdlib.compat as compat
compat.activate()

import subprocess
import arkhe_stdlib.safe_subprocess as ssp

try:
    ssp.run(b"rm -rf /", shell=True)
except Exception as e:
    print(f"Exception: {e}")

try:
    ssp.run([b"rm", b"-rf", b"/"])
except Exception as e:
    print(f"Exception: {e}")
