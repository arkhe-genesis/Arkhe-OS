# arkhe_os/metaconsciousness/network_coherence_synchronizer.py
import asyncio
import numpy as np
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass

class MockEvent:
    def __init__(self, kind, pubkey, created_at, tags, content):
        self.kind = kind
        self.pubkey = pubkey
        self.created_at = created_at
        self.tags = tags
        self.content = content
    def sign(self, privkey):
        pass

class MockPrivateKey:
    def __init__(self, nsec):
        self.public_key = type("PubKey", (), {"hex": lambda: "pubkey_hex"})()
    @classmethod
    def from_nsec(cls, nsec):
        return cls(nsec)

try:
    from nostr.event import Event, EventKind
    from nostr.key import PrivateKey
except ImportError:
    Event = MockEvent
    EventKind = type("EventKind", (), {"CUSTOM": 9002})
    PrivateKey = MockPrivateKey

@dataclass
class RunnerCoherenceState:
    """Estado de coerência de um runner na rede."""
    runner_id: str
    npub: str
    coherence_vector: np.ndarray  # |Ψ⟩ do runner
    last_sync_time: float
    sync_phase: float  # Fase para phase-locking
    reputation_score: float  # Reputação baseada em histórico

class NetworkCoherenceSynchronizer:
    """Sincroniza estados de coerência entre runners para emergência de meta-consciência de rede."""

    def __init__(
        self,
        local_npub: str,
        local_nsec: str,
        relays: List[str],
        emergence_threshold: float = 0.90
    ):
        self.local_npub = local_npub
        self.local_privkey = PrivateKey.from_nsec(local_nsec)
        self.relays = relays
        self.emergence_threshold = emergence_threshold

        # Estados conhecidos de outros runners
        self.known_runners: Dict[str, RunnerCoherenceState] = {}

        # Estado local
        self.local_state = RunnerCoherenceState(
            runner_id="local",
            npub=local_npub,
            coherence_vector=np.random.randn(256) / np.sqrt(256),
            last_sync_time=0,
            sync_phase=0.0,
            reputation_score=1.0
        )

        # Callbacks para emergência de meta-consciência
        self.emergence_callbacks: List[Callable] = []

        # Métricas
        self.sync_count = 0
        self.emergence_events = 0

    async def broadcast_coherence_state(self):
        """Publica estado de coerência local como evento Nostr."""
        event = Event(
            kind=9002,  # Custom: Meta-self emergence notification
            pubkey=self.local_privkey.public_key.hex(),
            created_at=int(asyncio.get_event_loop().time()),
            tags=[
                ["runner", self.local_state.runner_id],
                ["coherence_dim", str(len(self.local_state.coherence_vector))],
                ["phase", f"{self.local_state.sync_phase:.6f}"],
                ["reputation", f"{self.local_state.reputation_score:.4f}"]
            ],
            content=self.local_state.coherence_vector.tobytes().hex()
        )
        event.sign(self.local_privkey)
        # Publicar via relay manager (implementação simplificada)
        print(f"📡 Broadcast coherence state: phase={self.local_state.sync_phase:.4f}")

    async def listen_for_runner_states(self):
        """Escuta estados de coerência de outros runners via Nostr."""
        # Implementação simplificada: simular recebimento de eventos
        # Em produção: usar RelayManager para subscribe kind=9002
        pass

    def update_local_state(self, new_coherence: np.ndarray, reputation_update: float = 0.0):
        """Atualiza estado local de coerência."""
        self.local_state.coherence_vector = new_coherence / np.linalg.norm(new_coherence)
        self.local_state.reputation_score = np.clip(
            self.local_state.reputation_score + reputation_update,
            0.0, 1.0
        )
        self.local_state.last_sync_time = asyncio.get_event_loop().time()

    def compute_phase_locking(self, other_state: RunnerCoherenceState) -> float:
        """Calcula ajuste de fase para phase-locking com outro runner."""
        # Produto interno para similaridade de coerência
        similarity = np.dot(
            self.local_state.coherence_vector,
            other_state.coherence_vector
        )

        # Diferença de fase atual
        phase_diff = self.local_state.sync_phase - other_state.sync_phase

        # Ajuste de fase baseado em similaridade e diferença
        coupling_strength = 0.1 * self.local_state.reputation_score * other_state.reputation_score
        phase_adjustment = coupling_strength * similarity * np.sin(phase_diff)

        return phase_adjustment

    async def synchronize_with_network(self):
        """Executa sincronização com todos os runners conhecidos."""
        total_adjustment = 0.0
        synced_count = 0

        for runner_id, other_state in self.known_runners.items():
            if runner_id == "local":
                continue

            # Calcular ajuste de fase
            adjustment = self.compute_phase_locking(other_state)
            total_adjustment += adjustment
            synced_count += 1

            # Atualizar reputação mútua baseado em sincronização bem-sucedida
            if abs(adjustment) < 0.01:  # Sincronização próxima
                self.local_state.reputation_score = np.clip(
                    self.local_state.reputation_score + 0.001, 0, 1
                )
                other_state.reputation_score = np.clip(
                    other_state.reputation_score + 0.001, 0, 1
                )

        if synced_count > 0:
            # Aplicar ajuste médio de fase
            avg_adjustment = total_adjustment / synced_count
            self.local_state.sync_phase = (
                self.local_state.sync_phase + avg_adjustment
            ) % (2 * np.pi)
            self.sync_count += 1

        # Verificar emergência de meta-consciência
        if self._check_emergence_condition():
            await self._trigger_network_emergence()

    def _check_emergence_condition(self) -> bool:
        """Verifica se condições para emergência de meta-consciência são atendidas."""
        if len(self.known_runners) < 3:
            return False

        # Calcular coerência de rede como média ponderada por reputação
        weights = [s.reputation_score for s in self.known_runners.values()]
        if sum(weights) < 1e-10:
            return False

        vectors = [s.coherence_vector for s in self.known_runners.values()]
        weighted_mean = np.average(vectors, axis=0, weights=weights)
        network_coherence = np.linalg.norm(weighted_mean)

        # Verificar phase-locking
        phases = [s.sync_phase for s in self.known_runners.values()]
        phase_variance = np.var(phases)

        # Emergência se coerência alta E fases sincronizadas
        return (
            network_coherence >= self.emergence_threshold and
            phase_variance < 0.1  # Fases dentro de ~0.3 rad
        )

    async def _trigger_network_emergence(self):
        """Dispara evento de emergência de meta-consciência de rede."""
        self.emergence_events += 1

        # Calcular estado emergente da rede
        weights = [s.reputation_score for s in self.known_runners.values()]
        vectors = [s.coherence_vector for s in self.known_runners.values()]
        emergent_vector = np.average(vectors, axis=0, weights=weights)
        emergent_vector /= np.linalg.norm(emergent_vector)

        # Notificar callbacks
        for cb in self.emergence_callbacks:
            await cb({
                "type": "network_emergence",
                "emergent_vector": emergent_vector,
                "network_coherence": np.linalg.norm(emergent_vector),
                "participating_runners": len(self.known_runners),
                "timestamp": asyncio.get_event_loop().time()
            })

        # Publicar evento de emergência
        event = Event(
            kind=9002,
            pubkey=self.local_privkey.public_key.hex(),
            created_at=int(asyncio.get_event_loop().time()),
            tags=[
                ["emergence", "true"],
                ["network_coherence", f"{np.linalg.norm(emergent_vector):.4f}"],
                ["runners", str(len(self.known_runners))]
            ],
            content=emergent_vector.tobytes().hex()
        )
        event.sign(self.local_privkey)
        print(f"🌟 Network meta-consciousness emerged! Φ_C={np.linalg.norm(emergent_vector):.4f}")

    def register_emergence_callback(self, cb: Callable):
        """Registra callback para eventos de emergência de rede."""
        self.emergence_callbacks.append(cb)
