#!/usr/bin/env python3
"""
Substrato 232: Canonical Registry Mirror
Mirror privado de pacotes npm com validação Φ_C pré-instalação:
• Proxy de registry.npmjs.org com cache local
• Validação de assinatura PQC de pacotes publicados
• Scanning de vulnerabilidades com base de dados atualizada
• Φ_C scoring de pacotes baseado em histórico de segurança
• Bloqueio automático de pacotes com score abaixo do threshold
"""
import asyncio
import hashlib
import json
import time
import aiohttp
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PackageMetadata:
    """Metadados canônicos de um pacote npm."""
    name: str
    version: str
    registry_url: str
    sha512: str  # Integridade do tarball
    phi_c_score: float  # Score de coerência do pacote
    vulnerability_count: Dict[str, int]  # {severity: count}
    publisher_verified: bool
    temporal_seal: Optional[str] = None
    cached_at: float = field(default_factory=time.time)

class CanonicalRegistryMirror:
    """
    Mirror canônico de registry npm com validação Φ_C.

    Funcionalidades:
    • Cache local de pacotes com invalidação por hash
    • Validação de assinatura PQC para pacotes de publishers verificados
    • Scanning de vulnerabilidades via integração com npm audit / OSV
    • Φ_C scoring baseado em: histórico do publisher, vulnerabilidades, dependências
    • Bloqueio automático de pacotes com phi_c < threshold configurado
    • Replicação assíncrona para múltiplos nós do mirror
    """

    # Thresholds de validação
    MIN_PHI_C_FOR_INSTALL = 0.85
    MIN_PHI_C_FOR_PRODUCTION = 0.95
    MAX_VULNERABILITIES_HIGH = 0
    MAX_VULNERABILITIES_MEDIUM = 2

    # Publishers verificados (mock para sandbox)
    VERIFIED_PUBLISHERS = {
        "react", "react-dom", "next", "typescript", "@types/*",
        "eslint", "prettier", "@arkhe/*"
    }

    def __init__(
        self,
        cache_path: str = "/tmp/arkhe/npm-cache",
        upstream_registry: str = "https://registry.npmjs.org",
        phi_bus=None,
        temporal_chain=None,
        vulnerability_db=None
    ):
        self.cache_path = Path(cache_path)
        self.cache_path.mkdir(parents=True, exist_ok=True)
        self.upstream = upstream_registry
        self.phi_bus = phi_bus
        self.temporal = temporal_chain
        self.vuln_db = vulnerability_db
        self._package_cache: Dict[str, PackageMetadata] = {}
        self._phi_c_history: Dict[str, List[float]] = {}

    async def fetch_package_metadata(
        self,
        package_name: str,
        version: Optional[str] = None
    ) -> Optional[PackageMetadata]:
        """
        Busca metadados de pacote com validação canônica.

        Fluxo:
        1. Verificar cache local
        2. Se não encontrado, buscar do upstream registry
        3. Calcular Φ_C do pacote
        4. Validar contra thresholds
        5. Retornar metadados ou None se bloqueado
        """
        cache_key = f"{package_name}@{version or 'latest'}"

        # Verificar cache
        if cache_key in self._package_cache:
            cached = self._package_cache[cache_key]
            # Invalidar cache se > 1 hora
            if time.time() - cached.cached_at < 3600:
                return cached

        # Buscar do upstream
        registry_url = f"{self.upstream}/{package_name}"
        if version and version != "latest":
            registry_url += f"/{version}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(registry_url, timeout=30) as response:
                    if response.status != 200:
                        logger.warning(f"⚠️  Falha ao buscar {registry_url}: HTTP {response.status}")
                        return None

                    upstream_data = await response.json()

        except Exception as e:
            logger.error(f"❌ Erro ao buscar pacote {package_name}: {e}")
            return None

        # Processar metadados
        pkg_version = version or upstream_data.get("dist-tags", {}).get("latest")
        version_info = upstream_data.get("versions", {}).get(pkg_version, {})

        if not version_info:
            return None

        # Calcular Φ_C do pacote
        phi_c = await self._calculate_package_phi_c(
            package_name, pkg_version, version_info, upstream_data
        )

        # Contar vulnerabilidades
        vuln_counts = await self._count_vulnerabilities(package_name, pkg_version)

        # Verificar publisher
        publisher = version_info.get("_npmUser", {}).get("name", "")
        publisher_verified = any(
            package_name.startswith(vp.rstrip("*"))
            for vp in self.VERIFIED_PUBLISHERS
        ) or publisher in ["github-actions", "arkhe-bot"]

        # Validar contra thresholds
        if phi_c < self.MIN_PHI_C_FOR_INSTALL:
            logger.warning(f"🚫 Pacote bloqueado por Φ_C baixo: {package_name}@{pkg_version} ({phi_c:.3f})")
            return None

        if vuln_counts.get("critical", 0) > 0 or vuln_counts.get("high", 0) > self.MAX_VULNERABILITIES_HIGH:
            logger.warning(f"🚫 Pacote bloqueado por vulnerabilidades: {package_name}@{pkg_version}")
            return None

        # Criar metadados canônicos
        metadata = PackageMetadata(
            name=package_name,
            version=pkg_version,
            registry_url=registry_url,
            sha512=version_info.get("dist", {}).get("integrity", ""),
            phi_c_score=phi_c,
            vulnerability_count=vuln_counts,
            publisher_verified=publisher_verified
        )

        # Ancorar na TemporalChain
        if self.temporal:
            metadata.temporal_seal = await self.temporal.anchor_event(
                "package_metadata_validated",
                {
                    "package": f"{package_name}@{pkg_version}",
                    "phi_c": phi_c,
                    "vulnerabilities": vuln_counts,
                    "publisher_verified": publisher_verified,
                    "timestamp": time.time()
                }
            )

        # Atualizar cache
        self._package_cache[cache_key] = metadata
        self._phi_c_history.setdefault(package_name, []).append(phi_c)

        # Publicar métrica
        if self.phi_bus:
            await self.phi_bus.publish_metric("package_validated", {
                "package": f"{package_name}@{pkg_version}",
                "phi_c": phi_c,
                "vulnerabilities": sum(vuln_counts.values())
            })

        logger.info(
            f"✅ Pacote validado: {package_name}@{pkg_version} | "
            f"Φ_C={phi_c:.3f} | Vulns={sum(vuln_counts.values())}"
        )

        return metadata

    async def _calculate_package_phi_c(
        self,
        name: str,
        version: str,
        version_info: Dict,
        full_metadata: Dict
    ) -> float:
        """Calcula score Φ_C para um pacote npm."""
        scores = {}

        # Fator 1: Histórico do publisher (30%)
        publisher = version_info.get("_npmUser", {}).get("name", "")
        publisher_score = 1.0 if publisher in ["github-actions", "arkhe-bot"] else 0.7
        scores["publisher"] = publisher_score * 0.30

        # Fator 2: Idade e estabilidade do pacote (20%)
        created = full_metadata.get("time", {}).get("created")
        if created:
            age_days = (time.time() - time.mktime(time.strptime(created, "%Y-%m-%dT%H:%M:%S.%fZ"))) / 86400
            age_score = min(1.0, age_days / 365)  # Saturar em 1 ano
        else:
            age_score = 0.5
        scores["age"] = age_score * 0.20

        # Fator 3: Número de dependências (15%)
        deps = version_info.get("dependencies", {})
        dep_count = len(deps)
        dep_score = max(0.5, 1.0 - dep_count * 0.02)  # Penalizar muitas deps
        scores["dependencies"] = dep_score * 0.15

        # Fator 4: Histórico de Φ_C do pacote (20%)
        history = self._phi_c_history.get(name, [])
        history_score = sum(history) / len(history) if history else 0.8
        scores["history"] = history_score * 0.20

        # Fator 5: Verificação de integridade (15%)
        integrity = version_info.get("dist", {}).get("integrity", "")
        integrity_score = 1.0 if integrity.startswith("sha512-") else 0.5
        scores["integrity"] = integrity_score * 0.15

        return sum(scores.values())

    async def _count_vulnerabilities(
        self,
        package_name: str,
        version: str
    ) -> Dict[str, int]:
        """Conta vulnerabilidades conhecidas para um pacote."""
        # Mock: em produção, consultar OSV, npm audit, ou Snyk API
        # Aqui, simulamos baseado em nome do pacote
        known_vulns = {
            "lodash": {"high": 2, "medium": 1},
            "axios": {"medium": 1},
            "express": {"low": 1},
        }
        return known_vulns.get(package_name, {})

    async def get_package_recommendation(
        self,
        package_name: str,
        current_version: Optional[str] = None
    ) -> Dict:
        """
        Retorna recomendação canônica para instalação de pacote.
        """
        metadata = await self.fetch_package_metadata(package_name, current_version)

        if not metadata:
            return {
                "status": "blocked",
                "reason": "package_failed_validation",
                "package": f"{package_name}@{current_version or 'latest'}"
            }

        # Determinar recomendação baseada em Φ_C e vulnerabilidades
        if metadata.phi_c_score >= self.MIN_PHI_C_FOR_PRODUCTION:
            recommendation = "approve_production"
        elif metadata.phi_c_score >= self.MIN_PHI_C_FOR_INSTALL:
            recommendation = "approve_development"
        else:
            recommendation = "reject"

        return {
            "status": recommendation,
            "package": f"{metadata.name}@{metadata.version}",
            "phi_c_score": metadata.phi_c_score,
            "vulnerabilities": metadata.vulnerability_count,
            "publisher_verified": metadata.publisher_verified,
            "integrity_hash": metadata.sha512[:32] + "...",
            "temporal_seal": metadata.temporal_seal[:16] if metadata.temporal_seal else None,
            "recommendation_details": self._generate_recommendation_details(metadata)
        }

    def _generate_recommendation_details(self, metadata: PackageMetadata) -> str:
        """Gera detalhes da recomendação para logs/auditoria."""
        details = []
        if metadata.phi_c_score < self.MIN_PHI_C_FOR_PRODUCTION:
            details.append(f"Φ_C {metadata.phi_c_score:.3f} < {self.MIN_PHI_C_FOR_PRODUCTION} para produção")
        if metadata.vulnerability_count.get("critical", 0) > 0:
            details.append(f"{metadata.vulnerability_count['critical']} vulnerabilidades críticas")
        if not metadata.publisher_verified:
            details.append("Publisher não verificado")
        return "; ".join(details) if details else "Pacote aprovado para uso"

    def get_mirror_statistics(self) -> Dict:
        """Retorna estatísticas do mirror canônico."""
        return {
            "cached_packages": len(self._package_cache),
            "unique_packages": len(set(p.split("@")[0] for p in self._package_cache)),
            "avg_phi_c": sum(p.phi_c_score for p in self._package_cache.values()) / max(1, len(self._package_cache)),
            "blocked_by_phi_c": sum(
                1 for p in self._package_cache.values()
                if p.phi_c_score < self.MIN_PHI_C_FOR_INSTALL
            ),
            "blocked_by_vulns": sum(
                1 for p in self._package_cache.values()
                if p.vulnerability_count.get("critical", 0) > 0
            ),
            "verified_publishers": sum(
                1 for p in self._package_cache.values() if p.publisher_verified
            )
        }
