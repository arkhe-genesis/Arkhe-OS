#!/usr/bin/env python3
"""
ARKHE OS Substrate 250: Multi-Domain GPO Engine
Canon: ∞.Ω.∇+++.250.multi_domain_gpo

Suporte a Group Policy em florestas Active Directory multi-domínio
com resolução de conflitos, validação constitucional e auditoria cross-domain.
"""

import asyncio
import hashlib
import json
import logging
import time
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set

try:
    import ldap3  # Mock: em produção, usar ldap3 para AD queries
except ImportError:
    ldap3 = None

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)-8s | %(message)s')
logger = logging.getLogger(__name__)

# =============================================================================
# TIPOS CANÔNICOS DE MULTI-DOMAIN GPO
# =============================================================================

class DomainTrustType(Enum):
    """Tipos de trust entre domínios AD."""
    TWO_WAY = "two_way"
    ONE_WAY_INBOUND = "one_way_inbound"
    ONE_WAY_OUTBOUND = "one_way_outbound"
    NONE = "none"

@dataclass
class ADDomain:
    """Representação de um domínio Active Directory."""
    domain_name: str              # Ex: "production.arkhe.org"
    domain_sid: str               # Security Identifier do domínio
    forest_name: str              # Nome da floresta
    trust_relationships: Dict[str, DomainTrustType]  # domain_name -> trust_type
    arkhe_ou_path: str            # OU onde políticas ARKHE são aplicadas
    security_groups: List[str]    # Grupos para security filtering

    def can_receive_policy_from(self, source_domain: 'ADDomain') -> bool:
        """Verifica se este domínio pode receber políticas do domínio fonte."""
        trust = self.trust_relationships.get(source_domain.domain_name, DomainTrustType.NONE)
        return trust in [DomainTrustType.TWO_WAY, DomainTrustType.ONE_WAY_INBOUND]

@dataclass
class CrossDomainPolicy:
    """Política ARKHE com escopo multi-domínio."""
    gpo_name: str
    gpo_guid: str
    scope_domains: List[str]          # Domínios onde esta política se aplica
    enforcement_level: str            # "enforced", "preferred", "not_configured"
    security_filter_groups: List[str] # Grupos AD para filtering
    wmi_filter: Optional[str]         # Query WMI para targeting adicional
    constitutional_override: bool     # Se pode sobrescrever políticas locais
    arkhe_values: Dict[str, Any]      # Valores ARKHE a serem aplicados
    created_timestamp: float
    last_modified_timestamp: float
    temporal_chain_seal: Optional[str]

@dataclass
class PolicyApplicationResult:
    """Resultado da aplicação de política multi-domínio."""
    target_domain: str
    target_computer: str
    gpo_name: str
    applied: bool
    values_applied: int
    values_skipped: int  # Por conflito ou filtering
    values_rejected: int  # Por validação constitucional
    conflicts_resolved: Dict[str, str]  # conflicted_value -> resolution_reason
    constitutional_check: str
    temporal_chain_seal: Optional[str]
    application_timestamp: float

# =============================================================================
# ENGINE MULTI-DOMAIN GPO
# =============================================================================

class MultiDomainGPOEngine:
    """Motor de Group Policy para florestas Active Directory multi-domínio."""

    def __init__(self, forest_root: str, ldap_server: str,
                 bind_user: str, bind_password: str):
        self.forest_root = forest_root
        self.ldap_server = ldap_server
        self.credentials = (bind_user, bind_password)
        self._domains: Dict[str, ADDomain] = {}
        self._policies: Dict[str, CrossDomainPolicy] = {}
        self._application_history: List[PolicyApplicationResult] = []

    async def discover_forest_domains(self) -> List[ADDomain]:
        """Descobre domínios na floresta via LDAP."""
        domains = []

        try:
            if not ldap3:
                raise Exception("ldap3 not installed")
            # Conectar ao LDAP (mock: em produção, usar ldap3.Server/Connection)
            server = ldap3.Server(self.ldap_server, get_info=ldap3.ALL)
            conn = ldap3.Connection(server, user=self.credentials[0],
                                   password=self.credentials[1], auto_bind=True)

            # Query para domínios na floresta (mock)
            conn.search(
                search_base=f"DC={self.forest_root.replace('.', ',DC=')}",
                search_filter="(objectClass=domain)",
                attributes=["name", "objectSid", "trustPartner"]
            )

            for entry in conn.entries:
                domain = ADDomain(
                    domain_name=str(entry.name),
                    domain_sid=str(entry.objectSid),
                    forest_name=self.forest_root,
                    trust_relationships={},  # Preencher via query adicional
                    arkhe_ou_path=f"OU=ARKHE-Managed,DC={str(entry.name).replace('.', ',DC=')}",
                    security_groups=[f"ARKHE-Policy-Users@{entry.name}"]
                )
                domains.append(domain)
                self._domains[domain.domain_name] = domain

            conn.unbind()

        except Exception as e:
            logger.error(f"❌ Forest discovery failed: {e}")
            # Fallback: usar configuração estática
            domains = self._load_static_domain_config()
            for domain in domains:
                self._domains[domain.domain_name] = domain

        return domains

    def _load_static_domain_config(self) -> List[ADDomain]:
        """Configuração estática de fallback para domínios."""
        return [
            ADDomain(
                domain_name="production.arkhe.org",
                domain_sid="S-1-5-21-prod-123456",
                forest_name=self.forest_root,
                trust_relationships={
                    "development.arkhe.org": DomainTrustType.TWO_WAY,
                    "partner.arkhe.org": DomainTrustType.ONE_WAY_OUTBOUND
                },
                arkhe_ou_path="OU=ARKHE-Managed,DC=production,DC=arkhe,DC=org",
                security_groups=["ARKHE-Prod-Admins", "ARKHE-ASI-Service"]
            ),
            ADDomain(
                domain_name="development.arkhe.org",
                domain_sid="S-1-5-21-dev-789012",
                forest_name=self.forest_root,
                trust_relationships={
                    "production.arkhe.org": DomainTrustType.TWO_WAY
                },
                arkhe_ou_path="OU=ARKHE-Test,DC=development,DC=arkhe,DC=org",
                security_groups=["ARKHE-Dev-Team"]
            ),
            ADDomain(
                domain_name="partner.arkhe.org",
                domain_sid="S-1-5-21-partner-345678",
                forest_name=self.forest_root,
                trust_relationships={
                    "production.arkhe.org": DomainTrustType.ONE_WAY_INBOUND
                },
                arkhe_ou_path="OU=External-Access,DC=partner,DC=arkhe,DC=org",
                security_groups=["ARKHE-Partner-Access"]
            )
        ]

    def create_cross_domain_policy(self, gpo_name: str, scope_domains: List[str],
                                  arkhe_values: Dict[str, Any],
                                  enforcement_level: str = "preferred",
                                  constitutional_override: bool = False) -> CrossDomainPolicy:
        """Cria nova política com escopo multi-domínio."""
        # Validar que todos os domínios existem e têm trust adequado
        for domain_name in scope_domains:
            if domain_name not in self._domains:
                raise ValueError(f"Domain not found: {domain_name}")

        # Verificar trust relationships para políticas cross-domain
        if len(scope_domains) > 1:
            self._validate_cross_domain_trusts(scope_domains)

        policy = CrossDomainPolicy(
            gpo_name=gpo_name,
            gpo_guid=hashlib.sha3_256(f"{gpo_name}:{time.time()}".encode()).hexdigest(),
            scope_domains=scope_domains,
            enforcement_level=enforcement_level,
            security_filter_groups=[f"ARKHE-Policy-Users@{d}" for d in scope_domains],
            wmi_filter=None,
            constitutional_override=constitutional_override,
            arkhe_values=arkhe_values,
            created_timestamp=time.time(),
            last_modified_timestamp=time.time(),
            temporal_chain_seal=None
        )

        self._policies[policy.gpo_guid] = policy
        return policy

    def _validate_cross_domain_trusts(self, domain_names: List[str]):
        """Valida que domínios têm trust relationships adequados para políticas cross-domain."""
        for i, domain1 in enumerate(domain_names):
            for domain2 in domain_names[i+1:]:
                d1 = self._domains[domain1]
                d2 = self._domains[domain2]

                # Pelo menos um domínio deve confiar no outro
                trust_1_to_2 = d1.trust_relationships.get(domain2, DomainTrustType.NONE)
                trust_2_to_1 = d2.trust_relationships.get(domain1, DomainTrustType.NONE)

                if trust_1_to_2 == DomainTrustType.NONE and trust_2_to_1 == DomainTrustType.NONE:
                    raise ValueError(f"No trust relationship between {domain1} and {domain2}")

    async def apply_policy_to_domain(self, policy: CrossDomainPolicy,
                                    target_domain: str) -> List[PolicyApplicationResult]:
        """Aplica política a computadores em um domínio específico."""
        if target_domain not in policy.scope_domains:
            logger.warning(f"⚠️  Policy {policy.gpo_name} not scoped to domain {target_domain}")
            return []

        results = []

        # Obter lista de computadores no OU ARKHE do domínio (mock LDAP query)
        target_computers = self._get_target_computers(target_domain, policy.security_filter_groups)

        for computer in target_computers:
            result = await self._apply_policy_to_computer(policy, target_domain, computer)
            results.append(result)

            # Ancorar resultado na TemporalChain
            if result.applied or result.values_rejected > 0:
                result.temporal_chain_seal = await self._anchor_policy_application(result)

            self._application_history.append(result)

        return results

    def _get_target_computers(self, domain_name: str, security_groups: List[str]) -> List[str]:
        """Obtém lista de computadores alvo via LDAP com security filtering."""
        # Mock: retornar computadores simulados
        return [
            f"SRV-PROD-001.{domain_name}",
            f"SRV-PROD-002.{domain_name}",
            f"WS-ADMIN-042.{domain_name}"
        ]

    async def _apply_policy_to_computer(self, policy: CrossDomainPolicy,
                                       domain_name: str, computer_name: str) -> PolicyApplicationResult:
        """Aplica política a um computador específico com resolução de conflitos."""
        values_applied = 0
        values_skipped = 0
        values_rejected = 0
        conflicts_resolved = {}

        # Obter políticas existentes no computador (mock: consultar Registry local)
        existing_values = self._get_computer_registry_values(computer_name)

        for reg_path, new_value in policy.arkhe_values.items():
            # Verificar filtering por security groups (mock)
            if not self._check_security_filter(computer_name, policy.security_filter_groups):
                values_skipped += 1
                continue

            # Verificar conflito com valor existente
            if reg_path in existing_values:
                existing_value = existing_values[reg_path]
                if existing_value != new_value:
                    # Resolver conflito baseado em enforcement level
                    resolution = self._resolve_conflict(
                        reg_path, existing_value, new_value,
                        policy.enforcement_level, policy.constitutional_override
                    )
                    conflicts_resolved[reg_path] = resolution

                    if resolution == "skip":
                        values_skipped += 1
                        continue
                    elif resolution == "reject":
                        values_rejected += 1
                        continue
                    # else: "apply" - prosseguir

            # Validação constitucional antes de aplicar
            if not self._validate_constitutional(reg_path, new_value, domain_name):
                logger.warning(f"⚠️  Constitutional check failed: {reg_path} in {domain_name}")
                values_rejected += 1
                conflicts_resolved[reg_path] = "constitutional_rejection"
                continue

            # Aplicar valor (mock: em produção, via RPC/Registry API)
            success = self._set_registry_value(computer_name, reg_path, new_value)
            if success:
                values_applied += 1
            else:
                values_rejected += 1

        return PolicyApplicationResult(
            target_domain=domain_name,
            target_computer=computer_name,
            gpo_name=policy.gpo_name,
            applied=values_applied > 0,
            values_applied=values_applied,
            values_skipped=values_skipped,
            values_rejected=values_rejected,
            conflicts_resolved=conflicts_resolved,
            constitutional_check="passed" if values_rejected == 0 else "partial",
            temporal_chain_seal=None,  # Preenchido após ancoragem
            application_timestamp=time.time()
        )

    def _resolve_conflict(self, reg_path: str, existing_value: Any, new_value: Any,
                         enforcement: str, constitutional_override: bool) -> str:
        """Resolve conflito entre valor existente e novo valor de política."""
        # Regras de resolução baseadas em enforcement level
        if enforcement == "enforced":
            return "apply"  # Política enforced sempre prevalece
        elif enforcement == "preferred":
            if constitutional_override:
                return "apply"  # Override constitucional permite aplicar
            else:
                return "skip"  # Respeitar valor local se não for enforced
        else:  # not_configured
            return "skip"

    def _validate_constitutional(self, reg_path: str, value: Any, domain_name: str) -> bool:
        """Valida valor contra princípios constitucionais P1-P7 no contexto do domínio."""
        # P1: Verificação Formal - Security/FipsMode não pode ser desabilitado
        if reg_path == "Security/FipsMode" and value == 0:
            return False

        # P4: Federação Cross-Platform - Network/BusPort deve ser consistente entre domínios
        if reg_path == "Network/BusPort" and domain_name == "partner.arkhe.org":
            # Parceiros devem usar porta padrão para interoperabilidade
            return value == 8080

        # P7: Energia como Recurso - Thread pool não pode ser excessivo em domínios parceiros
        if reg_path == "Service/ThreadPoolSize" and domain_name == "partner.arkhe.org":
            return value <= 32  # Limitar recursos em domínios externos

        return True

    def _check_security_filter(self, computer_name: str, security_groups: List[str]) -> bool:
        """Verifica se computador pertence a grupos de segurança para filtering."""
        # Mock: simular verificação de associação a grupos AD
        # Em produção: consultar LDAP para group membership
        return True  # Mock: assumir que passa no filter

    def _get_computer_registry_values(self, computer_name: str) -> Dict[str, Any]:
        """Obtém valores de Registry existentes no computador (mock)."""
        return {
            "Network/BusPort": 8080,
            "Service/ThreadPoolSize": 16
        }

    def _set_registry_value(self, computer_name: str, reg_path: str, value: Any) -> bool:
        """Define valor de Registry no computador remoto (mock)."""
        # Em produção: usar RPC, WMI, ou PSRemoting para definir Registry remoto
        logger.debug(f"🔧 Setting {computer_name}: {reg_path} = {value}")
        return True  # Mock: assumir sucesso

    async def _anchor_policy_application(self, result: PolicyApplicationResult) -> str:
        """Ancora resultado de aplicação de política na TemporalChain."""
        payload = {
            "gpo_name": result.gpo_name,
            "target_domain": result.target_domain,
            "target_computer": result.target_computer,
            "values_applied": result.values_applied,
            "values_rejected": result.values_rejected,
            "constitutional_check": result.constitutional_check,
            "timestamp": result.application_timestamp
        }
        seal = hashlib.sha3_256(
            json.dumps(payload, sort_keys=True).encode()
        ).hexdigest()
        logger.debug(f"🔗 Policy application anchored: {seal[:16]}...")
        return seal

    def get_policy_status(self, domain_name: Optional[str] = None) -> Dict:
        """Retorna status consolidado de políticas aplicadas."""
        filtered_history = self._application_history
        if domain_name:
            filtered_history = [r for r in filtered_history if r.target_domain == domain_name]

        if not filtered_history:
            return {"policies_applied": 0}

        total_applied = sum(r.values_applied for r in filtered_history)
        total_rejected = sum(r.values_rejected for r in filtered_history)

        return {
            "domain": domain_name or "all",
            "total_applications": len(filtered_history),
            "computers_targeted": len(set(r.target_computer for r in filtered_history)),
            "values_applied": total_applied,
            "values_rejected": total_rejected,
            "constitutional_compliance_rate": 1.0 - (total_rejected / max(1, total_applied + total_rejected)),
            "last_application": max(r.application_timestamp for r in filtered_history)
        }
