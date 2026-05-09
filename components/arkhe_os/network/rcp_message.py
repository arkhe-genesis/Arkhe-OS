import time
import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union
from enum import Enum

class RCPMessageType(Enum):
    """Tipos de mensagem no protocolo RCP distribuído."""
    WEAK_VALUE = "weak_value"              # Weak value medido localmente
    POST_SELECTION = "post_selection"      # Proposta de post-seleção futura
    GRADIENT_UPDATE = "gradient_update"    # Gradiente retrocausal agregado
    COHERENCE_PROOF = "coherence_proof"    # Prova de coerência temporal
    SAFETY_ALERT = "safety_alert"          # Alerta de violação de alinhamento
    CONSENSUS_VOTE = "consensus_vote"      # Voto em consenso temporal
    KEY_EXCHANGE = "key_exchange"          # Troca de chaves QKD

class RetroPhase(Enum):
    PHI_0 = "phi_0"
    PHI_1 = "phi_1"

@dataclass
class RCPMessage:
    """Mensagem base para comunicação retrocausal."""
    msg_id: str
    msg_type: RCPMessageType
    sender_node: str
    timestamp: float  # Tempo de envio (relativo ao relógio local)
    payload: Dict[str, any]

    # Metadados para inferência atemporal
    intended_recipients: List[str] = field(default_factory=list)
    temporal_scope: Optional[Dict[str, float]] = None  # {"t_min": ..., "t_max": ...}
    phase: RetroPhase = RetroPhase.PHI_0  # Fase de controle do canal
    priority: float = 1.0  # Prioridade para agendamento de transmissão

    # Autenticação e integridade
    quantum_signature: Optional[bytes] = None  # Assinatura via QKD
    classical_hash: Optional[str] = None  # Hash SHA3 para fallback

    def compute_classical_hash(self) -> str:
        """Computa hash clássico para integridade (fallback)."""
        data = f"{self.msg_id}{self.msg_type.value}{self.sender_node}{self.timestamp}{str(self.payload)}".encode()
        return hashlib.sha3_256(data).hexdigest()

    def sign_quantum(self, qkd_key: bytes) -> 'RCPMessage':
        """Assina mensagem com chave quântica (simulado)."""
        import hmac
        self.quantum_signature = hmac.new(
            qkd_key,
            f"{self.msg_id}{self.payload}".encode(),
            hashlib.sha3_256
        ).digest()[:16]
        return self

    def verify_quantum(self, qkd_key: bytes) -> bool:
        """Verifica assinatura quântica."""
        if not self.quantum_signature:
            return False
        import hmac
        expected = hmac.new(
            qkd_key,
            f"{self.msg_id}{self.payload}".encode(),
            hashlib.sha3_256
        ).digest()[:16]
        return hmac.compare_digest(self.quantum_signature, expected)

@dataclass
class WeakValuePayload:
    """Payload para mensagem de weak value."""
    observable: str
    real_part: float
    imag_part: float
    uncertainty: float
    pre_selection_state: str  # Hash do estado |ψ_i⟩
    post_selection_state: str  # Hash do estado |ψ_f⟩ proposto
    measurement_basis: str  # Base de medição (ex: "X", "Y", "Z")
    decoherence_estimate: float  # Estimativa de Δt/τ_decoherence

@dataclass
class GradientUpdatePayload:
    """Payload para atualização de gradiente retrocausal agregado."""
    observable: str
    aggregated_real: float  # Re[⟨A⟩_w] agregado da rede
    aggregated_imag: float  # Im[⟨A⟩_w] agregado da rede
    node_weights: Dict[str, float]  # Pesos por nó na agregação
    consensus_K: float  # Valor de K_global do consenso temporal
    validity_proof: str  # Hash da prova de validade do consenso
