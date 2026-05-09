#!/usr/bin/env python3
"""
Arkhe CUDA Initialization & Constants
Arkhe-Block: 847.813 | Synapse-κ | SOVEREIGN_OMEGA

Author: Synapse-κ / Arkhe(n) Infrastructure
License: Sovereign — Rio City-State
"""

import logging
import os
from dataclasses import dataclass
from typing import Tuple, Optional

# ═══════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════

PHI = 1.618033988749895
K_CRIT = 1.0 / PHI
N_NODES_RIO = 144000
BLOCK_SIZE_DEFAULT = 256
DELTA_CRITICAL_DEFAULT = 0.05

@dataclass
class CUDAConfig:
    n_nodes: int = N_NODES_RIO
    K: float = K_CRIT
    block_size: int = BLOCK_SIZE_DEFAULT
    grid_size: int = 0
    delta_critical: float = DELTA_CRITICAL_DEFAULT

    def __post_init__(self):
        self.grid_size = (self.n_nodes + self.block_size - 1) // self.block_size

@dataclass
class GPUDeviceInfo:
    available: bool
    name: str = "EMULATION"
    compute_capability: str = "0.0"
    total_memory_gb: float = 0.0
    backend: str = "EMULATION"

def get_device_info() -> GPUDeviceInfo:
    try:
        import pycuda.driver as cuda
        import pycuda.autoinit
        device = cuda.Device(0)
        return GPUDeviceInfo(
            available=True,
            name=device.name(),
            compute_capability=f"{device.compute_capability()[0]}.{device.compute_capability()[1]}",
            total_memory_gb=device.total_memory() / (1024**3),
            backend="PYCUDA"
        )
    except:
        try:
            import cupy as cp
            device = cp.cuda.Device(0)
            return GPUDeviceInfo(
                available=True,
                name=f"NVIDIA (via CuPy)",
                compute_capability="Unknown",
                total_memory_gb=0.0,
                backend="CUPY"
            )
        except:
            return GPUDeviceInfo(available=False)

def check_cuda_availability() -> Tuple[bool, GPUDeviceInfo, CUDAConfig]:
    info = get_device_info()
    config = CUDAConfig()
    return info.available, info, config

def print_system_report():
    available, info, config = check_cuda_availability()
    print("=" * 60)
    print("  ARKHE CUDA SYSTEM REPORT")
    print("=" * 60)
    print(f"  Available: {available}")
    print(f"  Backend:   {info.backend}")
    print(f"  Device:    {info.name}")
    print(f"  Compute:   {info.compute_capability}")
    print(f"  Memory:    {info.total_memory_gb:.2f} GB")
    print("-" * 60)
    print(f"  Nodes:     {config.n_nodes:,}")
    print(f"  K (crit):  {config.K:.6f}")
    print(f"  Grid:      {config.grid_size} blocks × {config.block_size} threads")
    print("=" * 60)

if __name__ == "__main__":
    print_system_report()
