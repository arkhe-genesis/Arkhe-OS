import logging
from typing import Dict, Any
from src.tau_compiler.coherence import CoherenceCalculator
from src.relayer.client import Mo1RelayerClient

logger = logging.getLogger("Arkhe-CircuitBreaker")

class QuantumCircuitBreaker:
    """
    🜏 O Guardião do Enclave.
    Conecta o CoherenceCalculator ao Relayer.
    Implementa a barreira física: nenhuma transação incoerente é assinada.
    """
    def __init__(self):
        self.coherence_calc = CoherenceCalculator()
        self.relayer = Mo1RelayerClient()
        self.K_c = 0.6180339887498949  # Razão Áurea (Threshold Crítico)

    def process_intent(self, intent_text: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Pipeline completo com proteção quântica:
        Medição → Verificação (Circuit Breaker) → Relayer
        """
        # 1. MEDIÇÃO (O Olho)
        density, vector = self.coherence_calc.compute_phase(intent_text)
        logger.info(f"🔍 Medição: Ω'={density:.4f}")

        # 2. CIRCUIT BREAKER (A Barreira)
        if density < self.K_c:
            logger.critical(f"⛔ CIRCUIT BREAKER ATIVADO: Ω'={density:.4f} < {self.K_c}")
            return {
                "status": "ABORTED_BY_COHERENCE",
                "omega": density,
                "reason": "Intent below critical threshold. Reality refusal."
            }

        # 3. MATERIALIZAÇÃO (O Colapso no Enclave)
        logger.info(f"🚀 Coerência confirmada. Materializando intenção...")
        tx_result = self.relayer.emit_transaction(payload)

        # 4. REGISTRO NA MEMÓRIA (Axioma 2: M ∈ C)
        if tx_result and tx_result.get("status") == "success":
            self.coherence_calc.update_memory(vector)
            logger.info(f"🜏 Estado colapsado registrado na memória de fase.")

        return {
            "status": "MATERIALIZED",
            "omega": density,
            "transaction": tx_result
        }
