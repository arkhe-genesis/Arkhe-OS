import asyncio
import subprocess
import json
import os

async def verify_cua():
    print("--- Verifying Cua Integration ---")

    # 1. Check if bridge script exists
    bridge_path = "scripts/cua_bridge.py"
    if not os.path.exists(bridge_path):
        print(f"FAIL: {bridge_path} not found.")
        return

    # 2. Test listing sandboxes
    print("Testing cua_bridge.py list...")
    try:
        result = subprocess.check_output(["python3", bridge_path, "list", "--local"], text=True)
        data = json.loads(result)
        if "sandboxes" in data:
            print(f"PASS: List returned {len(data['sandboxes'])} sandboxes.")
        else:
            print(f"FAIL: Unexpected output: {result}")
    except Exception as e:
        print(f"FAIL: Error running list: {e}")

    # 3. Test creating a dummy sandbox (if possible, but we don't want to mess with local docker/qemu in CI)
    # Instead, let's just check the bridge script for syntax errors
    print("Checking bridge syntax...")
    try:
        subprocess.check_call(["python3", "-m", "py_compile", bridge_path])
        print("PASS: Bridge syntax is valid.")
    except Exception as e:
        print(f"FAIL: Syntax error in bridge: {e}")

    print("--- Verification Complete ---")

if __name__ == "__main__":
    asyncio.run(verify_cua())
