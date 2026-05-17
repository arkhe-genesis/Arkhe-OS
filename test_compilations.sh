#!/bin/bash
set -e

echo "=== Python syntax check ==="
python3 -m py_compile monitoring/dashboard.py
python3 -m py_compile jails/jail_orchestrator.py

echo "=== Rust build ==="
cd bhyve
cargo check
cd ..

echo "ALL CHECKS PASSED"
