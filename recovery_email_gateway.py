#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
recovery_email_gateway.py — Substrato 6046: Email Recovery Path

Transporte de e‑mail como fallback para a rede retrocausal ARKHE.
Permite store‑and‑forward de mensagens temporais validadas e reconciliação
posterior com o ledger quando o meio de comunicação primário é restabelecido.

Integra‑se com:
  - RetroRouter (roteamento)
  - ConsistencyOracle (validação)
  - TemporalHashChain (registro de reconciliação)

Uso:
  gateway = RecoveryEmailGateway(router, config)
  gateway.start()
  gateway.send_retry_queue()
  gateway.poll_and_reconcile()
"""

import json
import hashlib
import logging
import math
import os
import re
import smtplib
import ssl
import threading
import time
import uuid
from collections import deque
from dataclasses import dataclass, field, asdict
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders, message as email_message
from email.utils import formatdate, parsedate_to_datetime
from pathlib import Path
from queue import Queue, PriorityQueue
from typing import Any, Callable, Dict, Deque, List, Optional, Tuple, Union

import imaplib
import sqlite3

# Importações internas do ARKHE (ajuste conforme seu path)
from temporal_network import (
    TemporalMessage, ConsistencyReport, TemporalHashChain,
    RetrocausalValidator, CausalShield, TemporalConsistencyOracle,
    QUANTUM_NEGATIVE_WINDOW_SECONDS, DEFAULT_WINDOW_SECONDS,
    VERSION,
)

log = logging.getLogger("arkhe.recovery_mail")

# ============================================================================
# CONFIGURAÇÃO DE E‑MAIL
# ============================================================================
@dataclass
class EmailConfig:
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    imap_host: str = "imap.gmail.com"
    imap_port: int = 993
    email_address: str = ""
    app_password: str = ""          # senha de app, não a senha principal
    use_tls: bool = True
    max_retries: int = 5
    retry_backoff_base: float = 2.0  # exponential backoff
    imap_timeout: int = 30
    search_folder: str = "INBOX"
    sent_folder: str = "[ARKHE]/Sent"
    archive_folder: str = "[ARKHE]/Archive"
    rejected_folder: str = "[ARKHE]/Rejected"
    recovery_queue_db: str = "recovery_queue.sqlite"

    def validate(self) -> bool:
        return bool(self.email_address and self.app_password)

# ============================================================================
# EMAIL ADAPTER — Conversão TemporalMessage ↔ RFC 5322
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
                 chain_hash: str = "", score: float = 1.0,
                 key_id: Optional[str] = None) -> MIMEMultipart:
        email_msg = MIMEMultipart('mixed')
        email_msg['From'] = config.email_address
        email_msg['To'] = msg.receiver_seal
        email_msg['Subject'] = f"[ARKHE-RECOVERY] {msg.content[:50]}..."
        email_msg['Date'] = formatdate(time.time(), usegmt=True)
        email_msg['Message-ID'] = f"<{msg.id}@arkhe.recovery>"

        headers = {
            'version': VERSION,
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
        # Assinatura HMAC-SHA3-256 (simplificada)
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
            f"Modo: RECOVERY (transportado por e‑mail)\n"
            f"{'═'*40}\n\n"
            f"{msg.content}"
        )
        email_msg.attach(MIMEText(body_text, 'plain', 'utf-8'))

        # Payload binário (opcional: compactar com zlib)
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
    def from_email(cls, email_msg: email_message.Message) -> Optional[Dict]:
        try:
            headers = {}
            for key, header_name in cls.HEADER_MAP.items():
                value = email_msg.get(header_name, '')
                if value: headers[key] = value.strip()
            required = ['msg_id', 'target_timestamp', 'source_timestamp', 'sender_seal', 'receiver_seal']
            if not all(k in headers for k in required): return None
            body = ""
            if email_msg.is_multipart():
                for part in email_msg.walk():
                    if part.get_content_type() == 'text/plain' and 'attachment' not in str(part.get('Content-Disposition')):
                        body = part.get_payload(decode=True).decode('utf-8', errors='replace')
            else:
                body = email_msg.get_payload(decode=True).decode('utf-8', errors='replace')
            content = body.split('\n\n', 1)[-1] if '\n\n' in body else body
            return { **headers, 'content': content,
                     'encrypted': headers.get('encrypted','false').lower() == 'true',
                     'source_timestamp': float(headers['source_timestamp']),
                     'target_timestamp': float(headers['target_timestamp']),
                     'consistency_score': float(headers.get('consistency_score', '0')),
                     'recovery_mode': headers.get('recovery_mode', 'false') == 'true' }
        except Exception as e:
            log.error(f"Erro ao parsear e‑mail ARKHE: {e}")
            return None

# ============================================================================
# RECOVERY EMAIL GATEWAY
# ============================================================================
class RecoveryEmailGateway:
    def __init__(self, router, config: EmailConfig):
        self.router = router
        self.config = config
        self._smtp: Optional[smtplib.SMTP] = None
        self._imap: Optional[imaplib.IMAP4_SSL] = None
        self._outbox: Deque[Tuple[TemporalMessage, float, str]] = deque()  # (msg, score, chain_hash)
        self._inbox_pending: Deque[Dict] = deque()
        self._processed_ids = set()
        self._stats = {'sent': 0, 'received': 0, 'reconciled': 0, 'rejected': 0}
        self._running = False
        self._lock = threading.Lock()
        self._db_conn = sqlite3.connect(self.config.recovery_queue_db)
        self._init_db()

    def _init_db(self):
        with self._db_conn:
            self._db_conn.execute("""
                CREATE TABLE IF NOT EXISTS recovery_queue (
                    id TEXT PRIMARY KEY, msg_json TEXT,
                    queued_at REAL, retries INTEGER DEFAULT 0, last_retry REAL, status TEXT DEFAULT 'pending'
                )
            """)

    # ---------- Métodos de Envio ----------
    def enqueue(self, msg: TemporalMessage, score: float = 1.0, chain_hash: str = ""):
        # Persistir na fila
        with self._db_conn:
            self._db_conn.execute(
                "INSERT OR REPLACE INTO recovery_queue (id, msg_json, queued_at) VALUES (?,?,?)",
                (msg.id, json.dumps(asdict(msg)), time.time())
            )
        with self._lock:
            self._outbox.append((msg, score, chain_hash))

    def send_retry_queue(self):
        """Envia todos os itens pendentes da fila de recuperação."""
        while True:
            if not self._outbox: break
            with self._lock:
                msg, score, chain_hash = self._outbox.popleft()
            try:
                self._send_one(msg, score, chain_hash)
                self._stats['sent'] += 1
            except Exception as e:
                log.warning(f"Falha ao enviar {msg.id[:12]}: {e}. Reenfileirando...")
                self._outbox.appendleft((msg, score, chain_hash))
                time.sleep(self.config.retry_backoff_base)   # backoff e tenta de novo
                break

    def _send_one(self, msg: TemporalMessage, score: float, chain_hash: str):
        self._connect_smtp()
        email_msg = EmailAdapter.to_email(msg, self.config, chain_hash, score)
        for attempt in range(self.config.max_retries):
            try:
                self._smtp.send_message(email_msg, from_addr=self.config.email_address, to_addrs=[msg.receiver_seal])
                log.info(f"📧 Recovery email sent: {msg.id[:12]} (attempt {attempt+1})")
                return
            except smtplib.SMTPException as e:
                log.warning(f"SMTP attempt {attempt+1} failed: {e}")
                time.sleep(self.config.retry_backoff_base ** attempt)
        raise smtplib.SMTPException("Max retries exceeded")

    # ---------- Métodos de Recepção ----------
    def poll_inbox(self) -> List[Dict]:
        """Varre a caixa de entrada IMAP em busca de mensagens de recuperação ARKHE."""
        self._connect_imap()
        detected = []
        self._imap.select(self.config.search_folder)
        status, msgnums = self._imap.search(None, f'(SUBJECT "[ARKHE-RECOVERY]")')
        if status != 'OK': return detected
        ids = msgnums[0].split()
        for num in ids[-20:]:  # processa no máximo 20 por ciclo
            try:
                status, raw = self._imap.fetch(num, '(RFC822)')
                if status != 'OK': continue
                email_msg = email_message.message_from_bytes(raw[0][1])
                meta = EmailAdapter.from_email(email_msg)
                if not meta or meta['msg_id'] in self._processed_ids: continue
                self._processed_ids.add(meta['msg_id'])
                detected.append(meta)
                # Move para Archive após processamento
                self._imap.copy(num, self.config.archive_folder)
                self._imap.store(num, '+FLAGS', '\\Deleted')
            except Exception as e:
                log.error(f"Erro ao processar e‑mail {num}: {e}")
        self._imap.expunge()
        return detected

    def reconcile(self, messages: List[Dict]) -> Dict:
        """
        Reconcilia mensagens recebidas com o ledger temporal.
        Reaplica ConsistencyOracle, insere na cadeia e atualiza estatísticas.
        """
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
            # Revalidar com o Oracle (pode ter havido mudanças no ledger durante a desconexão)
            validator = self.router.validator if hasattr(self.router, 'validator') else RetrocausalValidator(self.router.ledger)
            vr = validator.validate(msg)
            if vr.accepted:
                # Inserir na TemporalHashChain local
                self.router.chain().insert_retrocausal(
                    msg.target_timestamp,
                    json.dumps({'msg_id': msg.id, 'content': msg.content}),
                    f"recovery-reconciled-score-{vr.score:.4f}",
                    abs(msg.target_timestamp - time.time()) / (365.25*86400)
                )
                result['accepted'] += 1
                self._stats['reconciled'] += 1
            else:
                result['rejected'] += 1
                if vr.report and vr.report.paradox_type:
                    result['paradoxes'] += 1
                    log.warning(f"Paradox detected during recovery reconciliation: {vr.report.paradox_type}")
                self._stats['rejected'] += 1
        return result

    # ---------- Conexões SMTP/IMAP ----------
    def _connect_smtp(self):
        if self._smtp: return
        try:
            self._smtp = smtplib.SMTP(self.config.smtp_host, self.config.smtp_port, timeout=30)
            if self.config.use_tls:
                self._smtp.starttls(context=ssl.create_default_context())
            self._smtp.login(self.config.email_address, self.config.app_password)
            log.info("SMTP conectado para recovery")
        except Exception as e:
            log.error(f"Falha SMTP: {e}")
            self._smtp = None
            raise

    def _connect_imap(self):
        if self._imap: return
        try:
            self._imap = imaplib.IMAP4_SSL(self.config.imap_host, self.config.imap_port, timeout=self.config.imap_timeout)
            self._imap.login(self.config.email_address, self.config.app_password)
            for folder in [self.config.archive_folder, self.config.rejected_folder, self.config.sent_folder]:
                try: self._imap.create(folder)
                except: pass
            log.info("IMAP conectado para recovery")
        except Exception as e:
            log.error(f"Falha IMAP: {e}")
            self._imap = None
            raise

    # ---------- API de Status ----------
    def status(self) -> Dict:
        with self._lock:
            return {
                'outbox_size': len(self._outbox),
                'processed_count': len(self._processed_ids),
                **self._stats,
                'smtp_connected': self._smtp is not None,
                'imap_connected': self._imap is not None,
            }

    def shutdown(self):
        self._running = False
        if self._smtp: self._smtp.quit()
        if self._imap: self._imap.logout()
        self._db_conn.close()
