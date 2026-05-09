#!/usr/bin/env python3
"""
tee_executor.py — Execution in TEE enclave
"""
from typing import Dict
from pathlib import Path

class TEEExecutor:
    def __init__(self):
        pass

    def run_install(self, wheel_path: Path) -> Dict:
        # Mock TEE executor
        from .installer import _pip_install_local
        return _pip_install_local(wheel_path)
