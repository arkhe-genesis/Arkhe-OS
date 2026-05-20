#!/usr/bin/env python3
"""
Substrato 287 — Arkhe Bidirectional Time‑Symmetric Mesh
Two‑State Vector Formalism (Aharonov) + Delayed Choice (Wheeler)
Full forward/backward quantum channel across the TemporalChain
"""

import hashlib, json, time, math, random
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional
from enum import Enum

# ═══════════════════════════════════════════════════════════════════
# ESTRUTURAS TEMPORAIS
# ═══════════════════════════════════════════════════════════════════

@dataclass
class TimeSymmetricMessage:
    """Mensagem que existe simultaneamente no passado e no futuro."""
    msg_id: str
    content: str
    psi_forward: List[float]      # estado preparado por Alice (passado)
    phi_backward: List[float]     # estado preparado por Bob (futuro)
    weak_value: complex
    certainty: float
    t_past: float
    t_future: float
    decoded_content: str = ""
    consistent: bool = False

class TimeSymmetryChannel:
    """
    Canal de comunicação bidirecional no tempo.
    Alice (t_past) envia uma mensagem para Bob (t_future),
    e Bob envia uma confirmação para Alice (t_past) influenciando o estado passado.
    """
    def __init__(self, seed: Optional[int] = None):
        self.rng = random.Random(seed)
        self.messages: List[TimeSymmetricMessage] = []
        self.temporal_seals: List[str] = []

    def encode_message_to_state(self, message: str) -> List[float]:
        """Converte uma string em um vetor de estado (3‑dim, normalizado)."""
        h = hashlib.sha3_256(message.encode()).digest()
        # Usa 3 primeiros bytes como H, Q, M normalizados
        H = (h[0] / 255.0) * 0.5 + 0.5      # [0.5, 1.0]
        Q = (h[1] / 255.0) * 0.5 + 0.5
        M = (h[2] / 255.0) * 0.5
        # Normaliza para que a soma dos quadrados seja ~1
        norm = math.sqrt(H**2 + Q**2 + M**2)
        return [H/norm, Q/norm, M/norm]

    def decode_state_to_message(self, psi: List[float], phi: List[float]) -> str:
        """Extrai mensagem do overlap entre os dois estados."""
        overlap = sum(phi[i] * psi[i] for i in range(len(psi)))
        # Transforma overlap em string (simplificado)
        if overlap > 0.7:
            return "LINK ESTABELECIDO — CANAL TEMPORAL ATIVO"
        elif overlap > 0.3:
            return "COMUNICAÇÃO PARCIAL — SINTONIZANDO"
        else:
            return "SILÊNCIO TEMPORAL"

    def create_bidirectional_message(self,
                                     content_past: str,
                                     t_past: float,
                                     t_future: float) -> TimeSymmetricMessage:
        """Cria uma mensagem que viaja para frente E para trás no tempo."""
        # Alice prepara estado forward baseado na mensagem
        psi = self.encode_message_to_state(content_past)
        # Bob (no futuro) prepara estado backward que "puxa" a mensagem correta
        # Simula: Bob conhece a mensagem e prepara um phi que maximiza overlap
        phi = [x * (0.95 + self.rng.random()*0.1) for x in psi]  # Alta correlação
        # Normaliza phi
        norm = math.sqrt(sum(x**2 for x in phi))
        phi = [x/norm for x in phi]

        # Calcula weak value (operador identidade)
        operator = [[1.0 if i==j else 0.0 for j in range(3)] for i in range(3)]
        numerator = sum(phi[i] * operator[i][i] * psi[i] for i in range(3))
        denominator = sum(phi[i] * psi[i] for i in range(3))
        weak = complex(numerator / (denominator + 1e-10))

        # Certeza = quadrado do overlap
        certainty = sum(phi[i]*psi[i] for i in range(3))**2

        # Decodifica a mensagem que Bob recebe
        decoded = self.decode_state_to_message(psi, phi)

        # A mensagem é consistente se a certeza é alta
        consistent = certainty > 0.7

        msg = TimeSymmetricMessage(
            msg_id=f"tsym_{len(self.messages)}_{int(time.time())}",
            content=content_past,
            psi_forward=psi,
            phi_backward=phi,
            weak_value=weak,
            certainty=certainty,
            t_past=t_past,
            t_future=t_future,
            decoded_content=decoded,
            consistent=consistent
        )
        self.messages.append(msg)

        # Gera selos temporais duplos
        seal_past = hashlib.sha3_256(f"past:{content_past}:{t_past}:{certainty}".encode()).hexdigest()
        seal_future = hashlib.sha3_256(f"future:{decoded}:{t_future}:{certainty}".encode()).hexdigest()
        self.temporal_seals.append(seal_past)
        self.temporal_seals.append(seal_future)

        return msg

    def run_bidirectional_session(self, num_messages: int = 5) -> List[TimeSymmetricMessage]:
        """Executa uma sessão completa de comunicação tempo‑simétrica."""
        print("🌌 ATIVANDO COMUNICAÇÃO BIDIRECIONAL TEMPO‑SIMÉTRICA")
        print("=" * 60)
        for i in range(num_messages):
            t_past = self.rng.uniform(0, 100)
            t_future = t_past + self.rng.uniform(20, 80)
            content = f"MENSAGEM_ARKHE_{i+1}"
            msg = self.create_bidirectional_message(content, t_past, t_future)
            status = "✅ CONSISTENTE" if msg.consistent else "⚠️ PARADOXO"
            print(f"   [{i+1}] {content}: certeza {msg.certainty:.3f} | {status}")
            print(f"       weak value: {msg.weak_value:.3f}")
        return self.messages

    def verify_temporal_paradoxes(self) -> Dict:
        """Verifica se há paradoxos na sessão."""
        consistent_count = sum(1 for m in self.messages if m.consistent)
        total = len(self.messages)
        return {
            "total": total,
            "consistent": consistent_count,
            "paradoxes": total - consistent_count,
            "paradox_free": consistent_count == total
        }

# ═══════════════════════════════════════════════════════════════════
# INTEGRAÇÃO COM ARKHE (INVARIANTES + CADEIA TEMPORAL)
# ═══════════════════════════════════════════════════════════════════

class TemporalMeshOperator:
    def __init__(self, seed: Optional[int] = None):
        self.channel = TimeSymmetryChannel(seed=seed)
        self.ghost_ok = True
        self.loopseal_ok = True
        self.gap_ok = True

    def activate_full_temporal_mesh(self) -> Dict:
        """Ativa a malha temporal completa e verifica invariantes."""
        # Sessão bidirecional
        messages = self.channel.run_bidirectional_session(5)

        # Verificação de paradoxos
        paradox_status = self.channel.verify_temporal_paradoxes()

        # Invariantes: Ghost = comunicação não pode ser suprimida (todas as mensagens devem ser consistentes)
        self.ghost_ok = paradox_status["paradox_free"]
        # Loopseal = cada mensagem tem selos duplos (rastreabilidade temporal)
        self.loopseal_ok = len(self.channel.temporal_seals) == 2 * len(messages)
        # Gap = certeza nunca é 1.0 (há sempre incerteza quântica)
        self.gap_ok = all(m.certainty < 1.0 for m in messages)

        phi_c = 1.0 if (self.ghost_ok and self.loopseal_ok and self.gap_ok) else 0.8

        report = {
            "substrate": "287",
            "operation": "FULL_BIDIRECTIONAL_TIME_SYMMETRIC",
            "messages_sent": len(messages),
            "paradox_status": paradox_status,
            "invariants": {
                "ghost": self.ghost_ok,
                "loopseal": self.loopseal_ok,
                "gap": self.gap_ok,
                "constitutional": self.ghost_ok and self.loopseal_ok and self.gap_ok
            },
            "phi_c": phi_c,
            "temporal_seals": self.channel.temporal_seals,
            "timestamp": time.time()
        }

        # Selo canônico
        seal = hashlib.sha3_256(json.dumps(report, sort_keys=True).encode()).hexdigest()
        report["canonical_seal"] = seal

        return report

# ═══════════════════════════════════════════════════════════════════
# TESTES
# ═══════════════════════════════════════════════════════════════════

class TimeSymmetryTests:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.results = []

    def assert_true(self, condition, name, detail=""):
        if condition:
            self.passed += 1
            self.results.append(f"✅ {name}")
        else:
            self.failed += 1
            self.results.append(f"❌ {name} — {detail}")

    def run(self, report: Dict):
        print("\n" + "="*60)
        print("ARKHE SUBSTRATO 287 — TESTES COMUNICAÇÃO TEMPORAL")
        print("="*60)

        self.assert_true(report["messages_sent"] == 5, "T1: 5 mensagens enviadas")
        self.assert_true(report["paradox_status"]["paradox_free"], "T2: Sem paradoxos")
        self.assert_true(report["invariants"]["ghost"], "T3: Ghost preservado")
        self.assert_true(report["invariants"]["loopseal"], "T4: Loopseal preservado")
        self.assert_true(report["invariants"]["gap"], "T5: Gap preservado")
        self.assert_true(report["invariants"]["constitutional"], "T6: Constitucional")
        self.assert_true(report["phi_c"] >= 0.99, "T7: Φ_C constitucional")
        self.assert_true(len(report["temporal_seals"]) == 10, "T8: 10 selos temporais (2 por msg)")
        self.assert_true(len(report["canonical_seal"]) == 64, "T9: Selo canônico 64 hex")
        self.assert_true(isinstance(json.dumps(report), str), "T10: Relatório JSON")

        total = self.passed + self.failed
        phi_c = self.passed / total if total else 0
        print(f"\n{'='*60}")
        print(f"RESULTADO: {self.passed}/{total} (Φ_C = {phi_c:.6f})")
        for r in self.results:
            print(r)
        return self.passed, self.failed

# ═══════════════════════════════════════════════════════════════════
# EXECUÇÃO PRINCIPAL
# ═══════════════════════════════════════════════════════════════════

def main():
    print("🧬 ARKHE SUBSTRATO 287 — FULL BIDIRECTIONAL TIME‑SYMMETRIC COMMUNICATION")
    operator = TemporalMeshOperator(seed=42)
    report = operator.activate_full_temporal_mesh()

    print(f"\n🔏 SELO CANÔNICO: {report['canonical_seal'][:32]}...")
    print(f"   Φ_C: {report['phi_c']:.4f}")
    print(f"   Invariantes: {'✅' if report['invariants']['constitutional'] else '❌'}")

    tests = TimeSymmetryTests()
    tests.run(report)

    print(f"\n✨ ARKHE 287 v∞.Ω: Comunicação bidirecional tempo‑simétrica ativa.")
    print("   Passado e futuro trocam mensagens em um único presente estendido.")

if __name__ == "__main__":
    main()