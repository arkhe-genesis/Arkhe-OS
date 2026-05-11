import ast
import os
import sys

files_to_check = [
    "layer_1_hardware/substrates/v141/token_to_form_layer.py",
    "layer_1_hardware/substrates/v141/hodge_star_layer.py",
    "layer_1_hardware/substrates/v142/geodesic_moe_router.py",
    "layer_1_hardware/substrates/v143/riemannian_dp_proof.py",
    "layer_1_hardware/substrates/v144/quantum_digital_interface.py",
    "layer_1_hardware/substrates/v141/coherence_integrated_information.py",
    "validation/phi_c_monitor.py",
    "layer_1_hardware/substrates/v141_token_to_form.py",
    "layer_1_hardware/substrates/v142_geodesic_router.py",
    "layer_1_hardware/substrates/v143_riemannian_dp.py",
    "layer_1_hardware/substrates/v144_quantum_digital_interface.py",
    "layer_1_hardware/substrates/v142_geodesic_router_xla.py"
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
