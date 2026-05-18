#!/usr/bin/env python3
"""
ARKHE OS Substrate 250: SIEM Event Forwarding Engine
Canon: ∞.Ω.∇+++.250.siem_integration

Forwarding de eventos do Windows Event Log para Splunk HEC e QRadar Syslog
com schema canônico ARKHE-CEF, buffering, retry e ancoragem na TemporalChain.
"""

import asyncio
import hashlib
import json
import logging
import ssl
import time
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import aiohttp

try:
    import win32evtlog  # Windows Event Log API
except ImportError:
    win32evtlog = None

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)-8s | %(message)s')
logger = logging.getLogger(__name__)

# =============================================================================
# TIPOS CANÔNICOS DE EVENTOS SIEM
# =============================================================================

class SIEMTarget(Enum):
    """Destinos SIEM suportados."""
    SPLUNK_HEC = "splunk_hec"
    QRADAR_SYSLOG = "qradar_syslog"
    BOTH = "both"

class EventSeverity(Enum):
    """Severidade de eventos mapeada para SIEM."""
    UNKNOWN = 0
    INFORMATIONAL = 3
    LOW = 4
    MEDIUM = 5
    HIGH = 6
    CRITICAL = 7

@dataclass
class ArkheEvent:
    """Representação canônica de um evento ARKHE para SIEM."""
    event_id: int                    # Windows EventId (3001-3099)
    event_name: str                  # Nome canônico (ex: "RegistryValueModified")
    severity: EventSeverity
    timestamp: float                 # Unix timestamp
    registry_path: Optional[str]     # Caminho no Registry (se aplicável)
    value_name: Optional[str]        # Nome do valor (se aplicável)
    old_value: Optional[Any]         # Valor anterior (se modificação)
    new_value: Optional[Any]         # Novo valor (se modificação)
    phi_c_before: Optional[float]    # Φ_C antes do evento
    phi_c_after: Optional[float]     # Φ_C depois do evento
    temporal_seal: Optional[str]     # Selo TemporalChain associado
    constitutional_check: str        # "passed", "failed", "not_applicable"
    source_host: str                 # Host onde o evento ocorreu
    user_context: str                # Contexto de usuário (SYSTEM, Admin, etc.)
    raw_message: str                 # Mensagem original do Event Log

    def to_cef(self) -> str:
        """Converte para formato CEF (Common Event Format) para QRadar."""
        extensions = []
        if self.registry_path:
            extensions.append(f"arkheRegistryPath={self.registry_path}")
        if self.value_name:
            extensions.append(f"arkheValueName={self.value_name}")
        if self.phi_c_before is not None:
            extensions.append(f"arkhePhiCBefore={self.phi_c_before}")
        if self.phi_c_after is not None:
            extensions.append(f"arkhePhiCAfter={self.phi_c_after}")
        if self.temporal_seal:
            extensions.append(f"arkheTemporalSeal={self.temporal_seal}")
        extensions.append(f"arkheConstitutionalCheck={self.constitutional_check}")

        cef_parts = [
            "CEF:0",
            "ARKHE",                    # Device Vendor
            "ASI",                      # Device Product
            "250.1.0",                  # Device Version
            str(self.event_id),         # Device Event Class ID
            self.event_name,            # Name
            str(self.severity.value),   # Severity
            "|".join(extensions)        # Extensions
        ]
        return "|".join(cef_parts)

    def to_splunk_json(self, hec_token: str) -> Dict:
        """Converte para JSON payload do Splunk HEC."""
        return {
            "time": int(self.timestamp),
            "host": self.source_host,
            "source": "arkhe:registry",
            "sourcetype": "arkhe:asi:events",
            "index": "arkhe_security",
            "event": {
                "event_id": self.event_id,
                "event_name": self.event_name,
                "severity": self.severity.name,
                "registry_path": self.registry_path,
                "value_name": self.value_name,
                "old_value": str(self.old_value) if self.old_value is not None else None,
                "new_value": str(self.new_value) if self.new_value is not None else None,
                "phi_c_before": self.phi_c_before,
                "phi_c_after": self.phi_c_after,
                "temporal_seal": self.temporal_seal,
                "constitutional_check": self.constitutional_check,
                "user_context": self.user_context,
                "raw_message": self.raw_message
            },
            "fields": {
                "arkhe_canon": "∞.Ω.∇+++.250.siem_integration",
                "arkhe_phi_c_delta": (self.phi_c_after or 0) - (self.phi_c_before or 0)
            }
        }

@dataclass
class SIEMConfig:
    """Configuração do forwarder SIEM."""
    splunk_hec_url: Optional[str] = None
    splunk_hec_token: Optional[str] = None
    splunk_index: str = "arkhe_security"
    qradar_host: Optional[str] = None
    qradar_port: int = 6514
    qradar_use_tls: bool = True
    qradar_cert_path: Optional[str] = None
    targets: SIEMTarget = SIEMTarget.BOTH
    filter_event_ids: Optional[List[int]] = None  # None = todos
    min_severity: EventSeverity = EventSeverity.INFORMATIONAL
    buffer_size: int = 1000
    retry_attempts: int = 3
    retry_delay_seconds: float = 5.0
    anchor_to_temporal_chain: bool = True

# =============================================================================
# FORWARDER SIEM
# =============================================================================

class SIEMForwarder:
    """Motor de forwarding de eventos ARKHE para SIEM corporativo."""

    # Mapeamento de EventId para schema canônico
    EVENT_SCHEMA_MAP = {
        3001: {"name": "RegistryValueModified", "severity": EventSeverity.MEDIUM},
        3002: {"name": "TemporalChainAnchored", "severity": EventSeverity.INFORMATIONAL},
        3003: {"name": "ModuleLoadStateChanged", "severity": EventSeverity.LOW},
        3004: {"name": "PhiCThresholdViolation", "severity": EventSeverity.HIGH},
        3005: {"name": "ConstitutionalCheckFailed", "severity": EventSeverity.CRITICAL},
        3006: {"name": "GPOPolicyApplied", "severity": EventSeverity.MEDIUM},
        3007: {"name": "UpgradeOrRollbackEvent", "severity": EventSeverity.MEDIUM},
    }

    def __init__(self, config: SIEMConfig):
        self.config = config
        self._buffer: List[ArkheEvent] = []
        self._session: Optional[aiohttp.ClientSession] = None
        self._qradar_writer: Optional[asyncio.StreamWriter] = None
        self._forwarding_stats = {
            "total_events": 0,
            "forwarded_splunk": 0,
            "forwarded_qradar": 0,
            "failed": 0,
            "buffered": 0
        }

    async def __aenter__(self):
        """Inicializa conexões assíncronas."""
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={"Authorization": f"Splunk {self.config.splunk_hec_token}"}
            if self.config.splunk_hec_token else {}
        )
        if self.config.qradar_use_tls and self.config.qradar_host:
            self._init_qradar_tls()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Fecha conexões e faz flush do buffer."""
        await self._flush_buffer()
        if self._session:
            await self._session.close()
        if self._qradar_writer:
            self._qradar_writer.close()
            await self._qradar_writer.wait_closed()

    def _init_qradar_tls(self):
        """Inicializa conexão TLS para QRadar."""
        if not self.config.qradar_host:
            return
        context = ssl.create_default_context()
        if self.config.qradar_cert_path:
            context.load_verify_locations(self.config.qradar_cert_path)
        # Conexão será estabelecida sob demanda
        self._qradar_context = context

    def parse_windows_event(self, event_record: Any) -> Optional[ArkheEvent]:
        """Parseia um registro do Windows Event Log para ArkheEvent."""
        event_id = event_record.EventID
        if event_id not in self.EVENT_SCHEMA_MAP:
            return None

        schema = self.EVENT_SCHEMA_MAP[event_id]

        # Extrair mensagem e campos personalizados (mock: em produção, usar evt_format_message)
        message = event_record.StringInserts[0] if event_record.StringInserts else ""

        # Extrair campos ARKHE da mensagem (formato: key=value)
        fields = self._parse_message_fields(message)

        return ArkheEvent(
            event_id=event_id,
            event_name=schema["name"],
            severity=schema["severity"],
            timestamp=time.time(),  # Em produção: usar event_record.TimeGenerated
            registry_path=fields.get("registry_path"),
            value_name=fields.get("value_name"),
            old_value=fields.get("old_value"),
            new_value=fields.get("new_value"),
            phi_c_before=float(fields["phi_c_before"]) if fields.get("phi_c_before") else None,
            phi_c_after=float(fields["phi_c_after"]) if fields.get("phi_c_after") else None,
            temporal_seal=fields.get("temporal_seal"),
            constitutional_check=fields.get("constitutional_check", "not_applicable"),
            source_host=event_record.ComputerName,
            user_context=fields.get("user_context", "SYSTEM"),
            raw_message=message
        )

    def _parse_message_fields(self, message: str) -> Dict[str, str]:
        """Extrai campos key=value da mensagem do Event Log."""
        fields = {}
        for part in message.split():
            if "=" in part:
                key, value = part.split("=", 1)
                fields[key] = value
        return fields

    def _should_forward(self, event: ArkheEvent) -> bool:
        """Verifica se evento deve ser forwardado baseado na configuração."""
        # Filtrar por EventId
        if self.config.filter_event_ids and event.event_id not in self.config.filter_event_ids:
            return False
        # Filtrar por severidade mínima
        if event.severity.value < self.config.min_severity.value:
            return False
        return True

    async def forward_event(self, event: ArkheEvent) -> bool:
        """Forwarda um evento para os destinos configurados."""
        if not self._should_forward(event):
            return True  # Não é erro, apenas filtrado

        self._forwarding_stats["total_events"] += 1
        success = True

        # Forward para Splunk HEC
        if self.config.targets in [SIEMTarget.SPLUNK_HEC, SIEMTarget.BOTH] and self.config.splunk_hec_url:
            splunk_success = await self._forward_to_splunk(event)
            if splunk_success:
                self._forwarding_stats["forwarded_splunk"] += 1
            else:
                success = False

        # Forward para QRadar Syslog
        if self.config.targets in [SIEMTarget.QRADAR_SYSLOG, SIEMTarget.BOTH] and self.config.qradar_host:
            qradar_success = await self._forward_to_qradar(event)
            if qradar_success:
                self._forwarding_stats["forwarded_qradar"] += 1
            else:
                success = False

        if not success:
            self._forwarding_stats["failed"] += 1
            # Buffer para retry se não exceder limite
            if len(self._buffer) < self.config.buffer_size:
                self._buffer.append(event)
                self._forwarding_stats["buffered"] += 1

        # Ancorar na TemporalChain se configurado
        if success and self.config.anchor_to_temporal_chain:
            await self._anchor_forwarded_event(event)

        return success

    async def _forward_to_splunk(self, event: ArkheEvent) -> bool:
        """Forwarda evento para Splunk HEC via HTTPS."""
        if not self._session or not self.config.splunk_hec_url:
            return False

        payload = event.to_splunk_json(self.config.splunk_hec_token)

        for attempt in range(self.config.retry_attempts):
            try:
                async with self._session.post(
                    f"{self.config.splunk_hec_url}/services/collector/event",
                    json=payload,
                    ssl=True
                ) as response:
                    if response.status == 200:
                        logger.debug(f"✅ Splunk: Event {event.event_id} forwarded")
                        return True
                    else:
                        logger.warning(f"⚠️ Splunk: HTTP {response.status}")
            except Exception as e:
                logger.warning(f"⚠️ Splunk attempt {attempt+1} failed: {e}")
                if attempt < self.config.retry_attempts - 1:
                    await asyncio.sleep(self.config.retry_delay_seconds)

        return False

    async def _forward_to_qradar(self, event: ArkheEvent) -> bool:
        """Forwarda evento para QRadar via Syslog/TLS."""
        if not self.config.qradar_host:
            return False

        cef_message = event.to_cef() + "\\n"

        for attempt in range(self.config.retry_attempts):
            try:
                # Estabelecer conexão se necessário (usando asyncio para evitar blocking I/O)
                if not self._qradar_writer:
                    reader, writer = await asyncio.open_connection(
                        self.config.qradar_host, self.config.qradar_port, ssl=self._qradar_context, server_hostname=self.config.qradar_host
                    )
                    self._qradar_writer = writer

                # Enviar mensagem CEF
                self._qradar_writer.write(cef_message.encode('utf-8'))
                await self._qradar_writer.drain()
                logger.debug(f"✅ QRadar: Event {event.event_id} forwarded")
                return True

            except Exception as e:
                logger.warning(f"⚠️ QRadar attempt {attempt+1} failed: {e}")
                if self._qradar_writer:
                    self._qradar_writer.close()
                    try:
                        await self._qradar_writer.wait_closed()
                    except Exception:
                        pass
                self._qradar_writer = None  # Reset para reconexão
                if attempt < self.config.retry_attempts - 1:
                    await asyncio.sleep(self.config.retry_delay_seconds)

        return False

    async def _flush_buffer(self):
        """Tenta re-forwardar eventos bufferizados."""
        if not self._buffer:
            return

        logger.info(f"🔄 Flushing {len(self._buffer)} buffered events...")
        remaining = []

        for event in self._buffer:
            success = await self.forward_event(event)
            if not success:
                remaining.append(event)

        self._buffer = remaining
        self._forwarding_stats["buffered"] = len(self._buffer)

        if remaining:
            logger.warning(f"⚠️ {len(remaining)} events still buffered after flush")

    async def _anchor_forwarded_event(self, event: ArkheEvent):
        """Ancora evento forwardado na TemporalChain."""
        # Mock: em produção, POST para endpoint da TemporalChain
        seal = hashlib.sha3_256(
            f"siem_forward:{event.event_id}:{event.timestamp}".encode()
        ).hexdigest()
        logger.debug(f"🔗 Event anchored to TemporalChain: {seal[:16]}...")

    def get_stats(self) -> Dict:
        """Retorna estatísticas de forwarding."""
        return {
            **self._forwarding_stats,
            "buffer_utilization": len(self._buffer) / self.config.buffer_size if self.config.buffer_size > 0 else 0,
            "success_rate": (self._forwarding_stats["forwarded_splunk"] + self._forwarding_stats["forwarded_qradar"]) /
                           max(1, self._forwarding_stats["total_events"])
        }

# =============================================================================
# POWERSHELL CMDLET PARA CONFIGURAÇÃO SIEM
# =============================================================================

"""
# ArkheSIEM.psm1 — ARKHE SIEM Configuration Module
# Canon: ∞.Ω.∇+++.250.powershell.siem

function Set-ArkheSIEMConfig {
    param(
        [string]$SplunkHECUrl,
        [string]$SplunkHECToken,
        [string]$QRadarHost,
        [int]$QRadarPort = 6514,
        [bool]$UseTLS = $true,
        [string]$MinSeverity = "Informational",
        [int[]]$FilterEventIds
    )

    # Salvar configuração no Registry
    $configPath = "HKLM:\\SOFTWARE\\ARKHE\\SIEM"
    if (-not (Test-Path $configPath)) { New-Item -Path $configPath -Force | Out-Null }

    Set-ItemProperty -Path $configPath -Name "SplunkHECUrl" -Value $SplunkHECUrl
    Set-ItemProperty -Path $configPath -Name "SplunkHECToken" -Value $SplunkHECToken
    Set-ItemProperty -Path $configPath -Name "QRadarHost" -Value $QRadarHost
    Set-ItemProperty -Path $configPath -Name "QRadarPort" -Value $QRadarPort
    Set-ItemProperty -Path $configPath -Name "UseTLS" -Value $UseTLS
    Set-ItemProperty -Path $configPath -Name "MinSeverity" -Value $MinSeverity
    if ($FilterEventIds) {
        Set-ItemProperty -Path $configPath -Name "FilterEventIds" -Value ($FilterEventIds -join ",")
    }

    # Reiniciar serviço de forwarding
    Restart-Service -Name "ArkheSIEMForwarder" -Force

    Write-Host "✅ SIEM configuration updated" -ForegroundColor Green
}

function Test-ArkheSIEMConnection {
    param(
        [ValidateSet("Splunk", "QRadar", "Both")]
        [string]$Target = "Both"
    )

    $results = @{}

    if ($Target -in @("Splunk", "Both")) {
        $config = Get-ItemProperty "HKLM:\\SOFTWARE\\ARKHE\\SIEM"
        try {
            $response = Invoke-WebRequest -Uri "$($config.SplunkHECUrl)/services/collector/health" `
                -Headers @{"Authorization" = "Splunk $($config.SplunkHECToken)"} `
                -TimeoutSec 10 -UseBasicParsing
            $results["Splunk"] = $response.StatusCode -eq 200
        } catch {
            $results["Splunk"] = $false
        }
    }

    if ($Target -in @("QRadar", "Both")) {
        # Teste de conexão TCP para QRadar
        $config = Get-ItemProperty "HKLM:\\SOFTWARE\\ARKHE\\SIEM"
        $tcpClient = New-Object System.Net.Sockets.TcpClient
        try {
            $tcpClient.Connect($config.QRadarHost, $config.QRadarPort)
            $results["QRadar"] = $tcpClient.Connected
        } catch {
            $results["QRadar"] = $false
        } finally {
            $tcpClient.Close()
        }
    }

    return $results
}

Export-ModuleMember -Function Set-ArkheSIEMConfig, Test-ArkheSIEMConnection
"""
