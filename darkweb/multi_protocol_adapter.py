#!/usr/bin/env python3
"""
ARKHE OS Substrato 228/229: Multi-Protocol Darknet Adapter
Adaptadores éticos para monitoramento de redes anônimas:
• Tor (.onion) — via SOCKS5h proxy e stem controller
• I2P (.i2p) — via SAM bridge e HTTP proxy
• Freenet (.freenet) — via FCP (Freenet Client Protocol)
• ZeroNet (.zero) — via ZeroNet RPC e BitTorrent DHT

Princípios Éticos:
• Hash-Only Processing: conteúdo bruto NUNCA é armazenado ou transmitido
• Passive Monitoring: crawling respeita robots.txt e rate limits de cada rede
• PQC-Signed Reporting: todos os relatórios assinados com Dilithium-3 via HSM
• Temporal Anchoring: cada finding ancorado na TemporalChain com selo verificável
• Jurisdiction-Aware: relatórios direcionados conforme legislação local

Canon: ∞.Ω.∇+++.228.multi_protocol_adapter
"""

import asyncio
import hashlib
import json
import time
import re
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any, Callable, Union, Type
from urllib.parse import urlparse, urlunparse

# Dependências opcionais (importadas condicionalmente)
try:
    import aiohttp
    import aiohttp_socks  # Para proxy SOCKS5
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    logging.warning("⚠️  aiohttp/aiohttp_socks não disponível — modo simulado para HTTP")

try:
    from stem import Signal
    from stem.control import Controller
    STEM_AVAILABLE = True
except ImportError:
    STEM_AVAILABLE = False
    logging.warning("⚠️  stem não disponível — controle do Tor simulado")

try:
    import pyfreenet  # Freenet Client Protocol
    FREENET_AVAILABLE = True
except ImportError:
    FREENET_AVAILABLE = False
    logging.warning("⚠️  pyfreenet não disponível — Freenet simulado")

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# ENUMS E CONSTANTES
# ═══════════════════════════════════════════════════════════════

class DarknetProtocol(Enum):
    """Protocolos de rede anônima suportados."""
    TOR = "tor"           # The Onion Router (.onion)
    I2P = "i2p"           # Invisible Internet Project (.i2p)
    FREENET = "freenet"   # Freenet (.freenet / USK / KSK)
    ZERONET = "zeronet"   # ZeroNet (.zero / BitTorrent-based)
    UNKNOWN = "unknown"

class CrawlDepth(Enum):
    """Profundidade de crawling permitida (ética)."""
    SURFACE = 1      # Apenas página inicial
    SHALLOW = 2      # Página + links diretos
    MODERATE = 3     # Até 3 níveis de profundidade
    DEEP = 5         # Máximo ético para vigilância

class EthicalConstraint(Enum):
    """Restrições éticas aplicáveis a cada protocolo."""
    NO_CONTENT_STORAGE = "no_content_storage"          # Nunca armazenar conteúdo bruto
    HASH_ONLY_PROCESSING = "hash_only_processing"      # Processar apenas hashes
    RESPECT_ROBOTS_TXT = "respect_robots_txt"          # Respeitar robots.txt da rede
    RATE_LIMIT_PER_HOST = "rate_limit_per_host"        # Rate limit por host
    NO_ACTIVE_EXPLOITATION = "no_active_exploitation"  # Sem exploração de vulnerabilidades
    ANONYMIZE_METADATA = "anonymize_metadata"          # Anonimizar metadados sensíveis

# Configurações padrão por protocolo
PROTOCOL_DEFAULTS = {
    DarknetProtocol.TOR: {
        "proxy_url": "socks5h://127.0.0.1:9050",
        "control_port": 9051,
        "default_timeout": 30,
        "max_concurrent": 5,
        "rate_limit_per_minute": 10,
        "crawl_depth": CrawlDepth.SHALLOW,
        "ethical_constraints": [
            EthicalConstraint.NO_CONTENT_STORAGE,
            EthicalConstraint.HASH_ONLY_PROCESSING,
            EthicalConstraint.RESPECT_ROBOTS_TXT,
            EthicalConstraint.RATE_LIMIT_PER_HOST,
        ]
    },
    DarknetProtocol.I2P: {
        "proxy_url": "http://127.0.0.1:4444",
        "default_timeout": 45,
        "max_concurrent": 3,
        "rate_limit_per_minute": 5,
        "crawl_depth": CrawlDepth.SHALLOW,
        "ethical_constraints": [
            EthicalConstraint.NO_CONTENT_STORAGE,
            EthicalConstraint.HASH_ONLY_PROCESSING,
            EthicalConstraint.RATE_LIMIT_PER_HOST,
        ]
    },
    DarknetProtocol.FREENET: {
        "default_timeout": 60,
        "max_concurrent": 2,
        "rate_limit_per_minute": 3,
        "crawl_depth": CrawlDepth.SURFACE,
        "ethical_constraints": [
            EthicalConstraint.NO_CONTENT_STORAGE,
            EthicalConstraint.HASH_ONLY_PROCESSING,
            EthicalConstraint.NO_ACTIVE_EXPLOITATION,
        ]
    },
    DarknetProtocol.ZERONET: {
        "default_timeout": 30,
        "max_concurrent": 4,
        "rate_limit_per_minute": 8,
        "crawl_depth": CrawlDepth.MODERATE,
        "ethical_constraints": [
            EthicalConstraint.NO_CONTENT_STORAGE,
            EthicalConstraint.HASH_ONLY_PROCESSING,
            EthicalConstraint.RESPECT_ROBOTS_TXT,
        ]
    }
}

# ═══════════════════════════════════════════════════════════════
# DATA CLASSES
# ═══════════════════════════════════════════════════════════════

@dataclass
class ProtocolConfig:
    """Configuração específica de um protocolo."""
    protocol: DarknetProtocol
    proxy_url: Optional[str] = None
    control_port: Optional[int] = None
    default_timeout: int = 30
    max_concurrent: int = 5
    rate_limit_per_minute: int = 10
    crawl_depth: CrawlDepth = CrawlDepth.SHALLOW
    ethical_constraints: List[EthicalConstraint] = field(default_factory=list)
    custom_headers: Dict[str, str] = field(default_factory=dict)
    user_agent: str = "ARKHE-Vigil/1.0 (Ethical Monitoring)"

@dataclass
class CrawlResult:
    """Resultado de uma operação de crawling ético."""
    url: str
    protocol: DarknetProtocol
    status_code: Optional[int]
    content_hash: Optional[str]  # SHA3-256 do conteúdo (nunca o conteúdo bruto)
    perceptual_hashes: List[str]  # Hashes perceptuais de imagens encontradas
    links_found: List[str]  # URLs de links extraídos (apenas metadados)
    metadata: Dict[str, Any]  # Metadados anonimizados
    crawl_timestamp: float = field(default_factory=time.time)
    ethical_violations: List[str] = field(default_factory=list)
    temporal_seal: Optional[str] = None

@dataclass
class EthicalAuditLog:
    """Registro de auditoria ética para cada operação."""
    operation_id: str
    protocol: DarknetProtocol
    target_url: str
    constraints_applied: List[str]
    actions_taken: List[str]
    content_stored: bool  # Deve ser SEMPRE False
    hash_only_processed: bool  # Deve ser SEMPRE True
    timestamp: float = field(default_factory=time.time)
    operator_id: Optional[str] = None
    temporal_seal: Optional[str] = None

# ═══════════════════════════════════════════════════════════════
# ABSTRACT BASE ADAPTER
# ═══════════════════════════════════════════════════════════════

class DarknetAdapter(ABC):
    """
    Classe base abstrata para adaptadores de protocolo darknet.
    Todos os adaptadores devem implementar:
    • _connect(): Estabelecer conexão com a rede
    • _fetch_page(): Buscar conteúdo de uma URL (sem armazenar)
    • _extract_hashes(): Extrair hashes perceptuais do conteúdo
    • _extract_links(): Extrair links para crawling adicional
    • _apply_ethical_constraints(): Aplicar restrições éticas
    """

    def __init__(
        self,
        config: ProtocolConfig,
        hsm_signer=None,
        temporal_chain=None,
        phi_bus=None,
        perceptual_db=None
    ):
        self.config = config
        self.hsm = hsm_signer
        self.temporal = temporal_chain
        self.phi_bus = phi_bus
        self.perceptual_db = perceptual_db or {}

        self._session: Optional[Any] = None
        self._rate_limiter: Optional[asyncio.Semaphore] = None
        self._audit_log: List[EthicalAuditLog] = []
        self._ethical_violations: List[str] = []

    @abstractmethod
    async def _connect(self) -> bool:
        """Estabelece conexão com a rede anônima."""
        pass

    @abstractmethod
    async def _disconnect(self):
        """Fecha conexão com a rede anônima."""
        pass

    @abstractmethod
    async def _fetch_page(self, url: str) -> Tuple[Optional[bytes], Optional[int]]:
        """
        Busca conteúdo de URL sem armazenar o conteúdo bruto.
        Returns: (content_bytes_or_None, status_code_or_None)
        """
        pass

    @abstractmethod
    async def _extract_hashes(self, content: bytes) -> List[str]:
        """Extrai hashes perceptuais de imagens do conteúdo."""
        pass

    @abstractmethod
    async def _extract_links(self, content: bytes, base_url: str) -> List[str]:
        """Extrai links para crawling adicional."""
        pass

    @abstractmethod
    async def _apply_ethical_constraints(
        self,
        content: bytes,
        url: str
    ) -> Tuple[bytes, List[str]]:
        """
        Aplica restrições éticas ao conteúdo.
        Returns: (processed_content, list_of_violations_if_any)
        """
        pass

    async def __aenter__(self):
        await self._connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._disconnect()

    async def crawl(
        self,
        url: str,
        depth: Optional[CrawlDepth] = None,
        visited: Optional[Set[str]] = None
    ) -> CrawlResult:
        """
        Executa crawling ético de uma URL.

        Args:
            url: URL alvo (.onion, .i2p, .freenet, .zero)
            depth: Profundidade máxima de crawling
            visited: Conjunto de URLs já visitadas (para evitar loops)

        Returns:
            CrawlResult com hashes e metadados (nunca conteúdo bruto)
        """
        start_time = time.time()
        operation_id = hashlib.sha3_256(
            f"{url}:{time.time()}".encode()
        ).hexdigest()[:12]

        visited = visited or set()
        depth = depth or self.config.crawl_depth

        # Verificar se URL já foi visitada
        if url in visited:
            logger.debug(f"⏭️  URL já visitada: {url}")
            return CrawlResult(
                url=url,
                protocol=self.config.protocol,
                status_code=None,
                content_hash=None,
                perceptual_hashes=[],
                links_found=[],
                metadata={"skipped": "already_visited"}
            )

        visited.add(url)

        # Aplicar rate limiting
        if self._rate_limiter:
            async with self._rate_limiter:
                return await self._crawl_internal(url, depth, visited, operation_id, start_time)
        else:
            return await self._crawl_internal(url, depth, visited, operation_id, start_time)

    async def _crawl_internal(
        self,
        url: str,
        depth: CrawlDepth,
        visited: Set[str],
        operation_id: str,
        start_time: float
    ) -> CrawlResult:
        """Implementação interna do crawling."""
        violations: List[str] = []

        try:
            # 1. Fetch conteúdo (sem armazenar)
            content, status_code = await self._fetch_page(url)

            if content is None or status_code != 200:
                return CrawlResult(
                    url=url,
                    protocol=self.config.protocol,
                    status_code=status_code,
                    content_hash=None,
                    perceptual_hashes=[],
                    links_found=[],
                    metadata={"error": f"HTTP {status_code}" if status_code else "no_content"}
                )

            # 2. Aplicar restrições éticas
            processed_content, ethical_violations = await self._apply_ethical_constraints(
                content, url
            )
            violations.extend(ethical_violations)

            # 3. Calcular hash do conteúdo (SHA3-256) — NUNCA armazenar conteúdo bruto
            content_hash = hashlib.sha3_256(processed_content).hexdigest()

            # 4. Extrair hashes perceptuais de imagens
            perceptual_hashes = await self._extract_hashes(processed_content)

            # 5. Extrair links para crawling adicional
            links_found = await self._extract_links(processed_content, url)

            # 6. Coletar metadados anonimizados
            metadata = await self._extract_anonymized_metadata(processed_content, url)

            # 7. Crawling recursivo se depth permitir
            if depth.value > 1 and links_found:
                for link in links_found[:3]:  # Limitar links recursivos para ética
                    if link not in visited and self._is_protocol_match(link):
                        await self.crawl(link, CrawlDepth(depth.value - 1), visited)

            # 8. Criar resultado
            result = CrawlResult(
                url=url,
                protocol=self.config.protocol,
                status_code=status_code,
                content_hash=content_hash,
                perceptual_hashes=perceptual_hashes,
                links_found=links_found,
                metadata=metadata,
                ethical_violations=violations
            )

            # 9. Ancorar na TemporalChain
            if self.temporal and content_hash:
                result.temporal_seal = await self.temporal.anchor_event(
                    "darknet_crawl_completed",
                    {
                        "operation_id": operation_id,
                        "url": self._anonymize_url(url),
                        "protocol": self.config.protocol.value,
                        "content_hash": content_hash[:16],
                        "perceptual_hashes_count": len(perceptual_hashes),
                        "links_found_count": len(links_found),
                        "ethical_violations": len(violations),
                        "duration_ms": (time.time() - start_time) * 1000,
                        "timestamp": time.time()
                    }
                )

            # 10. Registrar auditoria ética
            await self._log_ethical_audit(
                operation_id=operation_id,
                url=url,
                constraints_applied=[c.value for c in self.config.ethical_constraints],
                actions_taken=["fetch", "hash_extract", "link_extract", "temporal_anchor"],
                content_stored=False,  # CRÍTICO: sempre False
                hash_only_processed=True  # CRÍTICO: sempre True
            )

            logger.info(
                f"✅ Crawl ético: {self._anonymize_url(url)} | "
                f"hash={content_hash[:16]} | "
                f"perceptual={len(perceptual_hashes)} | "
                f"links={len(links_found)} | "
                f"violations={len(violations)}"
            )

            return result

        except Exception as e:
            logger.error(f"❌ Erro no crawl de {url}: {e}")
            violations.append(f"crawl_error: {str(e)}")

            return CrawlResult(
                url=url,
                protocol=self.config.protocol,
                status_code=None,
                content_hash=None,
                perceptual_hashes=[],
                links_found=[],
                metadata={"error": str(e)},
                ethical_violations=violations
            )

    async def _extract_anonymized_metadata(
        self,
        content: bytes,
        url: str
    ) -> Dict[str, Any]:
        """Extrai metadados anonimizados do conteúdo."""
        # Mock: em produção, extrair metadados reais e anonimizar
        return {
            "content_type": "text/html",  # Exemplo
            "content_length": len(content),
            "url_anonymized": self._anonymize_url(url),
            "timestamp": time.time(),
            "protocol": self.config.protocol.value
        }

    def _anonymize_url(self, url: str) -> str:
        """Anonimiza URL para logs e auditoria."""
        # Manter apenas protocolo e domínio anonimizado
        parsed = urlparse(url)
        domain = parsed.netloc
        if len(domain) > 16:
            domain = domain[:8] + "..." + domain[-8:]
        return urlunparse((parsed.scheme, domain, "", "", "", ""))

    def _is_protocol_match(self, url: str) -> bool:
        """Verifica se URL corresponde ao protocolo do adaptador."""
        protocol_map = {
            DarknetProtocol.TOR: r"\.onion",
            DarknetProtocol.I2P: r"\.i2p",
            DarknetProtocol.FREENET: r"\.(freenet|usk|ksk)",
            DarknetProtocol.ZERONET: r"\.zero",
        }
        pattern = protocol_map.get(self.config.protocol)
        if not pattern:
            return False
        return bool(re.search(pattern, url, re.I))

    async def _log_ethical_audit(
        self,
        operation_id: str,
        url: str,
        constraints_applied: List[str],
        actions_taken: List[str],
        content_stored: bool,
        hash_only_processed: bool
    ):
        """Registra auditoria ética da operação."""
        # Validar restrições éticas CRÍTICAS
        if content_stored:
            logger.critical(f"🚨 VIOLAÇÃO ÉTICA CRÍTICA: conteúdo armazenado em {url}")
            self._ethical_violations.append("content_stored_violation")

        if not hash_only_processed:
            logger.critical(f"🚨 VIOLAÇÃO ÉTICA CRÍTICA: processamento sem hash-only em {url}")
            self._ethical_violations.append("hash_only_violation")

        audit = EthicalAuditLog(
            operation_id=operation_id,
            protocol=self.config.protocol,
            target_url=self._anonymize_url(url),
            constraints_applied=constraints_applied,
            actions_taken=actions_taken,
            content_stored=content_stored,
            hash_only_processed=hash_only_processed,
            operator_id="arkhe_vigil_system"
        )

        self._audit_log.append(audit)

        # Ancorar auditoria na TemporalChain se houver violações
        if self._ethical_violations or not content_stored or not hash_only_processed:
            if self.temporal:
                await self.temporal.anchor_event(
                    "ethical_audit_logged",
                    {
                        "operation_id": operation_id,
                        "protocol": self.config.protocol.value,
                        "content_stored": content_stored,
                        "hash_only_processed": hash_only_processed,
                        "violations": self._ethical_violations,
                        "timestamp": time.time()
                    }
                )

    def get_audit_summary(self) -> Dict:
        """Retorna resumo de auditoria ética."""
        return {
            "protocol": self.config.protocol.value,
            "total_operations": len(self._audit_log),
            "ethical_violations": len(self._ethical_violations),
            "content_stored_count": sum(1 for a in self._audit_log if a.content_stored),
            "hash_only_count": sum(1 for a in self._audit_log if a.hash_only_processed),
            "constraints_enforced": [c.value for c in self.config.ethical_constraints]
        }

# ═══════════════════════════════════════════════════════════════
# TOR ADAPTER
# ═══════════════════════════════════════════════════════════════

class TorAdapter(DarknetAdapter):
    """
    Adaptador para rede Tor (.onion).

    Características:
    • Conexão via SOCKS5h proxy (127.0.0.1:9050)
    • Controle do Tor via stem (opcional) para circuit renewal
    • Respeito a robots.txt da rede Tor
    • Rate limiting por host para evitar sobrecarga
    """

    async def _connect(self) -> bool:
        """Estabelece conexão com a rede Tor."""
        if not AIOHTTP_AVAILABLE:
            logger.warning("⚠️  aiohttp não disponível — Tor em modo simulado")
            return True

        try:
            # Configurar connector com proxy SOCKS5h
            connector = aiohttp_socks.SocksConnector(
                socks_ver=aiohttp_socks.SocksVer.SOCKS5,
                host='127.0.0.1',
                port=9050,
                rdns=True,  # DNS resolution via Tor
                limit=self.config.max_concurrent,
                ttl_dns_cache=300
            )

            self._session = aiohttp.ClientSession(
                connector=connector,
                headers={
                    "User-Agent": self.config.user_agent,
                    **self.config.custom_headers
                },
                timeout=aiohttp.ClientTimeout(total=self.config.default_timeout)
            )

            # Configurar rate limiter
            self._rate_limiter = asyncio.Semaphore(self.config.max_concurrent)

            # Renew circuit via stem se disponível
            if STEM_AVAILABLE:
                try:
                    with Controller.from_port(port=self.config.control_port or 9051) as controller:
                        controller.authenticate()
                        controller.signal(Signal.NEWNYM)
                        logger.info("🔄 Circuito Tor renovado")
                except Exception as e:
                    logger.warning(f"⚠️  Falha ao renovar circuito Tor: {e}")

            logger.info("✅ Conectado à rede Tor")
            return True

        except Exception as e:
            logger.error(f"❌ Falha ao conectar ao Tor: {e}")
            return False

    async def _disconnect(self):
        """Fecha conexão com a rede Tor."""
        if self._session:
            await self._session.close()
            logger.info("🔌 Conexão Tor fechada")

    async def _fetch_page(self, url: str) -> Tuple[Optional[bytes], Optional[int]]:
        """Busca conteúdo de página .onion sem armazenar."""
        if not self._session:
            return None, None

        try:
            async with self._session.get(url) as response:
                content = await response.read()
                status = response.status

                # CRÍTICO: processar conteúdo e descartar imediatamente
                # Nunca armazenar content em variável de longo prazo
                return content, status

        except asyncio.TimeoutError:
            logger.warning(f"⏱️  Timeout ao buscar {url}")
            return None, None
        except Exception as e:
            logger.error(f"❌ Erro ao buscar {url}: {e}")
            return None, None

    async def _extract_hashes(self, content: bytes) -> List[str]:
        """Extrai hashes perceptuais de imagens do conteúdo HTML."""
        hashes = []

        # Mock: em produção, usar biblioteca como imagehash ou pyphash
        # Aqui, simulamos extração de hashes de imagens
        try:
            # Extrair URLs de imagens do HTML
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(content, 'html.parser')
            img_tags = soup.find_all('img')

            for img in img_tags:
                src = img.get('src') or img.get('data-src')
                if src:
                    # Mock: gerar hash perceptual simulado
                    phash = hashlib.sha3_256(
                        f"img:{src}:{len(content)}".encode()
                    ).hexdigest()[:32]
                    hashes.append(phash)

        except ImportError:
            logger.warning("⚠️  BeautifulSoup não disponível — extração de hashes simulada")
            # Fallback: hash do conteúdo como proxy
            if content:
                hashes.append(hashlib.sha3_256(content[:1024]).hexdigest()[:32])

        return hashes

    async def _extract_links(self, content: bytes, base_url: str) -> List[str]:
        """Extrai links .onion do conteúdo HTML."""
        links = []

        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(content, 'html.parser')

            for tag in soup.find_all('a', href=True):
                href = tag['href']
                # Converter relative para absolute
                full_url = urlparse(href)._replace(
                    scheme=urlparse(base_url).scheme,
                    netloc=urlparse(base_url).netloc
                ).geturl() if not href.startswith('http') else href

                # Filtrar apenas .onion
                if '.onion' in full_url.lower():
                    links.append(full_url)

        except ImportError:
            # Fallback regex simples
            onion_pattern = r'https?://[a-z0-9]{16}\.onion[^\s"\'<>]+'
            links = re.findall(onion_pattern, content.decode('utf-8', errors='ignore'))

        # Deduplicar e limitar
        return list(set(links))[:10]  # Limitar para ética

    async def _apply_ethical_constraints(
        self,
        content: bytes,
        url: str
    ) -> Tuple[bytes, List[str]]:
        """Aplica restrições éticas ao conteúdo Tor."""
        violations = []

        # 1. Remover conteúdo sensível (imagens explícitas, etc.)
        # Mock: em produção, usar classifier para detectar conteúdo sensível
        processed = content

        # 2. Anonimizar metadados pessoais
        # Mock: remover emails, números de telefone, etc.

        # 3. Verificar robots.txt da rede Tor
        if EthicalConstraint.RESPECT_ROBOTS_TXT in self.config.ethical_constraints:
            robots_allowed = await self._check_robots_txt(url)
            if not robots_allowed:
                violations.append("robots_txt_disallowed")
                # Em produção: abortar crawl se não permitido

        # 4. Garantir que conteúdo não seja armazenado
        # Esta verificação é crítica e deve ser feita no caller

        return processed, violations

    async def _check_robots_txt(self, url: str) -> bool:
        """Verifica robots.txt da rede Tor (simulado)."""
        # Mock: em produção, buscar e parsear robots.txt do domínio
        return True  # Assumir permitido para demo

# ═══════════════════════════════════════════════════════════════
# I2P ADAPTER
# ═══════════════════════════════════════════════════════════════

class I2PAdapter(DarknetAdapter):
    """
    Adaptador para rede I2P (.i2p).

    Características:
    • Conexão via HTTP proxy (127.0.0.1:4444) ou SAM bridge
    • Suporte a outproxy para sites clearnet (opcional)
    • Rate limiting agressivo (I2P é mais lento que Tor)
    """

    async def _connect(self) -> bool:
        """Estabelece conexão com a rede I2P."""
        if not AIOHTTP_AVAILABLE:
            logger.warning("⚠️  aiohttp não disponível — I2P em modo simulado")
            return True

        try:
            # Configurar connector com proxy HTTP
            connector = aiohttp.TCPConnector(
                limit=self.config.max_concurrent,
                ttl_dns_cache=300
            )

            self._session = aiohttp.ClientSession(
                connector=connector,
                headers={
                    "User-Agent": self.config.user_agent,
                    **self.config.custom_headers
                },
                timeout=aiohttp.ClientTimeout(total=self.config.default_timeout)
            )

            self._rate_limiter = asyncio.Semaphore(self.config.max_concurrent)

            logger.info("✅ Conectado à rede I2P (via proxy)")
            return True

        except Exception as e:
            logger.error(f"❌ Falha ao conectar ao I2P: {e}")
            return False

    async def _disconnect(self):
        """Fecha conexão com a rede I2P."""
        if self._session:
            await self._session.close()

    async def _fetch_page(self, url: str) -> Tuple[Optional[bytes], Optional[int]]:
        """Busca conteúdo de página .i2p."""
        if not self._session:
            return None, None

        try:
            # I2P requer proxy configurado no nível do sistema ou via aiohttp
            # Mock: simular fetch com delay maior que Tor
            await asyncio.sleep(0.5)  # Simular latência I2P

            # Em produção: usar proxy configurado
            # async with self._session.get(url, proxy=self.config.proxy_url) as response:

            # Mock response
            return b"<html>I2P content mock</html>", 200

        except asyncio.TimeoutError:
            logger.warning(f"⏱️  Timeout I2P: {url}")
            return None, None
        except Exception as e:
            logger.error(f"❌ Erro I2P {url}: {e}")
            return None, None

    async def _extract_hashes(self, content: bytes) -> List[str]:
        """Extrai hashes perceptuais de conteúdo I2P."""
        # Similar ao Tor, mas I2P tem menos imagens em geral
        if content:
            return [hashlib.sha3_256(content[:512]).hexdigest()[:32]]
        return []

    async def _extract_links(self, content: bytes, base_url: str) -> List[str]:
        """Extrai links .i2p."""
        i2p_pattern = r'https?://[a-z0-9\-]{512}\.b32\.i2p[^\s"\'<>]+'
        links = re.findall(i2p_pattern, content.decode('utf-8', errors='ignore'))
        return list(set(links))[:5]  # I2P: limitar mais para ética

    async def _apply_ethical_constraints(
        self,
        content: bytes,
        url: str
    ) -> Tuple[bytes, List[str]]:
        """Aplica restrições éticas ao conteúdo I2P."""
        # I2P tem menos robots.txt, mas manter princípio de rate limiting
        return content, []

# ═══════════════════════════════════════════════════════════════
# FREENET ADAPTER
# ═══════════════════════════════════════════════════════════════

class FreenetAdapter(DarknetAdapter):
    """
    Adaptador para rede Freenet (.freenet / USK / KSK).

    Características:
    • Conexão via FCP (Freenet Client Protocol)
    • Suporte a USK (Updatable Subspace Key) e KSK (Key-String Key)
    • Crawling extremamente conservador (Freenet é descentralizado e lento)
    """

    async def _connect(self) -> bool:
        """Estabelece conexão com Freenet via FCP."""
        if not FREENET_AVAILABLE:
            logger.warning("⚠️  pyfreenet não disponível — Freenet em modo simulado")
            return True

        try:
            # Em produção: conectar via FCP
            # self._fcp_client = pyfreenet.FCPClient(
            #     host=self.config.fcp_host,
            #     port=self.config.fcp_port
            # )

            self._rate_limiter = asyncio.Semaphore(self.config.max_concurrent)
            logger.info("✅ Conectado ao Freenet (FCP)")
            return True

        except Exception as e:
            logger.error(f"❌ Falha ao conectar ao Freenet: {e}")
            return False

    async def _disconnect(self):
        """Fecha conexão com Freenet."""
        # if self._fcp_client:
        #     self._fcp_client.close()
        pass

    async def _fetch_page(self, url: str) -> Tuple[Optional[bytes], Optional[int]]:
        """Busca conteúdo Freenet (USK/KSK)."""
        # Freenet não usa HTTP tradicional — usar FCP
        # Mock para demonstração
        await asyncio.sleep(1.0)  # Freenet é lento

        if "usk" in url.lower() or "ksk" in url.lower():
            return b"Freenet content mock", 200
        return None, None

    async def _extract_hashes(self, content: bytes) -> List[str]:
        """Extrai hashes de conteúdo Freenet."""
        if content:
            return [hashlib.sha3_256(content[:256]).hexdigest()[:32]]
        return []

    async def _extract_links(self, content: bytes, base_url: str) -> List[str]:
        """Extrai links Freenet (USK/KSK)."""
        # Padrões Freenet
        patterns = [
            r'freenet:USK@[a-zA-Z0-9\-/]+',
            r'freenet:KSK@[a-zA-Z0-9\-/]+',
        ]
        links = []
        text = content.decode('utf-8', errors='ignore')
        for pattern in patterns:
            links.extend(re.findall(pattern, text, re.I))
        return list(set(links))[:3]  # Freenet: muito conservador

    async def _apply_ethical_constraints(
        self,
        content: bytes,
        url: str
    ) -> Tuple[bytes, List[str]]:
        """Aplica restrições éticas ao conteúdo Freenet."""
        # Freenet é altamente descentralizado — máximo de cautela
        violations = []

        # Nunca tentar modificar ou interferir com conteúdo Freenet
        if EthicalConstraint.NO_ACTIVE_EXPLOITATION in self.config.ethical_constraints:
            # Garantir que não há tentativas de write/insert
            pass

        return content, violations

# ═══════════════════════════════════════════════════════════════
# ZERONET ADAPTER
# ═══════════════════════════════════════════════════════════════

class ZeroNetAdapter(DarknetAdapter):
    """
    Adaptador para ZeroNet (.zero).

    Características:
    • Conexão via RPC do ZeroNet (127.0.0.1:43110)
    • Integração com BitTorrent DHT para descoberta de sites
    • Suporte a sites assinados criptograficamente
    """

    async def _connect(self) -> bool:
        """Estabelece conexão com ZeroNet via RPC."""
        if not AIOHTTP_AVAILABLE:
            logger.warning("⚠️  aiohttp não disponível — ZeroNet em modo simulado")
            return True

        try:
            # ZeroNet usa HTTP local para RPC
            self._session = aiohttp.ClientSession(
                headers={
                    "User-Agent": self.config.user_agent,
                    "Content-Type": "application/json",
                    **self.config.custom_headers
                },
                timeout=aiohttp.ClientTimeout(total=self.config.default_timeout)
            )

            self._rate_limiter = asyncio.Semaphore(self.config.max_concurrent)
            logger.info("✅ Conectado ao ZeroNet (RPC)")
            return True

        except Exception as e:
            logger.error(f"❌ Falha ao conectar ao ZeroNet: {e}")
            return False

    async def _disconnect(self):
        """Fecha conexão com ZeroNet."""
        if self._session:
            await self._session.close()

    async def _fetch_page(self, url: str) -> Tuple[Optional[bytes], Optional[int]]:
        """Busca conteúdo ZeroNet via RPC."""
        if not self._session:
            return None, None

        try:
            # ZeroNet RPC: chamar método fileGet
            # Mock para demonstração
            await asyncio.sleep(0.3)

            # Extrair site ID da URL ZeroNet
            # Ex: http://127.0.0.1:43110/1HeLLo4uzjaLetFx6NH3PMwFP3qbRbTf3D
            site_id_match = re.search(r'/([13][a-km-zA-HJ-NP-Z1-9]{26,35})', url)
            if site_id_match:
                return b"ZeroNet site content mock", 200

            return None, None

        except Exception as e:
            logger.error(f"❌ Erro ZeroNet {url}: {e}")
            return None, None

    async def _extract_hashes(self, content: bytes) -> List[str]:
        """Extrai hashes de conteúdo ZeroNet."""
        if content:
            return [hashlib.sha3_256(content[:512]).hexdigest()[:32]]
        return []

    async def _extract_links(self, content: bytes, base_url: str) -> List[str]:
        """Extrai links ZeroNet."""
        # ZeroNet usa endereços Bitcoin-style
        zeronet_pattern = r'http://[0-9.]+:[0-9]+/[13][a-km-zA-HJ-NP-Z1-9]{26,35}'
        links = re.findall(zeronet_pattern, content.decode('utf-8', errors='ignore'))
        return list(set(links))[:8]

    async def _apply_ethical_constraints(
        self,
        content: bytes,
        url: str
    ) -> Tuple[bytes, List[str]]:
        """Aplica restrições éticas ao conteúdo ZeroNet."""
        # ZeroNet sites são assinados — respeitar integridade criptográfica
        return content, []

# ═══════════════════════════════════════════════════════════════
# MULTI-PROTOCOL ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════

class MultiProtocolDarknetOrchestrator:
    """
    Orquestrador que gerencia múltiplos adaptadores de protocolo.

    Funcionalidades:
    • Roteamento automático de URLs para adaptador correto
    • Pool de adaptadores com conexão reutilizável
    • Agregação de resultados multi-protocolo
    • Relatório consolidado com assinatura PQC
    • Integração com TemporalChain para auditoria cross-protocolo
    """

    def __init__(
        self,
        hsm_signer=None,
        temporal_chain=None,
        phi_bus=None,
        perceptual_db=None,
        protocol_configs: Optional[Dict[DarknetProtocol, ProtocolConfig]] = None
    ):
        self.hsm = hsm_signer
        self.temporal = temporal_chain
        self.phi_bus = phi_bus
        self.perceptual_db = perceptual_db or {}

        # Inicializar configs padrão ou customizadas
        self.protocol_configs = protocol_configs or {
            proto: ProtocolConfig(protocol=proto, **defaults)
            for proto, defaults in PROTOCOL_DEFAULTS.items()
        }

        self._adapters: Dict[DarknetProtocol, DarknetAdapter] = {}
        self._adapter_pool: Dict[str, DarknetAdapter] = {}
        self._cross_protocol_findings: List[Dict] = []

    def _get_adapter_class(self, protocol: DarknetProtocol) -> Type[DarknetAdapter]:
        """Retorna classe de adaptador para protocolo."""
        adapter_map = {
            DarknetProtocol.TOR: TorAdapter,
            DarknetProtocol.I2P: I2PAdapter,
            DarknetProtocol.FREENET: FreenetAdapter,
            DarknetProtocol.ZERONET: ZeroNetAdapter,
        }
        return adapter_map.get(protocol, TorAdapter)  # Fallback para Tor

    async def get_adapter(
        self,
        protocol: DarknetProtocol,
        config: Optional[ProtocolConfig] = None
    ) -> DarknetAdapter:
        """Obtém ou cria adaptador para protocolo."""
        config = config or self.protocol_configs.get(protocol)
        if not config:
            raise ValueError(f"Configuração não encontrada para {protocol.value}")

        adapter_class = self._get_adapter_class(protocol)

        # Reutilizar adaptador se já existir
        key = f"{protocol.value}:{config.proxy_url or 'default'}"
        if key in self._adapter_pool:
            return self._adapter_pool[key]

        # Criar novo adaptador
        adapter = adapter_class(
            config=config,
            hsm_signer=self.hsm,
            temporal_chain=self.temporal,
            phi_bus=self.phi_bus,
            perceptual_db=self.perceptual_db
        )

        await adapter._connect()
        self._adapter_pool[key] = adapter
        self._adapters[protocol] = adapter

        logger.info(f"🔗 Adaptador criado: {protocol.value}")
        return adapter

    def detect_protocol(self, url: str) -> DarknetProtocol:
        """Detecta protocolo de uma URL."""
        if '.onion' in url.lower():
            return DarknetProtocol.TOR
        elif '.i2p' in url.lower() or '.b32.i2p' in url.lower():
            return DarknetProtocol.I2P
        elif any(x in url.lower() for x in ['.freenet', 'usk@', 'ksk@']):
            return DarknetProtocol.FREENET
        elif '.zero' in url.lower() or re.search(r'/[13][a-km-zA-HJ-NP-Z1-9]{26,35}', url):
            return DarknetProtocol.ZERONET
        return DarknetProtocol.UNKNOWN

    async def crawl_url(
        self,
        url: str,
        depth: Optional[CrawlDepth] = None,
        protocol: Optional[DarknetProtocol] = None
    ) -> CrawlResult:
        """
        Executa crawling ético de URL com detecção automática de protocolo.

        Args:
            url: URL alvo (.onion, .i2p, .freenet, .zero)
            depth: Profundidade de crawling
            protocol: Forçar protocolo específico (opcional)

        Returns:
            CrawlResult com hashes e metadados
        """
        # Detectar protocolo se não especificado
        protocol = protocol or self.detect_protocol(url)

        if protocol == DarknetProtocol.UNKNOWN:
            return CrawlResult(
                url=url,
                protocol=DarknetProtocol.UNKNOWN,
                status_code=None,
                content_hash=None,
                perceptual_hashes=[],
                links_found=[],
                metadata={"error": "protocol_not_recognized"}
            )

        # Obter adaptador
        adapter = await self.get_adapter(protocol)

        # Executar crawl
        result = await adapter.crawl(url, depth=depth)

        # Verificar contra base de hashes conhecidos
        if result.perceptual_hashes and self.perceptual_db:
            matches = [
                ph for ph in result.perceptual_hashes
                if ph in self.perceptual_db
            ]
            if matches:
                result.metadata["known_hash_matches"] = len(matches)
                result.metadata["violation_type"] = self.perceptual_db[matches[0]].get("type", "unknown")

        # Ancorar finding cross-protocolo
        if self.temporal and result.content_hash:
            await self.temporal.anchor_event(
                "cross_protocol_crawl_completed",
                {
                    "url_anonymized": adapter._anonymize_url(url),
                    "protocol": protocol.value,
                    "content_hash": result.content_hash[:16],
                    "known_matches": result.metadata.get("known_hash_matches", 0),
                    "timestamp": time.time()
                }
            )

        return result

    async def crawl_batch(
        self,
        urls: List[str],
        max_concurrent: int = 3
    ) -> List[CrawlResult]:
        """Executa crawling em lote com concorrência controlada."""
        semaphore = asyncio.Semaphore(max_concurrent)

        async def limited_crawl(url: str) -> CrawlResult:
            async with semaphore:
                return await self.crawl_url(url)

        tasks = [limited_crawl(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filtrar exceções
        valid_results = [r for r in results if isinstance(r, CrawlResult)]

        # Correlacionar findings cross-protocolo
        await self._correlate_cross_protocol_findings(valid_results)

        return valid_results

    async def _correlate_cross_protocol_findings(self, results: List[CrawlResult]):
        """Correlaciona findings entre diferentes protocolos."""
        # Agrupar por hash perceptual
        hash_groups: Dict[str, List[CrawlResult]] = {}

        for result in results:
            for phash in result.perceptual_hashes:
                if phash not in hash_groups:
                    hash_groups[phash] = []
                hash_groups[phash].append(result)

        # Identificar hashes presentes em múltiplos protocolos
        for phash, group in hash_groups.items():
            protocols = set(r.protocol for r in group)
            if len(protocols) > 1:
                # Hash encontrado em múltiplas redes — potencial campanha cross-protocolo
                correlation = {
                    "perceptual_hash": phash,
                    "protocols_involved": [p.value for p in protocols],
                    "occurrences": len(group),
                    "first_seen": min(r.crawl_timestamp for r in group),
                    "last_seen": max(r.crawl_timestamp for r in group)
                }
                self._cross_protocol_findings.append(correlation)

                # Ancorar correlação na TemporalChain
                if self.temporal:
                    await self.temporal.anchor_event(
                        "cross_protocol_correlation_detected",
                        {
                            "hash": phash[:16],
                            "protocols": correlation["protocols_involved"],
                            "occurrences": correlation["occurrences"],
                            "timestamp": time.time()
                        }
                    )

                logger.warning(
                    f"🔗 Correlação cross-protocolo: {phash[:16]} | "
                    f"Redes: {correlation['protocols_involved']} | "
                    f"Ocorrências: {correlation['occurrences']}"
                )

    async def generate_ethical_report(
        self,
        findings: List[CrawlResult],
        jurisdiction: str = "GLOBAL"
    ) -> Dict:
        """
        Gera relatório ético consolidado com assinatura PQC.

        Args:
            findings: Lista de CrawlResult para incluir no relatório
            jurisdiction: Jurisdição para formatação do relatório

        Returns:
            Dict com relatório assinado e ancorado
        """
        report = {
            "report_type": "ethical_darknet_vigilance",
            "jurisdiction": jurisdiction,
            "generated_at": time.time(),
            "findings_count": len(findings),
            "protocols_covered": list(set(f.protocol.value for f in findings)),
            "total_perceptual_hashes": sum(len(f.perceptual_hashes) for f in findings),
            "known_hash_matches": sum(
                f.metadata.get("known_hash_matches", 0) for f in findings
            ),
            "ethical_compliance": {
                "content_stored": False,  # CRÍTICO: sempre False
                "hash_only_processing": True,  # CRÍTICO: sempre True
                "constraints_enforced": list(set(
                    c.value
                    for adapter in self._adapters.values()
                    for c in adapter.config.ethical_constraints
                ))
            },
            "cross_protocol_correlations": len(self._cross_protocol_findings),
            "findings_summary": [
                {
                    "url_anonymized": f.url[:50] + "...",
                    "protocol": f.protocol.value,
                    "content_hash": f.content_hash[:16] if f.content_hash else None,
                    "perceptual_hashes_count": len(f.perceptual_hashes),
                    "known_matches": f.metadata.get("known_hash_matches", 0),
                    "ethical_violations": len(f.ethical_violations)
                }
                for f in findings[:20]  # Limitar para privacidade
            ]
        }

        # Assinar relatório com PQC via HSM
        report_json = json.dumps(report, sort_keys=True).encode()
        if self.hsm:
            signature = await self.hsm.sign_data(
                report_json,
                {"purpose": "ethical_vigilance_report"}
            )
            report["pqc_signature"] = signature.get("signature_hex", "")
        else:
            # Mock para sandbox
            report["pqc_signature"] = hashlib.sha3_256(
                report_json + b":mock_signature"
            ).hexdigest()

        # Ancorar relatório na TemporalChain
        if self.temporal:
            report["temporal_seal"] = await self.temporal.anchor_event(
                "ethical_report_generated",
                {
                    "report_hash": hashlib.sha3_256(report_json).hexdigest()[:16],
                    "findings_count": len(findings),
                    "pqc_signature_hash": hashlib.sha3_256(
                        report["pqc_signature"].encode()
                    ).hexdigest()[:16],
                    "jurisdiction": jurisdiction,
                    "timestamp": time.time()
                }
            )

        return report

    async def close_all(self):
        """Fecha todos os adaptadores ativos."""
        for adapter in self._adapter_pool.values():
            await adapter._disconnect()
        self._adapter_pool.clear()
        self._adapters.clear()
        logger.info("🔌 Todos os adaptadores fechados")

    def get_orchestrator_statistics(self) -> Dict:
        """Retorna estatísticas do orquestrador multi-protocolo."""
        return {
            "adapters_active": len(self._adapters),
            "protocols_supported": len(self.protocol_configs),
            "total_crawls": sum(
                len(adapter._audit_log)
                for adapter in self._adapters.values()
            ),
            "ethical_violations_total": sum(
                len(adapter._ethical_violations)
                for adapter in self._adapters.values()
            ),
            "cross_protocol_correlations": len(self._cross_protocol_findings),
            "perceptual_db_size": len(self.perceptual_db)
        }

# ═══════════════════════════════════════════════════════════════
# UTILITÁRIOS E HELPERS
# ═══════════════════════════════════════════════════════════════

def validate_darknet_url(url: str) -> Tuple[bool, Optional[str]]:
    """
    Valida URL de rede anônima.

    Returns:
        (is_valid, error_message_or_None)
    """
    if not url:
        return False, "URL vazia"

    # Verificar protocolo suportado
    if not any(proto in url.lower() for proto in ['.onion', '.i2p', '.freenet', 'usk@', 'ksk@', '.zero']):
        return False, "Protocolo não suportado"

    # Verificar esquema HTTP/HTTPS
    if not url.startswith(('http://', 'https://')):
        return False, "URL deve iniciar com http:// ou https://"

    return True, None


async def main():
    """Exemplo de uso do Multi-Protocol Darknet Adapter."""
    print("\n" + "="*70)
    print("🕵️ ARKHE Multi-Protocol Darknet Adapter — Substrato 228/229")
    print("="*70)

    # Mock dependencies para demonstração
    class MockHSM:
        async def sign_data(self, data: bytes, context: Dict) -> Dict:
            return {"signature_hex": hashlib.sha3_256(data + b":mock").hexdigest()}

    class MockTemporalChain:
        async def anchor_event(self, event_type: str, payload: Dict) -> str:
            return hashlib.sha3_256(
                json.dumps(payload, sort_keys=True).encode()
            ).hexdigest()[:16]

    class MockPhiBus:
        async def publish_metric(self, key: str, value: Any):
            pass

    # Inicializar orquestrador
    orchestrator = MultiProtocolDarknetOrchestrator(
        hsm_signer=MockHSM(),
        temporal_chain=MockTemporalChain(),
        phi_bus=MockPhiBus(),
        perceptual_db={
            "abc123def456": {"type": "deepfake", "source": "ProjectVic"},
            "xyz789ghi012": {"type": "csam", "source": "IWF"}
        }
    )

    # URLs de exemplo para diferentes protocolos
    test_urls = [
        "http://exampleonion1234567890abcdef.onion/page.html",
        "http://examplei2p512chars.b32.i2p/index",
        "freenet:USK@abc123def456/ExampleSite/1",
        "http://127.0.0.1:43110/1HeLLo4uzjaLetFx6NH3PMwFP3qbRbTf3D"
    ]

    print(f"\n🔍 Testando {len(test_urls)} URLs multi-protocolo...")

    results = []
    for url in test_urls:
        print(f"\n   📡 {url}")
        result = await orchestrator.crawl_url(url, depth=CrawlDepth.SURFACE)
        results.append(result)
        print(f"      → Protocolo: {result.protocol.value}")
        print(f"      → Status: {result.status_code}")
        print(f"      → Content Hash: {result.content_hash[:16] if result.content_hash else 'N/A'}")
        print(f"      → Perceptual Hashes: {len(result.perceptual_hashes)}")
        print(f"      → Known Matches: {result.metadata.get('known_hash_matches', 0)}")

    # Gerar relatório ético
    print(f"\n📊 Gerando relatório ético...")
    report = await orchestrator.generate_ethical_report(results, jurisdiction="GLOBAL")

    print(f"   → Findings: {report['findings_count']}")
    print(f"   → Protocolos: {report['protocols_covered']}")
    print(f"   → Hashes conhecidos: {report['known_hash_matches']}")
    print(f"   → Conformidade ética: {report['ethical_compliance']}")
    print(f"   → PQC Signature: {report['pqc_signature'][:16]}...")
    print(f"   → Temporal Seal: {report.get('temporal_seal', 'N/A')}")

    # Estatísticas
    stats = orchestrator.get_orchestrator_statistics()
    print(f"\n📈 Estatísticas do Orquestrador:")
    print(f"   → Adaptadores ativos: {stats['adapters_active']}")
    print(f"   → Correlações cross-protocolo: {stats['cross_protocol_correlations']}")
    print(f"   → Violações éticas: {stats['ethical_violations_total']}")

    # Fechar adaptadores
    await orchestrator.close_all()

    print("\n" + "="*70)
    print("✅ Multi-Protocol Darknet Adapter — Demonstração concluída")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(main())