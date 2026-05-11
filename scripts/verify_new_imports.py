import ast
import os
import sys

files_to_check = [
    "layer_1_hardware/substrates/v141_xla/hodge_star_xla.py",
    "layer_1_hardware/substrates/v141_lanczos/distributed_lanczos.py",
    "layer_1_hardware/substrates/calibration/pentacene_calibration.py",
    "core/integration/arkhe_infinity_integration.py"
]

all_passed = True

for fpath in files_to_check:
    try:
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
        ast.parse(content)
        print(f"Syntax OK: {fpath}")
    except Exception as e:
        print(f"Syntax ERROR in {fpath}: {e}")
        all_passed = False

if all_passed:
    print("All generated files have valid syntax.")
    sys.exit(0)
else:
    sys.exit(1)
