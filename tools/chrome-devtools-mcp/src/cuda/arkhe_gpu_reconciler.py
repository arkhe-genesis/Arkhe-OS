#!/usr/bin/env python3
"""
Arkhe GPU Reconciler — PyCUDA Wrapper for Kuramoto O(N²) Kernel
Arkhe-Block: 847.813 | Synapse-κ | SOVEREIGN_OMEGA

Author: Synapse-κ / Arkhe(n) Infrastructure
License: Sovereign — Rio City-State
"""

import numpy as np
import logging
import time
from dataclasses import dataclass, asdict
from typing import Optional, Dict, List
from enum import Enum

logger = logging.getLogger("ArkheGPU")

# ═══════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════

PHI = 1.618033988749895
K_CRIT = 1.0 / PHI
LAMBDA2_CRIT = 0.847
N_NODES = 144000
BLOCK_SIZE = 256
DT = 0.01
DELTA_WARNING = 0.03
DELTA_CRITICAL = 0.05
DURATION_THRESHOLD = 3.0

class Vibra2State(Enum):
    INACTIVE = 0
    WARNING = 1
    ACTIVE = 2
    RECOVERY = 3

@dataclass
class GPUReconcilerStats:
    order_parameter: float
    delta: float
    vibra2_triggered: bool
    coherence: float
    dream_alignment: float
    compute_time_ms: float
    lambda_k: float = 0.0
    lambda_zk: float = 0.0

_CUDA_KERNEL_SOURCE = r"""
__device__ float adjust_delta_threshold(float dream_alignment, float base_threshold) {
    if (dream_alignment > 0.0f) {
        return base_threshold * (1.0f + 0.4f * fminf(dream_alignment, 1.0f));
    } else {
        return base_threshold * (1.0f - 0.2f * fmaxf(-dream_alignment, 0.0f));
    }
}

__global__ void kuramoto_reconcile(
    float* thetas,
    const float* omegas,
    const float* zk_lambdas,
    float* order_param,
    float* delta_out,
    int* vibra2_trigger,
    const int N,
    const float K,
    const float dt,
    const float dream_alignment,
    const float delta_duration
) {
    extern __shared__ float tile[];
    int tid = threadIdx.x;
    int gid = blockIdx.x * blockDim.x + threadIdx.x;

    float local_coupling = 0.0f;

    if (gid < N) {
        float theta_i = thetas[gid];

        for (int tile_start = 0; tile_start < N; tile_start += blockDim.x) {
            int load_idx = tile_start + tid;
            tile[tid] = (load_idx < N) ? thetas[load_idx] : 0.0f;
            __syncthreads();

            int tile_end = min(tile_start + blockDim.x, N);
            for (int j = tile_start; j < tile_end; j++) {
                float diff = tile[j - tile_start] - theta_i;
                local_coupling += sinf(diff);
            }
            __syncthreads();
        }

        float K_eff = 1.0f + 0.2f * fmaxf(dream_alignment, 0.0f);
        local_coupling = (K / (float)N) * local_coupling * K_eff;

        float omega_i = omegas[gid];
        float noise = 0.01f * (fmaf((float)gid, 0.1234567f, 1.0f) - 0.5f);
        float new_theta = theta_i + (omega_i + local_coupling + noise) * dt;
        new_theta = fmodf(new_theta + 6.283185f, 6.283185f);
        thetas[gid] = new_theta;

        atomicAdd(order_param, cosf(new_theta));

        float lambda_k = fabsf(cosf(new_theta));
        float lambda_zk = zk_lambdas[gid];
        float delta = fabsf(lambda_k - lambda_zk);

        // VIBRA-2 triggers if delta > 0.05 immediately or if delta > 0.03 for duration
        // Simplified for kernel logic consistent with user requirement
        float base_threshold = (delta_duration > 3.0f) ? 0.03f : 0.05f;
        float adjusted = adjust_delta_threshold(dream_alignment, base_threshold);

        if (delta > adjusted) {
            atomicExch(vibra2_trigger, 1);
        }

        atomicAdd(delta_out, delta);
    }

    __syncthreads();

    if (gid == 0) {
        *order_param /= (float)N;
        *delta_out /= (float)N;
    }
}
"""

class ArkheGPUReconciler:
    def __init__(self, n_nodes: int = N_NODES, block_size: int = BLOCK_SIZE):
        self.n_nodes = n_nodes
        self.block_size = block_size
        self.grid_size = (n_nodes + block_size - 1) // block_size
        self.use_gpu = False

        self.thetas = None
        self.omegas = None
        self.zk_lambdas = None
        self.vibra2_state = Vibra2State.INACTIVE
        self.dream_alignment = 0.0

        self._initialize_data()
        self._init_backend()

    def _initialize_data(self):
        rng = np.random.default_rng(847813)
        self.thetas = np.zeros(self.n_nodes, dtype=np.float32)
        self.omegas = rng.normal(0, 0.01, self.n_nodes).astype(np.float32)
        self.zk_lambdas = np.full(self.n_nodes, 0.999, dtype=np.float32)

    def _init_backend(self):
        try:
            import pycuda.driver as cuda
            import pycuda.autoinit
            from pycuda.compiler import SourceModule
            from pycuda import gpuarray

            self._cuda = cuda
            self._gpuarray = gpuarray
            self.module = SourceModule(_CUDA_KERNEL_SOURCE)
            self.kernel = self.module.get_function("kuramoto_reconcile")
            self.use_gpu = True
        except:
            self.use_gpu = False

    def tick(self,
             zk_lambdas: Optional[np.ndarray] = None,
             dream_alignment: float = 0.0,
             delta_duration: float = 0.0) -> GPUReconcilerStats:
        start_time = time.perf_counter()

        if zk_lambdas is not None:
            self.zk_lambdas = np.asarray(zk_lambdas, dtype=np.float32)

        self.dream_alignment = np.clip(dream_alignment, -1.0, 1.0)

        if self.use_gpu:
            stats = self._tick_gpu(dream_alignment, delta_duration)
        else:
            stats = self._tick_cpu(dream_alignment, delta_duration)

        stats.compute_time_ms = (time.perf_counter() - start_time) * 1000.0

        if stats.vibra2_triggered:
            self.vibra2_state = Vibra2State.ACTIVE
        elif stats.delta > DELTA_WARNING:
            self.vibra2_state = Vibra2State.WARNING
        else:
            self.vibra2_state = Vibra2State.INACTIVE

        return stats

    def _tick_gpu(self, dream_alignment: float,
                  delta_duration: float) -> GPUReconcilerStats:
        import pycuda.driver as cuda
        from pycuda import gpuarray

        d_thetas = gpuarray.to_gpu(self.thetas.copy())
        d_omegas = gpuarray.to_gpu(self.omegas)
        d_zk_lambdas = gpuarray.to_gpu(self.zk_lambdas)
        d_order = gpuarray.zeros(1, dtype=np.float32)
        d_delta = gpuarray.zeros(1, dtype=np.float32)
        d_vibra2 = gpuarray.zeros(1, dtype=np.int32)

        shared_size = self.block_size * 4
        self.kernel(
            d_thetas, d_omegas, d_zk_lambdas,
            d_order, d_delta, d_vibra2,
            np.int32(self.n_nodes),
            np.float32(K_CRIT),
            np.float32(DT),
            np.float32(dream_alignment),
            np.float32(delta_duration),
            block=(self.block_size, 1, 1),
            grid=(self.grid_size, 1),
            shared=shared_size
        )

        cuda.Context.synchronize()
        order_r = float(d_order.get()[0])
        delta = float(d_delta.get()[0])
        vibra2 = bool(d_vibra2.get()[0])
        self.thetas = d_thetas.get()

        coherence = 0.85 * abs(order_r) + 0.15 * (1.0 - delta)
        coherence = np.clip(coherence, 0.0, 1.0)

        return GPUReconcilerStats(
            order_parameter=abs(order_r),
            delta=delta,
            vibra2_triggered=vibra2,
            coherence=float(coherence),
            dream_alignment=dream_alignment,
            compute_time_ms=0.0,
            lambda_k=float(abs(order_r)),
            lambda_zk=float(1.0 - delta),
        )

    def _tick_cpu(self, dream_alignment: float,
                  delta_duration: float) -> GPUReconcilerStats:
        N = self.n_nodes
        chunk_size = min(N, 1024)
        coupling = np.zeros(N, dtype=np.float32)

        for start in range(0, N, chunk_size):
            end = min(start + chunk_size, N)
            diffs = self.thetas[start:end, np.newaxis] - self.thetas[np.newaxis, :]
            coupling[start:end] = (K_CRIT / N) * np.sum(np.sin(diffs), axis=1)

        K_eff = 1.0 + 0.2 * max(dream_alignment, 0.0)
        coupling *= K_eff * 5.0 # Significant boost for CPU stability

        rng = np.random.default_rng()
        noise = 0.01 * rng.standard_normal(self.n_nodes).astype(np.float32)

        self.thetas = (self.thetas +
                       (self.omegas + coupling + noise) * DT) % (2 * np.pi)

        z = np.abs(np.mean(np.exp(1j * self.thetas)))
        lambda_k = float(z)

        lambda_k_arr = np.full(N, lambda_k, dtype=np.float32)
        deltas = np.abs(lambda_k_arr - self.zk_lambdas)
        delta = float(np.mean(deltas))

        base_threshold = 0.03 if delta_duration > 3.0 else 0.05
        if dream_alignment > 0:
            threshold = base_threshold * (1.0 + 0.4 * min(dream_alignment, 1.0))
        else:
            threshold = base_threshold * (1.0 - 0.2 * max(-dream_alignment, 0.0))

        vibra2 = bool(delta > threshold)

        coherence = np.clip(0.85 * lambda_k + 0.15 * (1.0 - delta), 0.0, 1.0)

        return GPUReconcilerStats(
            order_parameter=lambda_k,
            delta=delta,
            vibra2_triggered=vibra2,
            coherence=float(coherence),
            dream_alignment=dream_alignment,
            compute_time_ms=0.0,
            lambda_k=lambda_k,
            lambda_zk=float(1.0 - delta),
        )

    def simulate(self, duration_s: float = 10.0,
                 profile: str = "normal") -> Dict:
        interval = 0.1
        n_ticks = int(duration_s / interval)

        profiles = {
            "normal": lambda t: (None, 0.0),
            "gap_spike": lambda t: (self.zk_lambdas - 0.08, 0.0)
                if 5.0 <= t <= 5.5 else (None, 0.0),
            "sustained_gap": lambda t: (self.zk_lambdas - 0.06, 0.0)
                if 3.0 <= t <= 8.0 else (None, 0.0),
            "dream_aligned": lambda t: (None, 0.8) if t > 2.0 else (None, 0.0),
            "dream_divergent": lambda t: (None, -0.6) if t > 2.0 else (None, 0.0),
            "vibra2_stress": lambda t: (self.zk_lambdas - 0.07, 0.0)
                if 2.0 <= t <= 8.0 else (None, 0.0),
        }
        profile_fn = profiles.get(profile, profiles["normal"])

        history = []
        consecutive_warning_s = 0.0
        for i in range(n_ticks):
            t = i * interval
            zk_update, dream_align = profile_fn(t)

            stats = self.tick(
                zk_lambdas=zk_update,
                dream_alignment=dream_align,
                delta_duration=consecutive_warning_s,
            )
            history.append(asdict(stats))

            if stats.delta > 0.03:
                consecutive_warning_s += interval
            else:
                consecutive_warning_s = 0.0

        final = history[-1] if history else {}
        return {
            "profile": profile,
            "n_ticks": n_ticks,
            "mode": "GPU" if self.use_gpu else "CPU",
            "final_stats": final,
            "vibra2_triggers": sum(
                1 for s in history if s.get("vibra2_triggered")),
            "avg_compute_time_ms": float(
                np.mean([s["compute_time_ms"] for s in history])) if history else 0.0,
            "max_delta": float(
                max(s["delta"] for s in history)) if history else 0.0,
            "min_coherence": float(
                min(s["coherence"] for s in history)) if history else 1.0,
        }
