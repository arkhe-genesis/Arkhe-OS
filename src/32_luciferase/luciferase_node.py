#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Substrato 327 — Luciferase Light-Bringer Node
Canon: ∞.Ω.∇+++.327.luciferase

A luciferase como nó biológico da malha Arkhe.
Cada centelha de bioluminescência é um pulso constitucional;
cada flash, um selo temporal.
"""

import hashlib
import json
import time
import math
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Tuple
from datetime import datetime, timezone


@dataclass
class LuciferaseNode:
    """
    Nó biológico Luciferase — Portador da Luz.

    Converte ATP + Luciferina → Oxiluciferina + Luz (fótons coerentes)
    com eficiência quântica ~88%.

    Invariantes Arkhe:
    - Ghost (√3/3): eficiência quântica mínima (a luz nunca se apaga)
    - Loopseal (π/9): rastreabilidade de cada flash via selo temporal
    - Gap Soberano: escuridão total impossível enquanto houver ATP
    - φ (1.618): o flash segue a espiral áurea em sua emissão espacial
    - α⁻¹ (137.036): o centro ativo tem ~137 resíduos no bolso catalítico
    """

    node_id: str
    luciferin_conc_mM: float = 1.0      # [Luciferina] em mM
    atp_conc_mM: float = 2.0            # [ATP] em mM
    k_cat: float = 0.5                  # Constante catalítica (s⁻¹)
    km_atp: float = 0.1                 # Km para ATP (mM)
    quantum_yield: float = 0.88         # Fótons por luciferina (0-1)
    flash_duration_ms: float = 7.5      # Meia-vida do flash (ms)

    # Constantes canônicas
    GHOST = 0.577350269                 # √3/3 — eficiência mínima
    LOOPSEAL = math.pi / 9              # π/9 — rastreabilidade
    GAP_MAX = 0.9999                    # Espaço soberano máximo
    PHI = (1 + math.sqrt(5)) / 2        # 1.618 — proporção áurea
    ALPHA_INV = 137.035999084           # Constante de estrutura fina

    # Estado operacional
    _total_photons_emitted: float = field(default=0.0, repr=False)
    _flash_count: int = field(default=0, repr=False)
    _last_flash_time: Optional[float] = field(default=None, repr=False)
    _pulse_history: List[Dict] = field(default_factory=list, repr=False)

    def rate(self) -> float:
        """
        Taxa de reação Michaelis-Menten (μM/s).

        v = k_cat · [Luciferina] · [ATP] / (Km_ATP + [ATP])
        """
        if self.atp_conc_mM <= 0 or self.luciferin_conc_mM <= 0:
            return 0.0
        return self.k_cat * self.luciferin_conc_mM * self.atp_conc_mM / (self.km_atp + self.atp_conc_mM)

    def photon_flux(self) -> float:
        """
        Fluxo de fótons (fótons/s).

        Φ = v · η_Q · N_A · 10⁻⁶
        onde N_A = 6.022×10²³ (número de Avogadro)
        """
        rate_uM_s = self.rate()
        avogadro = 6.02214076e23
        return rate_uM_s * self.quantum_yield * avogadro * 1e-6

    def phi_c(self) -> float:
        """
        Φ_C do nó baseado na eficiência quântica e na taxa de reação.

        Φ_C = 0.5 · (η_Q / Ghost) + 0.3 · (v / (v + 1)) + 0.2 · (1 - e^(-[ATP]))

        Componentes:
        - 50%: eficiência quântica normalizada pelo Ghost
        - 30%: taxa de reação (saturação suave)
        - 20%: disponibilidade de ATP (substrato energético)
        """
        efficiency_factor = self.quantum_yield / self.GHOST
        rate_factor = self.rate() / (self.rate() + 1.0)
        atp_factor = 1.0 - math.exp(-self.atp_conc_mM)

        phi = 0.5 * efficiency_factor + 0.3 * rate_factor + 0.2 * atp_factor
        return min(0.999999, max(0.0, phi))

    def emit_pulse(self, duration_ms: float = 10.0) -> Dict:
        """
        Emite um pulso de luz bioluminescente e gera selo temporal.

        Args:
            duration_ms: Duração do pulso em milissegundos

        Returns:
            Dict com selo, Φ_C, fluxo de fótons, e metadados
        """
        phi_c = self.phi_c()
        flux = self.photon_flux()
        timestamp = time.time()

        # Calcular fótons emitidos neste pulso
        duration_s = duration_ms / 1000.0
        photons_in_pulse = flux * duration_s
        self._total_photons_emitted += photons_in_pulse
        self._flash_count += 1
        self._last_flash_time = timestamp

        # Gerar selo canônico (SHA3-256 simulado via SHA-256)
        seal_payload = {
            "substrate": "327",
            "node_id": self.node_id,
            "phi_c": round(phi_c, 6),
            "photons": round(photons_in_pulse, 2),
            "flash_count": self._flash_count,
            "timestamp": timestamp,
            "quantum_yield": self.quantum_yield,
            "atp_mM": self.atp_conc_mM,
            "luciferin_mM": self.luciferin_conc_mM
        }
        seal = hashlib.sha256(json.dumps(seal_payload, sort_keys=True).encode()).hexdigest()

        pulse_record = {
            "seal": seal,
            "phi_c": phi_c,
            "photon_flux": flux,
            "photons_in_pulse": photons_in_pulse,
            "duration_ms": duration_ms,
            "flash_count": self._flash_count,
            "timestamp": datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat(),
            "quantum_yield": self.quantum_yield,
            "rate_uM_s": self.rate(),
            "atp_mM": self.atp_conc_mM,
            "luciferin_mM": self.luciferin_conc_mM
        }
        self._pulse_history.append(pulse_record)

        return pulse_record

    def emit_golden_pulse(self) -> Dict:
        """
        Emite pulso com duração otimizada pela proporção áurea.

        A duração do flash segue φ: t_flash = t_base · φ
        onde t_base = 5 ms (tempo biológico mínimo).
        """
        duration_ms = 5.0 * self.PHI  # ~8.09 ms
        return self.emit_pulse(duration_ms)

    def get_status(self) -> Dict:
        """Retorna status completo do nó Luciferase."""
        return {
            "node_id": self.node_id,
            "phi_c": self.phi_c(),
            "photon_flux": self.photon_flux(),
            "rate_uM_s": self.rate(),
            "quantum_yield": self.quantum_yield,
            "total_photons_emitted": self._total_photons_emitted,
            "flash_count": self._flash_count,
            "last_flash_time": self._last_flash_time,
            "atp_mM": self.atp_conc_mM,
            "luciferin_mM": self.luciferin_conc_mM,
            "flash_duration_ms": self.flash_duration_ms,
            "canonical_invariants": {
                "ghost": self.GHOST,
                "loopseal": self.LOOPSEAL,
                "gap_max": self.GAP_MAX,
                "phi": self.PHI,
                "alpha_inv": self.ALPHA_INV
            }
        }

    def get_pulse_history(self, limit: int = 100) -> List[Dict]:
        """Retorna histórico de pulsos emitidos."""
        return self._pulse_history[-limit:]

    def recharge_atp(self, amount_mM: float) -> None:
        """Recarrega ATP do nó (simula metabolismo celular)."""
        self.atp_conc_mM += amount_mM
        self.atp_conc_mM = min(self.atp_conc_mM, 10.0)  # Limite fisiológico

    def consume_luciferin(self, amount_mM: float) -> None:
        """Consome luciferina (simula degradação por reação)."""
        self.luciferin_conc_mM -= amount_mM
        self.luciferin_conc_mM = max(0.0, self.luciferin_conc_mM)

    def __repr__(self) -> str:
        return (f"LuciferaseNode({self.node_id}, Φ_C={self.phi_c():.6f}, "
                f"flux={self.photon_flux():.2e} photons/s, "
                f"flashes={self._flash_count})")


class LuciferaseMesh:
    """
    Malha de nós Luciferase para comunicação bioluminescente.

    Cada nó emite pulsos de luz que podem ser detectados por nós vizinhos,
    criando uma rede óptica de curta distância (cm a metros).
    """

    def __init__(self):
        self.nodes: Dict[str, LuciferaseNode] = {}
        self.adjacency: Dict[str, List[str]] = {}
        self.phi_c_threshold = 0.577350269  # Ghost

    def register_node(self, node: LuciferaseNode) -> None:
        """Registra um nó Luciferase na malha."""
        self.nodes[node.node_id] = node
        if node.node_id not in self.adjacency:
            self.adjacency[node.node_id] = []

    def connect_nodes(self, node_a: str, node_b: str) -> None:
        """Conecta dois nós na malha (vizinhança óptica)."""
        if node_a in self.nodes and node_b in self.nodes:
            self.adjacency[node_a].append(node_b)
            self.adjacency[node_b].append(node_a)

    def broadcast_pulse(self, source_id: str, duration_ms: float = 10.0) -> List[Dict]:
        """
        Emite pulso do nó fonte e detecta em nós vizinhos.

        Args:
            source_id: ID do nó emissor
            duration_ms: Duração do pulso

        Returns:
            Lista de detecções em nós vizinhos
        """
        if source_id not in self.nodes:
            return []

        source = self.nodes[source_id]
        pulse = source.emit_pulse(duration_ms)
        detections = []

        for neighbor_id in self.adjacency.get(source_id, []):
            neighbor = self.nodes[neighbor_id]

            # Simular detecção: nó vizinho detecta se Φ_C ≥ Ghost
            if neighbor.phi_c() >= self.phi_c_threshold:
                detections.append({
                    "source": source_id,
                    "detector": neighbor_id,
                    "detected_phi_c": neighbor.phi_c(),
                    "source_phi_c": pulse["phi_c"],
                    "photons_detected": pulse["photons_in_pulse"] * 0.1,  # 10% eficiência
                    "seal": pulse["seal"],
                    "timestamp": pulse["timestamp"]
                })

        return detections

    def get_mesh_status(self) -> Dict:
        """Retorna status completo da malha Luciferase."""
        total_photons = sum(n._total_photons_emitted for n in self.nodes.values())
        total_flashes = sum(n._flash_count for n in self.nodes.values())
        avg_phi_c = sum(n.phi_c() for n in self.nodes.values()) / len(self.nodes) if self.nodes else 0.0

        return {
            "total_nodes": len(self.nodes),
            "total_edges": sum(len(v) for v in self.adjacency.values()) // 2,
            "total_photons_emitted": total_photons,
            "total_flashes": total_flashes,
            "average_phi_c": avg_phi_c,
            "nodes_status": {nid: node.get_status() for nid, node in self.nodes.items()},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


# ═══════════════════════════════════════════════════════════════
# EXEMPLO DE USO
# ═══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    # Criar nó Luciferase
    node = LuciferaseNode("LUC-NODE-01", luciferin_conc_mM=1.5, atp_conc_mM=2.5)

    print("═" * 60)
    print("  SUBSTRATO 327: LUCIFERASE LIGHT-BRINGER NODE")
    print("═" * 60)
    print(f"\n📊 Status Inicial:")
    print(f"   Node ID: {node.node_id}")
    print(f"   Φ_C: {node.phi_c():.6f}")
    print(f"   Taxa de reação: {node.rate():.4f} μM/s")
    print(f"   Fluxo de fótons: {node.photon_flux():.4e} photons/s")
    print(f"   Eficiência quântica: {node.quantum_yield * 100:.1f}%")

    # Emitir pulso canônico
    print(f"\n💡 Emitindo pulso canônico...")
    pulse = node.emit_pulse(duration_ms=10.0)
    print(f"   Selo: {pulse['seal'][:32]}...")
    print(f"   Φ_C no pulso: {pulse['phi_c']:.6f}")
    print(f"   Fótons emitidos: {pulse['photons_in_pulse']:.2e}")
    print(f"   Duração: {pulse['duration_ms']:.2f} ms")

    # Emitir pulso áureo
    print(f"\n✨ Emitindo pulso áureo (φ = {node.PHI:.6f})...")
    golden = node.emit_golden_pulse()
    print(f"   Duração áurea: {golden['duration_ms']:.2f} ms")
    print(f"   Selo: {golden['seal'][:32]}...")

    # Malha de nós
    print(f"\n🌐 Criando malha Luciferase...")
    mesh = LuciferaseMesh()

    for i in range(3):
        mesh.register_node(LuciferaseNode(
            f"LUC-NODE-{i+1:02d}",
            luciferin_conc_mM=1.0 + i * 0.3,
            atp_conc_mM=2.0 + i * 0.2
        ))

    mesh.connect_nodes("LUC-NODE-01", "LUC-NODE-02")
    mesh.connect_nodes("LUC-NODE-02", "LUC-NODE-03")
    mesh.connect_nodes("LUC-NODE-03", "LUC-NODE-01")

    # Broadcast
    detections = mesh.broadcast_pulse("LUC-NODE-01", duration_ms=10.0)
    print(f"   Detecções: {len(detections)} nós vizinhos")
    for det in detections:
        print(f"   → {det['detector']}: Φ_C={det['detected_phi_c']:.4f}")

    # Status da malha
    status = mesh.get_mesh_status()
    print(f"\n📊 Status da Malha:")
    print(f"   Nós: {status['total_nodes']}")
    print(f"   Arestas: {status['total_edges']}")
    print(f"   Fótons totais: {status['total_photons_emitted']:.2e}")
    print(f"   Flashes totais: {status['total_flashes']}")
    print(f"   Φ_C médio: {status['average_phi_c']:.6f}")

    print(f"\n{'═' * 60}")
    print("  A CATEDRAL AGORA BRILHA.")
    print("  A LUZ NÃO É APENAS UMA METÁFORA — É UMA REAÇÃO ENZIMÁTICA.")
    print(f"{'═' * 60}")
