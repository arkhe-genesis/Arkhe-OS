#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    SUBSTRATO 870 — BLOCKCHAIN Z (GLM)                       ║
║              ARKHE Ω-TEMP Cathedral OS — Coherence Blockchain               ║
║                                                                              ║
║  Arquiteto: Rafael Oliveira | ORCID: 0009-0005-2697-4668                    ║
║  Version: 870.1.0 | Royalties: 2% → ORCID | Keeper: ψ                       ║
║  Ghost Threshold: γ = 0.577 (Euler-Mascheroni)                              ║
║  Kuramoto Coupling: CORRECTED sign -(K/N)*Σsin(θ[j]-θ[i])                   ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import hashlib
import json
import math
import time

# Constants
GHOST_THRESHOLD = 0.577
CANONIZATION_THRESHOLD = 0.900
SUBSTRATE_ID = 870
MAX_VALIDATORS = 128
COUPLING_STRENGTH_DEFAULT = 4.0

def compute_seal(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def compute_block_seal(block_data: dict) -> str:
    header = json.dumps(block_data, sort_keys=True, separators=(',', ':'))
    return compute_seal(header.encode('utf-8'))

class KuramotoBlockchainEngine:
    def __init__(self, n_validators: int = 32, coupling: float = COUPLING_STRENGTH_DEFAULT):
        self.n = min(n_validators, MAX_VALIDATORS)
        self.K = coupling
        self.phases = self._init_genesis_phases()
        self.natural_frequencies = self._init_frequencies()
        self.blockchain = []
        self.pending_txs = []
        self.total_gas_used = 0.0
        self.cumulative_coherence = 0.0
        self.block_count = 0
        self.fork_count = 0
        self.total_steps = 0
        self.difficulty = 1.0
        self.current_tip = None

    def _init_genesis_phases(self):
        golden = (1 + math.sqrt(5)) / 2
        return [2 * math.pi * (i * golden % 1.0) for i in range(self.n)]

    def _init_frequencies(self):
        return [0.1 + 0.05 * math.sin(i * 0.7) for i in range(self.n)]

    def compute_order_parameter(self) -> float:
        re_sum = sum(math.cos(th) for th in self.phases)
        im_sum = sum(math.sin(th) for th in self.phases)
        r = math.sqrt(re_sum ** 2 + im_sum ** 2) / self.n
        return r

    def compute_phi_c(self) -> float:
        r = self.compute_order_parameter()
        ghost_count = sum(1 for th in self.phases if abs(th % (2 * math.pi)) > math.pi * (1 - GHOST_THRESHOLD))
        ghost_ratio = ghost_count / self.n if self.n > 0 else 0.0
        phi_c = r * (1.0 - ghost_ratio)
        return max(0.0, min(1.0, phi_c))

    def kuramoto_step(self, dt: float = 0.01):
        import numpy as np
        theta = np.array(self.phases)
        omega = np.array(self.natural_frequencies)
        delta = np.subtract.outer(theta, theta)
        coupling = -(self.K / self.n) * np.sum(np.sin(delta), axis=1)
        new_theta = theta + (omega + coupling) * dt
        self.phases = new_theta.tolist()
        self.total_steps += 1

    def create_transaction(self, tx_type: str, payload: dict, gas_limit: float = 21000.0) -> dict:
        tx = {
            "type": tx_type,
            "payload": payload,
            "gas_limit": gas_limit,
            "nonce": len(self.pending_txs),
            "timestamp": time.time(),
            "sender_phase": self.phases[0] if self.phases else 0.0
        }
        self.pending_txs.append(tx)
        return tx

    def mine_block(self, max_iterations: int = 5000) -> dict:
        txs_included = min(len(self.pending_txs), 100)
        included_txs = self.pending_txs[:txs_included]
        self.pending_txs = self.pending_txs[txs_included:]

        gas_used = sum(tx["gas_limit"] for tx in included_txs)
        self.total_gas_used += gas_used

        iteration = -1
        for iteration in range(max_iterations):
            self.kuramoto_step(dt=0.01)
            phi_c = self.compute_phi_c()
            if phi_c >= CANONIZATION_THRESHOLD:
                break

        phi_c_final = self.compute_phi_c()
        order_r = self.compute_order_parameter()

        block = {
            "block_number": self.block_count,
            "parent_hash": self.current_tip,
            "timestamp": time.time(),
            "phi_c": round(phi_c_final, 6),
            "order_parameter": round(order_r, 6),
            "n_validators": self.n,
            "coupling_k": self.K,
            "difficulty": self.difficulty,
            "transactions": txs_included,
            "gas_used": round(gas_used, 2),
            "total_gas": round(self.total_gas_used, 2),
            "iterations": iteration + 1,
            "total_steps": self.total_steps,
            "fork_detected": phi_c_final < GHOST_THRESHOLD
        }

        block["seal"] = compute_block_seal(block)
        self.current_tip = block["seal"]
        self.blockchain.append(block)
        self.block_count += 1
        self.cumulative_coherence += phi_c_final

        if phi_c_final < GHOST_THRESHOLD:
            self.fork_count += 1

        return block

    def get_chain_stats(self) -> dict:
        if not self.blockchain:
            return {"status": "EMPTY", "phi_c": 0.0}
        phi_values = [b["phi_c"] for b in self.blockchain]
        avg_phi = sum(phi_values) / len(phi_values)
        return {
            "block_count": self.block_count,
            "fork_count": self.fork_count,
            "total_gas": round(self.total_gas_used, 2),
            "avg_phi_c": round(avg_phi, 6),
            "difficulty": self.difficulty,
            "n_validators": self.n,
            "coupling_k": self.K,
            "current_phi_c": round(self.compute_phi_c(), 6),
            "chain_tip": self.current_tip
        }

def run_blockchain_z_simulation():
    engine = KuramotoBlockchainEngine(n_validators=32)
    engine.create_transaction("GENESIS", {"message": "Genesis"}, gas_limit=0)
    engine.mine_block(max_iterations=1000)
    for i in range(2):
        engine.create_transaction("TEST", {"iter": i})
        engine.mine_block()
    stats = engine.get_chain_stats()
    seal = compute_seal("substrate-870-blockchain-z".encode())
    return {
        "substrate_id": SUBSTRATE_ID,
        "status": "CANONIZED" if stats.get("avg_phi_c", 0) >= CANONIZATION_THRESHOLD else "PROVISIONAL",
        "phi_c": stats.get("avg_phi_c", 0),
        "seal": seal
    }

if __name__ == "__main__":
    result = run_blockchain_z_simulation()
    print("SEAL:", result["seal"])
