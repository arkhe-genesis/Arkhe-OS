#!/usr/bin/env python3
"""
siem_integration.py — Integração nativa do ARKHE OS com SIEM corporativo.
Unifica logs de HSM, rotação de chaves, detecção de anomalias e compliance
em formato CEF/Syslog para Splunk, ELK, QRadar, Azure Sentinel e outros.
"""

import os
import json
import time
import socket
import logging
import threading
import queue
from pathlib import Path
from typing import Dict, List, Optional, Union
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from datetime import datetime, timezone

# ============================================================================
# Formatos de evento suportados
# ============================================================================
class SIEMFormat(Enum):
    CEF = "cef"              # Common Event Format (ArcSight)
    LEEF = "leef"            # Log Event Extended Format (QRadar)
    JSON = "json"            # JSON estruturado (Splunk HEC, ELK)
    SYSLOG_RFC5424 = "syslog" # Syslog padrão

class SIEMProtocol(Enum):
    UDP = "udp"
    TCP = "tcp"
    HTTP = "http"
    KAFKA = "kafka"

# ============================================================================
# Mapeamento de eventos ARKHE → Categorias SIEM
# ============================================================================
ARKHE_SIEM_CATEGORIES = {
    "integrity_check": {
        "signature_id": "ARKH-INT-001",
        "severity": "Medium",
        "category": "Integrity Verification"
    },
    "key_rotation": {
        "signature_id": "ARKH-KEY-001",
        "severity": "High",
        "category": "Key Management"
    },
    "anomaly_detected": {
        "signature_id": "ARKH-ANO-001",
        "severity": "Critical",
        "category": "Anomaly Detection"
    },
    "compliance_report": {
        "signature_id": "ARKH-CMP-001",
        "severity": "Low",
        "category": "Compliance"
    }
}

@dataclass
class SIEMConfig:
    """Configuração de integração SIEM."""
    enabled: bool = True
    default_format: SIEMFormat = SIEMFormat.CEF
    endpoints: List[Dict] = field(default_factory=lambda: [{
        "protocol": SIEMProtocol.UDP,
        "host": "siem.internal",
        "port": 514,
        "format": SIEMFormat.CEF
    }])
    facility: str = "local0"
    arkhe_version: str = "∞.Ω.∇.170"
    batch_size: int = 100
    send_interval_sec: float = 1.0
    queue_maxsize: int = 10000
    retry_attempts: int = 3
    tls_enabled: bool = False
    tls_cert_path: Optional[str] = None
    tls_key_path: Optional[str] = None

class SIEMFormatter:
    """Formatador de eventos para padrões SIEM."""

    @staticmethod
    def to_cef(event: Dict) -> str:
        """Converte evento para Common Event Format (CEF)."""
        vendor = "ARKHE"
        product = "ArkheOS"
        version = event.get("version", "1.0")
        signature_id = event.get("signature_id", "ARKH-GEN-000")
        name = event.get("name", "Unknown Event")
        severity = event.get("severity", "Medium")

        # Cabeçalho CEF
        header = f"CEF:0|{vendor}|{product}|{version}|{signature_id}|{name}|{severity}|"

        # Extensões CEF (pares chave=valor)
        extensions = {
            "start": datetime.fromtimestamp(event["timestamp"], tz=timezone.utc).strftime("%b %d %Y %H:%M:%S UTC"),
            "src": event.get("source_ip", "127.0.0.1"),
            "suser": event.get("username", "arkhe_system"),
            "outcome": "success" if event.get("success", True) else "failure",
            "reason": event.get("reason", ""),
            "requestContext": json.dumps(event.get("context", {}))[:1024],
            "cs1Label": "KeyID",
            "cs1": event.get("key_id", ""),
            "cs2Label": "EventID",
            "cs2": event.get("event_id", ""),
            "cs3Label": "Framework",
            "cs3": event.get("framework", ""),
            "cn1Label": "AnomalyCount",
            "cn1": str(event.get("anomaly_count", 0)),
            "cn2Label": "ComplianceRate",
            "cn2": str(event.get("compliance_rate", 0))
        }

        # Build CEF extension string
        extension_str = " ".join(f"{k}={v}" for k, v in extensions.items() if v)

        return header + extension_str

    @staticmethod
    def to_leef(event: Dict) -> str:
        """Converte evento para LEEF (QRadar)."""
        vendor = "ARKHE"
        product = "ArkheOS"
        version = event.get("version", "1.0")
        event_id = event.get("event_id", "0")

        # Cabeçalho LEEF
        header = f"LEEF:2.0|{vendor}|{product}|{version}|{event_id}|"

        # Atributos LEEF
        attributes = {
            "devTime": datetime.fromtimestamp(event["timestamp"], tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "sev": str({"Critical": 10, "High": 8, "Medium": 5, "Low": 3}.get(event.get("severity", "Medium"), 5)),
            "cat": event.get("category", "Unknown"),
            "src": event.get("source_ip", "127.0.0.1"),
            "usrName": event.get("username", "arkhe_system"),
            "keyId": event.get("key_id", ""),
            "eventId": event.get("event_id", ""),
            "msg": event.get("description", ""),
            "url": event.get("url", ""),
            "anomalyCount": str(event.get("anomaly_count", 0)),
            "complianceRate": str(event.get("compliance_rate", 0))
        }

        # Build tab-separated attributes
        attr_str = "\t".join(f"{k}={v}" for k, v in attributes.items() if v)

        return header + attr_str

    @staticmethod
    def to_json(event: Dict) -> str:
        """Converte evento para JSON estruturado (Splunk HEC, ELK)."""
        json_event = {
            "timestamp": datetime.fromtimestamp(event["timestamp"], tz=timezone.utc).isoformat(),
            "source": "ArkheOS",
            "sourcetype": event.get("category", "unknown"),
            "host": socket.gethostname(),
            "index": "arkhe_security",
            "event": {
                "id": event.get("event_id", ""),
                "name": event.get("name", ""),
                "severity": event.get("severity", ""),
                "category": event.get("category", ""),
                "description": event.get("description", ""),
                "outcome": "success" if event.get("success", True) else "failure",
                "source_ip": event.get("source_ip", ""),
                "key_id": event.get("key_id", ""),
                "username": event.get("username", ""),
                "framework": event.get("framework", ""),
                "anomaly_count": event.get("anomaly_count", 0),
                "compliance_rate": event.get("compliance_rate", 0),
                "context": event.get("context", {}),
                "raw": event.get("raw", "")
            }
        }
        return json.dumps(json_event, default=str)

    @staticmethod
    def to_syslog(event: Dict) -> str:
        """Converte evento para Syslog RFC 5424."""
        priority = 134  # local0.info
        version = 1
        timestamp = datetime.fromtimestamp(event["timestamp"], tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        hostname = socket.gethostname()
        app_name = "ArkheOS"
        procid = str(os.getpid())
        msgid = event.get("signature_id", "ARKH-GEN-000")

        # Structured data
        structured_data = f'[arkhe@48577 eventId="{event.get("event_id", "")}" severity="{event.get("severity", "")}" keyId="{event.get("key_id", "")}"]'

        # Message
        msg = event.get("description", "No description")

        return f"<{priority}>{version} {timestamp} {hostname} {app_name} {procid} {msgid} {structured_data} {msg}"

class SIEMEndpoint:
    """Endpoint de envio para SIEM."""

    def __init__(self, config: Dict, formatter: SIEMFormatter):
        self.config = config
        self.formatter = formatter
        self.protocol = config["protocol"]
        self.host = config["host"]
        self.port = config["port"]
        self.format = config.get("format", SIEMFormat.CEF)
        self._socket = None
        self._session = None

    def connect(self) -> bool:
        """Estabelece conexão com o endpoint SIEM."""
        try:
            if self.protocol in (SIEMProtocol.UDP, SIEMProtocol.TCP):
                sock_type = socket.SOCK_DGRAM if self.protocol == SIEMProtocol.UDP else socket.SOCK_STREAM
                self._socket = socket.socket(socket.AF_INET, sock_type)
                if self.protocol == SIEMProtocol.TCP:
                    self._socket.connect((self.host, self.port))
                return True
            elif self.protocol == SIEMProtocol.HTTP:
                import requests
                self._session = requests.Session()
                self._session.headers.update({
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.config.get('token', '')}"
                })
                return True
        except Exception as e:
            logging.error(f"Failed to connect to SIEM {self.host}:{self.port}: {e}")
            return False

    def send(self, event: Dict) -> bool:
        """Envia um evento formatado para o SIEM."""
        try:
            # Formatar evento conforme o formato configurado
            format_methods = {
                SIEMFormat.CEF: self.formatter.to_cef,
                SIEMFormat.LEEF: self.formatter.to_leef,
                SIEMFormat.JSON: self.formatter.to_json,
                SIEMFormat.SYSLOG_RFC5424: self.formatter.to_syslog
            }

            formatted = format_methods[self.format](event)

            if isinstance(formatted, str):
                formatted = formatted.encode('utf-8')

            # Enviar via protocolo apropriado
            if self.protocol == SIEMProtocol.UDP:
                self._socket.sendto(formatted, (self.host, self.port))
            elif self.protocol == SIEMProtocol.TCP:
                self._socket.send(formatted)
            elif self.protocol == SIEMProtocol.HTTP:
                import requests
                response = self._session.post(
                    f"https://{self.host}:{self.port}/services/collector/event",
                    json=json.loads(formatted) if self.format == SIEMFormat.JSON else {"event": formatted.decode('utf-8')},
                    timeout=5
                )
                return response.status_code == 200

            return True
        except Exception as e:
            logging.error(f"Failed to send SIEM event: {e}")
            return False

    def close(self):
        """Fecha conexão com o endpoint."""
        if self._socket:
            self._socket.close()
        if self._session:
            self._session.close()

class UnifiedSIEMIntegration:
    """
    Integração unificada com SIEM corporativo para monitoramento de segurança.
    Coleta eventos de todos os módulos ARKHE (integridade, HSM, rotação de chaves,
    detecção de anomalias, compliance) e os envia formatados para o SIEM.
    """

    def __init__(self, config: SIEMConfig = None):
        self.config = config or SIEMConfig()
        self.formatter = SIEMFormatter()
        self.endpoints = []
        self.event_queue = queue.Queue(maxsize=self.config.queue_maxsize)
        self._sender_thread = None
        self._running = False
        self._stats = {
            "events_queued": 0,
            "events_sent": 0,
            "events_dropped": 0,
            "last_send_time": None
        }

        # Inicializar endpoints
        if self.config.enabled:
            for ep_config in self.config.endpoints:
                endpoint = SIEMEndpoint(ep_config, self.formatter)
                if endpoint.connect():
                    self.endpoints.append(endpoint)

            if self.endpoints:
                logging.info(f"SIEM integration initialized with {len(self.endpoints)} endpoints")

    def start(self):
        """Inicia o envio assíncrono de eventos."""
        if self._running or not self.endpoints:
            return

        self._running = True
        self._sender_thread = threading.Thread(target=self._send_loop, daemon=True)
        self._sender_thread.start()
        logging.info("SIEM sender thread started")

    def stop(self):
        """Para o envio de eventos."""
        self._running = False
        if self._sender_thread:
            self._sender_thread.join(timeout=5)
        for endpoint in self.endpoints:
            endpoint.close()

    def send_event(self, event_type: str, event_data: Dict):
        """
        Enfileira um evento de segurança para envio ao SIEM.

        Args:
            event_type: Tipo do evento (integrity_check, key_rotation, etc.)
            event_data: Dados específicos do evento
        """
        if not self.endpoints:
            return

        # Enriquecer evento com metadados SIEM
        category_info = ARKHE_SIEM_CATEGORIES.get(event_type, {})

        siem_event = {
            "event_id": event_data.get("event_id", ""),
            "name": event_type,
            "signature_id": category_info.get("signature_id", "ARKH-GEN-000"),
            "severity": category_info.get("severity", "Medium"),
            "category": category_info.get("category", "Unknown"),
            "timestamp": event_data.get("timestamp", time.time()),
            "source_ip": event_data.get("source_ip", ""),
            "username": event_data.get("username", os.environ.get("USER", "arkhe_system")),
            "key_id": event_data.get("key_id", ""),
            "description": event_data.get("description", ""),
            "success": event_data.get("success", True),
            "reason": event_data.get("reason", ""),
            "framework": event_data.get("framework", ""),
            "anomaly_count": event_data.get("anomaly_count", 0),
            "compliance_rate": event_data.get("compliance_rate", 0),
            "context": event_data.get("context", {}),
            "version": self.config.arkhe_version
        }

        try:
            self.event_queue.put_nowait(siem_event)
            self._stats["events_queued"] += 1
        except queue.Full:
            self._stats["events_dropped"] += 1
            logging.error("SIEM event queue full - dropping event")

    def _send_loop(self):
        """Loop principal de envio de eventos."""
        batch = []
        last_send = time.time()

        while self._running:
            try:
                # Coletar eventos da fila
                try:
                    for _ in range(self.config.batch_size):
                        event = self.event_queue.get_nowait()
                        batch.append(event)
                except queue.Empty:
                    pass

                # Enviar batch se tamanho ou intervalo atingido
                if batch and (len(batch) >= self.config.batch_size or
                             time.time() - last_send >= self.config.send_interval_sec):
                    self._send_batch(batch)
                    batch = []
                    last_send = time.time()
                    self._stats["last_send_time"] = time.time()

                time.sleep(0.1)
            except Exception as e:
                logging.error(f"SIEM send loop error: {e}")

    def _send_batch(self, events: List[Dict]):
        """Envia lote de eventos para todos os endpoints."""
        for endpoint in self.endpoints:
            for event in events:
                success = False
                for attempt in range(self.config.retry_attempts):
                    if endpoint.send(event):
                        success = True
                        break
                    time.sleep(0.5)

                if success:
                    self._stats["events_sent"] += 1
                else:
                    self._stats["events_dropped"] += 1

    def get_stats(self) -> Dict:
        """Retorna estatísticas de envio para o SIEM."""
        return {
            **self._stats,
            "queue_size": self.event_queue.qsize(),
            "endpoints_connected": len(self.endpoints),
            "formats_used": list(set(ep.format.name for ep in self.endpoints)) if self.endpoints else []
        }

# ============================================================================
# Fábrica de eventos para módulos ARKHE → SIEM
# ============================================================================
class ARKHESecurityEvents:
    """Interface padronizada para enviar eventos de segurança ao SIEM."""

    def __init__(self, siem: UnifiedSIEMIntegration = None):
        self.siem = siem or UnifiedSIEMIntegration()

    def on_integrity_check(self, success: bool, key_id: str = "", details: str = "", **kwargs):
        """Evento de verificação de integridade."""
        self.siem.send_event("integrity_check", {
            "success": success,
            "key_id": key_id,
            "description": f"Integrity check {'passed' if success else 'failed'}: {details}",
            "timestamp": time.time(),
            **kwargs
        })

    def on_key_rotation(self, old_key_id: str, new_key_id: str, approved_by: str = "", **kwargs):
        """Evento de rotação de chave."""
        self.siem.send_event("key_rotation", {
            "event_id": f"ROT-{int(time.time())}",
            "success": True,
            "key_id": new_key_id,
            "description": f"Key rotated: {old_key_id} -> {new_key_id}",
            "context": {"old_key": old_key_id, "approved_by": approved_by},
            "timestamp": time.time(),
            **kwargs
        })

    def on_anomaly_detected(self, anomaly_type: str, severity: str, key_id: str, description: str, **kwargs):
        """Evento de anomalia detectada."""
        self.siem.send_event("anomaly_detected", {
            "event_id": f"ANO-{int(time.time())}",
            "success": False,
            "key_id": key_id,
            "severity": severity,
            "description": description,
            "context": {"anomaly_type": anomaly_type, "auto_mitigated": kwargs.get("auto_mitigated", False)},
            "timestamp": time.time(),
            **kwargs
        })

    def on_compliance_report(self, framework: str, compliance_rate: float, critical_gaps: int, **kwargs):
        """Evento de relatório de compliance."""
        self.siem.send_event("compliance_report", {
            "event_id": f"CMP-{int(time.time())}",
            "success": critical_gaps == 0,
            "framework": framework,
            "compliance_rate": compliance_rate,
            "description": f"Compliance report for {framework}: {compliance_rate:.0%} compliant",
            "anomaly_count": critical_gaps,
            "timestamp": time.time(),
            **kwargs
        })

# ============================================================================
# Integração automática via __init__.py
# ============================================================================
def get_siem_integration(config_path: Optional[str] = None) -> UnifiedSIEMIntegration:
    """
    Retorna instância do SIEM integration configurada.

    Args:
        config_path: Caminho para arquivo JSON de configuração
    """
    if config_path and Path(config_path).exists():
        with open(config_path, 'r') as f:
            config_data = json.load(f)

            # Converter enums
            if "default_format" in config_data:
                config_data["default_format"] = SIEMFormat[config_data["default_format"].upper()]

            for ep in config_data.get("endpoints", []):
                if "protocol" in ep:
                    ep["protocol"] = SIEMProtocol[ep["protocol"].upper()]
                if "format" in ep:
                    ep["format"] = SIEMFormat[ep["format"].upper()]

        config = SIEMConfig(**config_data)
    else:
        # Default SIEM disabled configuration if not explicitly provided
        config = SIEMConfig(enabled=False)

    return UnifiedSIEMIntegration(config)

# ============================================================================
# Exemplo de uso rápido
# ============================================================================
if __name__ == "__main__":
    # Configuração de exemplo
    config = SIEMConfig(
        enabled=True,
        default_format=SIEMFormat.CEF,
        endpoints=[
            {
                "protocol": SIEMProtocol.UDP,
                "host": "localhost",
                "port": 514,
                "format": SIEMFormat.CEF
            }
        ]
    )

    # Iniciar integração
    siem = UnifiedSIEMIntegration(config)
    events = ARKHESecurityEvents(siem)
    siem.start()

    # Simular eventos de segurança
    events.on_integrity_check(success=True, key_id="package_signing_01")
    events.on_key_rotation(old_key_id="old_20260501", new_key_id="new_20260505", approved_by="multisig_3of5")
    events.on_anomaly_detected("BRUTE_FORCE_ATTEMPT", "High", "package_signing_01", "3 failures in 60 seconds")
    events.on_compliance_report("nist_800-57", 0.95, 0)

    # Aguardar envio
    time.sleep(2)
    print("📊 SIEM Stats:", siem.get_stats())
    siem.stop()
