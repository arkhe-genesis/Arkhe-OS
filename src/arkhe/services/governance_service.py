# src/arkhe/services/governance_service.py
"""
Substrato 189 — Governance Service (qhttp://)
Serviço distribuído que expõe o kernel de governança via protocolo qhttp://.
Roda em múltiplos nós da Wheeler Mesh e audita decisões de qualquer origem.
"""
import hashlib, json, time, threading
from typing import Dict, Optional
from dataclasses import asdict
from arkhe.kernel.ping_governance_v2 import (
    PingGovernanceKernelV2, CounterArgument, GovernanceDecision, PingAuditResult
)
from arkhe.layers.unix_substrate import WheelerNode, SATOFrame, MeshRouter
from arkhe.layers.auth_orcid import OrcidAuthProvider
from arkhe.layers.constraints import TemporalChainClient

class GovernanceService:
    """
    Serviço de governança não‑local.

    Escuta requisições de auditoria via qhttp:// e responde com
    PingAuditResult assinado e ancorado na TemporalChain.

    Sincroniza o registro de auditorias entre nós via CRDT.
    """

    def __init__(self, node_id: str, mesh: MeshRouter,
                 temporal: TemporalChainClient,
                 auth: OrcidAuthProvider,
                 port: int = 9004):
        self.node_id = node_id
        self.mesh = mesh
        self.temporal = temporal
        self.auth = auth
        self.port = port

        # Kernel de governança (uma instância por nó)
        self.kernel = PingGovernanceKernelV2()

        # Registro local de auditorias (sincronizado via CRDT)
        self.audit_log: Dict[str, PingAuditResult] = {}
        self._lock = threading.RLock()

        # Fila de requisições recebidas
        self.inbox: list = []
        self._running = False
        self._thread = None

    def start(self):
        """Inicia o serviço de governança."""
        self._running = True
        self._thread = threading.Thread(target=self._event_loop, daemon=True)
        self._thread.start()
        print(f"🛡️ Governance Service iniciado em {self.node_id}:{self.port}")

    def _event_loop(self):
        """Loop principal: processa requisições do inbox."""
        while self._running:
            # Processar frames recebidos (simulação — em produção, callback do mesh)
            while self.inbox:
                frame = self.inbox.pop(0)
                self._handle_request(frame)
            time.sleep(0.1)

    def receive_frame(self, frame: SATOFrame):
        """Recebe frame do mesh e enfileira para processamento."""
        self.inbox.append(frame)

    def _handle_request(self, frame: SATOFrame):
        """Processa uma requisição de auditoria."""
        try:
            data = json.loads(frame.payload)

            if data.get("type") == "governance_audit":
                response = self._audit_decision(data)
                self._send_response(frame.source_node, response)

            elif data.get("type") == "governance_sync":
                self._handle_sync(data)

        except Exception as e:
            self._send_error(frame.source_node, str(e))

    def _audit_decision(self, data: dict) -> dict:
        """Executa auditoria de governança."""
        # Verificar autenticação do autor
        author_orcid = data.get("author_orcid", "anonymous")
        auth_token = data.get("auth_token", "")
        identity = self.auth.get_identity(auth_token)
        if identity:
            author_orcid = identity.orcid

        # Construir contra‑argumentos
        counters = [
            CounterArgument(**c) for c in data.get("counter_evidence", [])
        ]

        # Executar auditoria
        result = self.kernel.audit_decision(
            decision_id=data["decision_id"],
            decision_description=data["decision_description"],
            initial_confidence=data["initial_confidence"],
            supporting_evidence=data.get("supporting_evidence", []),
            counter_evidence=counters,
            risk_score=data["risk_score"],
            author_orcid=author_orcid,
            num_monte_carlo=data.get("num_monte_carlo", 100),
        )

        # Ancorar na TemporalChain
        anchor = self.temporal.anchor_content(
            content_hash=result.seal,
            metadata={
                "type": "governance_audit",
                "decision_id": result.decision_id,
                "final_decision": result.final_decision.name,
                "phi_c_after": result.phi_c_after,
                "author_orcid": author_orcid,
            }
        )

        # Registrar localmente e propagar via CRDT
        with self._lock:
            self.audit_log[result.decision_id] = result

        # Construir resposta
        response = {
            "type": "governance_audit_response",
            "decision_id": result.decision_id,
            "final_decision": result.final_decision.name,
            "confidence_after_reconstruction": result.confidence_after_reconstruction,
            "phi_c_before": result.phi_c_before,
            "phi_c_after": result.phi_c_after,
            "initial_pi": result.initial_pi,
            "final_pi": result.final_pi,
            "monte_carlo_robustness": result.monte_carlo_robustness,
            "conditions": result.conditions,
            "constitutional_warnings": result.constitutional_warnings,
            "seal": result.seal,
            "temporal_anchor": anchor,
            "node_id": self.node_id,
        }
        return response

    def _send_response(self, dest: str, data: dict):
        """Envia resposta via mesh."""
        frame = SATOFrame(
            payload=json.dumps(data).encode(),
            dest=dest
        )
        self.mesh.route(frame, self.node_id)

    def _send_error(self, dest: str, error: str):
        """Envia erro via mesh."""
        frame = SATOFrame(
            payload=json.dumps({"type": "governance_error", "error": error}).encode(),
            dest=dest
        )
        self.mesh.route(frame, self.node_id)

    def _handle_sync(self, data: dict):
        """Recebe sincronização CRDT de outro nó."""
        remote_audits = data.get("audits", {})
        with self._lock:
            for decision_id, audit_data in remote_audits.items():
                if decision_id not in self.audit_log:
                    # Reconstruir PingAuditResult do dict
                    self.audit_log[decision_id] = PingAuditResult(**audit_data)

    def get_audit(self, decision_id: str) -> Optional[dict]:
        """Retorna auditoria local pelo ID."""
        with self._lock:
            result = self.audit_log.get(decision_id)
            return asdict(result) if result else None

    def broadcast_audit_log(self):
        """Propaga o registro de auditorias para todos os pares."""
        with self._lock:
            sync_data = {
                "type": "governance_sync",
                "audits": {k: asdict(v) for k, v in self.audit_log.items()},
                "node_id": self.node_id,
                "timestamp": time.time(),
            }
        # Enviar para todos os pares conhecidos
        for peer in self.mesh.get_peers():
            frame = SATOFrame(payload=json.dumps(sync_data).encode(), dest=peer)
            self.mesh.route(frame, self.node_id)

    def get_stats(self) -> dict:
        """Retorna estatísticas do serviço de governança."""
        kernel_stats = self.kernel.get_governance_stats()
        with self._lock:
            kernel_stats["local_audits"] = len(self.audit_log)
        kernel_stats["node_id"] = self.node_id
        return kernel_stats