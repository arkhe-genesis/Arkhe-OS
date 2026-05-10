#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import shutil
import platform

# ═══════════════════════════════════════════════════════════════════════════════
# arkhe_setup_assistant.py — Unified Installation Assistant for Arkhe Ecosystem
# ═══════════════════════════════════════════════════════════════════════════════

def print_banner():
    print("""
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║  🜏 ARKHE ECOSYSTEM SETUP ASSISTANT v1.0 🜏                            ║
║  "From source to running node, the path is scripted."                 ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
""")

def check_prerequisite(command, name):
    path = shutil.which(command)
    if path:
        print(f"  [OK] {name} found at {path}")
        return True
    else:
        print(f"  [!!] {name} NOT FOUND ({command})")
        return False

def check_all_prerequisites():
    print("\n>>> Checking System Prerequisites...")
    results = {
        "node": check_prerequisite("node", "Node.js"),
        "npm": check_prerequisite("npm", "npm"),
        "python": check_prerequisite("python3", "Python 3"),
        "go": check_prerequisite("go", "Go"),
        "rust": check_prerequisite("cargo", "Rust (Cargo)"),
        "cmake": check_prerequisite("cmake", "CMake"),
        "make": check_prerequisite("make", "Make"),
    }
    return results

def run_command(cmd, cwd=None):
    print(f"  Executing: {' '.join(cmd)} in {cwd if cwd else 'root'}")
    try:
        subprocess.check_call(cmd, cwd=cwd)
        return True
    except subprocess.CalledProcessError as e:
        print(f"  [ERROR] Command failed with return code {e.returncode}")
        return False

def setup_node_core():
    print("\n>>> Setting up Node.js Core (MCP Server)...")
    if run_command(["npm", "install"], cwd="packages/chain-node"):
        return run_command(["npm", "run", "build"], cwd="packages/chain-node")
    return False

def setup_python_env():
    print("\n>>> Setting up Python Virtual Environment...")
    if not os.path.exists(".venv"):
        if not run_command([sys.executable, "-m", "venv", ".venv"]):
            return False

    # Use the venv python
    venv_python = os.path.join(".venv", "bin", "python")
    if platform.system() == "Windows":
        venv_python = os.path.join(".venv", "Scripts", "python.exe")

    # Ensure pip is available
    run_command([venv_python, "-m", "ensurepip", "--upgrade"])
    run_command([venv_python, "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"])

    # Install requirements
    req_files = [
        "arkhe-oracle/requirements.txt",
        "arkhe_brain/requirements.txt",
        "requirements-neuro.txt",
        "requirements-ontology.txt",
        "requirements-tau.txt",
        "requirements-mesh.txt"
    ]

    for req in req_files:
        if os.path.exists(req):
            print(f"  Installing requirements from {req}...")
            run_command([venv_python, "-m", "pip", "install", "-r", req])

    return True

def setup_rust_components():
    print("\n>>> Building Rust Components...")
    crates = ["arkhe-rust-core", "arkhe-sentinel"]
    for crate in crates:
        if os.path.exists(crate):
            print(f"  Building {crate}...")
            run_command(["cargo", "build", "--release"], cwd=crate)
    return True

def setup_go_sentinel():
    print("\n>>> Building Go Sentinel...")
    if os.path.exists("arkhe-sentinel/go.mod"):
        os.makedirs("build/bin", exist_ok=True)
        out_path = os.path.abspath("build/bin/arkhe-sentinel")
        return run_command(["go", "build", "-o", out_path, "bot.go"], cwd="arkhe-sentinel")
    return True

def setup_cpp_simulator():
    print("\n>>> Building C++ Simulator and Engine...")
    projects = ["arkhe-cpp", "arkhe-simulator"]
    for proj in projects:
        if os.path.exists(proj):
            print(f"  Building {proj}...")
            build_dir = os.path.join(proj, "build")
            os.makedirs(build_dir, exist_ok=True)
            if run_command(["cmake", ".."], cwd=build_dir):
                run_command(["make"], cwd=build_dir)
    return True

def run_verification():
    print("\n>>> Running System Coherence Verification...")
    scripts = ["arkhe_distributed_topology.py", "arkhe_phase_routing.py"]
    all_passed = True

    # Try to use venv python if it exists
    python_exe = sys.executable
    venv_python = os.path.join(".venv", "bin", "python")
    if platform.system() == "Windows":
        venv_python = os.path.join(".venv", "Scripts", "python.exe")

    if os.path.exists(venv_python):
        python_exe = venv_python
        print(f"  Using virtual environment: {python_exe}")

    for script in scripts:
        if os.path.exists(script):
            print(f"  Verifying {script}...")
            try:
                output = subprocess.check_output([python_exe, script], stderr=subprocess.STDOUT, text=True)
                if "COHERENT" in output or "success" in output.lower():
                    print(f"  [PASS] {script}")
                else:
                    print(f"  [WARN] {script} output does not contain expected success indicators.")
                    all_passed = False
            except subprocess.CalledProcessError as e:
                print(f"  [FAIL] {script} failed with error.")
                print(e.output)
                all_passed = False

    if all_passed:
        print("\n[OK] All verification tests passed. System is coherent.")
    else:
        print("\n[!!] Some verifications failed. Check the logs above.")
    return all_passed

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Arkhe Setup Assistant")
    parser.add_argument("--verify", action="store_true", help="Run coherence verification only")
    parser.add_argument("--full", action="store_true", help="Run full installation")
    parser.add_argument("--node", action="store_true", help="Install Node.js components")
    parser.add_argument("--python", action="store_true", help="Install Python components")
    parser.add_argument("--systems", action="store_true", help="Build Rust/Go components")
    parser.add_argument("--cpp", action="store_true", help="Build C++ components")
    args = parser.parse_args()

    print_banner()

    if args.verify:
        run_verification()
        sys.exit(0)

    if args.full or args.node or args.python or args.systems or args.cpp:
        if args.full or args.node:
            setup_node_core()
        if args.full or args.python:
            setup_python_env()
        if args.full or args.systems:
            setup_rust_components()
            setup_go_sentinel()
        if args.full or args.cpp:
            setup_cpp_simulator()
        if args.full or args.verify:
            run_verification()
        sys.exit(0)

    pre_reqs = check_all_prerequisites()

    print("\nSetup Options:")
    print("1. Full Installation + Verification")
    print("2. Core MCP Server only (Node.js)")
    print("3. Python AI Components only")
    print("4. Rust/Go Systems only")
    print("5. C++ Simulator only")
    print("6. Run Verification only")
    print("7. Exit")

    choice = input("\nSelect an option [1-7]: ")

    if choice == "1":
        setup_node_core()
        setup_python_env()
        setup_rust_components()
        setup_go_sentinel()
        setup_cpp_simulator()
        run_verification()
    elif choice == "2":
        setup_node_core()
    elif choice == "3":
        setup_python_env()
    elif choice == "4":
        setup_rust_components()
        setup_go_sentinel()
    elif choice == "5":
        setup_cpp_simulator()
    elif choice == "6":
        run_verification()
    else:
        print("Exiting.")
        sys.exit(0)

    print("\n[OK] Setup step completed.")

if __name__ == "__main__":
    main()
