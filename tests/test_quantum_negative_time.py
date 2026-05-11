"""
Testes específicos para tempo negativo quântico.
Valida a implementação baseada no experimento da Universidade de Toronto.
"""

import pytest
import time
import math
from components.agi.system32.temporal.retrocausal_consistency import (
    TemporalConsistencyOracle,
    TemporalMessage,
    CausalShield,
    QUANTUM_NEGATIVE_WINDOW_SECONDS,
)

class AuditLedger:
    def __init__(self, path):
        self.path = path
        self.records = []
    def get_records(self):
        return self.records
    def record(self, type_, payload):
        self.records.append({'type': type_, 'payload': payload, 'timestamp': time.time()})

class TestQuantumNegativeTime:
    """Testes para validação de tempo negativo quântico."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.ledger = AuditLedger("/tmp/test_quantum.db")
        self.oracle = TemporalConsistencyOracle(
            self.ledger,
            quantum_window=QUANTUM_NEGATIVE_WINDOW_SECONDS
        )

    def test_is_quantum_negative_time_method(self):
        """Testa o método de detecção de tempo quântico."""
        # Dentro da janela (1e-12 s)
        assert self.oracle._is_quantum_negative_time(-5e-13) == True
        assert self.oracle._is_quantum_negative_time(-1e-12) == True

        # Fora da janela
        assert self.oracle._is_quantum_negative_time(-2e-12) == False
        assert self.oracle._is_quantum_negative_time(-1.0) == False
        assert self.oracle._is_quantum_negative_time(-100) == False

        # Tempo positivo (nunca é negativo)
        assert self.oracle._is_quantum_negative_time(0.0) == False
        assert self.oracle._is_quantum_negative_time(1.0) == False
        assert self.oracle._is_quantum_negative_time(1e-12) == False

    def test_quantum_negative_time_consistent(self):
        """Tempo negativo quântico deve ser consistente."""
        msg = TemporalMessage(
            id="qtest-001",
            content="quantum photon",
            source_timestamp=1000.0,
            target_timestamp=1000.0 - 5e-13,  # -0.5 picosegundo
            sender_seal="SRC",
            receiver_seal="DST",
        )

        result = self.oracle.evaluate(msg)

        assert result.consistent == True
        assert result.quantum_coherent == True
        assert result.score >= 0.9
        assert result.paradox_type is None

    def test_classical_negative_time_detected_as_anomaly(self):
        """Tempo negativo clássico (> janela) deve ser sinalizado."""
        msg = TemporalMessage(
            id="ctest-001",
            content="past message",
            source_timestamp=1000.0,
            target_timestamp=1000.0 - 1.0,  # -1 segundo (FORA da janela)
            sender_seal="SRC",
            receiver_seal="DST",
        )

        result = self.oracle.evaluate(msg)

        # Score reduzido mas não necessariamente inconsistent
        assert result.score < 1.0
        assert result.quantum_coherent == False

        # Pode haver violação registrada
        violations_found = any("negativo" in v.lower() or "penalidade" in v.lower()
                               for v in result.violations)
        if result.score < 0.999:  # se não for 1.0, deve haver violação
            assert violations_found or len(result.violations) > 0

    def test_grandfather_paradox_still_detected(self):
        """Paradoxo do avô (tempo negativo grande) deve ser detectado."""
        import json

        # Registro futuro no ledger (simulando paradoxo)
        self.ledger.record("extratemporal_message_sent", {
            'msg_id': 'genesis-msg',
            'action': 'block_creation',
            'content_hash': 'aaa000'
        })

        msg = TemporalMessage(
            id="grandfather-001",
            content="prevent the creation of genesis",
            source_timestamp=1000.0,
            target_timestamp=500.0,  # 500 segundos atrás (FORA da janela)
            sender_seal="ANOMALY-01",
            receiver_seal="DST",
        )

        result = self.oracle.evaluate(msg)

        # Score deve ser baixo ou paradoxo detectado
        is_paradox = result.paradox_type is not None
        is_low_score = result.score < 0.5

        assert is_paradox or is_low_score, \
            f"Paradoxo do avô não detectado! Score: {result.score}, Tipo: {result.paradox_type}"

    def test_extreme_negative_time_rejected(self):
        """Tempo negativo extremo deve ser rejeitado."""
        msg = TemporalMessage(
            id="extreme-neg-001",
            content="going back millions of years",
            source_timestamp=1000.0,
            target_timestamp=1000.0 - (365.25 * 86400 * 100),  # -100 anos
            sender_seal="SRC",
            receiver_seal="DST",
        )

        result = self.oracle.evaluate(msg)

        # Score muito reduzido
        assert result.score < 0.5
        assert result.quantum_coherent == False

    def test_zero_delta_time(self):
        """Δt = 0 deve ser tratado como clássico (sem anomalia)."""
        msg = TemporalMessage(
            id="zero-001",
            content="instantaneous",
            source_timestamp=1000.0,
            target_timestamp=1000.0,
            sender_seal="SRC",
            receiver_seal="DST",
        )

        result = self.oracle.evaluate(msg, zk_proof={"prover_seal": "test", "challenge": "test", "response": "test", "timestamp": time.time()})

        # Delta zero é perfeitamente válido
        assert result.score >= 0.999
        assert result.quantum_coherent == False

    def test_small_positive_time(self):
        """Tempo positivo pequeno deve ser consistente."""
        msg = TemporalMessage(
            id="pos-001",
            content="future message",
            source_timestamp=1000.0,
            target_timestamp=1000.0 + 1e-15,  # femtossegundo futuro
            sender_seal="SRC",
            receiver_seal="DST",
        )

        result = self.oracle.evaluate(msg, zk_proof={"prover_seal": "test", "challenge": "test", "response": "test", "timestamp": time.time()})

        assert result.consistent
        assert not result.quantum_coherent  # Não é "negativo" quântico

    def test_quantum_window_configurability(self):
        """A janela quântica deve ser configurável por instância."""
        # Oracle com janela maior
        oracle_wide = TemporalConsistencyOracle(
            self.ledger, quantum_window=1e-6  # 1 microsegundo
        )

        msg = TemporalMessage(
            id="wide-001",
            content="wide window test",
            source_timestamp=1000.0,
            target_timestamp=1000.0 - 5e-7,  # -0.5 microsegundo
            sender_seal="SRC",
            receiver_seal="DST",
        )

        # Com janela ampla, -0.5 μs é aceito
        result_wide = oracle_wide.evaluate(msg)
        assert result_wide.quantum_coherent == True
        assert result_wide.consistent

        # Com janela padrão (1e-12), -0.5 μs é rejeitado como quântico
        result_default = self.oracle.evaluate(msg)
        assert result_default.quantum_coherent == False
        assert result_default.score < 1.0

    def test_consecutive_quantum_messages(self):
        """Múltiplas mensagens quânticas consecutivas devem ser consistentes entre si."""
        base_ts = 1000.0
        quantum_offset = 5e-13

        for i in range(5):
            msg = TemporalMessage(
                id=f"qchain-{i}",
                content=f"quantum step {i}",
                source_timestamp=base_ts,
                target_timestamp=base_ts - quantum_offset,
                sender_seal="SRC",
                receiver_seal="DST",
            )
            result = self.oracle.evaluate(msg)
            assert result.consistent, f"Mensagem quântica {i} falhou"
            assert result.quantum_coherent


class TestCausalShieldQuantum:
    """Testa o CausalShield com tempo negativo."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.ledger = AuditLedger("/tmp/test_quantum_shield.db")

    def test_shield_allows_quantum_negative_time(self):
        shield = CausalShield(self.ledger)

        msg = TemporalMessage(
            id="shield-test",
            content="quantum message",
            source_timestamp=1000.0,
            target_timestamp=1000.0 - 5e-13,
            sender_seal="TEST-SRC",
            receiver_seal="TEST-DST",
        )

        ok, reason = shield.eval(msg)

        # Shields shouldn't block quantum-coherent messages
        assert ok == True, f"Shield bloqueou tempo quântico: {reason}"

    def test_shield_rate_limit_excludes_quantum(self):
        """Rate limit não deve contar mensagens quânticas."""
        import json

        # Preencher rate limit com mensagens normais
        shield = CausalShield(self.ledger)

        # Criar 200 entradas de rate limit enviando mensagens normais
        for i in range(200):
            msg = TemporalMessage(
                id=f"normal-{i}",
                content=f"msg {i}",
                source_timestamp=1000.0,
                target_timestamp=1000.0,  # tempo zero (normal)
                sender_seal="RATE-LIMITED",
                receiver_seal="DST",
            )
            shield.eval(msg)

        # Agora tentar mensagem quântica (deve passar)
        quantum_msg = TemporalMessage(
            id="quantum-escape",
            content="quantum bypass",
            source_timestamp=1000.0,
            target_timestamp=1000.0 - 5e-13,  # tempo quântico
            sender_seal="RATE-LIMITED",  # mesmo selo
            receiver_seal="DST",
        )

        ok, reason = shield.eval(quantum_msg)
        # Mensagem quântica deve ser permitida (rate limit não aplica a Δt quântico)
        assert ok == True, f"Rate limit bloqueou mensagem quântica: {reason}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
