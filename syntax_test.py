import sys
import py_compile

files_to_test = [
    "arkhe_os/network/cathedral_network_154.py",
    "arkhe_os/network/interplanetary_ipfs.py",
    "arkhe_os/network/ritual_154_ipfs.py",
    "arkhe_os/sensors/quantum_magnetometer_152.py",
    "arkhe_os/meta/substrate_149_151.py",
    "arkhe_os/molecular_workshop/oracle_136.py",
]

errors = 0
for f in files_to_test:
    try:
        py_compile.compile(f, doraise=True)
        print(f"✅ Syntax OK: {f}")
    except Exception as e:
        print(f"❌ Syntax Error in {f}: {e}")
        errors += 1

if errors > 0:
    sys.exit(1)
sys.exit(0)
