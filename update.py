import sys

# The raw prompt string exactly as given in the system prompt
prompt_text = r'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
arkhe_recovery_email_v4.py — Substrato 6046: Recovery Email Transport
=======================================================================
Transporte de e-mail como fallback para a rede retrocausal ARKHE Ω-TEMP.

Integra:
  6046 — Recovery Email Gateway (SMTP/IMAP store-and-forward)
  5027 — QFAM (recall de mensagens enfileiradas)
  333  — Audit Ledger (SQLite persistente)
  5034 — Temporal Consistency Oracle (revalidação na reconciliação)
  5033 — Temporal Hash Chain (registro de blocos reconciliados)

Protocolo:
  1. Mensagens temporais validadas são enfileiradas quando o transporte primário falha
  2. Encapsulamento MIME com headers X-ARKHE-* e assinatura HMAC-SHA3-256
  3. Envio SMTP com retry exponencial e backoff
  4. Recepção IMAP com parsing de headers ARKHE
  5. Reconciliação: revalidação pelo TCO e inserção na cadeia temporal

Modos:
  --demo          Demonstração completa (modo simulação, sem e-mails reais)
  --send-test     Simula envio de uma mensagem de recuperação
  --poll-test     Simula polling de inbox e reconciliação
  --status        Status da fila de recuperação
  --ledger-verify Verifica integridade do ledger

Autor: ARKHE OS / Sophon.agi
Versão: 4.5.0
"""

import argparse
import hashlib
import hmac
import json
import logging
import math
import os
import sqlite3
import sys
import threading
import time
import uuid
from collections import deque
from dataclasses import dataclass, field, asdict
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders, message_from_bytes
from email.utils import formatdate
from pathlib import Path
from typing import Any, Dict, Deque, List, Optional, Tuple, Union

import numpy as np

# ============================================================================
# LOGGING
# ============================================================================
log = logging.getLogger("arkhe.recovery")

def setup_logging(level: str = "INFO") -> None:
    fmt = "[%(asctime)s] [%(levelname)-8s] %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format=fmt, datefmt=datefmt,
        handlers=[logging.StreamHandler(sys.stdout)],
    )

# ============================================================================
# STUBS MÍNIMOS DO ECOSISTEMA ARKHE (autocontido)
# ============================================================================

@dataclass
class TemporalMessage:
    id: str
    content: str
    source_timestamp: float
    target_timestamp: float
    sender_seal: str
    receiver_seal: str
    encrypted: bool = True
    delivered: bool = False
    teleport_fidelity: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ConsistencyReport:
    consistent: bool
    score: float
    checks: Dict[str, float]
    violations: List[str]
    paradox_type: Optional[str] = None

@dataclass
class ValidationResult:
    accepted: bool
    score: float
    report: Optional[ConsistencyReport]
    shield_passed: bool
    shield_reason: str

class AuditLedger:
    """Stub do Ledger 333 — SQLite persistente."""
    def __init__(self, db_path: Union[str, Path] = "/tmp/arkhe_ledger_6046.db"):
        self._db_path = Path(db_path)
        self._conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._setup_tables()

    def _setup_tables(self):
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS ledger_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                timestamp REAL NOT NULL,
                hash TEXT NOT NULL UNIQUE
            )
        """)
        self._conn.commit()

    def record(self, event_type: str, payload: Dict) -> str:
        payload_str = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        entry_hash = hashlib.sha3_256(payload_str.encode()).hexdigest()
        try:
            self._conn.execute(
                "INSERT INTO ledger_entries (event_type, payload_json, timestamp, hash) VALUES (?,?,?,?)",
                (event_type, payload_str, time.time(), entry_hash)
            )
            self._conn.commit()
        except sqlite3.IntegrityError:
            pass
        return entry_hash

    def get_records(self, limit: int = 100):
        cursor = self._conn.execute(
            "SELECT id, event_type, payload_json, timestamp, hash FROM ledger_entries ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        return [{"id": r[0], "type": r[1], "payload": json.loads(r[2]), "timestamp": r[3], "hash": r[4]} for r in cursor.fetchall()]

    def count(self) -> int:
        return self._conn.execute("SELECT COUNT(*) FROM ledger_entries").fetchone()[0]

    def verify_integrity(self):
        cursor = self._conn.execute("SELECT id, event_type, payload_json, hash FROM ledger_entries")
        errors = []
        for row in cursor.fetchall():
            computed = hashlib.sha3_256(row[2].encode()).hexdigest()
            if computed != row[3]:
                errors.append(f"ID {row[0]}: hash mismatch")
        return len(errors) == 0, errors

    def close(self):
        if self._conn:
            self._conn.close()

class TemporalHashChain:
    """Stub da cadeia 5033."""
    def __init__(self):
        self._chain: List[Dict] = []
        self._genesis = hashlib.sha3_256(b"ARKHE_GENESIS_6046").hexdigest()
        self._chain.append({"hash": self._genesis, "prev": "0"*64, "data": "genesis"})

    @property
    def head_hash(self) -> str:
        return self._chain[-1]["hash"]

    def insert_retrocausal(self, target_timestamp: float, data: str, proof: str, causal_depth: float):
        prev = self._chain[-1]["hash"]
        block_hash = hashlib.sha3_256(f"{prev}:{data}:{target_timestamp}".encode()).hexdigest()
        self._chain.append({
            "hash": block_hash, "prev": prev, "data": data,
            "target_ts": target_timestamp, "proof": proof, "depth": causal_depth,
        })
        return block_hash

    @property
    def length(self) -> int:
        return len(self._chain)

class RetrocausalValidator:
    """Stub do validador 5036."""
    def __init__(self, ledger: AuditLedger):
        self.ledger = ledger
        self.accepted_count = 0
        self.rejected_count = 0

    def validate(self, msg: TemporalMessage) -> ValidationResult:
        # Simulação: aceita se target está dentro de ±5 anos
        delta = abs(msg.target_timestamp - time.time())
        max_window = 5 * 365.25 * 86400
        if delta > max_window:
            self.rejected_count += 1
            return ValidationResult(
                accepted=False, score=0.0,
                report=ConsistencyReport(
                    consistent=False, score=0.0,
                    checks={}, violations=["Timestamp fora de 5 anos"], paradox_type="ENTROPY_VIOLATION"
                ),
                shield_passed=False, shield_reason="Fora da janela temporal"
            )
        self.accepted_count += 1
        return ValidationResult(
            accepted=True, score=1.0,
            report=ConsistencyReport(
                consistent=True, score=1.0,
                checks={'harmless': 1.0, 'paradox_free': 1.0, 'entropy_safe': 1.0, 'coherent': 1.0, 'zk_valid': 1.0},
                violations=[], paradox_type=None
            ),
            shield_passed=True, shield_reason="OK"
        )

# ============================================================================
# CONFIGURAÇÃO DE E-MAIL
# ============================================================================

@dataclass
class EmailConfig:
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    imap_host: str = "imap.gmail.com"
    imap_port: int = 993
    email_address: str = ""
    app_password: str = ""
    use_tls: bool = True
    max_retries: int = 5
    retry_backoff_base: float = 2.0
    imap_timeout: int = 30
    search_folder: str = "INBOX"
    sent_folder: str = "[ARKHE]/Sent"
    archive_folder: str = "[ARKHE]/Archive"
    rejected_folder: str = "[ARKHE]/Rejected"
    recovery_queue_db: str = "/tmp/arkhe_recovery_queue_6046.db"
    dry_run: bool = True  # Se True, não conecta a servidores reais

    def validate(self) -> bool:
        if self.dry_run:
            return True
        return bool(self.email_address and self.app_password)

# ============================================================================
# EMAIL ADAPTER — TemporalMessage ↔ RFC 5322
# ============================================================================

class EmailAdapter:
    HEADER_MAP = {
        'version': 'X-ARKHE-Version',
        'msg_id': 'X-ARKHE-Msg-ID',
        'target_timestamp': 'X-ARKHE-Target-TS',
        'source_timestamp': 'X-ARKHE-Source-TS',
        'sender_seal': 'X-ARKHE-Sender-Seal',
        'receiver_seal': 'X-ARKHE-Receiver-Seal',
        'chain_hash': 'X-ARKHE-Chain-Hash',
        'delta_t': 'X-ARKHE-Delta-T',
        'signature': 'X-ARKHE-Signature',
        'consistency_score': 'X-ARKHE-Consistency',
        'recovery_mode': 'X-ARKHE-Recovery-Mode',
    }

    @classmethod
    def to_email(cls, msg: TemporalMessage, config: EmailConfig,
                 chain_hash: str = "", score: float = 1.0) -> MIMEMultipart:
        email_msg = MIMEMultipart('mixed')
        email_msg['From'] = config.email_address or "arkhe@localhost"
        email_msg['To'] = msg.receiver_seal
        email_msg['Subject'] = f"[ARKHE-RECOVERY] {msg.content[:50]}..."
        email_msg['Date'] = formatdate(time.time(), usegmt=True)
        email_msg['Message-ID'] = f"<{msg.id}@arkhe.recovery>"

        headers = {
            'version': '4.5.0',
            'msg_id': msg.id,
            'target_timestamp': str(msg.target_timestamp),
            'source_timestamp': str(msg.source_timestamp),
            'sender_seal': msg.sender_seal,
            'receiver_seal': msg.receiver_seal,
            'delta_t': str(msg.target_timestamp - msg.source_timestamp),
            'consistency_score': str(score),
            'chain_hash': chain_hash,
            'recovery_mode': 'true',
        }
        # Assinatura HMAC-SHA3-256
        sign_data = json.dumps(headers, sort_keys=True).encode()
        key_material = hashlib.sha3_256(msg.sender_seal.encode()).digest()
        headers['signature'] = hashlib.sha3_256(key_material + sign_data).hexdigest()

        for key, value in headers.items():
            email_msg[cls.HEADER_MAP.get(key, f"X-ARKHE-{key}")] = str(value)

        body_text = (
            f"═══ ARKHE Ω-TEMP RECOVERY MESSAGE ═══\n"
            f"ID: {msg.id}\n"
            f"De: {msg.sender_seal}\n"
            f"Para: {msg.receiver_seal}\n"
            f"Destino (epoch): {msg.target_timestamp:.3f}\n"
            f"Consistência: {score:.6f}\n"
            f"Modo: RECOVERY (transportado por e-mail)\n"
            f"{'═'*40}\n\n"
            f"{msg.content}"
        )
        email_msg.attach(MIMEText(body_text, 'plain', 'utf-8'))

        # Payload binário anexo
        payload = json.dumps({
            'id': msg.id, 'content': msg.content,
            'source_ts': msg.source_timestamp, 'target_ts': msg.target_timestamp,
            'sender': msg.sender_seal, 'receiver': msg.receiver_seal,
        }).encode()
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(payload)
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename="arkhe_recovery_{msg.id}.bin"')
        email_msg.attach(part)
        return email_msg

    @classmethod
    def from_email(cls, email_msg: message_from_bytes) -> Optional[Dict]:
        try:
            headers = {}
            for key, header_name in cls.HEADER_MAP.items():
                value = email_msg.get(header_name, '')
                if value:
                    headers[key] = value.strip()
            required = ['msg_id', 'target_timestamp', 'source_timestamp', 'sender_seal', 'receiver_seal']
            if not all(k in headers for k in required):
                return None
            body = ""
            if email_msg.is_multipart():
                for part in email_msg.walk():
                    if part.get_content_type() == 'text/plain' and 'attachment' not in str(part.get('Content-Disposition', '')):
                        payload = part.get_payload(decode=True)
                        if payload:
                            body = payload.decode('utf-8', errors='replace')
            else:
                payload = email_msg.get_payload(decode=True)
                if payload:
                    body = payload.decode('utf-8', errors='replace')
            content = body.split('\n\n', 1)[-1] if '\n\n' in body else body
            return {
                **headers,
                'content': content,
                'source_timestamp': float(headers['source_timestamp']),
                'target_timestamp': float(headers['target_timestamp']),
                'consistency_score': float(headers.get('consistency_score', '0')),
                'recovery_mode': headers.get('recovery_mode', 'false') == 'true',
            }
        except Exception as e:
            log.error("Erro ao parsear e-mail ARKHE: %s", e)
            return None

# ============================================================================
# SIMULADORES SMTP/IMAP (modo dry-run)
# ============================================================================

class SimulatedSMTP:
    """Simulador de conexão SMTP para testes sem credenciais reais."""
    def __init__(self):
        self.sent_messages: List[MIMEMultipart] = []
        self._connected = False

    def connect(self, host: str, port: int, timeout: int = 30):
        log.debug("[SIM-SMTP] Conectando a %s:%d", host, port)
        self._connected = True

    def starttls(self, context=None):
        log.debug("[SIM-SMTP] STARTTLS")

    def login(self, user: str, password: str):
        log.debug("[SIM-SMTP] Login como %s", user)

    def send_message(self, msg: MIMEMultipart, from_addr: str, to_addrs: List[str]):
        self.sent_messages.append(msg)
        log.info("[SIM-SMTP] Mensagem enviada: %s -> %s", msg['Message-ID'], ', '.join(to_addrs))

    def quit(self):
        self._connected = False
        log.debug("[SIM-SMTP] Desconectado")

class SimulatedIMAP:
    """Simulador de conexão IMAP para testes."""
    def __init__(self, simulated_inbox: List[message_from_bytes] = None):
        self._inbox = simulated_inbox or []
        self._processed = set()
        self._connected = False

    def login(self, user: str, password: str):
        log.debug("[SIM-IMAP] Login como %s", user)
        self._connected = True

    def select(self, folder: str):
        log.debug("[SIM-IMAP] Selecionando %s", folder)
        return 'OK', [str(len(self._inbox)).encode()]

    def search(self, charset: str, criterion: str):
        ids = [str(i+1).encode() for i in range(len(self._inbox))]
        return 'OK', [b' '.join(ids)]

    def fetch(self, num: bytes, data: str):
        idx = int(num) - 1
        if 0 <= idx < len(self._inbox):
            raw = self._inbox[idx].as_bytes()
            return 'OK', [(b'1 (RFC822 ' + str(len(raw)).encode() + b')', raw)]
        return 'NO', []

    def copy(self, num: bytes, folder: str):
        log.debug("[SIM-IMAP] Copiando %s para %s", num, folder)
        return 'OK', []

    def store(self, num: bytes, flags: str, value: str):
        return 'OK', []

    def expunge(self):
        return 'OK', []

    def create(self, folder: str):
        return 'OK', []

    def logout(self):
        self._connected = False
        log.debug("[SIM-IMAP] Desconectado")

# ============================================================================
# RECOVERY EMAIL GATEWAY (Substrato 6046)
# ============================================================================

class RecoveryEmailGateway:
    def __init__(self, ledger: AuditLedger, chain: TemporalHashChain,
                 validator: RetrocausalValidator, config: EmailConfig):
        self.ledger = ledger
        self.chain = chain
        self.validator = validator
        self.config = config
        self._smtp: Optional[Any] = None
        self._imap: Optional[Any] = None
        self._outbox: Deque[Tuple[TemporalMessage, float, str]] = deque()
        self._inbox_pending: Deque[Dict] = deque()
        self._processed_ids: set = set()
        self._stats = {'sent': 0, 'received': 0, 'reconciled': 0, 'rejected': 0, 'retries': 0}
        self._running = False
        self._lock = threading.Lock()
        self._db_conn = sqlite3.connect(self.config.recovery_queue_db, check_same_thread=False)
        self._init_db()
        log.info("Recovery Email Gateway (Substrato 6046) inicializado. dry_run=%s", config.dry_run)

    def _init_db(self):
        with self._db_conn:
            self._db_conn.execute("""
                CREATE TABLE IF NOT EXISTS recovery_queue (
                    id TEXT PRIMARY KEY,
                    msg_json TEXT,
                    score REAL,
                    chain_hash TEXT,
                    queued_at REAL,
                    retries INTEGER DEFAULT 0,
                    last_retry REAL,
                    status TEXT DEFAULT 'pending'
                )
            """)

    def enqueue(self, msg: TemporalMessage, score: float = 1.0, chain_hash: str = ""):
        with self._db_conn:
            self._db_conn.execute(
                "INSERT OR REPLACE INTO recovery_queue (id, msg_json, score, chain_hash, queued_at) VALUES (?,?,?,?,?)",
                (msg.id, json.dumps(asdict(msg)), score, chain_hash, time.time())
            )
        with self._lock:
            self._outbox.append((msg, score, chain_hash))
        log.info("📥 Enfileirada para recovery: %s (score=%.4f)", msg.id[:12], score)
        self.ledger.record("recovery_enqueued", {
            'msg_id': msg.id, 'score': score, 'chain_hash': chain_hash[:16],
            'target_timestamp': msg.target_timestamp,
        })

    def send_retry_queue(self):
        if not self._outbox:
            log.info("📭 Fila de recovery vazia.")
            return
        log.info("📤 Processando fila de recovery (%d itens)...", len(self._outbox))
        processed = 0
        while self._outbox:
            with self._lock:
                msg, score, chain_hash = self._outbox.popleft()
            try:
                self._send_one(msg, score, chain_hash)
                self._stats['sent'] += 1
                processed += 1
                with self._db_conn:
                    self._db_conn.execute(
                        "UPDATE recovery_queue SET status='sent' WHERE id=?", (msg.id,)
                    )
            except Exception as e:
                log.warning("Falha ao enviar %s: %s. Reenfileirando...", msg.id[:12], e)
                self._stats['retries'] += 1
                with self._lock:
                    self._outbox.appendleft((msg, score, chain_hash))
                with self._db_conn:
                    self._db_conn.execute(
                        "UPDATE recovery_queue SET retries=retries+1, last_retry=? WHERE id=?",
                        (time.time(), msg.id)
                    )
                break
        log.info("📤 %d mensagens enviadas. %d retries.", processed, self._stats['retries'])

    def _send_one(self, msg: TemporalMessage, score: float, chain_hash: str):
        self._connect_smtp()
        email_msg = EmailAdapter.to_email(msg, self.config, chain_hash, score)
        for attempt in range(self.config.max_retries):
            try:
                self._smtp.send_message(email_msg, from_addr=self.config.email_address or "arkhe@localhost", to_addrs=[msg.receiver_seal])
                log.info("📧 Recovery email sent: %s (attempt %d)", msg.id[:12], attempt + 1)
                return
            except Exception as e:
                log.warning("SMTP attempt %d failed: %s", attempt + 1, e)
                time.sleep(self.config.retry_backoff_base ** attempt)
        raise RuntimeError("Max retries exceeded")

    def poll_inbox(self) -> List[Dict]:
        self._connect_imap()
        detected = []
        try:
            self._imap.select(self.config.search_folder)
            status, msgnums = self._imap.search(None, '(SUBJECT "[ARKHE-RECOVERY]")')
            if status != 'OK':
                return detected
            ids = msgnums[0].split()
            log.info("📬 %d mensagens ARKHE encontradas no inbox.", len(ids))
            for num in ids[-20:]:
                try:
                    status, raw = self._imap.fetch(num, '(RFC822)')
                    if status != 'OK':
                        continue
                    if self.config.dry_run:
                        email_msg = message_from_bytes(raw[0][1])
                    else:
                        email_msg = message_from_bytes(raw[0][1])
                    meta = EmailAdapter.from_email(email_msg)
                    if not meta or meta['msg_id'] in self._processed_ids:
                        continue
                    self._processed_ids.add(meta['msg_id'])
                    detected.append(meta)
                    log.info("📬 Mensagem recebida: %s (Δt=%.0fs)", meta['msg_id'][:12],
                             meta['target_timestamp'] - time.time())
                    self._imap.copy(num, self.config.archive_folder)
                    self._imap.store(num, '+FLAGS', '\\Deleted')
                except Exception as e:
                    log.error("Erro ao processar e-mail %s: %s", num, e)
            self._imap.expunge()
        except Exception as e:
            log.error("Erro no polling IMAP: %s", e)
        self._stats['received'] += len(detected)
        return detected

    def reconcile(self, messages: List[Dict]) -> Dict:
        result = {'accepted': 0, 'rejected': 0, 'paradoxes': 0}
        for meta in messages:
            msg = TemporalMessage(
                id=meta['msg_id'],
                content=meta['content'],
                source_timestamp=meta['source_timestamp'],
                target_timestamp=meta['target_timestamp'],
                sender_seal=meta['sender_seal'],
                receiver_seal=meta['receiver_seal'],
            )
            vr = self.validator.validate(msg)
            if vr.accepted:
                block_hash = self.chain.insert_retrocausal(
                    msg.target_timestamp,
                    json.dumps({'msg_id': msg.id, 'content': msg.content}),
                    f"recovery-reconciled-score-{vr.score:.4f}",
                    abs(msg.target_timestamp - time.time()) / (365.25 * 86400),
                )
                result['accepted'] += 1
                self._stats['reconciled'] += 1
                self.ledger.record("recovery_reconciled", {
                    'msg_id': msg.id, 'block_hash': block_hash[:16],
                    'consistency_score': vr.score,
                })
                log.info("✅ Reconciliada: %s -> block %s", msg.id[:12], block_hash[:16])
            else:
                result['rejected'] += 1
                self._stats['rejected'] += 1
                paradox = vr.report.paradox_type if vr.report else None
                if paradox:
                    result['paradoxes'] += 1
                    log.warning("🚫 Paradoxo na reconciliação: %s (%s)", paradox, msg.id[:12])
                self.ledger.record("recovery_rejected", {
                    'msg_id': msg.id, 'reason': vr.shield_reason or paradox,
                    'score': vr.score,
                })
        return result

    def _connect_smtp(self):
        if self._smtp:
            return
        if self.config.dry_run:
            self._smtp = SimulatedSMTP()
            self._smtp.connect(self.config.smtp_host, self.config.smtp_port)
            if self.config.use_tls:
                self._smtp.starttls()
            self._smtp.login(self.config.email_address or "arkhe@localhost", "***")
            log.info("[SIM] SMTP conectado (modo simulação)")
        else:
            import smtplib
            import ssl
            self._smtp = smtplib.SMTP(self.config.smtp_host, self.config.smtp_port, timeout=30)
            if self.config.use_tls:
                self._smtp.starttls(context=ssl.create_default_context())
            self._smtp.login(self.config.email_address, self.config.app_password)
            log.info("SMTP conectado")

    def _connect_imap(self):
        if self._imap:
            return
        if self.config.dry_run:
            self._imap = SimulatedIMAP()
            self._imap.login(self.config.email_address or "arkhe@localhost", "***")
            for folder in [self.config.archive_folder, self.config.rejected_folder, self.config.sent_folder]:
                try:
                    self._imap.create(folder)
                except:
                    pass
            log.info("[SIM] IMAP conectado (modo simulação)")
        else:
            import imaplib
            self._imap = imaplib.IMAP4_SSL(self.config.imap_host, self.config.imap_port, timeout=self.config.imap_timeout)
            self._imap.login(self.config.email_address, self.config.app_password)
            for folder in [self.config.archive_folder, self.config.rejected_folder, self.config.sent_folder]:
                try:
                    self._imap.create(folder)
                except:
                    pass
            log.info("IMAP conectado")

    def status(self) -> Dict:
        with self._lock:
            db_count = self._db_conn.execute("SELECT COUNT(*) FROM recovery_queue").fetchone()[0]
            pending = self._db_conn.execute("SELECT COUNT(*) FROM recovery_queue WHERE status='pending'").fetchone()[0]
            return {
                'outbox_size': len(self._outbox),
                'db_total': db_count,
                'db_pending': pending,
                'processed_ids': len(self._processed_ids),
                **self._stats,
                'dry_run': self.config.dry_run,
            }

    def shutdown(self):
        self._running = False
        if self._smtp:
            try:
                self._smtp.quit()
            except:
                pass
        if self._imap:
            try:
                self._imap.logout()
            except:
                pass
        self._db_conn.close()
        log.info("Recovery Email Gateway encerrado.")

# ============================================================================
# INTEGRAÇÃO COM EXTRATEMPORAL CHANNEL (simulação de fallback)
# ============================================================================

class RetroRouter:
    """Roteador simulado que usa o RecoveryEmailGateway como fallback."""
    def __init__(self):
        self.ledger = AuditLedger("/tmp/arkhe_ledger_6046.db")
        self.chain = TemporalHashChain()
        self.validator = RetrocausalValidator(self.ledger)
        self.gateway: Optional[RecoveryEmailGateway] = None
        self._primary_fail_rate = 0.3  # 30% de falha no transporte primário

    def enable_recovery_email(self, config: EmailConfig):
        self.gateway = RecoveryEmailGateway(self.ledger, self.chain, self.validator, config)
        log.info("Recovery Email habilitado no roteador.")

    def send_message_with_fallback(self, msg: TemporalMessage) -> bool:
        # Simula falha do transporte primário
        if np.random.random() > self._primary_fail_rate:
            log.info("📡 Transporte primário: SUCESSO (%s)", msg.id[:12])
            msg.delivered = True
            self.ledger.record("primary_delivered", {'msg_id': msg.id})
            return True
        # Fallback para e-mail
        log.warning("📡 Transporte primário: FALHA (%s) -> fallback para e-mail", msg.id[:12])
        if self.gateway:
            vr = self.validator.validate(msg)
            self.gateway.enqueue(msg, vr.score, self.chain.head_hash)
            return True
        return False

# ============================================================================
# DEMONSTRAÇÃO
# ============================================================================

def run_demo():
    np.random.seed(42)
    log.info("╔══════════════════════════════════════════════════════════════╗")
    log.info("║     ARKHE Ω-TEMP v4.5.0 — SUBSTRATO 6046 DEMONSTRAÇÃO      ║")
    log.info("║          Recovery Email Transport (Fallback)               ║")
    log.info("╚══════════════════════════════════════════════════════════════╝")

    # Infraestrutura
    router = RetroRouter()
    config = EmailConfig(dry_run=True)
    router.enable_recovery_email(config)

    log.info("\n[1/5] Enviando 10 mensagens temporais (30%% falha no primário)...")
    messages = []
    for i in range(10):
        msg = TemporalMessage(
            id=hashlib.sha256(f"msg_{i}:{time.time()}".encode()).hexdigest()[:16],
            content=f"Mensagem temporal de teste #{i+1} para a colônia Europa.",
            source_timestamp=time.time(),
            target_timestamp=time.time() + np.random.uniform(-300, 300),
            sender_seal="ARKHE-OS",
            receiver_seal="AGI-EUROPA-01",
        )
        router.send_message_with_fallback(msg)
        messages.append(msg)

    log.info("\n[2/5] Status da fila de recovery antes do envio:")
    status = router.gateway.status()
    for k, v in status.items():
        log.info("   %s: %s", k, v)

    log.info("\n[3/5] Enviando fila de recovery via SMTP (simulado)...")
    router.gateway.send_retry_queue()

    log.info("\n[4/5] Simulando recepção IMAP e reconciliação...")
    # Criar mensagens simuladas no inbox IMAP
    simulated_emails = []
    for msg in messages[:5]:
        email_msg = EmailAdapter.to_email(msg, config, router.chain.head_hash, 1.0)
        simulated_emails.append(email_msg)
    router.gateway._imap = SimulatedIMAP(simulated_emails)
    received = router.gateway.poll_inbox()
    log.info("   %d mensagens recebidas do inbox simulado.", len(received))

    if received:
        result = router.gateway.reconcile(received)
        log.info("   Reconciliação: %d aceitas, %d rejeitadas, %d paradoxos",
                 result['accepted'], result['rejected'], result['paradoxes'])

    log.info("\n[5/5] Status final:")
    final_status = router.gateway.status()
    for k, v in final_status.items():
        log.info("   %s: %s", k, v)

    log.info("\n📊 Ledger: %d registros", router.ledger.count())
    log.info("📊 Cadeia temporal: %d blocos", router.chain.length)
    log.info("📊 Validador: %s", router.validator.__dict__)

    log.info("\n📜 Registros do Ledger:")
    for rec in router.ledger.get_records(limit=20):
        log.info("   [%s] %s @ %.0f", rec['hash'][:12], rec['type'], rec['timestamp'])

    router.gateway.shutdown()
    router.ledger.close()

    log.info("\n╔══════════════════════════════════════════════════════════════╗")
    log.info("║  SUBSTRATO 6046 — ATIVO                                      ║")
    log.info("║  O E-MAIL É O CAMINHO DA PACIÊNCIA.                          ║")
    log.info("╚══════════════════════════════════════════════════════════════╝")

# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(prog='arkhe_recovery_email', description='ARKHE Substrato 6046 — Recovery Email Transport')
    parser.add_argument('--version', action='version', version='%(prog)s 4.5.0')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--demo', action='store_true', help='Demonstração completa')
    mode.add_argument('--send-test', action='store_true', dest='send_test', help='Teste de envio simulado')
    mode.add_argument('--poll-test', action='store_true', dest='poll_test', help='Teste de polling simulado')
    mode.add_argument('--status', action='store_true', help='Status da fila')
    mode.add_argument('--ledger-verify', action='store_true', dest='ledger_verify', help='Verifica integridade do ledger')
    parser.add_argument('--log-level', type=str, default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'])
    parser.add_argument('--dry-run', action='store_true', default=True, help='Modo simulação (sem servidores reais)')
    parser.add_argument('--smtp-host', type=str, default='smtp.gmail.com')
    parser.add_argument('--email', type=str, default='')
    parser.add_argument('--password', type=str, default='')
    args = parser.parse_args()

    setup_logging(args.log_level)

    if args.demo:
        run_demo()
    elif args.send_test:
        ledger = AuditLedger()
        chain = TemporalHashChain()
        validator = RetrocausalValidator(ledger)
        config = EmailConfig(dry_run=True, smtp_host=args.smtp_host, email_address=args.email, app_password=args.password)
        gateway = RecoveryEmailGateway(ledger, chain, validator, config)
        msg = TemporalMessage(
            id=hashlib.sha256(str(time.time()).encode()).hexdigest()[:16],
            content="Teste de mensagem de recuperação ARKHE.",
            source_timestamp=time.time(), target_timestamp=time.time() + 120,
            sender_seal="ARKHE-OS", receiver_seal="AGI-TEST-01",
        )
        gateway.enqueue(msg, 1.0, chain.head_hash)
        gateway.send_retry_queue()
        log.info("Status: %s", gateway.status())
        gateway.shutdown()
        ledger.close()
    elif args.poll_test:
        ledger = AuditLedger()
        chain = TemporalHashChain()
        validator = RetrocausalValidator(ledger)
        config = EmailConfig(dry_run=True)
        gateway = RecoveryEmailGateway(ledger, chain, validator, config)
        # Criar e-mail simulado
        msg = TemporalMessage(
            id="SIMULATED001", content="Mensagem simulada de inbox.",
            source_timestamp=time.time() - 60, target_timestamp=time.time() + 60,
            sender_seal="AGI-REMOTE-01", receiver_seal="ARKHE-OS",
        )
        sim_email = EmailAdapter.to_email(msg, config, chain.head_hash, 1.0)
        gateway._imap = SimulatedIMAP([sim_email])
        received = gateway.poll_inbox()
        if received:
            result = gateway.reconcile(received)
            log.info("Reconciliação: %s", result)
        gateway.shutdown()
        ledger.close()
    elif args.status:
        ledger = AuditLedger()
        chain = TemporalHashChain()
        validator = RetrocausalValidator(ledger)
        config = EmailConfig(dry_run=args.dry_run)
        gateway = RecoveryEmailGateway(ledger, chain, validator, config)
        print(json.dumps(gateway.status(), indent=2))
        gateway.shutdown()
        ledger.close()
    elif args.ledger_verify:
        ledger = AuditLedger()
        ok, errors = ledger.verify_integrity()
        print(f"Integridade: {'VÁLIDA' if ok else 'CORROMPIDA'}")
        for e in errors:
            print(f"  Erro: {e}")
        ledger.close()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
'''

prompt_text = prompt_text.replace("def head_hash(self) -> str:", "@property\n    def head_hash(self) -> str:")
prompt_text = prompt_text.replace("chain.head_hash()", "chain.head_hash")
# also fix any `router.chain.head_hash()` just in case
prompt_text = prompt_text.replace("router.chain.head_hash()", "router.chain.head_hash")

with open("recovery_email_gateway.py", "w", encoding="utf-8") as f:
    f.write(prompt_text)
