"""
Inventory – SBOM CycloneDX + reconciliação contínua de runtime
"""
import hashlib
import json
import asyncio
from typing import Dict, List, Optional
from dataclasses import dataclass, field

class Inventory:
    """
    Inventário de software com SBOM ancorada e reconciliação runtime.
    """

    def __init__(self, temporal_chain):
        self.temporal = temporal_chain
        self.sboms: Dict[str, Dict] = {}  # release_id -> SBOM
        self.runtime_state: Dict[str, List[str]] = {}  # release -> componentes runtime
        self.reconcile_tasks: Dict[str, asyncio.Task] = {}

    async def build_sbom(self, release_id: str) -> str:
        """
        INV‑2.1: Gera SBOM no formato CycloneDX simplificado.
        """
        sbom = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.5",
            "serialNumber": f"urn:uuid:{hashlib.sha3_256(release_id.encode()).hexdigest()[:32]}",
            "version": 1,
            "metadata": {
                "timestamp": __import__('time').time(),
                "tools": [{"vendor": "ARKHE", "name": "MA-S2-SBOM-Generator", "version": "9008.0"}]
            },
            "components": self._generate_components(release_id)
        }
        self.sboms[release_id] = sbom
        return json.dumps(sbom, sort_keys=True)

    def _generate_components(self, release_id: str) -> List[Dict]:
        """Gera componentes sintéticos baseados no release."""
        seed = int(hashlib.sha3_256(release_id.encode()).hexdigest()[:4], 16)
        libs = ["arkhe-core", "qhttp-wheeler", "guardian-attractor",
                "temporal-chain", "fleet-orchestrator", "pentacene-backend"]
        components = []
        for lib in libs:
            version = f"{1 + (seed % 9)}.{seed % 20}.{seed % 100}"
            components.append({
                "type": "library",
                "name": lib,
                "version": version,
                "purl": f"pkg:pypi/{lib}@{version}",
                "hashes": [{"alg": "SHA3-256", "content": hashlib.sha3_256(f"{lib}@{version}".encode()).hexdigest()}]
            })
        return components

    async def reconcile_runtime(self, release_id: str):
        """
        INV‑2.2: Reconciliação contínua entre SBOM e runtime.
        Detecta drift de componentes.
        """
        await asyncio.sleep(0.01)  # Simulação não-bloqueante
        sbom = self.sboms.get(release_id, {})
        expected = {c["name"] for c in sbom.get("components", [])}
        runtime = self.runtime_state.get(release_id, set())
        drift = expected - set(runtime)
        return {
            "release": release_id,
            "expected_components": len(expected),
            "runtime_components": len(runtime),
            "drift_detected": len(drift) > 0,
            "missing": list(drift)
        }

    def register_runtime(self, release_id: str, components: List[str]):
        self.runtime_state[release_id] = components
