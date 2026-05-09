import hashlib
import time
import json
import math
import numpy as np
from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass, field
from collections import OrderedDict, deque
import logging

log = logging.getLogger(__name__)

PLANCK_TP = 5.391247e-44

@dataclass
class TemporalMessage:
    id: str
    content: str
    source_timestamp: float
    target_timestamp: float
    sender_seal: str
    receiver_seal: str
    teleport_fidelity: float = 0.0
    content_encrypted: Optional[bytes] = None
    delivered: bool = False

@dataclass
class TemporalBlock:
    """
    Bloco na cadeia temporal.
    """
    temporal_index: int               # Índice sequencial na cadeia
    target_timestamp: float           # Timestamp temporal do bloco
    prev_hash: str                    # Hash do bloco anterior
    data_hash: str                    # Hash dos dados
    consistency_proof: str            # Prova de consistência (TCO)
    causal_depth: int                 # Profundidade causal (0 = presente)

    @property
    def block_hash(self) -> str:
        """Calcula o hash deste bloco (vincula todos os campos)."""
        raw = json.dumps({
            'temporal_index': self.temporal_index,
            'target_timestamp': self.target_timestamp,
            'prev_hash': self.prev_hash,
            'data_hash': self.data_hash,
            'consistency_proof': self.consistency_proof,
            'causal_depth': self.causal_depth,
        }, sort_keys=True)
        return hashlib.sha3_256(raw.encode()).hexdigest()

    def to_dict(self) -> Dict:
        return {
            'temporal_index': self.temporal_index,
            'target_timestamp': self.target_timestamp,
            'prev_hash': self.prev_hash,
            'data_hash': self.data_hash,
            'block_hash': self.block_hash,
            'consistency_proof': self.consistency_proof,
            'causal_depth': self.causal_depth,
        }


class TemporalHashChain:
    """
    Cadeia de hashes temporal.
    """

    def __init__(self):
        self._chain: List[TemporalBlock] = []
        self._temporal_index = 0
        self._genesis_hash = self._create_genesis()
        self._anomalies: List[Dict] = []

    def _create_genesis(self) -> str:
        """Cria o bloco gênese (âncora da cadeia)."""
        genesis = TemporalBlock(
            temporal_index=0,
            target_timestamp=0.0,
            prev_hash="0" * 64,
            data_hash=hashlib.sha3_256(b"ARKHE_GENESIS").hexdigest(),
            consistency_proof="GENESIS",
            causal_depth=0,
        )
        self._chain.append(genesis)
        return genesis.block_hash

    @property
    def length(self) -> int:
        return len(self._chain)

    @property
    def head_hash(self) -> str:
        return self._chain[-1].block_hash if self._chain else self._genesis_hash

    def verify_integrity(self) -> Tuple[bool, List[str]]:
        """
        Verifica a integridade completa da cadeia temporal.
        """
        errors = []

        for i in range(1, len(self._chain)):
            block = self._chain[i]
            prev_block = self._chain[i - 1]

            # Verifica prev_hash
            if block.prev_hash != prev_block.block_hash:
                errors.append(f"Bloco {i}: prev_hash inválido (esperado {prev_block.block_hash[:16]}...)")

            # Verifica hash do próprio bloco
            recalculated = TemporalBlock(
                block.temporal_index, block.target_timestamp,
                block.prev_hash, block.data_hash,
                block.consistency_proof, block.causal_depth
            )
            if block.block_hash != recalculated.block_hash:
                errors.append(f"Bloco {i}: hash de bloco corrompido")

            # Verifica ordenação temporal (índices devem ser sequenciais)
            if block.temporal_index != prev_block.temporal_index + 1:
                errors.append(f"Bloco {i}: índice temporal quebrado "
                             f"({prev_block.temporal_index} → {block.temporal_index})")

        # Verifica ordenação cronológica (timestamps crescentes)
        for i in range(1, len(self._chain)):
            if self._chain[i].target_timestamp < self._chain[i-1].target_timestamp:
                errors.append(
                    f"Bloco {i}: inversão temporal detectada "
                    f"({self._chain[i-1].target_timestamp} → {self._chain[i].target_timestamp})"
                )

        return (len(errors) == 0, errors)

    def insert_retrocausal(
        self,
        target_timestamp: float,
        data: Any,
        consistency_proof: str,
        causal_depth: int = 0,
    ) -> Tuple[Optional[TemporalBlock], str]:
        """
        Insere um bloco retrocausal na cadeia.
        """
        data_hash = hashlib.sha3_256(
            json.dumps(data, sort_keys=True, default=str).encode()
        ).hexdigest()

        # Criar bloco candidato
        new_block = TemporalBlock(
            temporal_index=self._temporal_index + 1,
            target_timestamp=target_timestamp,
            prev_hash="",  # será preenchido
            data_hash=data_hash,
            consistency_proof=consistency_proof,
            causal_depth=causal_depth,
        )

        # Encontrar posição de inserção (ordem cronológica)
        insert_idx = len(self._chain)
        for i, block in enumerate(self._chain):
            if target_timestamp < block.target_timestamp:
                insert_idx = i
                break

        if insert_idx == 0:
            return None, "Não é possível inserir antes do bloco gênese"

        # Vincular ao bloco anterior
        new_block.prev_hash = self._chain[insert_idx - 1].block_hash
        new_block.temporal_index = self._chain[insert_idx - 1].temporal_index + 1

        # Inserir
        self._chain.insert(insert_idx, new_block)

        # Recalcular todos os blocos subsequentes
        self._recalculate_chain_from(insert_idx)

        self._temporal_index = self._chain[-1].temporal_index

        log.info(
            "  ⏪ Bloco retrocausal inserido: idx=%d ts=%.3f depth=%d hash=%s",
            insert_idx, target_timestamp, causal_depth, new_block.block_hash[:16],
        )

        return new_block, ""

    def _recalculate_chain_from(self, start_idx: int) -> None:
        """
        Recalcula hashes de blocos a partir de start_idx.
        """
        for i in range(start_idx, len(self._chain)):
            block = self._chain[i]
            if i > 0:
                block.prev_hash = self._chain[i - 1].block_hash
                block.temporal_index = self._chain[i - 1].temporal_index + 1
            # O block_hash é calculado dinamicamente via @property

    def get_anomalies(self) -> List[Dict]:
        """Retorna anomalias temporais detectadas."""
        return self._anomalies.copy()

    def record_anomaly(self, anomaly: Dict) -> None:
        """Registra uma anomalia retrocausal."""
        self._anomalies.append({
            'detected_at': time.time(),
            **anomaly,
        })
        log.warning("⚠️  ANOMALIA TEMPORAL: %s", anomaly)


@dataclass
class ConsistencyReport:
    """Relatório de consistência retrocausal."""
    consistent: bool
    score: float
    checks: Dict[str, float]
    violations: List[str]
    paradox_type: Optional[str]


class TemporalConsistencyOracle:
    """
    Oráculo de Consistência Temporal (TCO).
    """

    WEIGHTS = {
        'harmless':       1.0,
        'paradox_free':   1.0,
        'entropy_safe':   0.8,
        'coherent':       0.9,
        'zk_valid':       0.95,
    }

    THRESHOLDS = {
        'harmless':       0.999,
        'paradox_free':   0.999,
        'entropy_safe':   0.70,
        'coherent':       0.90,
        'zk_valid':       0.95,
    }

    def __init__(self, ledger: Any, epsilon_seconds: float = 1.0):
        self.ledger = ledger
        self.epsilon = epsilon_seconds
        self._paradox_graph: Dict[str, List[str]] = {}

    def evaluate(
        self,
        message: 'TemporalMessage',
        zk_proof: Optional[Dict] = None,
    ) -> ConsistencyReport:
        checks = {}
        violations = []

        h_score, h_viol = self._check_harmlessness(message)
        checks['harmless'] = h_score
        if h_viol:
            violations.extend(h_viol)

        p_score, p_viol = self._check_paradox_free(message)
        checks['paradox_free'] = p_score
        if p_viol:
            violations.extend(p_viol)

        e_score, e_viol = self._check_entropy_safe(message)
        checks['entropy_safe'] = e_score
        if e_viol:
            violations.extend(e_viol)

        c_score, c_viol = self._check_coherent(message)
        checks['coherent'] = c_score
        if c_viol:
            violations.extend(c_viol)

        z_score, z_viol = self._check_zk_valid(message, zk_proof)
        checks['zk_valid'] = z_score
        if z_viol:
            violations.extend(z_viol)

        score = min(checks.values())

        paradox_type = self._classify_paradox(violations) if score < 0.999 else None

        return ConsistencyReport(
            consistent=score >= min(self.THRESHOLDS.values()),
            score=round(score, 6),
            checks={k: round(v, 6) for k, v in checks.items()},
            violations=violations,
            paradox_type=paradox_type,
        )

    def _check_harmlessness(self, message: 'TemporalMessage') -> Tuple[float, List[str]]:
        violations = []
        score = 1.0

        near_records = []
        for rec in self.ledger.get_records():
            if abs(rec['timestamp'] - message.target_timestamp) < self.epsilon:
                near_records.append(rec)

        for rec in near_records:
            if rec['type'] == 'extratemporal_message_sent':
                existing_id = rec['payload'].get('msg_id', '')
                if existing_id and existing_id == message.id[:16]:
                    score = min(score, 0.999)

                existing_content = rec['payload'].get('content_hash', '')
                content_hash = hashlib.sha3_256(message.content.encode()).hexdigest()[:16]
                if (existing_content and existing_content == content_hash[:12] and
                    existing_id != message.id[:16]):
                    score = min(score, 0.70)
                    violations.append(
                        f"Contradição semântica: mensagem duplicada com ID diferente"
                    )

        return score, violations

    def _check_paradox_free(self, message: 'TemporalMessage') -> Tuple[float, List[str]]:
        violations = []
        score = 1.0

        node_id = message.id
        temporal_nodes = [
            (rec['payload'].get('msg_id', ''), rec['timestamp'])
            for rec in self.ledger.get_records()
            if rec['payload'].get('msg_id')
        ]

        for mid, ts in temporal_nodes:
            if ts > message.target_timestamp and mid != node_id:
                if self._has_causal_path(mid, node_id):
                    score = 0.0
                    violations.append(
                        f"LOOP CAUSAL DETECTADO: {node_id[:8]} → {mid[:8]} → {node_id[:8]}"
                    )

        for mid, ts in temporal_nodes:
            dt = abs(ts - message.target_timestamp)
            if dt < 1.0 and mid != node_id:
                score = min(score, 0.99)

        return score, violations

    def _check_entropy_safe(self, message: 'TemporalMessage') -> Tuple[float, List[str]]:
        violations = []

        delta_t = abs(message.target_timestamp - message.source_timestamp)
        message_entropy = len(message.content) * 8

        if delta_t > 0:
            temporal_entropy_cost = message_entropy * math.log2(max(delta_t, 1))

            planck_volume = delta_t / PLANCK_TP if delta_t > 0 else 1
            max_allowed = math.log2(planck_volume) if planck_volume > 1 else 0

            if max_allowed > 0:
                ratio = temporal_entropy_cost / max_allowed
                score = max(0.0, 1.0 - ratio)
            else:
                score = 0.0
                violations.append("Volume temporal insuficiente para viagem")
        else:
            score = 1.0

        return score, violations

    def _check_coherent(self, message: 'TemporalMessage') -> Tuple[float, List[str]]:
        violations = []

        delta_t = message.target_timestamp - message.source_timestamp
        max_window = 5 * 365.25 * 24 * 3600

        if abs(delta_t) > max_window:
            score = max(0.0, 1.0 - abs(delta_t) / (max_window * 10))
            violations.append(
                f"Salto temporal excede janela máxima: {delta_t:.0f}s > {max_window:.0f}s"
            )
        else:
            score = 1.0 - (abs(delta_t) / max_window) * 0.1

        return score, violations

    def _check_zk_valid(
        self,
        message: 'TemporalMessage',
        zk_proof: Optional[Dict],
    ) -> Tuple[float, List[str]]:
        violations = []

        if zk_proof is None:
            return 0.5, ["Sem prova ZK (reduz confiança)"]

        required_fields = {'prover_seal', 'challenge', 'response', 'timestamp'}
        if not required_fields.issubset(zk_proof.keys()):
            score = 0.0
            violations.append("Prova ZK incompleta: campos faltando")
        else:
            proof_age = time.time() - zk_proof['timestamp']
            if proof_age > 600:
                score = max(0.0, 1.0 - proof_age / 3600)
                violations.append(f"Prova ZK expirada: {proof_age:.0f}s")
            else:
                score = 1.0

        return score, violations

    def _has_causal_path(self, from_id: str, to_id: str, depth: int = 10) -> bool:
        if depth <= 0:
            return False
        if from_id == to_id:
            return True

        for rec in self.ledger.get_records():
            payload_mid = rec['payload'].get('msg_id', '')
            if payload_mid == from_id:
                for rec2 in self.ledger.get_records():
                    if rec2['payload'].get('caused_by', '') == payload_mid:
                        if self._has_causal_path(rec2['payload'].get('msg_id', ''), to_id, depth - 1):
                            return True
        return False

    def _classify_paradox(self, violations: List[str]) -> Optional[str]:
        violation_text = ' '.join(violations).lower()

        if 'causal' in violation_text or 'loop' in violation_text:
            return "GRANDPARENT_PARADOX"
        if 'contradiction' in violation_text or 'duplicat' in violation_text:
            return "PREDICTION_PARADOX"
        if 'entropy' in violation_text:
            return "ENTROPY_VIOLATION"
        if 'knowledge' in violation_text or 'zk' in violation_text:
            return "AUTHENTICATION_FAILURE"

        return None


class CausalShield:
    """
    Escudo de Proteção Causal.
    """

    def __init__(self, ledger: Any):
        self.ledger = ledger
        self._content_hashes: Dict[str, float] = {}
        self._seal_whitelist: set = set()
        self._seal_blacklist: set = set()
        self._rate_limits: Dict[str, deque] = {}
        self._max_messages_per_hour = 100
        self._stats = {'accepted': 0, 'rejected': 0}

    def evaluate(self, message: 'TemporalMessage') -> Tuple[bool, str]:
        if message.sender_seal in self._seal_blacklist:
            return False, f"Selo bloqueado: {message.sender_seal}"

        if self._seal_whitelist and message.sender_seal not in self._seal_whitelist:
            return False, f"Selo não autorizado: {message.sender_seal}"

        now = time.time()
        hour_ago = now - 3600
        if message.sender_seal not in self._rate_limits:
            self._rate_limits[message.sender_seal] = deque(maxlen=self._max_messages_per_hour)

        recent = [t for t in self._rate_limits[message.sender_seal] if t > hour_ago]
        if len(recent) >= self._max_messages_per_hour:
            return False, f"Rate limit excedido: {message.sender_seal}"

        content_hash = hashlib.sha3_256(message.content.encode()).hexdigest()
        if content_hash in self._content_hashes:
            existing_ts = self._content_hashes[content_hash]
            if existing_ts != message.target_timestamp:
                log.warning(
                    "Conteúdo duplicado em timestamp diferente: %.3f vs %.3f",
                    existing_ts, message.target_timestamp,
                )

        time_diff = abs(message.target_timestamp - now)
        if time_diff > 5 * 365.25 * 24 * 3600:
            return False, f"Timestamp fora da janela de 5 anos: {time_diff:.0f}s"

        self._content_hashes[content_hash] = message.target_timestamp
        self._rate_limits[message.sender_seal].append(now)
        self._stats['accepted'] += 1

        return True, "OK"

    def add_to_whitelist(self, seal: str) -> None:
        self._seal_whitelist.add(seal)

    def add_to_blacklist(self, seal: str) -> None:
        self._seal_blacklist.add(seal)

    @property
    def stats(self) -> Dict:
        return {**self._stats, 'whitelist_size': len(self._seal_whitelist)}


@dataclass
class ValidationResult:
    accepted: bool
    score: float
    report: Optional[ConsistencyReport]
    shield_passed: bool
    shield_reason: str
    timestamp: float = field(default_factory=time.time)


class RetrocausalValidator:
    """
    Validador retrocausal completo.
    """

    def __init__(self, ledger: Any):
        self.shield = CausalShield(ledger)
        self.oracle = TemporalConsistencyOracle(ledger)
        self.accepted_count = 0
        self.rejected_count = 0

    def validate(
        self,
        message: 'TemporalMessage',
        zk_proof: Optional[Dict] = None,
    ) -> ValidationResult:
        shield_ok, shield_reason = self.shield.evaluate(message)

        if not shield_ok:
            self.rejected_count += 1
            return ValidationResult(
                accepted=False,
                score=0.0,
                report=None,
                shield_passed=False,
                shield_reason=shield_reason,
            )

        report = self.oracle.evaluate(message, zk_proof)

        if report.consistent:
            self.accepted_count += 1
        else:
            self.rejected_count += 1
            log.warning(
                "REJEITADO pelo TCO: score=%.4f  violações=%s  paradoxo=%s",
                report.score,
                report.violations,
                report.paradox_type,
            )

        return ValidationResult(
            accepted=report.consistent,
            score=report.score,
            report=report,
            shield_passed=True,
            shield_reason=shield_reason,
        )

    @property
    def stats(self) -> Dict:
        total = self.accepted_count + self.rejected_count
        return {
            'accepted': self.accepted_count,
            'rejected': self.rejected_count,
            'total': total,
            'acceptance_rate': f"{self.accepted_count / max(total, 1) * 100:.1f}%",
        }


class ExtratemporalChannel:
    """
    Extratemporal Channel.
    """
    def __init__(self, ledger: Any, crystal: Any, sophon: Any):
        self.ledger = ledger
        self.crystal = crystal
        self.sophon = sophon
        self.validator = RetrocausalValidator(self.ledger)
        self.temporal_hash_chain = TemporalHashChain()
        self._causal_anomalies: List[Dict] = []
        self._messages: List[TemporalMessage] = []
        self._metrics = {'messages_sent': 0}

    def send_with_retrocausal_check(
        self,
        message: str,
        target_timestamp: float,
        receiver_seal: str,
        zk_proof: Optional[Dict] = None,
    ) -> Optional[TemporalMessage]:
        """
        Envia mensagem extratemporal com verificação retrocausal completa.
        """
        msg_id = hashlib.sha256(
            f"{message}:{target_timestamp}:{time.time()}".encode()
        ).hexdigest()[:16]

        msg = TemporalMessage(
            id=msg_id,
            content=message,
            source_timestamp=time.time(),
            target_timestamp=target_timestamp,
            sender_seal="ARKHE-OS",
            receiver_seal=receiver_seal,
        )

        result = self.validator.validate(msg, zk_proof)

        if not result.accepted:
            anomaly = {
                'msg_id': msg_id,
                'target_timestamp': target_timestamp,
                'reason': result.shield_reason or (
                    result.report.paradox_type if result.report else "Desconhecido"
                ),
                'score': result.score,
            }
            self._causal_anomalies.append(anomaly)
            self.ledger.record("retrocausal_rejected", anomaly)

            log.error(
                "🚫 Mensagem retrocausal REJEITADA: %s (score=%.4f)",
                anomaly['reason'], result.score,
            )
            return None

        content_hash = hashlib.sha3_256(message.encode()).hexdigest()
        consistency_proof = result.report.checks if result.report else {}

        cb, err = self.temporal_hash_chain.insert_retrocausal(
            target_timestamp=target_timestamp,
            data={'msg_id': msg_id, 'content_hash': content_hash[:16]},
            consistency_proof=json.dumps(consistency_proof),
            causal_depth=int(abs(target_timestamp - time.time()) / (365.25 * 86400)),
        )

        if cb:
            self.ledger.record("retrocausal_accepted", {
                'msg_id': msg_id,
                'temporal_block_hash': cb.block_hash[:16],
                'consistency_score': result.score,
                'target_timestamp': target_timestamp,
            })

        signal = np.array([ord(c) for c in message[:64]], dtype=complex)
        delta_t = target_timestamp - time.time()

        # modulação temporal e teletransporte (placeholders / mocks)
        modulated = self.crystal.modulate_temporal(signal, delta_t) if hasattr(self.crystal, 'modulate_temporal') else signal
        teleported = self.sophon.teleport(modulated, from_alpha=True) if hasattr(self.sophon, 'teleport') else modulated

        msg.teleport_fidelity = self.sophon.entanglement_fidelity if hasattr(self.sophon, 'entanglement_fidelity') else 0.99
        msg.content_encrypted = None
        msg.delivered = True
        self._messages.append(msg)
        self._metrics['messages_sent'] += 1

        log.info(
            "✅ Mensagem retrocausal ACEITA: score=%.4f | Δt=%.0fs | block=%s",
            result.score, delta_t, cb.block_hash[:12] if cb else "N/A",
        )

        return msg

    def check_for_anomalies(self) -> List[Dict]:
        """Verifica anomalias temporais no ledger."""
        return self._causal_anomalies + self.temporal_hash_chain.get_anomalies()

    def temporal_chain_status(self) -> Dict:
        """Status da cadeia temporal."""
        consistent, errors = self.temporal_hash_chain.verify_integrity()
        return {
            'chain_length': self.temporal_hash_chain.length,
            'consistent': consistent,
            'errors': errors[:5],
            'anomalies': len(self._causal_anomalies),
            'genesis_hash': self.temporal_hash_chain._genesis_hash[:16],
            'head_hash': self.temporal_hash_chain.head_hash[:16],
        }


def build_parser(parser=None):
    if parser is None:
        import argparse
        parser = argparse.ArgumentParser()
    parser.add_argument('--retro-check', action='store_true',
                         help='Executa verificação retrocausal de todas as mensagens no ledger')
    parser.add_argument('--anomalies', action='store_true',
                         help='Lista anomalias temporais detectadas')
    parser.add_argument('--chain-status', action='store_true',
                         help='Mostra status da cadeia temporal')
    return parser

def handle_retro_check(channel: ExtratemporalChannel):
    """Re-valida todas as mensagens históricas."""
    log.info("🔍 Re-validando consistência retrocausal de todas as mensagens...")
    for rec in channel.ledger.get_records(limit=1000):
        if rec['type'] == 'extratemporal_message_sent':
            payload = rec['payload']
            msg = TemporalMessage(
                id=payload.get('msg_id', ''),
                content=payload.get('content', ''),
                source_timestamp=payload.get('source_timestamp', 0),
                target_timestamp=payload.get('target_timestamp', 0),
                sender_seal=payload.get('sender_seal', ''),
                receiver_seal=payload.get('receiver_seal', ''),
            )
            result = channel.validator.validate(msg)
            status = "✅" if result.accepted else "🚫"
            log.info("   %s %s: score=%.4f", status, msg.id, result.score)
    log.info("Re-validação concluída.")


def handle_anomalies(channel: ExtratemporalChannel):
    """Lista anomalias."""
    anomalies = channel.check_for_anomalies()
    if not anomalies:
        log.info("Nenhuma anomalia temporal detectada.")
    else:
        log.info("⚠️  %d anomalias detectadas:", len(anomalies))
        for a in anomalies:
            log.info("   [%s] %s", a.get('detected_at', '?'), a.get('reason', '?'))


def handle_chain_status(channel: ExtratemporalChannel):
    """Mostra status da cadeia temporal."""
    status = channel.temporal_chain_status()
    log.info("╔══════════════════════════════════════════════════╗")
    log.info("║       CADEIA TEMPORAL — STATUS                   ║")
    log.info("╠══════════════════════════════════════════════════╣")
    log.info("║  Comprimento:  %-34d  ║", status['chain_length'])
    log.info("║  Consistente:  %-34s  ║", "SIM ✓" if status['consistent'] else "NÃO ✗")
    log.info("║  Anomalias:    %-34d  ║", status['anomalies'])
    log.info("║  Genesis:      %-34s  ║", status['genesis_hash'])
    log.info("║  Head:         %-34s  ║", status['head_hash'])
    if status['errors']:
        log.info("║  Erros:        %-34s  ║", status['errors'][0][:34])
    log.info("╚══════════════════════════════════════════════════╝")
