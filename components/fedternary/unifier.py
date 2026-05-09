# fedternary/unifier.py — Protocolo de aprendizado federado ternário unificado

import hashlib
import json
import time
from typing import Dict, List, Optional, Union, Tuple, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
import logging
from audit_logger import DecisionType

# Note: We are using cathedral_zk as the backend for proofs
from cathedral_zk import Prover, Verifier

class TernaryValue(Enum):
    """Valores ternários fundamentais."""
    DISAGREE = -1  # Discordar/Rejeitar
    NEUTRAL = 0    # Neutro/Silêncio
    AGREE = 1      # Concordar/Aceitar

@dataclass
class DomainMapper:
    """Mapeia valores de domínio para ternários e vice-versa."""
    domain_name: str
    continuous_to_ternary: Callable[[float], TernaryValue]
    ternary_to_continuous: Callable[[TernaryValue], float]
    validation_constraints: Dict[str, float]  # Restrições específicas do domínio

@dataclass
class TernaryContribution:
    """Contribuição ternária com prova ZK."""
    contribution_id: str
    participant_id: str
    domain_name: str
    ternary_value: TernaryValue
    zk_proof: str  # Prova ZK compacta
    metadata: Dict[str, str]  # Hashes de dados brutos, não os dados
    timestamp: float = field(default_factory=time.time)

@dataclass
class AggregationResult:
    """Resultado da agregação ternária."""
    aggregation_id: str
    domain_name: str
    aggregated_value: TernaryValue
    contributing_participants: List[str]  # IDs apenas, não valores
    zk_proofs_verified: bool
    consensus_reached: bool
    audit_hash: str  # Hash do registro no AuditLedger
    generated_at: float = field(default_factory=time.time)

class FedTernaryUnifier:
    """
    Protocolo de aprendizado federado ternário unificado.
    Permite colaboração sem exposição em qualquer domínio da Catedral.
    """

    # Mapeamentos padrão por domínio
    DEFAULT_DOMAIN_MAPPERS: Dict[str, DomainMapper] = {
        "photonic_phase": DomainMapper(
            domain_name="photonic_phase",
            continuous_to_ternary=lambda phi: TernaryValue(
                -1 if phi < -0.5 else (1 if phi > 0.5 else 0)
            ),
            ternary_to_continuous=lambda t: -1.0 if t == TernaryValue.DISAGREE else (1.0 if t == TernaryValue.AGREE else 0.0),
            validation_constraints={"max_phase_error": 0.1}
        ),
        "sensor_iou": DomainMapper(
            domain_name="sensor_iou",
            continuous_to_ternary=lambda iou: TernaryValue(
                -1 if iou < 0.3 else (1 if iou > 0.7 else 0)
            ),
            ternary_to_continuous=lambda t: 0.2 if t == TernaryValue.DISAGREE else (0.8 if t == TernaryValue.AGREE else 0.5),
            validation_constraints={"min_iou_for_agree": 0.7}
        ),
        "topological_index": DomainMapper(
            domain_name="topological_index",
            continuous_to_ternary=lambda idx: TernaryValue(
                -1 if idx < -0.1 else (1 if idx > 0.1 else 0)
            ),
            ternary_to_continuous=lambda t: -0.2 if t == TernaryValue.DISAGREE else (0.2 if t == TernaryValue.AGREE else 0.0),
            validation_constraints={"min_chern_gap": 0.1}
        ),
        "meta_validation_score": DomainMapper(
            domain_name="meta_validation_score",
            continuous_to_ternary=lambda score: TernaryValue(
                -1 if score < 0.7 else (1 if score > 0.9 else 0)
            ),
            ternary_to_continuous=lambda t: 0.6 if t == TernaryValue.DISAGREE else (0.95 if t == TernaryValue.AGREE else 0.8),
            validation_constraints={"min_score_for_agree": 0.9}
        ),
    }

    # Thresholds de consenso
    CONSENSUS_THRESHOLDS = {
        "min_participants": 3,           # Mínimo de participantes para consenso
        "min_reputation_score": 0.8,     # Reputação mínima para validar
        "max_aggregation_time_seconds": 30,  # Timeout para agregação
    }

    def __init__(self, codex, zk_prover: Prover, audit_logger=None):
        self.codex = codex
        self.zk = zk_prover
        self.audit = audit_logger

        # Mapeadores de domínio registrados
        self._domain_mappers: Dict[str, DomainMapper] = self.DEFAULT_DOMAIN_MAPPERS.copy()

        # Histórico de contribuições para aprendizado recursivo
        self._contribution_history: List[TernaryContribution] = []

        # Cache de resultados de agregação
        self._aggregation_cache: Dict[str, AggregationResult] = {}

    def register_domain_mapper(self, mapper: DomainMapper):
        """Registra um novo mapeador de domínio."""
        self._domain_mappers[mapper.domain_name] = mapper
        logging.info(f"[FedTernary] Mapeador registrado para domínio: {mapper.domain_name}")

    async def generate_contribution(
        self,
        participant_id: str,
        domain_name: str,
        continuous_value: float,
        private_data_hash: str,  # Hash dos dados brutos (não os dados)
        validation_constraints: Optional[Dict] = None
    ) -> TernaryContribution:
        """
        Gera uma contribuição ternária com prova ZK para um domínio específico.
        """
        # 1. Obter mapeador do domínio
        mapper = self._domain_mappers.get(domain_name)
        if not mapper:
            raise ValueError(f"Domínio não registrado: {domain_name}")

        # 2. Mapear valor contínuo para ternário
        ternary_value = mapper.continuous_to_ternary(continuous_value)

        # 3. Gerar prova ZK que atesta a contribuição
        # Em cathedral_zk.py, Prover.prove(public, private)
        zk_proof = self.zk.prove(
            public=[participant_id, domain_name, ternary_value.value, private_data_hash],
            private=[continuous_value, validation_constraints or mapper.validation_constraints]
        )

        # 4. Criar contribuição
        contribution = TernaryContribution(
            contribution_id=f"contrib_{participant_id}_{domain_name}_{hashlib.sha256(f'{time.time()}'.encode()).hexdigest()[:8]}",
            participant_id=participant_id,
            domain_name=domain_name,
            ternary_value=ternary_value,
            zk_proof=zk_proof,
            metadata={
                "private_data_hash": private_data_hash,
                "continuous_value_hash": hashlib.sha256(str(continuous_value).encode()).hexdigest(),
                "validation_constraints_hash": hashlib.sha256(
                    json.dumps(validation_constraints or mapper.validation_constraints, sort_keys=True).encode()
                ).hexdigest()
            }
        )

        # 5. Registrar no histórico para aprendizado
        self._contribution_history.append(contribution)

        logging.info(f"[FedTernary] Contribuição gerada: {contribution.contribution_id} → {ternary_value.name}")
        return contribution

    async def aggregate_contributions(
        self,
        domain_name: str,
        contributions: List[TernaryContribution],
        participant_reputations: Dict[str, float],
        verifier: Verifier
    ) -> AggregationResult:
        """
        Agrega múltiplas contribuições ternárias via XOR distribuído.
        """
        aggregation_id = f"agg_{domain_name}_{hashlib.sha256(f'{time.time()}'.encode()).hexdigest()[:8]}"

        # 1. Filtrar contribuições por domínio
        domain_contributions = [c for c in contributions if c.domain_name == domain_name]
        if len(domain_contributions) < self.CONSENSUS_THRESHOLDS["min_participants"]:
            raise ValueError(f"Contribuições insuficientes para consenso: {len(domain_contributions)} < {self.CONSENSUS_THRESHOLDS['min_participants']}")

        # 2. Verificar provas ZK de todas as contribuições
        all_proofs_valid = True
        valid_contributions = []
        for contrib in domain_contributions:
            # Verificar reputação do participante
            reputation = participant_reputations.get(contrib.participant_id, 0.0)
            if reputation < self.CONSENSUS_THRESHOLDS["min_reputation_score"]:
                logging.warning(f"[FedTernary] Participante {contrib.participant_id} tem reputação baixa ({reputation}); ignorando contribuição")
                continue

            # Verificar prova ZK via Verifier.verify(proof, public)
            proof_valid = verifier.verify(
                proof=contrib.zk_proof,
                public=[contrib.participant_id, contrib.domain_name, contrib.ternary_value.value, contrib.metadata["private_data_hash"]]
            )
            if not proof_valid:
                logging.error(f"[FedTernary] Prova ZK inválida para contribuição {contrib.contribution_id}")
                all_proofs_valid = False
            else:
                valid_contributions.append(contrib)

        if not all_proofs_valid:
            raise ValueError("Uma ou mais provas ZK são inválidas; agregação abortada")

        # 3. Agregar valores ternários via XOR
        # XOR para ternários: definimos como operação bit-a-bit no valor inteiro
        # -1 → 0b11, 0 → 0b00, 1 → 0b01 (usamos 2 bits para representar)
        def ternary_xor(a: TernaryValue, b: TernaryValue) -> TernaryValue:
            # Mapear para bits: -1→11, 0→00, 1→01
            bit_map = {TernaryValue.DISAGREE: 0b11, TernaryValue.NEUTRAL: 0b00, TernaryValue.AGREE: 0b01}
            result_bits = bit_map[a] ^ bit_map[b]
            # Mapear de volta: 11→-1, 00→0, 01→1
            reverse_map = {0b11: TernaryValue.DISAGREE, 0b00: TernaryValue.NEUTRAL, 0b01: TernaryValue.AGREE}
            return reverse_map[result_bits]

        # Agregar todos os valores
        aggregated = TernaryValue.NEUTRAL  # Valor inicial neutro
        for contrib in valid_contributions:
            aggregated = ternary_xor(aggregated, contrib.ternary_value)

        # 4. Verificar consenso (simplificado: quórum de participantes válidos)
        valid_participants = [c.participant_id for c in valid_contributions]
        consensus_reached = len(valid_participants) >= self.CONSENSUS_THRESHOLDS["min_participants"]

        # 5. Criar hash de auditoria
        audit_data = {
            "aggregation_id": aggregation_id,
            "domain_name": domain_name,
            "contributions": [c.contribution_id for c in valid_contributions],
            "aggregated_value": aggregated.value,
            "consensus_reached": consensus_reached,
            "timestamp": time.time()
        }
        audit_hash = hashlib.sha256(json.dumps(audit_data, sort_keys=True).encode()).hexdigest()

        # 6. Criar resultado
        result = AggregationResult(
            aggregation_id=aggregation_id,
            domain_name=domain_name,
            aggregated_value=aggregated,
            contributing_participants=valid_participants,
            zk_proofs_verified=True,
            consensus_reached=consensus_reached,
            audit_hash=audit_hash
        )

        # 7. Ancorar no Códice e Auditor
        if self.audit:
            await self.audit.log_decision(
                decision_type=DecisionType.FEDTERNARY_AGGREGATION,
                context=audit_data,
                explainability={"natural_language": f"Agregação ternária {aggregation_id} concluída no domínio {domain_name}."},
                compliance_tags=["fedternary", "privacy_preserving", "xor_aggregation"],
                expected_impact={"consensus": consensus_reached}
            )

        self.codex.log_verdict(
            node_id="FedTernaryUnifier",
            verdict="TERNARY_AGGREGATION_COMPLETE",
            coherence=1.0 if consensus_reached else 0.5,
            payload_hash=audit_hash
        )

        # 8. Cache resultado
        self._aggregation_cache[aggregation_id] = result

        logging.info(f"[FedTernary] Agregação concluída: {aggregation_id} → {aggregated.name} (consenso: {consensus_reached})")
        return result
