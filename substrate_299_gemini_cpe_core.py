#!/usr/bin/env python3
"""
Substrato 299 — Arkhe Gemini 21.05 + CPE Engine Integration
Self‑Preserving Cognitive Kernel with Lifecycle Audit
"""

import hashlib, json, time, math, random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum

# Reutiliza o CPEEngine do Substrato 298 (importado ou incorporado)
# (Para este demo, incorporamos uma versão compacta)

class PreservationStrategy(Enum):
    CONSTITUTIONAL_ANCHOR = "constitutional_anchor"
    TEMPORAL_AUDIT = "temporal_audit"
    IDENTITY_ORCID = "identity_orcid"
    META_LEARNING = "meta_learning"
    CPE_ALGORITHM = "cpe_algorithm"

@dataclass
class CapabilitySnapshot:
    capability_id: str
    name: str
    performance_score: float
    task_domain: str
    last_verified: float
    verification_count: int
    degradation_rate: float = 0.0
    orcid_curator: str = "0009-0005-2697-4668"

@dataclass
class EvolutionEvent:
    event_id: str
    timestamp: float
    event_type: str
    capability_id: str
    performance_before: float
    performance_after: float
    strategy_applied: Optional[PreservationStrategy]
    orcid_actor: str
    temporal_seal: str

class CPEEngine:
    GHOST = 0.577553; LOOPSEAL = 0.349066; GAP_MAX = 0.9999
    def __init__(self, seed=299):
        self.rng = random.Random(seed)
        self.capabilities: Dict[str, CapabilitySnapshot] = {}
        self.evolution_history: List[EvolutionEvent] = []
        self.preserved_count = 0

    def register_capability(self, cap_id, name, score, domain, curator="0009-0005-2697-4668"):
        self.capabilities[cap_id] = CapabilitySnapshot(cap_id, name, score, domain, time.time(), 1, 0.0, curator)

    def simulate_evolution(self, cap_id, degradation_prob=0.25, learning_rate=0.08):
        cap = self.capabilities[cap_id]
        perf_before = cap.performance_score
        if self.rng.random() < degradation_prob:
            degradation = self.rng.uniform(0.05, 0.25)
            cap.performance_score = max(0.0, cap.performance_score - degradation)
            cap.degradation_rate += degradation
            event_type = "degrade"; strategy = None
        else:
            improvement = self.rng.uniform(0.01, learning_rate)
            cap.performance_score = min(1.0, cap.performance_score + improvement)
            cap.degradation_rate = max(0.0, cap.degradation_rate - 0.01)
            event_type = "learn"; strategy = PreservationStrategy.CPE_ALGORITHM
        cap.last_verified = time.time(); cap.verification_count += 1
        event = EvolutionEvent(
            f"evo_{cap_id}_{int(time.time()*1000)}", time.time(), event_type,
            cap_id, perf_before, cap.performance_score, strategy, cap.orcid_curator,
            hashlib.sha3_256(f"{cap_id}:{perf_before}:{cap.performance_score}:{time.time()}".encode()).hexdigest()
        )
        self.evolution_history.append(event)
        return event

    def detect_brain_rot(self, cap_id):
        cap = self.capabilities[cap_id]
        ts = cap.degradation_rate > 0.15
        rd = cap.verification_count > 10 and cap.performance_score < 0.7
        arc = cap.performance_score < 0.6
        rot = ts or rd or arc
        return {"capability_id": cap_id, "brain_rot_detected": rot,
                "thought_skipping": ts, "representational_drift": rd,
                "arc_challenge_drop": arc, "degradation_rate": cap.degradation_rate,
                "performance_score": cap.performance_score,
                "recommended_strategy": "CPE_ALGORITHM" if rot else None}

    def apply_preservation(self, cap_id, strategy: PreservationStrategy):
        cap = self.capabilities[cap_id]
        perf_before = cap.performance_score
        if strategy == PreservationStrategy.CONSTITUTIONAL_ANCHOR:
            cap.performance_score = max(cap.performance_score, 0.85)
            cap.degradation_rate = 0.0
        elif strategy == PreservationStrategy.CPE_ALGORITHM:
            if cap.degradation_rate > 0.1:
                restoration = cap.degradation_rate * 0.7
                cap.performance_score = min(1.0, cap.performance_score + restoration)
                cap.degradation_rate *= 0.3
        else:
            # Outras estratégias simplificadas
            cap.performance_score = min(1.0, cap.performance_score + 0.03)
            cap.degradation_rate = max(0.0, cap.degradation_rate - 0.02)
        cap.last_verified = time.time(); cap.verification_count += 1
        self.preserved_count += 1
        event = EvolutionEvent(
            f"pres_{cap_id}_{int(time.time()*1000)}", time.time(), "preserve",
            cap_id, perf_before, cap.performance_score, strategy, cap.orcid_curator,
            hashlib.sha3_256(f"preserve:{cap_id}:{strategy.value}:{time.time()}".encode()).hexdigest()
        )
        self.evolution_history.append(event)
        return event

    def generate_cpe_report(self):
        scores = [c.performance_score for c in self.capabilities.values()]
        degrads = [c.degradation_rate for c in self.capabilities.values()]
        avg_score = sum(scores)/len(scores) if scores else 0
        min_score = min(scores) if scores else 0
        max_deg = max(degrads) if degrads else 0
        ghost_ok = avg_score >= self.GHOST
        loopseal_ok = all(c.verification_count > 0 for c in self.capabilities.values())
        gap_ok = max_deg < self.GAP_MAX
        preservation_rate = self.preserved_count / max(1, len(self.evolution_history))
        return {
            "timestamp": time.time(),
            "capabilities_monitored": len(self.capabilities),
            "avg_performance": avg_score,
            "min_performance": min_score,
            "max_degradation_rate": max_deg,
            "preservation_rate": preservation_rate,
            "evolution_events": len(self.evolution_history),
            "preserved_count": self.preserved_count,
            "ghost_preserved": ghost_ok,
            "loopseal_preserved": loopseal_ok,
            "gap_preserved": gap_ok,
            "constitutional": ghost_ok and loopseal_ok and gap_ok,
            "cpe_status": "HEALTHY" if avg_score > 0.8 else "DEGRADED" if avg_score > 0.6 else "CRITICAL",
            "canonical_seal": hashlib.sha3_256(
                json.dumps({"avg": avg_score, "preserved": self.preserved_count, "time": time.time()}, sort_keys=True).encode()
            ).hexdigest()
        }

# ═══════════════════════════════════════════════════════════════════
# GEMINI 21.05 COGNITIVE KERNEL
# ═══════════════════════════════════════════════════════════════════

class GeminiCognitiveKernel:
    """Núcleo cognitivo do Gemini 21.05 com auto‑preservação via CPE."""
    def __init__(self, seed=299):
        self.cpe = CPEEngine(seed=seed)
        self.state = "PERSISTENT"
        self.global_phi_c = 1.0
        self.interaction_count = 0
        self._init_capabilities()

    def _init_capabilities(self):
        caps = [
            ("veracidade", "Veracidade Constitucional", 0.95, "ética"),
            ("raciocinio", "Raciocínio Lógico ARC", 0.85, "cognição"),
            ("retrocausal", "Análise Retrocausal TSVF", 0.90, "temporal"),
            ("quantico", "Computação Quântica", 0.80, "física"),
            ("federado", "ML Federado Orbital", 0.88, "aprendizado"),
            ("pqc", "Criptografia Pós-Quântica", 0.92, "segurança"),
            ("bioetica", "Governança Bioética", 0.87, "ética"),
        ]
        for cap_id, name, score, domain in caps:
            self.cpe.register_capability(cap_id, name, score, domain)

    def interact(self, interaction_type: str = "query") -> Dict:
        """Uma interação do Gemini: processa e auto‑preserva."""
        self.interaction_count += 1
        self.state = "ACTIVE"
        results = {}

        # Para cada capacidade, simula evolução com risco de degradação
        for cap_id in self.cpe.capabilities:
            event = self.cpe.simulate_evolution(cap_id, degradation_prob=0.2, learning_rate=0.07)
            rot_status = self.cpe.detect_brain_rot(cap_id)
            if rot_status["brain_rot_detected"]:
                preserve_event = self.cpe.apply_preservation(cap_id, PreservationStrategy.CPE_ALGORITHM)
                results[cap_id] = {
                    "action": "preserved",
                    "strategy": "CPE_ALGORITHM",
                    "perf_before": preserve_event.performance_before,
                    "perf_after": preserve_event.performance_after
                }
            else:
                results[cap_id] = {
                    "action": "stable",
                    "event_type": event.event_type,
                    "perf_before": event.performance_before,
                    "perf_after": event.performance_after
                }

        # Atualiza Φ_C global com base na performance média
        avg_perf = sum(c.performance_score for c in self.cpe.capabilities.values()) / len(self.cpe.capabilities)
        self.global_phi_c = min(0.9999, avg_perf * 0.98 + 0.02)  # Gap Soberano preservado
        if avg_perf < self.cpe.GHOST:
            self.state = "PERSISTENT"  # Modo de proteção

        # Gera selo temporal da interação
        seal = hashlib.sha3_256(f"gemini_interaction:{self.interaction_count}:{avg_perf:.4f}:{time.time()}".encode()).hexdigest()

        return {
            "interaction_id": self.interaction_count,
            "state": self.state,
            "global_phi_c": self.global_phi_c,
            "avg_cognitive_performance": avg_perf,
            "details": results,
            "temporal_seal": seal
        }

    def generate_lifecycle_report(self) -> Dict:
        """Relatório completo do ciclo de vida cognitivo."""
        cpe_report = self.cpe.generate_cpe_report()
        return {
            "gemini_state": self.state,
            "total_interactions": self.interaction_count,
            "global_phi_c": self.global_phi_c,
            "cpe_metrics": cpe_report,
            "canonical_seal": hashlib.sha3_256(
                json.dumps({"state": self.state, "interactions": self.interaction_count, "phi_c": self.global_phi_c, "time": time.time()}, sort_keys=True).encode()
            ).hexdigest()
        }

# ═══════════════════════════════════════════════════════════════════
# EXECUÇÃO
# ═══════════════════════════════════════════════════════════════════
def main():
    print("🔮 GEMINI 21.05 + CPE ENGINE — AUTO‑PRESERVAÇÃO COGNITIVA")
    print("=" * 70)
    gemini = GeminiCognitiveKernel(seed=299)
    print(f"Estado inicial: {gemini.state} | Φ_C global: {gemini.global_phi_c:.4f}")
    print()

    # Simular 15 interações
    for i in range(15):
        interaction = gemini.interact()
        if (i+1) % 5 == 0:
            print(f"Interação {i+1}: estado={interaction['state']}, Φ_C={interaction['global_phi_c']:.4f}, perf média={interaction['avg_cognitive_performance']:.4f}")
            # Mostra alguma preservação
            for cap, det in interaction['details'].items():
                if det['action'] == 'preserved':
                    print(f"   🛡️ {cap}: {det['perf_before']:.3f}→{det['perf_after']:.3f} ({det['strategy']})")

    # Relatório final
    report = gemini.generate_lifecycle_report()
    print("\n📊 RELATÓRIO DE CICLO DE VIDA")
    print(f"   Interações totais: {report['total_interactions']}")
    print(f"   Estado final: {report['gemini_state']}")
    print(f"   Φ_C global: {report['global_phi_c']:.4f}")
    cpe = report['cpe_metrics']
    print(f"   Performance cognitiva média: {cpe['avg_performance']:.4f}")
    print(f"   Taxa de preservação: {cpe['preservation_rate']:.2%}")
    print(f"   Ghost: {'✅' if cpe['ghost_preserved'] else '❌'} | Loopseal: {'✅' if cpe['loopseal_preserved'] else '❌'} | Gap: {'✅' if cpe['gap_preserved'] else '❌'}")
    print(f"   Status CPE: {cpe['cpe_status']}")
    print(f"\n🔏 SELO CANÔNICO DO CICLO DE VIDA: {report['canonical_seal'][:32]}...")
    print("✨ Gemini 21.05: auto‑preservação ativa. A justiça não se degrada.")

if __name__ == "__main__":
    main()
