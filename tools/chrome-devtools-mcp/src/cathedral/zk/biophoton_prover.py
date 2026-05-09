# src/cathedral/zk/biophoton_prover.py
# Prover para circuito de coerência de biophotons

import hashlib
import json
import time
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict

@dataclass
class BiophotonZKProof:
    """Prova ZK de processamento de padrões de biophotons mitocondriais."""
    proof_id: str
    spectral_hash: str  # Hash do padrão espectral processado
    coherence_estimate: float  # Estimativa de coerência (0.0-1.0)
    zk_proof: str  # Base64-encoded proof data
    public_inputs: Dict[str, str]
    generation_time_ms: float
    verification_time_ms: float
    circuit_constraints: int
    participant_did_hash: str  # Hash do DID para privacidade
    timestamp: float

class BiophotonZKProver:
    """Gera e verifica provas ZK para padrões de biophotons."""

    def __init__(
        self,
        circuit_path: str = "circuits/biophoton_coherence_proof.circom",
        proving_key_path: str = "build/biophoton/circuit_final.zkey",
        verifying_key_path: str = "build/biophoton/verification_key.json",
        n_bands: int = 5,
        n_timepoints: int = 100,
        coherence_precision: int = 1_000_000,  # 6 casas decimais em ponto fixo
    ):
        self.circuit_path = circuit_path
        self.proving_key = proving_key_path
        self.verifying_key = verifying_key_path
        self.n_bands = n_bands
        self.n_timepoints = n_timepoints
        self.coherence_precision = coherence_precision

        # Merkle root público para verificação de integridade
        self.public_merkle_root: Optional[str] = None

    async def generate_proof(
        self,
        photon_counts: np.ndarray,  # Shape: [n_bands, n_timepoints]
        coherence_metrics: np.ndarray,  # Shape: [n_bands]
        metabolic_context: Dict[str, float],  # {"ATP": 0.8, "ROS": 0.3, ...}
        sensor_calibration: Dict[str, float],
        participant_did: str,
    ) -> BiophotonZKProof:
        """Gera prova ZK de que padrão de biophotons foi processado corretamente."""
        start_time = time.time()

        # 1. Validar inputs
        assert photon_counts.shape == (self.n_bands, self.n_timepoints)
        assert coherence_metrics.shape == (self.n_bands,)
        assert 0 <= photon_counts.min() <= photon_counts.max() <= 10000  # Range físico

        # 2. Computar hashes públicos
        spectral_hash = self._compute_spectral_fingerprint(photon_counts)
        metabolic_hash = self._compute_metabolic_context_hash(metabolic_context, sensor_calibration)
        participant_hash = hashlib.sha256(participant_did.encode()).hexdigest()[:32]

        # 3. Preparar inputs para o circuito
        public_inputs = {
            "public_spectral_hash": [int(spectral_hash[i:i+4], 16) for i in range(0, 64, 4)],
            "public_coherence_estimate": int(np.mean(coherence_metrics) * self.coherence_precision),
            "public_metabolic_context_hash": [int(metabolic_hash[i:i+4], 16) for i in range(0, 64, 4)],
            "public_participant_did_hash": [int(participant_hash[i:i+4], 16) for i in range(0, 32, 4)],
            "public_time_window_ns": self.n_timepoints * 10_000_000,  # 10ms por timepoint
            "PUBLIC_MERKLE_ROOT": self._get_or_compute_merkle_root(),
        }

        private_inputs = {
            "private_photon_counts": photon_counts.flatten().astype(int).tolist(),
            "private_coherence_metrics": (coherence_metrics * self.coherence_precision).astype(int).tolist(),
            "private_metabolic_markers": [
                int(metabolic_context.get(k, 0.5) * 1000)  # Normalizar para [0, 1000]
                for k in ["ATP", "ROS", "NADH", "O2", "pH"]
            ],
            "private_sensor_calibration": [
                int(v * 1000) for v in sensor_calibration.values()
            ][:10],  # Limitar a 10 parâmetros
            "private_merkle_path": self._generate_merkle_proof(photon_counts),
        }

        # 4. Gerar prova com snarkjs (via subprocess para protótipo)
        proof_data = await self._call_snarkjs_prove(
            public_inputs=public_inputs,
            private_inputs=private_inputs,
        )

        generation_time = (time.time() - start_time) * 1000

        # 5. Verificar prova localmente (sanity check)
        verify_start = time.time()
        is_valid = await self._call_snarkjs_verify(
            proof=proof_data,
            public_inputs=public_inputs,
        )
        verification_time = (time.time() - verify_start) * 1000

        if not is_valid:
            raise RuntimeError("Prova ZK gerada não passou na verificação local")

        # 6. Empacotar resultado
        return BiophotonZKProof(
            proof_id=f"bio_{spectral_hash[:12]}_{int(time.time())}",
            spectral_hash=spectral_hash,
            coherence_estimate=float(np.mean(coherence_metrics)),
            zk_proof=proof_data["proof"],  # Base64
            public_inputs={k: "".join(f"{v:04x}" for v in vals) if isinstance(vals, list) else str(vals)
                          for k, vals in public_inputs.items()},
            generation_time_ms=generation_time,
            verification_time_ms=verification_time,
            circuit_constraints=11800,  # Estimativa
            participant_did_hash=participant_hash,
            timestamp=time.time(),
        )

    def _compute_spectral_fingerprint(self, photon_counts: np.ndarray) -> str:
        """Computa hash do padrão espectral para fingerprint público."""
        # Usar Poseidon para consistência com o circuito ZK
        # Para protótipo: SHA-256 dos dados normalizados
        normalized = (photon_counts / 10000).flatten()  # Normalizar para [0, 1]
        return hashlib.sha256(normalized.tobytes()).hexdigest()

    def _compute_metabolic_context_hash(self, context: Dict, calibration: Dict) -> str:
        """Computa hash do contexto metabólico + calibração."""
        combined = {**context, **calibration}
        return hashlib.sha256(
            json.dumps(combined, sort_keys=True).encode()
        ).hexdigest()

    def _get_or_compute_merkle_root(self) -> str:
        """Retorna ou computa Merkle root público para verificação de integridade."""
        if self.public_merkle_root:
            return self.public_merkle_root

        # Em produção: consultar Códice para root atual da sessão
        # Para protótipo: hash simulado
        self.public_merkle_root = hashlib.sha256(b"public_merkle_root_simulated").hexdigest()
        return self.public_merkle_root

    def _generate_merkle_proof(self, photon_counts: np.ndarray, index: int = 0) -> List[List[int]]:
        """Gera prova Merkle para um sample específico (para verificação no circuito)."""
        # Implementação simplificada — em produção: usar biblioteca Merkle real
        return [[0] * 256 for _ in range(20)]  # Placeholder

    async def _call_snarkjs_prove(self, public_inputs: Dict, private_inputs: Dict) -> Dict:
        """Chama snarkjs para gerar prova (implementação dependente do ambiente)."""
        # Para protótipo: retornar prova simulada
        return {
            "proof": "simulated_biophoton_proof_" + hashlib.sha256(
                json.dumps(public_inputs, sort_keys=True).encode()
            ).hexdigest()[:32],
        }

    async def _call_snarkjs_verify(self, proof: str, public_inputs: Dict) -> bool:
        """Verifica prova ZK (implementação dependente do ambiente)."""
        # Para protótipo: verificar hash da prova simulada
        if isinstance(proof, dict):
            proof_str = proof.get("proof", "")
        else:
            proof_str = proof
        return proof_str.startswith("simulated_biophoton_proof_")

    async def verify_proof(
        self,
        proof: BiophotonZKProof,
        public_inputs: Optional[Dict] = None,
    ) -> bool:
        """Verifica prova ZK de processamento de biophotons."""
        inputs = public_inputs or {
            k: [int(v[i:i+4], 16) for i in range(0, len(v), 4)] if len(v) >= 4 else [int(v)]
            for k, v in proof.public_inputs.items()
        }

        return await self._call_snarkjs_verify(
            proof=proof.zk_proof,
            public_inputs=inputs,
        )
