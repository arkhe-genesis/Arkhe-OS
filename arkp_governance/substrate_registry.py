#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
substrate_registry.py — Substrato 189
Substrate Registry — Registro Canônico de todos os Substratos da Catedral

Mantem metadados de viés (π), coerência (Φ_C), e estado de governança
para todos os substratos ARKHE. O registro é imutável via selos canônicos.

Formato do registro:
  {
    "substrate_id": "6184",
    "name": "circRNA Quantum Regulator",
    "domain": "biologia_quantica",
    "version": "6.6.0",
    "phi_c": 0.6544,
    "pi": 0.15,
    "state": "HEALTHY",
    "artifacts": 7,
    "tests": 6,
    "pass_rate": 1.0,
    "canonical_seal": "a9b00f9f6488e6ff",
    "dependencies": ["6180", "6181"],
    "governance_history": [...]
  }
"""

import json
import hashlib
import time
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field, asdict
from pathlib import Path


@dataclass
class SubstrateMetadata:
    """Metadados canônicos de um substrato."""
    substrate_id: str
    name: str
    domain: str
    version: str
    phi_c: float = 0.5
    pi: float = 0.5
    state: str = "HEALTHY"
    artifacts: int = 0
    tests: int = 0
    pass_rate: float = 0.0
    lines_of_code: int = 0
    canonical_seal: str = ""
    dependencies: List[str] = field(default_factory=list)
    governance_history: List[Dict] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    last_updated: float = field(default_factory=time.time)


class SubstrateRegistry:
    """
    Registro canônico de substratos da Catedral ARKHE.

    Mantem um banco de dados JSON de todos os substratos com seus
    metadados de saude epistemica e dependencias.
    """

    def __init__(self, registry_path: Optional[str] = None):
        self.registry_path = registry_path or "substrate_registry.json"
        self.substrates: Dict[str, SubstrateMetadata] = {}
        self._load_registry()

    def _load_registry(self) -> None:
        """Carrega registro do disco se existir."""
        path = Path(self.registry_path)
        if path.exists():
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                for sid, meta in data.items():
                    self.substrates[sid] = SubstrateMetadata(**meta)
            except Exception:
                pass

    def _save_registry(self) -> None:
        """Salva registro no disco."""
        data = {sid: asdict(meta) for sid, meta in self.substrates.items()}
        with open(self.registry_path, 'w') as f:
            json.dump(data, f, indent=2, sort_keys=True)

    def register(self, metadata: SubstrateMetadata) -> str:
        """Registra um novo substrato."""
        metadata.canonical_seal = self._compute_seal(metadata)
        self.substrates[metadata.substrate_id] = metadata
        self._save_registry()
        return metadata.canonical_seal

    def update(self, substrate_id: str, **kwargs) -> SubstrateMetadata:
        """Atualiza metadados de um substrato."""
        if substrate_id not in self.substrates:
            raise ValueError(f"Substrato {substrate_id} nao registrado")

        meta = self.substrates[substrate_id]
        for key, value in kwargs.items():
            if hasattr(meta, key):
                setattr(meta, key, value)

        meta.last_updated = time.time()
        meta.canonical_seal = self._compute_seal(meta)
        self._save_registry()
        return meta

    def get(self, substrate_id: str) -> Optional[SubstrateMetadata]:
        """Retorna metadados de um substrato."""
        return self.substrates.get(substrate_id)

    def list_all(self) -> List[SubstrateMetadata]:
        """Lista todos os substratos registrados."""
        return list(self.substrates.values())

    def list_by_domain(self, domain: str) -> List[SubstrateMetadata]:
        """Lista substratos por dominio."""
        return [m for m in self.substrates.values() if m.domain == domain]

    def list_by_state(self, state: str) -> List[SubstrateMetadata]:
        """Lista substratos por estado de saude."""
        return [m for m in self.substrates.values() if m.state == state]

    def get_dependencies(self, substrate_id: str) -> List[str]:
        """Retorna dependencias de um substrato."""
        meta = self.substrates.get(substrate_id)
        return meta.dependencies if meta else []

    def get_dependents(self, substrate_id: str) -> List[str]:
        """Retorna substratos que dependem do substrato dado."""
        return [sid for sid, meta in self.substrates.items()
                if substrate_id in meta.dependencies]

    def compute_global_phi_c(self) -> float:
        """Computa Φ_C global da Catedral."""
        if not self.substrates:
            return 0.0
        return sum(m.phi_c for m in self.substrates.values()) / len(self.substrates)

    def compute_global_pi(self) -> float:
        """Computa π global da Catedral."""
        if not self.substrates:
            return 1.0
        return sum(m.pi for m in self.substrates.values()) / len(self.substrates)

    def _compute_seal(self, metadata: SubstrateMetadata) -> str:
        """Computa selo canônico de um substrato."""
        data = asdict(metadata)
        # Remover campos volateis do selo
        data.pop('governance_history', None)
        data.pop('last_updated', None)
        return hashlib.sha3_256(
            json.dumps(data, sort_keys=True, separators=(',', ':')).encode()
        ).hexdigest()[:16]

    def generate_ecosystem_report(self) -> Dict[str, Any]:
        """Gera relatorio completo do ecossistema."""
        domains = {}
        states = {}
        for meta in self.substrates.values():
            domains[meta.domain] = domains.get(meta.domain, 0) + 1
            states[meta.state] = states.get(meta.state, 0) + 1

        return {
            'total_substrates': len(self.substrates),
            'total_artifacts': sum(m.artifacts for m in self.substrates.values()),
            'total_tests': sum(m.tests for m in self.substrates.values()),
            'total_lines_of_code': sum(m.lines_of_code for m in self.substrates.values()),
            'global_phi_c': self.compute_global_phi_c(),
            'global_pi': self.compute_global_pi(),
            'domains': domains,
            'states': states,
            'substrates': [asdict(m) for m in self.substrates.values()],
        }
