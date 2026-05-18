#!/usr/bin/env python3
"""
ARKHE OS Substrate 216: Federated Grammar Registry Service
Canon: ∞.Ω.∇+++.216.federation.grammar_registry
Função: Serviço federado para compartilhamento seguro de gramáticas
tree-sitter/ANTLR entre organizações, com privacidade diferencial
e validação de integridade via PQC.
"""

import asyncio
import hashlib
import json
import time
import aiohttp
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Set
from enum import Enum, auto
from pathlib import Path
import logging
import numpy as np

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)-8s | %(message)s')
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# TIPOS CANÔNICOS DE FEDERAÇÃO
# ═══════════════════════════════════════════════════════════════

class GrammarEngine(Enum):
    """Motores de gramática suportados."""
    TREE_SITTER = "tree_sitter"
    ANTLR4 = "antlr4"
    REGEX = "regex"
    CUSTOM = "custom"

@dataclass
class GrammarMetadata:
    """Metadados de uma gramática federada."""
    grammar_id: str                    # UUID único
    language: str                      # Nome da linguagem
    engine: GrammarEngine              # tree-sitter, antlr4, etc.
    version: str                       # Versão da gramática
    source_org_hash: str               # Hash anonimizado da organização fonte
    grammar_hash: str                  # SHA3-256 do conteúdo da gramática
    pqc_signature: str                 # Assinatura PQC do agregador
    phi_c_contribution: float          # Contribuição para Φ_C global (0.0-1.0)
    privacy_epsilon: float             # ε para privacidade diferencial [2.0, 5.0]
    created_at: float
    last_updated: float
    download_count: int = 0
    validation_status: str = "pending"  # pending, validated, rejected

    def to_dict(self) -> Dict:
        return {
            **asdict(self),
            "engine": self.engine.value
        }

@dataclass
class FederatedGrammar:
    """Gramática federada com conteúdo e metadados."""
    metadata: GrammarMetadata
    grammar_content: str              # Conteúdo da gramática (WASM, .g4, etc.)
    dependencies: List[str]           # Dependências de outras gramáticas
    test_samples: List[Dict]          # Samples de teste para validação
    security_rules: List[Dict]        # Regras de segurança associadas

    def compute_content_hash(self) -> str:
        """Calcula hash do conteúdo da gramática."""
        return hashlib.sha3_256(self.grammar_content.encode()).hexdigest()

    def verify_integrity(self) -> bool:
        """Verifica integridade da gramática."""
        return self.compute_content_hash() == self.metadata.grammar_hash

# ═══════════════════════════════════════════════════════════════
# CLIENTE DO AGREGADOR FEDERADO
# ═══════════════════════════════════════════════════════════════

class FederatedGrammarClient:
    """Cliente para interação com agregador federado de gramáticas."""

    def __init__(
        self,
        aggregator_url: str,
        org_id: str,
        pqc_public_key: str,
        privacy_epsilon: float = 3.0
    ):
        self.aggregator_url = aggregator_url.rstrip('/')
        self.org_id = org_id
        self.org_hash = hashlib.sha3_256(org_id.encode()).hexdigest()[:32]
        self.pqc_public_key = pqc_public_key
        self.privacy_epsilon = privacy_epsilon
        self.session: Optional[aiohttp.ClientSession] = None

        # Cache local de gramáticas
        self._local_grammars: Dict[str, FederatedGrammar] = {}
        self._sync_timestamp: float = 0

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def fetch_global_grammars(
        self,
        languages: Optional[List[str]] = None,
        min_phi_c: float = 0.85
    ) -> List[GrammarMetadata]:
        """Busca metadados de gramáticas globais do agregador."""
        # Em sandbox/mock, simularemos o agregador.
        # Caso houvesse um backend real:
        """
        params = {
            "org_hash": self.org_hash,
            "min_phi_c": min_phi_c,
            "timestamp": time.time()
        }
        if languages:
            params["languages"] = ",".join(languages)

        async with self.session.get(
            f"{self.aggregator_url}/api/v1/grammars",
            params=params,
            headers={"X-PQC-Public-Key": self.pqc_public_key}
        ) as response:
            ...
        """
        # MOCK IMPLEMENTATION PARA O DEMO
        logger.info(f"Mock fetching grammars for {languages}")
        await asyncio.sleep(0.5)

        mock_grammars = []
        for lang in (languages or ["python", "cobol", "rust"]):
            mock_grammars.append(GrammarMetadata(
                grammar_id=f"grammar_{lang}_{int(time.time())}",
                language=lang,
                engine=GrammarEngine.TREE_SITTER,
                version="1.0.0",
                source_org_hash="other_org_hash",
                grammar_hash="hash_placeholder",
                pqc_signature="pqc_sig_placeholder",
                phi_c_contribution=0.92,
                privacy_epsilon=3.0,
                created_at=time.time(),
                last_updated=time.time(),
                validation_status="validated"
            ))
        return mock_grammars

    async def download_grammar(self, grammar_id: str) -> Optional[FederatedGrammar]:
        """Baixa conteúdo completo de uma gramática federada."""
        # MOCK IMPLEMENTATION PARA O DEMO
        await asyncio.sleep(0.3)
        lang = grammar_id.split('_')[1] if '_' in grammar_id else "unknown"
        content = f"(program (statement)*) // Mock content for {lang}"
        content_hash = hashlib.sha3_256(content.encode()).hexdigest()

        metadata = GrammarMetadata(
            grammar_id=grammar_id,
            language=lang,
            engine=GrammarEngine.TREE_SITTER,
            version="1.0.0",
            source_org_hash="other_org_hash",
            grammar_hash=content_hash,
            pqc_signature="pqc_sig_placeholder",
            phi_c_contribution=0.92,
            privacy_epsilon=3.0,
            created_at=time.time(),
            last_updated=time.time(),
            validation_status="validated"
        )

        grammar = FederatedGrammar(
            metadata=metadata,
            grammar_content=content,
            dependencies=[],
            test_samples=[],
            security_rules=[]
        )

        self._local_grammars[grammar_id] = grammar
        logger.info(f"✅ Gramática baixada (mock): {grammar_id} ({metadata.language})")
        return grammar

    async def contribute_grammar(
        self,
        grammar: FederatedGrammar,
        apply_privacy: bool = True
    ) -> Optional[str]:
        """Contribui com uma gramática local para a federação."""
        # Aplicar privacidade diferencial antes de enviar
        if apply_privacy:
            grammar = self._apply_differential_privacy(grammar, self.privacy_epsilon)

        # Calcular hash do conteúdo
        grammar.metadata.grammar_hash = grammar.compute_content_hash()

        # Preparar payload
        payload = {
            "metadata": grammar.metadata.to_dict(),
            "content": grammar.grammar_content,
            "dependencies": grammar.dependencies,
            "test_samples": grammar.test_samples,
            "security_rules": grammar.security_rules,
            "contributor_org_hash": self.org_hash,
            "privacy_epsilon": self.privacy_epsilon,
            "timestamp": time.time()
        }

        # Assinar payload com PQC local (mock)
        payload["contributor_signature"] = self._mock_pqc_sign(json.dumps(payload, sort_keys=True))

        # MOCK IMPLEMENTATION PARA O DEMO
        await asyncio.sleep(0.5)
        logger.info(f"✅ Gramática contribuída (mock): {grammar.metadata.grammar_id}")
        return grammar.metadata.grammar_id

    def _apply_differential_privacy(
        self,
        grammar: FederatedGrammar,
        epsilon: float
    ) -> FederatedGrammar:
        """Aplica privacidade diferencial ao conteúdo da gramática."""
        # Mock: em produção, aplicar ruído Laplace a metadados sensíveis
        # Aqui: apenas adicionar noise a contagens de uso

        # Adicionar ruído a download_count
        if grammar.metadata.download_count > 0:
            noise = np.random.laplace(0, 1/epsilon)
            grammar.metadata.download_count = max(0,
                int(grammar.metadata.download_count + noise))

        # Ofuscar parcialmente security_rules se epsilon baixo
        if epsilon < 3.0 and grammar.security_rules:
            # Remover regras com descrição muito específica
            grammar.security_rules = [
                r for r in grammar.security_rules
                if len(r.get("description", "")) < 100  # Heurística simples
            ]

        return grammar

    def _mock_pqc_sign(self, message: str) -> str:
        """Mock de assinatura PQC para sandbox."""
        return hashlib.sha3_256(f"{message}:{self.org_id}:{time.time()}".encode()).hexdigest()

    def _verify_aggregator_signature(self, data: Dict) -> bool:
        """Verifica assinatura PQC do agregador (mock)."""
        # Em produção: verificar com chave pública do agregador
        expected_sig = hashlib.sha3_256(
            f"{json.dumps(data, sort_keys=True)}:{self.pqc_public_key}".encode()
        ).hexdigest()
        return data.get("aggregator_signature") == expected_sig[:64]

    def get_local_grammar(self, language: str, engine: GrammarEngine) -> Optional[FederatedGrammar]:
        """Busca gramática no cache local por linguagem e engine."""
        for grammar in self._local_grammars.values():
            if (grammar.metadata.language == language and
                grammar.metadata.engine == engine):
                return grammar
        return None

    def sync_local_cache(self, max_age_hours: float = 24.0) -> int:
        """Sincroniza cache local com agregador se necessário."""
        if time.time() - self._sync_timestamp < max_age_hours * 3600:
            return 0  # Cache ainda válido

        # Em produção: buscar atualizações do agregador
        # Mock: apenas atualizar timestamp
        self._sync_timestamp = time.time()
        return len(self._local_grammars)

# ═══════════════════════════════════════════════════════════════
# INTEGRADOR COM UNI-KERNEL
# ═══════════════════════════════════════════════════════════════

class UniKernelGrammarIntegrator:
    """Integra gramáticas federadas com o Uni‑Kernel Polyglot."""

    def __init__(
        self,
        kernel_device: str = "/dev/arkhe_uni",
        federation_client: Optional[FederatedGrammarClient] = None
    ):
        self.kernel_device = kernel_device
        self.federation_client = federation_client
        self._registered_grammars: Dict[str, str] = {}  # language -> grammar_id

    async def sync_grammars_to_kernel(
        self,
        languages: Optional[List[str]] = None,
        min_phi_c: float = 0.85
    ) -> int:
        """Sincroniza gramáticas federadas para o kernel module."""
        if not self.federation_client:
            logger.error("❌ Federation client not configured")
            return 0

        # Buscar gramáticas disponíveis
        metadata_list = await self.federation_client.fetch_global_grammars(
            languages=languages,
            min_phi_c=min_phi_c
        )

        registered_count = 0
        for metadata in metadata_list:
            # Verificar se já registrada
            if metadata.language in self._registered_grammars:
                continue

            # Baixar conteúdo da gramática
            grammar = await self.federation_client.download_grammar(metadata.grammar_id)
            if not grammar:
                continue

            # Registrar no kernel module via ioctl
            if self._register_grammar_in_kernel(grammar):
                self._registered_grammars[metadata.language] = metadata.grammar_id
                registered_count += 1

                logger.info(
                    f"✅ Gramática registrada no kernel: "
                    f"{metadata.language} ({metadata.engine.value})"
                )

        return registered_count

    def _register_grammar_in_kernel(self, grammar: FederatedGrammar) -> bool:
        """Registra gramática no kernel module via ioctl (mock)."""
        # Em produção: usar fcntl.ioctl com estrutura correta
        # Mock: simular registro bem-sucedido

        logger.debug(
            f"🔧 Registering grammar in kernel: "
            f"{grammar.metadata.language} (hash: {grammar.metadata.grammar_hash[:16]}...)"
        )

        # Simular tempo de registro
        time.sleep(0.01)

        return True

    async def auto_update_grammars(self, check_interval_hours: float = 6.0):
        """Loop de atualização automática de gramáticas."""
        while True:
            try:
                updated = await self.sync_grammars_to_kernel()
                if updated > 0:
                    logger.info(f"🔄 {updated} gramáticas atualizadas no kernel")

                await asyncio.sleep(check_interval_hours * 3600)

            except Exception as e:
                logger.error(f"❌ Erro na atualização automática: {e}")
                await asyncio.sleep(300)  # Retry após 5 min em caso de erro

# ═══════════════════════════════════════════════════════════════
# DEMONSTRAÇÃO
# ═══════════════════════════════════════════════════════════════

async def demonstrate_federation():
    """Demonstra fluxo de federação de gramáticas."""
    print(f"\n🌍 Demonstrando Federação de Gramáticas — Substrate 216")
    print(f"   Integração: Federated Registry ↔ Uni‑Kernel Polyglot\n")

    # Configurar cliente federado (mock)
    async with FederatedGrammarClient(
        aggregator_url="https://federated-grammars.arkhe.org",
        org_id="org_alpha_demo",
        pqc_public_key="pqc:dilithium3:pub:abc123...",
        privacy_epsilon=3.0
    ) as client:

        # 1. Buscar gramáticas disponíveis
        print("🔍 Buscando gramáticas federadas...")
        grammars = await client.fetch_global_grammars(
            languages=["python", "cobol", "rust"],
            min_phi_c=0.85
        )

        print(f"✅ {len(grammars)} gramáticas encontradas:")
        for g in grammars:
            print(f"   • {g.language:12s} ({g.engine.value:12s}) | "
                  f"Φ_C={g.phi_c_contribution:.2f} | ε={g.privacy_epsilon}")

        # 2. Baixar uma gramática
        if grammars:
            print(f"\n📥 Baixando gramática: {grammars[0].language}...")
            grammar = await client.download_grammar(grammars[0].grammar_id)

            if grammar:
                print(f"✅ Gramática baixada:")
                print(f"   ID: {grammar.metadata.grammar_id[:16]}...")
                print(f"   Versão: {grammar.metadata.version}")
                print(f"   Tamanho: {len(grammar.grammar_content)} bytes")
                print(f"   Dependências: {len(grammar.dependencies)}")
                print(f"   Regras de segurança: {len(grammar.security_rules)}")

        # 3. Contribuir com gramática local (mock)
        print(f"\n📤 Contribuindo gramática local...")
        local_grammar = FederatedGrammar(
            metadata=GrammarMetadata(
                grammar_id="local_demo_001",
                language="demo_lang",
                engine=GrammarEngine.TREE_SITTER,
                version="1.0.0",
                source_org_hash=client.org_hash,
                grammar_hash="demo_hash_123",
                pqc_signature="demo_sig_456",
                phi_c_contribution=0.92,
                privacy_epsilon=3.0,
                created_at=time.time(),
                last_updated=time.time()
            ),
            grammar_content='(program (statement)*)',
            dependencies=[],
            test_samples=[{"input": "demo code", "expected": "parsed"}],
            security_rules=[]
        )

        contributed_id = await client.contribute_grammar(local_grammar)
        if contributed_id:
            print(f"✅ Gramática contribuída: {contributed_id[:16]}...")

        # 4. Integrar com Uni‑Kernel
        print(f"\n🔗 Integrando com Uni‑Kernel Polyglot...")
        integrator = UniKernelGrammarIntegrator(
            kernel_device="/dev/arkhe_uni",
            federation_client=client
        )

        registered = await integrator.sync_grammars_to_kernel(
            languages=["python", "cobol"],
            min_phi_c=0.85
        )

        print(f"✅ {registered} gramáticas registradas no kernel")

        # 5. Verificar cache local
        cached = integrator.federation_client.get_local_grammar(
            "python", GrammarEngine.TREE_SITTER
        )
        if cached:
            print(f"✅ Gramática Python disponível no cache local")

    print(f"\n🌍 Federação de Gramáticas — OPERATIONAL")
    print(f"Canon: ∞.Ω.∇+++.216.federation.grammar_registry")

if __name__ == "__main__":
    asyncio.run(demonstrate_federation())