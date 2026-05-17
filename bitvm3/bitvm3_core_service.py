#!/usr/bin/env python3
"""
ARKHE OS Substrato 198‑G: BitVM3‑core Verification Service
Canon: ∞.Ω.∇+++.198.G
Função: Serviço de verificação on‑chain via circuitos garbled (Yao‑style),
         integrado com TemporalChain para ancoragem de Assert e Disprove.
Isomorfismo: GC ↔ Paridade (181), Disprove ↔ Espelho (181), Assert ↔ Compulsão (181)
"""

import asyncio
import hashlib
import json
import time
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum, auto
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# ESTRUTURAS DE DADOS
# ═══════════════════════════════════════════════════════════════

class VerificationStatus(Enum):
    """Status de uma instância BitVM3‑core."""
    SETUP = "setup"                    # Setup concluído, aguardando Assert
    ASSERTED = "asserted"             # Assert publicado na TemporalChain
    CHALLENGED = "challenged"         # Disprove publicado (prova inválida)
    RESOLVED = "resolved"             # Timeout expirado, prova aceita
    EXPIRED = "expired"               # Timeout sem Assert

@dataclass
class GarbledCircuitArtifact:
    """Artefatos do circuito garbled gerados durante setup."""
    session_id: str
    garbled_circuit: bytes            # Circuito garbled completo
    encoding_info: bytes              # Informação de encoding (𝑒)
    decoding_info: bytes              # Informação de decoding (𝑑)
    false_output_label: bytes         # Label que decodifica para False
    gs_public_key: bytes              # Chave pública do GS scheme
    circuit_hash: str                 # Hash do circuito para verificação
    timestamp: float = field(default_factory=time.time)

@dataclass
class AssertRecord:
    """Registro de uma transação Assert."""
    assert_id: str
    session_id: str
    prover_id: str
    gs_signature: bytes               # Assinatura GS revelando encoding da prova
    claimed_statement_hash: str        # Hash do statement sendo provado
    temporal_seal: Optional[str] = None
    timestamp: float = field(default_factory=time.time)

@dataclass
class DisproveRecord:
    """Registro de uma transação Disprove."""
    disprove_id: str
    assert_id: str
    challenger_id: str
    false_output_label: bytes          # Label que decodifica para False
    temporal_seal: Optional[str] = None
    timestamp: float = field(default_factory=time.time)

# ═══════════════════════════════════════════════════════════════
# GARBLED CIRCUIT ENGINE (Yao‑style backend)
# ═══════════════════════════════════════════════════════════════

class GarbledCircuitEngine:
    """
    Motor de circuitos garbled Yao‑style.

    Em produção: usar biblioteca como `garbled‑circuit` ou `scalable‑gc`.
    Para MVP: simular com AES‑based half‑gates.
    """

    def __init__(self, security_parameter: int = 128):
        self.kappa = security_parameter
        self._sessions: Dict[str, GarbledCircuitArtifact] = {}

    async def garble_function(
        self,
        function_bytecode: bytes,
        input_size_bits: int,
        session_id: str
    ) -> GarbledCircuitArtifact:
        """
        Executa Gb(1^𝜅, 𝑓) → (𝐹, 𝑒, 𝑑).

        Simula garbling Yao‑style com half‑gates.
        """
        logger.info(f"🔧 Garbling circuito para sessão {session_id}")

        # Simular geração de circuito garbled
        # Em produção: usar biblioteca de GC real
        rng = np.random.RandomState(int(hashlib.sha3_256(session_id.encode()).hexdigest()[:8], 16))

        # Tamanho simulado do circuito garbled
        num_gates = len(function_bytecode) * 8  # ~1 gate por byte de bytecode
        circuit_size = num_gates * 16  # 16 bytes por half‑gate

        garbled_circuit = rng.bytes(circuit_size)
        encoding_info = rng.bytes(input_size_bits * 16)  # 2 labels por bit × 16 bytes
        decoding_info = rng.bytes(2 * 16)  # 2 output labels × 16 bytes

        # Label que decodifica para False (posição 0 nos outputs)
        false_output_label = decoding_info[:16]

        circuit_hash = hashlib.sha3_256(garbled_circuit).hexdigest()

        artifact = GarbledCircuitArtifact(
            session_id=session_id,
            garbled_circuit=garbled_circuit,
            encoding_info=encoding_info,
            decoding_info=decoding_info,
            false_output_label=false_output_label,
            gs_public_key=self._derive_gs_public_key(encoding_info),
            circuit_hash=circuit_hash
        )

        self._sessions[session_id] = artifact
        logger.info(f"✅ Circuito garbled gerado: {circuit_hash[:16]}...")

        return artifact

    def _derive_gs_public_key(self, encoding_info: bytes) -> bytes:
        """Deriva chave pública GS a partir da informação de encoding."""
        # Lamport: pk = hash dos pares de labels
        return hashlib.sha3_256(encoding_info).digest()[:32]

    async def encode_input(
        self,
        session_id: str,
        plaintext_input: bytes
    ) -> bytes:
        """
        Executa En(𝑒, 𝑥) → 𝐿𝑥.
        Simula encoding do input para o circuito garbled.
        """
        if session_id not in self._sessions:
            raise ValueError(f"Sessão {session_id} não encontrada")

        artifact = self._sessions[session_id]
        rng = np.random.RandomState(int(hashlib.sha3_256(plaintext_input).hexdigest()[:8], 16))

        # Simular: cada bit do input gera 16 bytes de label
        input_labels = rng.bytes(len(plaintext_input) * 8 * 16)

        return input_labels

    async def evaluate(
        self,
        session_id: str,
        garbled_input: bytes
    ) -> Tuple[bytes, bool]:
        """
        Executa Ev(𝐹, 𝐿𝑥) → 𝐿𝑦 e De(𝑑, 𝐿𝑦) → 𝑦.
        Retorna (output_label, is_valid).
        """
        if session_id not in self._sessions:
            raise ValueError(f"Sessão {session_id} não encontrada")

        artifact = self._sessions[session_id]

        # Simular avaliação: hash do input determina output
        eval_hash = hashlib.sha3_256(garbled_input).digest()

        # Determinar se a prova é válida baseado em heurística
        # Em produção: executar o GC real
        is_valid = (eval_hash[0] & 0x01) == 1  # 50% de chance para simulação

        if is_valid:
            # Output label que decodifica para True
            output_label = artifact.decoding_info[16:32]
        else:
            # Output label que decodifica para False
            output_label = artifact.false_output_label

        return output_label, is_valid

    def extract_proof_from_signature(
        self,
        session_id: str,
        gs_signature: bytes
    ) -> bytes:
        """
        Simula GS.Extract(pk, 𝜎) → 𝐿𝑥.
        Extrai o encoding do input a partir da assinatura GS.
        """
        if session_id not in self._sessions:
            raise ValueError(f"Sessão {session_id} não encontrada")

        # Em Lamport: a assinatura é exatamente os labels revelados
        return gs_signature

# ═══════════════════════════════════════════════════════════════
# TEMPORALCHAIN INTEGRATION
# ═══════════════════════════════════════════════════════════════

class TemporalChainAnchor:
    """Interface para ancoragem na TemporalChain (Substrato 9018)."""

    def __init__(self, endpoint: str = "http://localhost:9018"):
        self.endpoint = endpoint
        self._events: List[Dict] = []

    async def anchor_event(self, event_type: str, payload: Dict) -> str:
        """Ancora evento e retorna selo temporal."""
        event_data = {
            "event_type": event_type,
            "payload": payload,
            "timestamp": time.time(),
            "nonce": hashlib.sha3_256(str(time.time()).encode()).hexdigest()[:8]
        }
        seal = hashlib.sha3_256(
            json.dumps(event_data, sort_keys=True).encode()
        ).hexdigest()

        self._events.append({"seal": seal, "data": event_data})
        logger.info(f"🔐 Evento '{event_type}' ancorado (selo: {seal[:16]}...)")
        return seal

# ═══════════════════════════════════════════════════════════════
# BITVM3‑CORE SERVICE
# ═══════════════════════════════════════════════════════════════

class BitVM3CoreService:
    """
    Serviço de verificação BitVM3‑core para a Catedral.

    Implementa o protocolo completo:
    1. Setup: Prover gera GC do verificador SNARK + chave GS
    2. Assert: Prover publica assinatura GS com encoding da prova
    3. Challenge: Challenger avalia GC off‑chain
    4. Disprove: Se inválido, Challenger publica false‑output label
    5. Resolve: Se válido e timeout expira, prova é aceita

    Isomorfismo com o Tear (181):
        • Setup → Compulsão Bruta (intenção inicial)
        • GC Evaluation → Paridade (bifurcação da verificação)
        • Disprove → Espelho (feedback fecha o loop)
    """

    DEFAULT_TIMEOUT_BLOCKS = 144  # ~24 horas em Bitcoin

    def __init__(
        self,
        gc_engine: GarbledCircuitEngine = None,
        temporal_chain: TemporalChainAnchor = None,
        timeout_blocks: int = None
    ):
        self.gc = gc_engine or GarbledCircuitEngine()
        self.temporal = temporal_chain or TemporalChainAnchor()
        self.timeout_blocks = timeout_blocks or self.DEFAULT_TIMEOUT_BLOCKS

        self._asserts: Dict[str, AssertRecord] = {}
        self._disproves: Dict[str, DisproveRecord] = {}
        self._sessions: Dict[str, GarbledCircuitArtifact] = {}

    # ── FASE 1: SETUP ──
    async def setup(
        self,
        function_bytecode: bytes,
        input_size_bits: int,
        prover_id: str,
        statement_hash: str
    ) -> GarbledCircuitArtifact:
        """
        BitVM3‑core.Setup(1^𝜅, 𝑄) → (sid, 𝑆, aux).

        Gera o circuito garbled do verificador e prepara a transação Assert.
        """
        session_id = hashlib.sha3_256(
            f"{prover_id}:{statement_hash}:{time.time()}".encode()
        ).hexdigest()[:16]

        logger.info(f"🔧 BitVM3‑core SETUP: sessão {session_id}")

        # 1. Garblar a função de verificação
        artifact = await self.gc.garble_function(
            function_bytecode=function_bytecode,
            input_size_bits=input_size_bits,
            session_id=session_id
        )

        # 2. Construir Assert (template)
        # Assert.output[0] = Hashlock(H(𝐿*)) ∨ (RelTimelock(Δ) ∧ CheckSig_prover)
        assert_template = {
            "session_id": session_id,
            "prover_id": prover_id,
            "statement_hash": statement_hash,
            "gs_public_key": artifact.gs_public_key.hex(),
            "false_output_hash": hashlib.sha3_256(artifact.false_output_label).hexdigest(),
            "timeout_blocks": self.timeout_blocks,
            "circuit_hash": artifact.circuit_hash
        }

        # 3. Ancorar setup na TemporalChain
        assert_template["temporal_seal"] = await self.temporal.anchor_event(
            "bitvm3_setup_completed",
            assert_template
        )

        self._sessions[session_id] = artifact
        logger.info(f"✅ Setup concluído: circuito {artifact.circuit_hash[:16]}...")

        return artifact

    # ── FASE 2: ASSERT ──
    async def assert_proof(
        self,
        session_id: str,
        prover_id: str,
        proof_data: bytes
    ) -> AssertRecord:
        """
        BitVM3‑core.Execute: Prover publica Assert com assinatura GS.

        A assinatura GS revela o encoding da prova para o circuito garbled.
        """
        if session_id not in self._sessions:
            raise ValueError(f"Sessão {session_id} não encontrada")

        logger.info(f"📜 BitVM3‑core ASSERT: sessão {session_id}")

        # 1. Codificar a prova como input do GC
        garbled_input = await self.gc.encode_input(session_id, proof_data)

        # A assinatura GS É o garbled input (propriedade de extractability)
        gs_signature = garbled_input

        # 2. Criar registro Assert
        assert_id = hashlib.sha3_256(
            f"{session_id}:assert:{time.time()}".encode()
        ).hexdigest()[:16]

        record = AssertRecord(
            assert_id=assert_id,
            session_id=session_id,
            prover_id=prover_id,
            gs_signature=gs_signature,
            claimed_statement_hash=hashlib.sha3_256(proof_data).hexdigest()
        )

        # 3. Ancorar na TemporalChain
        record.temporal_seal = await self.temporal.anchor_event(
            "bitvm3_assert_posted",
            {
                "assert_id": assert_id,
                "session_id": session_id,
                "prover_id": prover_id,
                "gs_signature_hash": hashlib.sha3_256(gs_signature).hexdigest()[:16],
                "timestamp": record.timestamp
            }
        )

        self._asserts[assert_id] = record
        logger.info(f"✅ Assert publicado: {assert_id} (selo: {record.temporal_seal[:16]}...)")

        return record

    # ── FASE 3: CHALLENGE (OFF‑CHAIN) ──
    async def evaluate_offchain(
        self,
        session_id: str,
        assert_id: str
    ) -> Tuple[bytes, bool]:
        """
        Challenger avalia o GC off‑chain.

        Retorna (output_label, is_valid).
        """
        if session_id not in self._sessions:
            raise ValueError(f"Sessão {session_id} não encontrada")

        if assert_id not in self._asserts:
            raise ValueError(f"Assert {assert_id} não encontrado")

        record = self._asserts[assert_id]

        # Extrair encoding da prova a partir da assinatura GS
        garbled_input = self.gc.extract_proof_from_signature(
            session_id, record.gs_signature
        )

        # Avaliar circuito garbled
        output_label, is_valid = await self.gc.evaluate(session_id, garbled_input)

        logger.info(f"🔍 Avaliação off‑chain: válido={is_valid}")

        return output_label, is_valid

    # ── FASE 4: DISPROVE ──
    async def disprove(
        self,
        session_id: str,
        assert_id: str,
        challenger_id: str,
        false_output_label: bytes
    ) -> DisproveRecord:
        """
        Challenger publica Disprove com o false‑output label.

        Só é válido se o label corresponde ao hashlock do Assert.
        """
        if session_id not in self._sessions:
            raise ValueError(f"Sessão {session_id} não encontrada")

        artifact = self._sessions[session_id]

        # Verificar que o label submetido é realmente o false‑output label
        expected_hash = hashlib.sha3_256(artifact.false_output_label).hexdigest()
        submitted_hash = hashlib.sha3_256(false_output_label).hexdigest()

        if expected_hash != submitted_hash:
            raise ValueError("Label submetido não corresponde ao false‑output label")

        logger.info(f"⚡ BitVM3‑core DISPROVE: sessão {session_id}")

        # Criar registro Disprove
        disprove_id = hashlib.sha3_256(
            f"{assert_id}:disprove:{time.time()}".encode()
        ).hexdigest()[:16]

        record = DisproveRecord(
            disprove_id=disprove_id,
            assert_id=assert_id,
            challenger_id=challenger_id,
            false_output_label=false_output_label
        )

        # Ancorar na TemporalChain
        record.temporal_seal = await self.temporal.anchor_event(
            "bitvm3_disprove_posted",
            {
                "disprove_id": disprove_id,
                "assert_id": assert_id,
                "challenger_id": challenger_id,
                "label_hash": submitted_hash[:16],
                "timestamp": record.timestamp
            }
        )

        self._disproves[disprove_id] = record
        logger.info(f"✅ Disprove publicado: {disprove_id} (selo: {record.temporal_seal[:16]}...)")

        return record

    # ── FASE 5: RESOLVE ──
    def get_verification_status(self, session_id: str) -> VerificationStatus:
        """Retorna o status atual da verificação."""
        if session_id not in self._sessions:
            return VerificationStatus.EXPIRED

        # Verificar se há algum Assert para esta sessão
        session_asserts = [
            a for a in self._asserts.values() if a.session_id == session_id
        ]

        if not session_asserts:
            return VerificationStatus.SETUP

        latest_assert = session_asserts[-1]

        # Verificar se há Disprove para este Assert
        session_disproves = [
            d for d in self._disproves.values() if d.assert_id == latest_assert.assert_id
        ]

        if session_disproves:
            return VerificationStatus.CHALLENGED

        # Verificar timeout
        elapsed = time.time() - latest_assert.timestamp
        if elapsed > self.timeout_blocks * 600:  # ~10 min por bloco
            return VerificationStatus.RESOLVED

        return VerificationStatus.ASSERTED

# ═══════════════════════════════════════════════════════════════
# TESTES UNITÁRIOS
# ═══════════════════════════════════════════════════════════════

async def test_bitvm3_core():
    """Testa o BitVM3‑core Verification Service."""
    print("\n" + "="*70)
    print("TESTE: BitVM3‑core Verification Service — Substrato 198‑G")
    print("="*70)

    service = BitVM3CoreService()

    # Teste 1: Setup
    print("\n[Teste 1] Setup do circuito garbled")
    function_bytecode = b"SNARK_VERIFIER_BYTECODE"
    artifact = await service.setup(
        function_bytecode=function_bytecode,
        input_size_bits=128,
        prover_id="operator-01",
        statement_hash="0xabcdef1234567890"
    )
    print(f"  Circuito: {artifact.circuit_hash[:16]}...")
    assert artifact.garbled_circuit is not None
    assert artifact.false_output_label is not None
    print("  ✅ Setup concluído")

    # Teste 2: Assert com prova válida
    print("\n[Teste 2] Assert com prova válida")
    valid_proof = b"valid_proof_data_128_bits"
    assert_record = await service.assert_proof(
        session_id=artifact.session_id,
        prover_id="operator-01",
        proof_data=valid_proof
    )
    print(f"  Assert ID: {assert_record.assert_id}")
    assert assert_record.gs_signature is not None
    print("  ✅ Assert publicado")

    # Teste 3: Avaliação off‑chain
    print("\n[Teste 3] Avaliação off‑chain pelo Challenger")
    output_label, is_valid = await service.evaluate_offchain(
        session_id=artifact.session_id,
        assert_id=assert_record.assert_id
    )
    print(f"  Prova válida? {is_valid}")

    if not is_valid:
        # Teste 4: Disprove
        print("\n[Teste 4] Disprove (prova inválida)")
        disprove_record = await service.disprove(
            session_id=artifact.session_id,
            assert_id=assert_record.assert_id,
            challenger_id="challenger-01",
            false_output_label=output_label
        )
        print(f"  Disprove ID: {disprove_record.disprove_id}")
        assert disprove_record.false_output_label is not None
        print("  ✅ Disprove publicado")

    # Teste 5: Status
    print("\n[Teste 5] Status da verificação")
    status = service.get_verification_status(artifact.session_id)
    print(f"  Status: {status.value}")
    assert status in [VerificationStatus.ASSERTED, VerificationStatus.CHALLENGED]
    print("  ✅ Status verificado")

    print("\n" + "="*70)
    print("✅ TODOS OS TESTES PASSARAM")
    print("="*70)

if __name__ == "__main__":
    asyncio.run(test_bitvm3_core())
