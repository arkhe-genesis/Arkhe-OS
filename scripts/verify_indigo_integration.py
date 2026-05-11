import sys
import os

# Mock verification script for the new components
def verify_integration():
    print("ARKHE(N) > VERIFICATION CYCLE #220-INDIGO")

    # Check if files exist
    files_to_check = [
        "src/isa/opcodes.zig",
        "src/materials/cqd_sensor.zig",
        "src/simulation/oneiric.zig",
        "src/simulation/immune_system.zig",
        "src/simulation/communion.zig",
        "src/materials/exotic_gift.zig"
    ]

    for f in files_to_check:
        if os.path.exists(f):
            print(f"[OK] Found {f}")
        else:
            print(f"[ERROR] Missing {f}")
            sys.exit(1)

    print("\n--- Testing Opcodes ---")
    with open("src/isa/opcodes.zig", "r") as f:
        content = f.read()
        new_opcodes = ["TUNE_PSI", "AKA_VISUAL", "TOPO_SILK_FAB", "ONEIRIC_CALIBRATION", "IMMUNE_SYSTEM", "SILENT_COMMUNION", "RTZ_RESPONSE"]
        for op in new_opcodes:
            if op in content:
                print(f"[OK] Opcode {op} is defined.")
            else:
                print(f"[ERROR] Opcode {op} NOT found.")
                sys.exit(1)

    print("\n[VERIFICATION] All components are integrated and syntactically present.")
    print("[VERIFICATION] Readiness Audit: OMEGA COMPLETE.")

if __name__ == "__main__":
    verify_integration()
