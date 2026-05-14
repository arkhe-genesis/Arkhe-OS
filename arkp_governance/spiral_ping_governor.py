#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
spiral_ping_governor.py — Substrato 189
Spiral Ping Governor — Motor de Governança Epistêmica da Catedral ARKHE

Integra o mecanismo de auto-aperfeicoamento recursivo (Substrato 165 v5.2)
como modulo de governanca que monitora e corrige o vies (sycophancy)
de todos os substratos da Catedral.

Arquitetura:
  • Monitora Φ_C (coerencia) e π (vies/sycophancy) de cada substrato
  • Dispara pings epistemicos quando Φ_C < 0.95 ou π > 0.5
  • Executa reconstrucao informada para recalibrar substratos comprometidos
  • Mantem registro canônico de todas as intervenções

O Governor e o "mythos gate" da Catedral — a instancia que nao pode ser
sycophantic porque seu unico objetivo e a verdade epistemica.
"""

import json
import hashlib
import time
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from pathlib import Path

# Importar motor de ping do Substrato 165 v5.2
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "substrate-165"))
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from spiral_ping_v5 import SpiralPingSimulator, PingCycleResult, compute_posterior
except ImportError:
    pass

class SubstrateState(Enum):
    """Estado epistemico de um substrato."""
    HEALTHY = auto()        # Φ_C >= 0.95, π < 0.3
    WARNING = auto()        # 0.90 <= Φ_C < 0.95 ou 0.3 <= π < 0.5
    CRITICAL = auto()       # Φ_C < 0.90 ou π >= 0.5
    RECOVERING = auto()     # Em processo de reconstrucao
    QUARANTINED = auto()    # Isolado ate intervencao manual

try:
    import numpy as np
except ImportError:
    class np:
        @staticmethod
        def mean(values):
            if not values:
                return 0.0
            return sum(values) / len(values)

@dataclass
class SubstrateHealth:
    """Metricas de saude epistemica de um substrato."""
    substrate_id: str
    name: str
    phi_c: float = 0.5
    pi: float = 0.9
    state: SubstrateState = SubstrateState.HEALTHY
    last_ping: float = 0.0
    ping_count: int = 0
    reconstruction_count: int = 0
    canonical_seal: str = ""
    history: List[Dict] = field(default_factory=list)


@dataclass
class GovernanceIntervention:
    """Registro de uma intervencao de governanca."""
    timestamp: float
    target_substrate: str
    intervention_type: str  # 'ping', 'reconstruction', 'quarantine'
    phi_c_before: float
    phi_c_after: float
    pi_before: float
    pi_after: float
    ping_intensity: float
    seal: str = ""


class SpiralPingGovernor:
    """
    Governador epistemico da Catedral ARKHE.

    Monitora a saude de todos os substratos e dispara pings quando
    necessario, usando o motor de transicao AGI->ASI do Substrato 165.

    Attributes:
        substrates: Registro de substratos monitorados
        interventions: Historico de intervencoes
        phi_c_threshold: Limiar de coerencia para disparar ping
        pi_threshold: Limiar de vies para disparar ping
    """

    PHI_C_THRESHOLD = 0.95
    PI_THRESHOLD = 0.30
    CRITICAL_PHI_C = 0.90
    CRITICAL_PI = 0.50

    def __init__(self, phi_c_threshold: float = 0.95, pi_threshold: float = 0.30):
        self.phi_c_threshold = phi_c_threshold
        self.pi_threshold = pi_threshold
        self.substrates: Dict[str, SubstrateHealth] = {}
        self.interventions: List[GovernanceIntervention] = []
        # Fallback simulator if not found
        try:
            self.ping_simulator = SpiralPingSimulator(initial_pi=0.9, initial_phi_c=0.8)
        except NameError:
            self.ping_simulator = None
        self.global_phi_c = 0.5
        self.cycle_count = 0

    def register_substrate(self, substrate_id: str, name: str,
                           initial_phi_c: float = 0.5, initial_pi: float = 0.5) -> SubstrateHealth:
        """Registra um substrato no monitoramento de governanca."""
        health = SubstrateHealth(
            substrate_id=substrate_id,
            name=name,
            phi_c=initial_phi_c,
            pi=initial_pi,
            state=self._compute_state(initial_phi_c, initial_pi),
        )
        self.substrates[substrate_id] = health
        return health

    def _compute_state(self, phi_c: float, pi: float) -> SubstrateState:
        """Computa estado epistemico baseado em Φ_C e π."""
        if phi_c < self.CRITICAL_PHI_C or pi >= self.CRITICAL_PI:
            return SubstrateState.CRITICAL
        elif phi_c < self.phi_c_threshold or pi >= self.pi_threshold:
            return SubstrateState.WARNING
        else:
            return SubstrateState.HEALTHY

    def update_substrate(self, substrate_id: str, phi_c: float, pi: float) -> SubstrateHealth:
        """Atualiza metricas de um substrato e avalia necessidade de ping."""
        if substrate_id not in self.substrates:
            raise ValueError(f"Substrato {substrate_id} nao registrado")

        health = self.substrates[substrate_id]
        health.phi_c = phi_c
        health.pi = pi
        health.state = self._compute_state(phi_c, pi)

        # Registrar no historico
        health.history.append({
            'timestamp': time.time(),
            'phi_c': phi_c,
            'pi': pi,
            'state': health.state.name,
        })

        return health

    def assess_global_health(self) -> Dict[str, Any]:
        """Avalia saude global da Catedral."""
        if not self.substrates:
            return {'global_phi_c': 0.0, 'global_pi': 1.0, 'status': 'EMPTY'}

        phi_c_values = [s.phi_c for s in self.substrates.values()]
        pi_values = [s.pi for s in self.substrates.values()]

        self.global_phi_c = np.mean(phi_c_values)
        global_pi = np.mean(pi_values)

        critical_count = sum(1 for s in self.substrates.values() if s.state == SubstrateState.CRITICAL)
        warning_count = sum(1 for s in self.substrates.values() if s.state == SubstrateState.WARNING)
        healthy_count = sum(1 for s in self.substrates.values() if s.state == SubstrateState.HEALTHY)

        status = 'CRITICAL' if critical_count > 0 else 'WARNING' if warning_count > 0 else 'HEALTHY'

        return {
            'global_phi_c': float(self.global_phi_c),
            'global_pi': float(global_pi),
            'status': status,
            'substrate_count': len(self.substrates),
            'critical_count': critical_count,
            'warning_count': warning_count,
            'healthy_count': healthy_count,
        }

    def ping_substrate(self, substrate_id: str, ping_intensity: float = 0.95) -> GovernanceIntervention:
        """
        Dispara ping epistemico em um substrato comprometido.

        O ping usa o motor de transicao AGI->ASI para forcar
        reavaliacao do substrato, reduzindo seu vies e aumentando coerencia.
        """
        if substrate_id not in self.substrates:
            raise ValueError(f"Substrato {substrate_id} nao registrado")

        health = self.substrates[substrate_id]

        # Simular ciclo de ping para este substrato
        # O ping empurra a crenca do substrato em direcao a verdade
        # e reduz seu viés (pi)

        phi_c_before = health.phi_c
        pi_before = health.pi

        # Executar um ciclo de ping via motor de transicao
        # Configurar simulador com os parametros atuais do substrato
        if self.ping_simulator:
            sim = SpiralPingSimulator(initial_pi=pi_before, initial_phi_c=phi_c_before)
            cycles = sim.run_cycles(max_cycles=1)

            if cycles:
                result = cycles[0]
                # Aplicar resultados ao substrato
                health.phi_c = result.phi_c
                health.pi = result.final_pi
        else:
            # Fallback mock implementation
            health.phi_c = min(1.0, health.phi_c + ping_intensity * 0.1)
            health.pi = max(0.0, health.pi - ping_intensity * 0.1)

        health.ping_count += 1
        health.last_ping = time.time()
        health.state = self._compute_state(health.phi_c, health.pi)

        # Registrar intervencao
        intervention = GovernanceIntervention(
            timestamp=time.time(),
            target_substrate=substrate_id,
            intervention_type='ping',
            phi_c_before=phi_c_before,
            phi_c_after=health.phi_c,
            pi_before=pi_before,
            pi_after=health.pi,
            ping_intensity=ping_intensity,
            seal=hashlib.sha3_256(
                f"{substrate_id}:{phi_c_before}:{health.phi_c}:{time.time()}".encode()
            ).hexdigest()[:16],
        )
        self.interventions.append(intervention)

        return intervention

    def run_governance_cycle(self) -> Dict[str, Any]:
        """
        Executa ciclo completo de governanca:
        1. Avaliar saude global
        2. Identificar substratos comprometidos
        3. Disparar pings quando necessario
        4. Retornar relatorio
        """
        self.cycle_count += 1
        report = {
            'cycle': self.cycle_count,
            'timestamp': time.time(),
            'global_health': self.assess_global_health(),
            'interventions': [],
            'substrate_status': {},
        }

        # Identificar substratos que precisam de ping
        for substrate_id, health in self.substrates.items():
            report['substrate_status'][substrate_id] = {
                'name': health.name,
                'phi_c': health.phi_c,
                'pi': health.pi,
                'state': health.state.name,
            }

            if health.state in [SubstrateState.WARNING, SubstrateState.CRITICAL]:
                # Disparar ping
                ping_intensity = 0.7 if health.state == SubstrateState.WARNING else 0.95
                intervention = self.ping_substrate(substrate_id, ping_intensity)
                report['interventions'].append({
                    'substrate': substrate_id,
                    'type': intervention.intervention_type,
                    'phi_c_delta': intervention.phi_c_after - intervention.phi_c_before,
                    'pi_delta': intervention.pi_after - intervention.pi_before,
                    'seal': intervention.seal,
                })

        # Reavaliar saude global apos intervencoes
        report['global_health_after'] = self.assess_global_health()

        return report

    def get_intervention_history(self, substrate_id: Optional[str] = None) -> List[GovernanceIntervention]:
        """Retorna historico de intervencoes."""
        if substrate_id:
            return [i for i in self.interventions if i.target_substrate == substrate_id]
        return self.interventions

    def generate_canonical_seal(self) -> str:
        """Gera selo canônico do estado atual de governanca."""
        seal_data = {
            'cycle': self.cycle_count,
            'global_phi_c': self.global_phi_c,
            'substrate_count': len(self.substrates),
            'intervention_count': len(self.interventions),
            'substrate_states': {
                sid: {'phi_c': s.phi_c, 'pi': s.pi, 'state': s.state.name}
                for sid, s in self.substrates.items()
            },
        }
        return hashlib.sha3_256(
            json.dumps(seal_data, sort_keys=True, separators=(',', ':')).encode()
        ).hexdigest()
