# proactive_notifications.py — Motor de notificações proativas respeitosas

import asyncio
import json
import hashlib
import logging
import time
from typing import Dict, List, Optional, Literal, Callable
from dataclasses import dataclass, field
from enum import Enum, auto
from datetime import datetime

from audit_logger import AuditLogger, AuditRecord, DecisionType
from explainability_engine import ExplainabilityEngine, ExplanationPersona
from dynamic_consent_protocol import DynamicConsentProtocol, PrivacyProfile

class NotificationChannel(Enum):
    EMAIL = auto()
    SMS = auto()
    PUSH = auto()
    IN_APP = auto()
    NONE = auto()

class NotificationPriority(Enum):
    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()
    CRITICAL = auto()

@dataclass
class NotificationMessage:
    citizen_id: str
    decision_id: str
    channel: NotificationChannel
    priority: NotificationPriority
    subject: str
    body_text: str
    content_hash: str
    generated_at: float

class ProactiveNotificationEngine:
    """
    Motor de notificações proativas que respeita perfis de consentimento.
    """

    def __init__(self, consent_protocol: DynamicConsentProtocol, audit_logger: AuditLogger):
        self.consent = consent_protocol
        self.audit = audit_logger
        self._channel_handlers: Dict[NotificationChannel, Callable] = {}
        self.delivery_log: List[NotificationMessage] = []

    def register_channel_handler(self, channel: NotificationChannel, handler: Callable):
        self._channel_handlers[channel] = handler

    async def process_decision(self, record: AuditRecord, citizen_id: str):
        """Processa uma decisão e notifica o cidadão se permitido."""

        # 1. Verifica consentimento (usando o protocolo de consentimento dinâmico)
        # Para este mock, assumimos que o cidadão deu consentimento se valid_action for True
        if not self.consent.validate_action(citizen_id, "notifications"):
            logging.info(f"[NOTIFY] Notificação negada por falta de consentimento para {citizen_id}")
            return

        # 2. Determina Persona adaptada
        persona = self.consent.get_adapted_persona(citizen_id)

        # 3. Gera mensagem (simulado)
        subject = f"Ação da Catedral: {record.decision_type.name}"
        body = f"Olá, a Catedral tomou uma decisão que afeta você. Tipo: {record.decision_type.name}. " \
               f"Confiança: {record.context.get('confidence', 'N/A')}"

        content_hash = hashlib.sha256(body.encode()).hexdigest()

        message = NotificationMessage(
            citizen_id=citizen_id,
            decision_id=record.decision_id,
            channel=NotificationChannel.IN_APP, # Padrão
            priority=NotificationPriority.MEDIUM,
            subject=subject,
            body_text=body,
            content_hash=content_hash,
            generated_at=time.time()
        )

        # 4. Envia via handler
        handler = self._channel_handlers.get(message.channel)
        if handler:
            success = await handler(message)
            if success:
                self.delivery_log.append(message)
                # Registra no Audit Ledger
                await self.audit.log_decision(
                    DecisionType.MANUAL_OVERRIDE,
                    context={"citizen_id": citizen_id, "notification_id": content_hash[:8]},
                    explainability={"reason": "Notificação proativa enviada"},
                    compliance_tags=["FS-55", "notification_sent"],
                    expected_impact={"benefit": 1.0, "risk": 0.0}
                )
                return True
        return False
