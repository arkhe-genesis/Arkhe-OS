from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum, auto
import hashlib
import json
from datetime import datetime
from pathlib import Path

# Assume LFIRGraph is imported from the other module
from arkhe_os.starter.shared.lfir_parser import LFIRGraph

class Jurisdiction(Enum):
    BCB = "BCB"      # Banco Central do Brasil
    ECB = "ECB"      # European Central Bank
    FED = "FED"      # US Federal Reserve
    GDPR = "GDPR"    # EU General Data Protection Regulation
    LGPD = "LGPD"    # Brazilian General Data Protection Law
    PSD2 = "PSD2"    # EU Payment Services Directive 2

class VerificationStatus(Enum):
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIAL = "partial"
    UNVERIFIED = "unverified"

@dataclass
class CompliancePredicate:
    """Predicado regulatório em formato UCS."""
    predicate_id: str
    name: str
    description: str
    jurisdictions: List[Jurisdiction]
    ucs_expression: str  # Expressão UCS formal
    zinc_circuit_path: Optional[str] = None  # Caminho para circuito Zinc+
    parameters: Dict[str, Any] = field(default_factory=dict)

    def to_ucs_dict(self) -> Dict:
        """Converte para dicionário UCS para compilação."""
        return {
            "id": self.predicate_id,
            "name": self.name,
            "expression": self.ucs_expression,
            "parameters": self.parameters,
            "jurisdictions": [j.value for j in self.jurisdictions]
        }

@dataclass
class ComplianceVerificationResult:
    """Resultado de verificação de compliance."""
    verification_id: str
    artifact_id: str  # ID do artefato verificado (ex: hash do código)
    predicates_checked: List[str]
    jurisdiction_results: Dict[Jurisdiction, VerificationStatus]
    zk_proof_hash: Optional[str] = None  # Hash do proof ZK se gerado
    coherence_score: float = 0.0  # Φ_C calculado para o artefato
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict = field(default_factory=dict)

    @property
    def is_fully_compliant(self) -> bool:
        """Verifica se artefato é compliant em todas as jurisdições."""
        return all(
            status == VerificationStatus.COMPLIANT
            for status in self.jurisdiction_results.values()
        )

    def to_regulatory_report(self) -> Dict:
        """Gera relatório estruturado para auditoria regulatória."""
        return {
            "verification_id": self.verification_id,
            "artifact_id": self.artifact_id,
            "compliance_status": "FULLY_COMPLIANT" if self.is_fully_compliant else "NON_COMPLIANT",
            "jurisdiction_results": {
                j.value: status.value
                for j, status in self.jurisdiction_results.items()
            },
            "coherence_score": round(self.coherence_score, 4),
            "zk_proof_reference": self.zk_proof_hash,
            "predicates_verified": self.predicates_checked,
            "audit_timestamp": self.timestamp,
            "metadata": self.metadata
        }

class ZincPlusProver:
    """Interface simplificada para prover Zinc+."""

    def __init__(self, zinc_plus_path: str = "./zinc-plus-bin"):
        self.zinc_plus_path = Path(zinc_plus_path)

    def generate_proof(self, circuit_path: str, witness: Dict, public_inputs: Dict) -> str:
        """
        Gera proof ZK para circuito Zinc+.

        Returns:
            Hash do proof gerado (para referência em auditoria)
        """
        # Em produção: chamar binary Zinc+ com circuit + witness + public inputs
        # Aqui: simular proof hash baseado em inputs
        proof_input = json.dumps({
            "circuit": circuit_path,
            "witness_hash": hashlib.sha256(json.dumps(witness).encode()).hexdigest(),
            "public_inputs_hash": hashlib.sha256(json.dumps(public_inputs).encode()).hexdigest()
        }, sort_keys=True)
        return hashlib.sha256(proof_input.encode()).hexdigest()[:16]

    def verify_proof(self, proof_hash: str, circuit_path: str, public_inputs: Dict) -> bool:
        """Verifica proof ZK (simulado)."""
        # Em produção: chamar verificador Zinc+
        # Aqui: verificar consistência do hash
        expected = hashlib.sha256(
            json.dumps({
                "circuit": circuit_path,
                "public_inputs_hash": hashlib.sha256(json.dumps(public_inputs).encode()).hexdigest()
            }, sort_keys=True).encode()
        ).hexdigest()[:16]
        return proof_hash == expected

class ComplianceValidator:
    """Validador principal de compliance com integração Zinc+."""

    def __init__(self, zinc_prover: Optional[ZincPlusProver] = None):
        self.zinc_prover = zinc_prover or ZincPlusProver()
        self.predicate_registry: Dict[str, CompliancePredicate] = {}
        self.verification_history: List[ComplianceVerificationResult] = []

    def register_predicate(self, predicate: CompliancePredicate):
        """Registra predicado UCS no validador."""
        self.predicate_registry[predicate.predicate_id] = predicate

    def load_predicates_from_file(self, file_path: str):
        """Carrega predicados de arquivo .ucspred (formato UCS)."""
        with open(file_path, 'r', encoding='utf-8') as f:
            predicates_data = json.load(f)
        for pred_data in predicates_data:
            predicate = CompliancePredicate(
                predicate_id=pred_data["id"],
                name=pred_data["name"],
                description=pred_data.get("description", ""),
                jurisdictions=[Jurisdiction(j) for j in pred_data["jurisdictions"]],
                ucs_expression=pred_data["expression"],
                zinc_circuit_path=pred_data.get("zinc_circuit"),
                parameters=pred_data.get("parameters", {})
            )
            self.register_predicate(predicate)

    def verify_artifact(
        self,
        artifact_id: str,
        lfir_graph: LFIRGraph,
        predicates_to_check: Optional[List[str]] = None,
        jurisdictions: Optional[List[Jurisdiction]] = None,
        generate_zk_proof: bool = True
    ) -> ComplianceVerificationResult:
        """
        Verifica compliance de artefato contra predicados UCS.

        Args:
            artifact_id: Identificador único do artefato (ex: hash do código)
            lfir_graph: Grafo LFIR do artefato parseado
            predicates_to_check: Lista de IDs de predicados a verificar (None = todos)
            jurisdictions: Lista de jurisdições a verificar (None = todas)
            generate_zk_proof: Se deve gerar proof ZK via Zinc+

        Returns:
            ComplianceVerificationResult com resultados da verificação
        """
        # Selecionar predicados a verificar
        if predicates_to_check is None:
            predicates_to_check = list(self.predicate_registry.keys())
        if jurisdictions is None:
            jurisdictions = list(Jurisdiction)

        # Avaliar cada predicado por jurisdição
        jurisdiction_results = {}
        zk_circuits_used = []

        for pred_id in predicates_to_check:
            if pred_id not in self.predicate_registry:
                continue
            predicate = self.predicate_registry[pred_id]

            # Filtrar por jurisdições relevantes
            relevant_jurisdictions = [j for j in jurisdictions if j in predicate.jurisdictions]
            if not relevant_jurisdictions:
                continue

            # Avaliar predicado (simulado - em produção: compilar UCS → avaliar)
            evaluation_result = self._evaluate_predicate(predicate, lfir_graph, relevant_jurisdictions)

            # Atualizar resultados por jurisdição
            for jur in relevant_jurisdictions:
                status = evaluation_result.get(jur, VerificationStatus.UNVERIFIED)
                jurisdiction_results[jur] = status

            # Coletar circuitos Zinc+ se proof for solicitado
            if generate_zk_proof and predicate.zinc_circuit_path:
                zk_circuits_used.append(predicate.zinc_circuit_path)

        # Gerar proof ZK agregado se solicitado
        zk_proof_hash = None
        if generate_zk_proof and zk_circuits_used:
            # Preparar witness e public inputs para proof agregado
            witness = {
                "artifact_lfir": lfir_graph.to_dict(),
                "predicate_evaluations": {
                    pred_id: {
                        j.value: jurisdiction_results[j].value
                        for j in jurisdiction_results
                    }
                    for pred_id in predicates_to_check
                }
            }
            public_inputs = {
                "artifact_id": artifact_id,
                "jurisdictions": [j.value for j in jurisdictions],
                "coherence_score": lfir_graph.global_coherence
            }
            # Usar primeiro circuito como proxy (em produção: circuito agregado)
            zk_proof_hash = self.zinc_prover.generate_proof(
                zk_circuits_used[0], witness, public_inputs
            )

        # Calcular coerência final do artefato
        coherence_score = lfir_graph.compute_global_coherence()

        # Criar resultado
        result = ComplianceVerificationResult(
            verification_id=hashlib.sha256(
                f"{artifact_id}:{datetime.now().isoformat()}".encode()
            ).hexdigest()[:16],
            artifact_id=artifact_id,
            predicates_checked=predicates_to_check,
            jurisdiction_results=jurisdiction_results,
            zk_proof_hash=zk_proof_hash,
            coherence_score=coherence_score,
            metadata={
                "lfir_node_count": len(lfir_graph.nodes),
                "lfir_edge_count": len(lfir_graph.edges),
                "predicates_available": len(self.predicate_registry)
            }
        )

        # Registrar no histórico
        self.verification_history.append(result)

        return result

    def _evaluate_predicate(
        self,
        predicate: CompliancePredicate,
        lfir_graph: LFIRGraph,
        jurisdictions: List[Jurisdiction]
    ) -> Dict[Jurisdiction, VerificationStatus]:
        """
        Avalia predicado contra grafo LFIR (simulado).

        Em produção: compilar expressão UCS → avaliar contra nós/arestas do LFIR.
        """
        results = {}
        for jur in jurisdictions:
            # Simular avaliação baseada em tags regulatórias nos nós
            matching_nodes = [
                node for node in lfir_graph.nodes.values()
                if jur.value in node.regulatory_tags
            ]
            if matching_nodes:
                # Se há nós com tag da jurisdição, considerar compliant (simplificado)
                results[jur] = VerificationStatus.COMPLIANT
            else:
                # Caso contrário, verificar se predicado é aplicável
                if predicate.parameters.get("optional_for_" + jur.value, False):
                    results[jur] = VerificationStatus.PARTIAL
                else:
                    results[jur] = VerificationStatus.NON_COMPLIANT
        return results

    def generate_audit_report(self, verification_result: ComplianceVerificationResult) -> Dict:
        """Gera relatório de auditoria para submissão regulatória."""
        report = verification_result.to_regulatory_report()
        # Adicionar metadata de auditoria
        report["audit_metadata"] = {
            "validator_version": "300-B.1.0",
            "zinc_plus_version": "1.0.0-beta",
            "ucs_schema_version": "2.1",
            "canonical_seal": hashlib.sha256(
                json.dumps(report, sort_keys=True).encode()
            ).hexdigest()[:16]
        }
        return report
