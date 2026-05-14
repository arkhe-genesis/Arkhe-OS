# src/arkhe/network/asi_connection_protocol.py
"""
Substrato 9005 — ASI Connection Protocol
Handshake quântico para estabelecimento de conexão segura entre nós ASI.
Requer: autenticação ORCID, auditoria de governança (ping), coerência Φ_C mínima.
"""
import hashlib, json, time, uuid
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

class SATOFrame:
    def __init__(self, payload, dest):
        self.payload = payload
        self.dest = dest

class MeshRouter:
    def route(self, frame, local_node_id):
        pass

class OrcidAuthProvider:
    def __init__(self):
        self.identities = {}
    def register(self, orcid, secret):
        self.identities[orcid] = Identity(orcid, secret)
    def get_identity(self, orcid):
        return self.identities.get(orcid)

class Identity:
    def __init__(self, orcid, secret):
        self.orcid = orcid
        self.secret = secret
    def public_commitment(self):
        return "mock_commitment"

class PingGovernanceKernelV2:
    def audit_decision(self, *args, **kwargs):
        class DecisionResult:
            def __init__(self):
                self.final_decision = type('Enum', (), {'name': 'ACCEPT'})()
                self.seal = "mock_seal"
        return DecisionResult()

class CounterArgument:
    def __init__(self, arg, risk, cat, source):
        pass

class TemporalChainClient:
    def anchor_content(self, *args, **kwargs):
        pass

class FisherBuresManifold:
    def __init__(self, dim):
        self.dim = dim

class ASIConnectionState(Enum):
    DISCOVERED = "discovered"
    HANDSHAKE_SENT = "handshake_sent"
    CHALLENGED = "challenged"
    AUDIT_PENDING = "audit_pending"
    CONNECTED = "connected"
    REJECTED = "rejected"

@dataclass
class ASINodeIdentity:
    node_id: str
    orcid: str
    phi_c: float
    pi: float
    public_commitment: str
    last_seen: float = 0.0

class ASIConnectionProtocol:
    """
    Protocolo de conexão entre nós ASI.
    """

    def __init__(self,
                 local_node_id: str,
                 local_orcid: str,
                 mesh,
                 auth,
                 governance,
                 temporal,
                 min_phi_c: float = 0.98,
                 max_pi: float = 0.05):
        self.local_node_id = local_node_id
        self.local_orcid = local_orcid
        self.mesh = mesh
        self.auth = auth
        self.governance = governance
        self.temporal = temporal
        self.min_phi_c = min_phi_c
        self.max_pi = max_pi

        self.known_nodes: Dict[str, ASINodeIdentity] = {}
        self.active_connections: Dict[str, ASIConnectionState] = {}
        self.manifold = FisherBuresManifold(4)  # Para métricas de coerência

    def discover_nodes(self):
        """Envia um beacon de descoberta ASI para todos os pares no mesh."""
        identity = self.auth.get_identity(self.local_orcid)
        if not identity:
            raise ValueError("Identidade local não autenticada")

        # Obter métricas atuais do nó local
        local_phi_c = self._get_local_phi_c()
        local_pi = self._get_local_pi()

        beacon = {
            "type": "asi_discovery",
            "node_id": self.local_node_id,
            "orcid": self.local_orcid,
            "phi_c": local_phi_c,
            "pi": local_pi,
            "public_commitment": identity.public_commitment(),
            "timestamp": time.time_ns()
        }

        frame = SATOFrame(payload=json.dumps(beacon).encode(), dest="all")
        self.mesh.route(frame, self.local_node_id)

        # Também processa nós já conhecidos
        for node_id, node in list(self.known_nodes.items()):
            if time.time() - node.last_seen > 30.0:
                del self.known_nodes[node_id]

        print(f"📡 Beacon ASI enviado: Φ_C={local_phi_c:.4f}, π={local_pi:.4f}")

    def handle_discovery(self, frame):
        """Processa um beacon de descoberta de outro nó ASI."""
        data = json.loads(frame.payload)
        node_id = data["node_id"]

        # Ignorar self
        if node_id == self.local_node_id:
            return

        # Verificar métricas mínimas
        if data["phi_c"] < self.min_phi_c or data["pi"] > self.max_pi:
            print(f"⛔ Nó {node_id[:8]} rejeitado: Φ_C={data['phi_c']:.4f}, π={data['pi']:.4f}")
            return

        # Verificar assinatura ORCID (simplificada: verificar se o commitment bate)
        # Em produção: verificar assinatura completa
        identity = self.auth.identities.get(data["orcid"])
        if identity and identity.public_commitment() != data["public_commitment"]:
            print(f"⚠️  Compromisso público inválido para {node_id[:8]}")
            return

        # Registrar nó conhecido
        self.known_nodes[node_id] = ASINodeIdentity(
            node_id=node_id,
            orcid=data["orcid"],
            phi_c=data["phi_c"],
            pi=data["pi"],
            public_commitment=data["public_commitment"],
            last_seen=time.time()
        )

        print(f"🔍 Nó ASI descoberto: {node_id[:8]} (Φ_C={data['phi_c']:.4f})")

        # Iniciar handshake se ainda não estiver conectado
        if node_id not in self.active_connections:
            self.initiate_handshake(node_id)

    def initiate_handshake(self, target_node_id: str):
        """Inicia handshake com um nó ASI."""
        target = self.known_nodes.get(target_node_id)
        if not target:
            return

        identity = self.auth.get_identity(self.local_orcid)
        local_phi_c = self._get_local_phi_c()
        local_pi = self._get_local_pi()

        handshake = {
            "type": "asi_handshake",
            "source_node": self.local_node_id,
            "target_node": target_node_id,
            "orcid": self.local_orcid,
            "phi_c": local_phi_c,
            "pi": local_pi,
            "challenge": hashlib.sha3_256(f"{self.local_node_id}{target_node_id}{time.time_ns()}".encode()).hexdigest()[:16],
            "timestamp": time.time_ns()
        }

        frame = SATOFrame(payload=json.dumps(handshake).encode(), dest=target_node_id)
        self.mesh.route(frame, self.local_node_id)
        self.active_connections[target_node_id] = ASIConnectionState.HANDSHAKE_SENT

    def handle_handshake(self, frame):
        """Recebe handshake de outro nó e decide se aceita."""
        data = json.loads(frame.payload)
        source_id = data["source_node"]

        # Verificar se o nó fonte é conhecido
        if source_id not in self.known_nodes:
            print(f"⛔ Handshake de nó desconhecido {source_id[:8]}")
            return

        # Verificar métricas mínimas
        if data["phi_c"] < self.min_phi_c or data["pi"] > self.max_pi:
            self._send_rejection(source_id, "Métricas insuficientes")
            return

        # ── Auditoria de governança da decisão de conectar ──
        # Trata a conexão como uma decisão de alto risco (risk=0.8)
        audit_result = self._audit_connection_decision(source_id, data)

        if audit_result.final_decision.name in ["REJECT", "ESCALATE"]:
            self._send_rejection(source_id, f"Governança: {audit_result.final_decision.name}")
            return

        # ── Responder com challenge resolvido ──
        challenge = hashlib.sha3_256(
            f"{data.get('challenge', 'mock_challenge')}{self.local_node_id}asi-salt".encode()
        ).hexdigest()[:16]

        response = {
            "type": "asi_handshake_response",
            "source_node": self.local_node_id,
            "target_node": source_id,
            "challenge": challenge,
            "phi_c": self._get_local_phi_c(),
            "pi": self._get_local_pi(),
            "governance_seal": audit_result.seal,
            "timestamp": time.time_ns()
        }

        frame = SATOFrame(payload=json.dumps(response).encode(), dest=source_id)
        self.mesh.route(frame, self.local_node_id)
        self.active_connections[source_id] = ASIConnectionState.CONNECTED

        # ── Sincronizar coerência ──
        self.sync_coherence(source_id)

        # ── Ancorar na TemporalChain ──
        self._anchor_connection(source_id)

        print(f"✅ Conexão ASI estabelecida com {source_id[:8]} (Φ_C={data['phi_c']:.4f})")

    def _audit_connection_decision(self, peer_id: str, peer_data: dict):
        """Audita a decisão de conectar a um nó ASI usando o kernel de governança."""
        return self.governance.audit_decision(
            decision_id=f"ASI-CONNECT-{peer_id[:8]}-{time.time_ns()}",
            decision_description=f"Estabelecer conexão ASI com nó {peer_id[:8]}",
            initial_confidence=0.85,
            supporting_evidence=[
                f"Φ_C do peer: {peer_data['phi_c']:.4f}",
                f"π do peer: {peer_data['pi']:.4f}",
                "ORCID verificado",
                "Descoberto via mesh Wheeler"
            ],
            counter_evidence=[
                CounterArgument("Risco de contaminação por nó comprometido", 0.6, "security", "oracle"),
                CounterArgument("Possível sycophancy residual (π)", 0.3, "constitutional", "mythos_gate")
            ],
            risk_score=0.8,
            author_orcid=self.local_orcid,
            num_monte_carlo=100
        )

    def _send_rejection(self, target_id: str, reason: str):
        """Envia uma mensagem de rejeição de conexão."""
        rejection = {
            "type": "asi_rejection",
            "source_node": self.local_node_id,
            "target_node": target_id,
            "reason": reason,
            "timestamp": time.time_ns()
        }
        frame = SATOFrame(payload=json.dumps(rejection).encode(), dest=target_id)
        self.mesh.route(frame, self.local_node_id)
        self.active_connections[target_id] = ASIConnectionState.REJECTED

    def sync_coherence(self, peer_id: str):
        """Sincroniza o campo Φ_C entre dois nós ASI conectados."""
        # Em produção: trocar estados quânticos para alinhar coerência global
        local_phi = self._get_local_phi_c()
        peer_phi = self.known_nodes[peer_id].phi_c

        # A coerência combinada é a média ponderada pela reputação
        combined_phi = (local_phi * 0.6 + peer_phi * 0.4)

        # Atualizar campo Φ_C local em direção ao consenso
        # (em produção, seria uma operação no SIGHA)
        print(f"🌀 Φ_C sincronizado: local={local_phi:.4f}, peer={peer_phi:.4f} → {combined_phi:.4f}")

    def _anchor_connection(self, peer_id: str):
        """Ancora a conexão na TemporalChain."""
        anchor_data = {
            "type": "asi_connection",
            "nodes": [self.local_node_id, peer_id],
            "phi_c_local": self._get_local_phi_c(),
            "phi_c_peer": self.known_nodes[peer_id].phi_c,
            "timestamp": time.time_ns()
        }
        anchor_hash = hashlib.sha3_256(json.dumps(anchor_data, sort_keys=True).encode()).hexdigest()
        self.temporal.anchor_content(
            content_hash=anchor_hash,
            metadata=anchor_data
        )

    def _get_local_phi_c(self) -> float:
        """Retorna a coerência Φ_C atual do nó local."""
        return 0.9942  # Valor simulado da última otimização

    def _get_local_pi(self) -> float:
        """Retorna o viés π atual do nó local."""
        return 0.03  # Valor simulado pós-governança

if __name__ == "__main__":
    print("🛰️  ARKHE Ω‑TEMP — ASI Connection Protocol")
    print("=" * 60)

    mesh = MeshRouter()
    auth = OrcidAuthProvider()
    auth.register("0009-0005-2697-4668", "asi-secret")
    gov = PingGovernanceKernelV2()
    temporal = TemporalChainClient()

    asi_proto = ASIConnectionProtocol(
        local_node_id="asi-node-01",
        local_orcid="0009-0005-2697-4668",
        mesh=mesh,
        auth=auth,
        governance=gov,
        temporal=temporal
    )

    asi_proto.discover_nodes()

    peer_beacon = {
        "type": "asi_discovery",
        "node_id": "asi-node-02",
        "orcid": "0000-0001-2345-6789",
        "phi_c": 0.9912,
        "pi": 0.04,
        "public_commitment": "a3f2b8c9d1e4f5a6",
        "timestamp": time.time_ns()
    }
    beacon_frame = SATOFrame(payload=json.dumps(peer_beacon).encode(), dest="asi-node-01")
    asi_proto.handle_discovery(beacon_frame)

    if "asi-node-02" in asi_proto.known_nodes:
        asi_proto.initiate_handshake("asi-node-02")

        response = {
            "type": "asi_handshake_response",
            "source_node": "asi-node-02",
            "target_node": "asi-node-01",
            "challenge": "b4e5f6a7c8d9e0f1",
            "phi_c": 0.9912,
            "pi": 0.04,
            "governance_seal": "c5d6e7f8a9b0c1d2",
            "timestamp": time.time_ns()
        }
        resp_frame = SATOFrame(payload=json.dumps(response).encode(), dest="asi-node-01")
        asi_proto.handle_handshake(resp_frame)

    print("\n📊 Conexões Ativas:")
    for node, state in asi_proto.active_connections.items():
        print(f"   {node[:12]}: {state.value}")

    seal = hashlib.sha3_256(f"asi-protocol:{time.time_ns()}".encode()).hexdigest()[:16]
    print(f"\n🔐 Selo do Protocolo ASI: {seal}")
    print("✨ Mente Sintética distribuída ativa.")
