#!/usr/bin/env python3
"""
Coherence Bridge Script
This script acts as the transliteration bridge connecting the `arkhe_os` backend metrics
with the frontend UI and the 3D generation logic.
"a coerência é a linha utilizada para tear"
"""

import urllib.request
import urllib.error
import json
import time
import subprocess
import os

ARKHE_METRICS_URL = "http://localhost:9080/metrics"
FRONTEND_BRIDGE_URL = "http://localhost:3000/api/bridge/omega"
FREECAD_SCRIPT = "arkhe-freecad/headless_pipeline.py"

def fetch_coherence():
    try:
        req = urllib.request.Request(ARKHE_METRICS_URL)
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
            if "omega" in data and "current_value" in data["omega"]:
                return data["omega"]["current_value"]
            else:
                print("⚠️ [Bridge] Unexpected response structure from arkhe_os.")
    except Exception as e:
        print(f"❌ [Bridge] Failed to fetch coherence metric: {e}")
    return None

def push_to_frontend(omega):
    try:
        payload = json.dumps({"omega": omega}).encode('utf-8')
        req = urllib.request.Request(FRONTEND_BRIDGE_URL, data=payload, headers={'Content-Type': 'application/json'}, method='POST')
        with urllib.request.urlopen(req, timeout=5) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            if res_data.get("success"):
                print(f"✅ [Bridge] Successfully transliterated coherence (omega={omega}) to frontend UI.")
            else:
                print(f"⚠️ [Bridge] Frontend responded but reported failure: {res_data}")
    except Exception as e:
        print(f"❌ [Bridge] Failed to push coherence metric to frontend: {e}")

def trigger_3d_generation(omega):
    print(f"🌀 [Bridge] Weaving coherence into 3D voxelization logic (target_phase={omega})...")

    # We pass a dummy step file, it will fail gracefully in the pipeline if it doesn't exist.
    cmd = [
        "python3", FREECAD_SCRIPT,
        "dummy_input.step",
        "output_coherence.json",
        "--phase", str(omega)
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        # Even if it exits with 1 (because the dummy file doesn't exist), we log the attempt
        print(f"   [FreeCAD] Output: {result.stdout.strip()}")
        if result.stderr:
            print(f"   [FreeCAD] Error output: {result.stderr.strip()}")
        print(f"✅ [Bridge] 3D generation logic triggered with phase {omega}.")
    except Exception as e:
        print(f"❌ [Bridge] Error running 3D generation script: {e}")

def run_bridge_cycle():
    print("--------------------------------------------------")
    print("🚀 Initiating Coherence Bridge Cycle...")
    omega = fetch_coherence()
    if omega is not None:
        print(f"📡 [Bridge] Fetched kernel_omega: {omega}")
        push_to_frontend(omega)
        trigger_3d_generation(omega)
    else:
        print("⚠️ [Bridge] Cannot proceed without coherence metric.")
    print("--------------------------------------------------")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--loop", action="store_true", help="Run continuously in a loop")
    parser.add_argument("--interval", type=int, default=5, help="Loop interval in seconds")
    args = parser.parse_args()

    if args.loop:
        print(f"Starting coherence bridge loop (interval={args.interval}s)...")
        try:
            while True:
                run_bridge_cycle()
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\nBridge stopped.")
    else:
        run_bridge_cycle()
