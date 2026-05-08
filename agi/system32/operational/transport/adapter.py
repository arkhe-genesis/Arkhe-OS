#!/usr/bin/env python3
"""
transport/adapter.py — Transport Adapter Core (Substrate 326.1)
Abstração de transporte com roteamento baseado em coerência.
"""
import asyncio
import hashlib
import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Callable
import logging

logger = logging.getLogger(__name__)

class TransportType(Enum):
    """Tipos de transporte suportados."""
    TOR = "tor"
    MASTER_DNS_VPN = "masterdnsvpn"
    SLIPSTREAM = "slipstream"
    DIRECT_TCP = "direct_tcp"
    CUSTOM = "custom"

@dataclass
class TransportMetrics:
    """Métricas de desempenho e coerência de um transporte."""
    transport_type: TransportType
    config_hash: str  # Hash da configuração para cache
    latency_ms: float = 0.0
    packet_loss_rate: float = 0.0
    jitter_ms: float = 0.0
    coherence_history: List[float] = field(default_factory=list)
    last_success: float = 0.0
    last_failure: float = 0.0
    success_count: int = 0
    failure_count: int = 0

    @property
    def coherence_avg(self) -> float:
        """Média de coerência histórica (últimos 100 eventos)."""
        recent = self.coherence_history[-100:]
        return sum(recent) / len(recent) if recent else 0.0

    @property
    def reliability(self) -> float:
        """Taxa de sucesso histórica."""
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 0.0

    def record_success(self, coherence: float):
        """Registra transmissão bem-sucedida."""
        self.success_count += 1
        self.last_success = time.time()
        self.coherence_history.append(coherence)
        # Manter histórico limitado
        if len(self.coherence_history) > 1000:
            self.coherence_history.pop(0)

    def record_failure(self):
        """Registra falha de transmissão."""
        self.failure_count += 1
        self.last_failure = time.time()

@dataclass
class TransportConfig:
    """Configuração de um transporte específico."""
    transport_type: TransportType
    enabled: bool = True
    priority: float = 1.0  # Peso inicial para CTS
    config: Dict = field(default_factory=dict)  # Config específica do plugin
    coherence_threshold: float = 0.7  # Φ_C mínimo para usar este transporte
    max_latency_ms: float = 5000.0  # Latência máxima aceitável
    max_packet_loss: float = 0.1  # Taxa de perda máxima aceitável

    def to_hash(self) -> str:
        """Hash canônico da configuração para cache/verificação."""
        data = {k: v for k, v in asdict(self).items() if k != 'config'}
        if 'transport_type' in data and isinstance(data['transport_type'], TransportType):
            data['transport_type'] = data['transport_type'].value
        data['config'] = json.dumps(self.config, sort_keys=True)
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:16]

class BaseTransportAdapter(ABC):
    """Interface base para plugins de transporte."""

    def __init__(self, config: TransportConfig, coherence_monitor):
        self.config = config
        self.coherence_monitor = coherence_monitor
        self.metrics = TransportMetrics(
            transport_type=config.transport_type,
            config_hash=config.to_hash()
        )
        self._initialized = False

    @abstractmethod
    async def connect(self) -> bool:
        """Estabelece conexão com o transporte. Retorna True se sucesso."""
        pass

    @abstractmethod
    async def disconnect(self):
        """Fecha conexão com o transporte."""
        pass

    @abstractmethod
    async def send(self, data: bytes, destination: str,
                   timeout: float = 30.0) -> Tuple[bool, Optional[str]]:
        """
        Envia dados via este transporte.
        Returns: (success, error_message)
        """
        pass

    @abstractmethod
    async def receive(self, source: Optional[str] = None,
                      timeout: float = 30.0) -> Tuple[Optional[bytes], Optional[str]]:
        """
        Recebe dados via este transporte.
        Returns: (data, error_message)
        """
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, float]:
        """
        Verifica saúde do transporte.
        Returns: dict com latência, perda, jitter, etc.
        """
        pass

    def update_metrics(self, latency: float, loss: float, jitter: float):
        """Atualiza métricas de desempenho."""
        self.metrics.latency_ms = latency
        self.metrics.packet_loss_rate = loss
        self.metrics.jitter_ms = jitter

    def is_healthy(self) -> bool:
        """Verifica se transporte está saudável para uso."""
        if not self._initialized:
            return False
        if self.metrics.latency_ms > self.config.max_latency_ms:
            return False
        if self.metrics.packet_loss_rate > self.config.max_packet_loss:
            return False
        if self.metrics.coherence_avg < self.config.coherence_threshold:
            return False
        return True

    def compute_cts(self) -> float:
        """Computa Coherence Transport Score (CTS) para este transporte."""
        # Pesos canônicos
        alpha, beta, gamma, delta = 0.5, 0.2, 0.2, 0.1

        # Coerência histórica
        coh_hist = self.metrics.coherence_avg

        # Normalização de latência (0-1, menor é melhor)
        lat_norm = 1.0 - min(1.0, self.metrics.latency_ms / self.config.max_latency_ms)

        # Normalização de perda (0-1, menor é melhor)
        loss_norm = 1.0 - min(1.0, self.metrics.packet_loss_rate / self.config.max_packet_loss)

        # Score de segurança baseado no tipo de transporte
        security_scores = {
            TransportType.TOR: 1.0,
            TransportType.MASTER_DNS_VPN: 0.95,
            TransportType.SLIPSTREAM: 0.9,
            TransportType.DIRECT_TCP: 0.7,
            TransportType.CUSTOM: 0.8,
        }
        security = security_scores.get(self.config.transport_type, 0.7)

        # CTS combinado
        cts = (alpha * coh_hist +
               beta * lat_norm +
               gamma * loss_norm +
               delta * security)

        # Aplicar prioridade da configuração
        return cts * self.config.priority

class TransportAdapter:
    """Adapter principal que gerencia múltiplos transportes com roteamento por coerência."""

    def __init__(self, config_path: Path, coherence_monitor):
        self.config_path = config_path
        self.coherence_monitor = coherence_monitor
        self.transports: Dict[TransportType, BaseTransportAdapter] = {}
        self.plugin_registry: Dict[str, type] = {}
        self._active_transport: Optional[TransportType] = None
        self._fallback_chain: List[TransportType] = []
        self._config: Dict[TransportType, TransportConfig] = {}

        # Carregar configuração
        self._load_config()
        # Registrar plugins padrão
        self._register_default_plugins()

    def _load_config(self):
        """Carrega configuração de transportes do arquivo YAML/JSON."""
        import yaml
        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)

        for t_type, t_config in config.get('transports', {}).items():
            transport_type = TransportType(t_type)
            self._config[transport_type] = TransportConfig(
                transport_type=transport_type,
                enabled=t_config.get('enabled', True),
                priority=t_config.get('priority', 1.0),
                config=t_config.get('config', {}),
                coherence_threshold=t_config.get('coherence_threshold', 0.7),
                max_latency_ms=t_config.get('max_latency_ms', 5000.0),
                max_packet_loss=t_config.get('max_packet_loss', 0.1),
            )

        # Configurar cadeia de fallback
        fallback_order = config.get('fallback_order', [
            TransportType.TOR.value,
            TransportType.MASTER_DNS_VPN.value,
            TransportType.SLIPSTREAM.value,
            TransportType.DIRECT_TCP.value,
        ])
        self._fallback_chain = [TransportType(t) for t in fallback_order]

    def _register_default_plugins(self):
        """Registra plugins de transporte padrão."""
        from .plugins import (
            TorAdapter, MasterDnsVPNAdapter,
            SlipStreamAdapter, DirectTCPAdapter
        )
        self.plugin_registry = {
            TransportType.TOR: TorAdapter,
            TransportType.MASTER_DNS_VPN: MasterDnsVPNAdapter,
            TransportType.SLIPSTREAM: SlipStreamAdapter,
            TransportType.DIRECT_TCP: DirectTCPAdapter,
        }

    def register_plugin(self, transport_type: TransportType,
                       adapter_class: type):
        """Registra um plugin de transporte customizado."""
        self.plugin_registry[transport_type] = adapter_class
        logger.info(f"Plugin registrado: {transport_type.value} -> {adapter_class.__name__}")

    async def initialize(self):
        """Inicializa todos os transportes habilitados."""
        for t_type, config in self._config.items():
            if not config.enabled:
                logger.info(f"Transporte {t_type.value} desabilitado — pulando")
                continue

            if t_type not in self.plugin_registry:
                logger.warning(f"Plugin não encontrado para {t_type.value} — pulando")
                continue

            # Instanciar adapter
            adapter_class = self.plugin_registry[t_type]
            adapter = adapter_class(config, self.coherence_monitor)

            # Conectar ao transporte
            if await adapter.connect():
                self.transports[t_type] = adapter
                logger.info(f"✅ Transporte {t_type.value} inicializado")
            else:
                logger.warning(f"❌ Falha ao conectar {t_type.value}")

        # Selecionar transporte inicial baseado em CTS
        await self._select_best_transport()

    async def _select_best_transport(self):
        """Seleciona o melhor transporte disponível baseado em CTS."""
        best_cts = -1.0
        best_type = None

        for t_type, adapter in self.transports.items():
            if adapter.is_healthy():
                cts = adapter.compute_cts()
                if cts > best_cts:
                    best_cts = cts
                    best_type = t_type

        if best_type:
            self._active_transport = best_type
            logger.info(f"🎯 Transporte ativo: {best_type.value} (CTS={best_cts:.3f})")
        else:
            logger.warning("⚠️  Nenhum transporte saudável disponível")
            self._active_transport = None

    async def send(self, data: bytes, destination: str,
                   timeout: float = 30.0,
                   require_coherence: float = 0.7) -> Tuple[bool, Optional[str]]:
        """
        Envia dados usando o melhor transporte disponível.
        Implementa fallback automático se o transporte ativo falhar.
        """
        # Tentar com transporte ativo primeiro
        if self._active_transport and self._active_transport in self.transports:
            adapter = self.transports[self._active_transport]
            success, error = await adapter.send(data, destination, timeout)

            if success:
                # Atualizar métricas com coerência observada
                coherence = self.coherence_monitor.evaluate_transmission_coherence(data)
                adapter.metrics.record_success(coherence)

                # Reavaliar se ainda é o melhor transporte
                await self._select_best_transport()
                return True, None
            else:
                # Registrar falha
                adapter.metrics.record_failure()
                logger.warning(f"❌ Falha no transporte ativo {self._active_transport.value}: {error}")

        # Fallback: tentar cadeia de fallback
        for t_type in self._fallback_chain:
            if t_type == self._active_transport:
                continue  # Já tentamos
            if t_type not in self.transports:
                continue

            adapter = self.transports[t_type]
            if not adapter.is_healthy():
                continue

            logger.info(f"🔄 Fallback para {t_type.value}...")
            success, error = await adapter.send(data, destination, timeout)

            if success:
                coherence = self.coherence_monitor.evaluate_transmission_coherence(data)
                adapter.metrics.record_success(coherence)
                self._active_transport = t_type  # Promover fallback a ativo
                logger.info(f"✅ Fallback bem-sucedido: {t_type.value}")
                return True, None

        # Todas as tentativas falharam
        return False, f"All transports failed. Last error: {error if 'error' in locals() else 'None'}"

    async def receive(self, source: Optional[str] = None,
                      timeout: float = 30.0) -> Tuple[Optional[bytes], Optional[str]]:
        """Recebe dados do transporte ativo (ou de qualquer um se source especificado)."""
        if source:
            # Receber de transporte específico se source conhecido
            for t_type, adapter in self.transports.items():
                if adapter.is_healthy():
                    data, error = await adapter.receive(source, timeout)
                    if not error:
                        return data, None
            return None, "No healthy transport could receive from source"
        else:
            # Receber do transporte ativo
            if self._active_transport and self._active_transport in self.transports:
                adapter = self.transports[self._active_transport]
                return await adapter.receive(None, timeout)
            return None, "No active transport available"

    async def health_check_all(self) -> Dict[str, Dict]:
        """Verifica saúde de todos os transportes e retorna relatório."""
        report = {}
        for t_type, adapter in self.transports.items():
            metrics = await adapter.health_check()
            adapter.update_metrics(
                latency=metrics.get('latency_ms', 0),
                loss=metrics.get('packet_loss_rate', 0),
                jitter=metrics.get('jitter_ms', 0)
            )
            report[t_type.value] = {
                'healthy': adapter.is_healthy(),
                'cts': adapter.compute_cts(),
                'metrics': asdict(adapter.metrics),
                'config_hash': adapter.config.to_hash(),
            }
        return report

    def get_active_transport_info(self) -> Optional[Dict]:
        """Retorna informações do transporte ativo."""
        if self._active_transport and self._active_transport in self.transports:
            adapter = self.transports[self._active_transport]
            return {
                'type': self._active_transport.value,
                'cts': adapter.compute_cts(),
                'healthy': adapter.is_healthy(),
                'metrics': asdict(adapter.metrics),
            }
        return None

    async def shutdown(self):
        """Encerra todos os transportes."""
        for adapter in self.transports.values():
            await adapter.disconnect()
        logger.info("🔌 Todos os transportes encerrados")
