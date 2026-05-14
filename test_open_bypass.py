import sys
import os
sys.path.insert(0, "substrates/9015_arkhe_stdlib")
os.environ["ARKHE_STDLIB_ENABLED"] = "1"
import arkhe_stdlib.compat as compat
compat.activate()

import arkhe_stdlib.safe_open as so

try:
    so.open("/etc//passwd")
except Exception as e:
    print(f"Exception 1: {e}")

try:
    so.open("/etc/./passwd")
except Exception as e:
    print(f"Exception 2: {e}")
