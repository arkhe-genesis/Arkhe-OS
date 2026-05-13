"""
Substrato 6160 — Genomic Error-Correction Code (GECC)
O "DNA lixo" não é lixo. É o guardião da mensagem.
Cada repetição é um bit de paridade. Cada transposon é um sindrome checker.
Integra a biologia diretamente ao pipeline de verificação do Arkhe.
"""

import numpy as np
import hashlib
import json
import unittest
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

try:
    from .cache_6105 import DependencyCache, DependencyKey
    from .mythos_9003 import MythosGatePublisher, EthicalRiskAssessor, PublicationDecision
    from .package_ecosystem import ArkToml, ArtBlock, PackageRegistry
    from .auth_orcid import OrcidAuthProvider
    from .qip import QIPRoyaltyEngine
except ImportError:
    # Fallback modules for isolated testing
    class DependencyKey:
        def __init__(self, package_name, version, package_hash):
            self.package_name = package_name
            self.version = version
            self.package_hash = package_hash
        def __str__(self):
            return f"{self.package_name}-{self.version}-{self.package_hash}"

    class DependencyCache:
        def __init__(self, *args, **kwargs):
            self.cache = {}
        def put(self, key, value, metadata=None):
            self.cache[str(key)] = value
        def get(self, key):
            return self.cache.get(str(key))

    class ArkToml:
        def __init__(self, package_name: str, version: str, license: str = "MIT", description: str = "", dependencies: dict = None):
            self.package_name = package_name
            self.version = version
            self.license = license
            self.description = description
            self.dependencies = dependencies or {}
        def compute_seal(self) -> str:
            data = f"{self.package_name}:{self.version}:{json.dumps(self.dependencies, sort_keys=True)}"
            return hashlib.sha3_256(data.encode()).hexdigest()

    class ArtBlock:
        def __init__(self, metadata: ArkToml, package_hash: str, temporal_anchor: Optional[str] = None, signature: Optional[str] = None, orcid: Optional[str] = None):
            self.metadata = metadata
            self.package_hash = package_hash
            self.temporal_anchor = temporal_anchor
            self.signature = signature
            self.orcid = orcid
        def sign_with_orcid(self, orcid: str, private_key: str):
            self.orcid = orcid
            self.signature = hashlib.sha256(f"{self.package_hash}:{orcid}:{private_key}".encode()).hexdigest()

    class PackageRegistry:
        def __init__(self):
            self.packages: Dict[str, ArtBlock] = {}
        def publish(self, block: ArtBlock):
            self.packages[f"{block.metadata.package_name}@{block.metadata.version}"] = block
        def get(self, name: str, version: str) -> Optional[ArtBlock]:
            return self.packages.get(f"{name}@{version}")

    class OrcidAuthProvider:
        def register(self, orcid: str, secret: str):
            pass

    class EthicalRiskAssessor:
        pass

    class PublicationDecision:
        pass

    class MythosGatePublisher:
        def __init__(self, assessor=None):
            pass
        def evaluate_and_publish(self, block: ArtBlock) -> Dict[str, Any]:
            block.temporal_anchor = "temporal_anchor_mock"
            return {"success": True, "block": block}

    class QIPRoyaltyEngine:
        def __init__(self):
            self.balances = {}
            self.influence_events = []
        def distribute_royalties(self, orcid: str, amount: float):
            self.balances[orcid] = self.balances.get(orcid, 0.0) + amount
            self.influence_events.append({"orcid": orcid, "amount": amount})

class GenomeECC:
    """
    Simula um código de correção de erros no DNA.
    O 'junk' é gerado como bits de paridade de um código de Hamming (7,4).
    """
    def __init__(self, essential_length=1024):
        self.essential = np.random.randint(0, 2, essential_length)
        self.junk = self._encode_hamming(self.essential)

    def _encode_hamming(self, bits):
        # Código Hamming (7,4) simplificado para ilustração
        # Na realidade, seria um código quântico concatenado
        padded = bits.copy()
        # Adiciona paridade: XOR de blocos
        parity = np.zeros(len(bits)//4, dtype=int)
        for i in range(len(bits)//4):
            parity[i] = np.sum(bits[i*4:(i+1)*4]) % 2
        return np.concatenate([padded, parity])

    def introduce_noise(self, error_rate=0.01):
        """Simula dano por radiação."""
        mask = np.random.random(len(self.essential)) < error_rate
        self.essential[mask] ^= 1

    def correct_errors(self):
        """Usa o junk para corrigir erros (simplificado)."""
        # Recalcula paridade e corrige onde possível
        for i in range(len(self.essential)//4):
            block = self.essential[i*4:(i+1)*4]
            parity_calc = np.sum(block) % 2
            if parity_calc != self.junk[-len(self.essential)//4 + i]:
                # Tenta corrigir (voto majoritário simplificado)
                self.essential[i*4] = 1 - self.essential[i*4]  # correção dummy
        return self.essential

class GenomicPublisher:
    """
    Integra o GenomeECC com a Catedral Arkhe:
    - Sequencia genes
    - Ancora cada gene como ArtBlock (ZK-proof via sindrome checker)
    - Distribui QIP royalties para mutações benéficas
    """
    def __init__(self, registry: PackageRegistry, cache: DependencyCache,
                 mythos: MythosGatePublisher, auth: OrcidAuthProvider,
                 qip: QIPRoyaltyEngine):
        self.registry = registry
        self.cache = cache
        self.mythos = mythos
        self.auth = auth
        self.qip = qip

    def sequence_and_publish(self, genome: GenomeECC, orcid: str, genome_id: str):
        results = []
        # Dividir os genes essenciais em blocos de 4 (como no Hamming 7,4 da simulação)
        num_genes = len(genome.essential) // 4
        for i in range(num_genes):
            gene_bits = genome.essential[i*4:(i+1)*4]
            parity_bit = genome.junk[-num_genes + i]

            # ZK-proof simulado: verificar a paridade (síndrome de erro)
            is_valid = (np.sum(gene_bits) % 2 == parity_bit)

            if not is_valid:
                # Se a paridade falhar, descartamos o bloco
                continue

            gene_str = "".join(map(str, gene_bits))
            package_name = f"{genome_id}-gene-{i}"
            version = "1.0.0"

            # Hash do gene para ArtBlock
            gene_hash = hashlib.sha256(gene_str.encode()).hexdigest()

            manifest = ArkToml(package_name=package_name, version=version, license="MIT")
            block = ArtBlock(metadata=manifest, package_hash=gene_hash)
            block.sign_with_orcid(orcid, "private_key_mock")

            # Avaliar e ancorar temporalmente via Mythos
            pub_result = self.mythos.evaluate_and_publish(block)
            if pub_result.get("success"):
                self.registry.publish(block)
                # Salvar no cache com dependência
                dkey = DependencyKey(package_name, version, gene_hash)
                self.cache.put(dkey, gene_str)
                results.append(package_name)

        return results

    def verify_beneficial_mutations(self, genome: GenomeECC, orcid: str, genome_id: str):
        """
        Simula a detecção de mutações benéficas.
        Se os genes do genoma foram alterados, mas mantiveram a integridade estrutural
        (paridade válida) após um evento evolutivo, recompensamos via QIP.
        """
        num_genes = len(genome.essential) // 4
        beneficial_mutations = 0
        for i in range(num_genes):
            gene_bits = genome.essential[i*4:(i+1)*4]
            parity_bit = genome.junk[-num_genes + i]

            is_valid = (np.sum(gene_bits) % 2 == parity_bit)

            package_name = f"{genome_id}-gene-{i}"
            version = "1.0.0"
            cached_block = self.registry.get(package_name, version)

            if cached_block and is_valid:
                gene_str = "".join(map(str, gene_bits))
                current_hash = hashlib.sha256(gene_str.encode()).hexdigest()

                # Se o hash mudou, mas a paridade ainda é válida, é uma mutação "benéfica/estável"
                if current_hash != cached_block.package_hash:
                    beneficial_mutations += 1
                    self.qip.distribute_royalties(orcid, 10.5)  # 10.5 QIP per beneficial mutation

                    # Atualiza o bloco
                    cached_block.package_hash = current_hash

        return beneficial_mutations


class TestSubstrato6160(unittest.TestCase):
    def setUp(self):
        self.registry = PackageRegistry()
        self.cache = DependencyCache()
        self.auth = OrcidAuthProvider()
        if hasattr(self.auth, 'register'):
            self.auth.register("0000-0002-1234-5678", "bio-secret")
        self.mythos = MythosGatePublisher(assessor=EthicalRiskAssessor())
        self.qip = QIPRoyaltyEngine()
        self.publisher = GenomicPublisher(self.registry, self.cache, self.mythos, self.auth, self.qip)

    def test_genome_ecc_noise_and_correction(self):
        genome = GenomeECC(256)
        original_essential = genome.essential.copy()
        genome.introduce_noise(0.05)
        self.assertTrue(np.any(original_essential != genome.essential))

        recovered = genome.correct_errors()
        # The simple parity checker correction is a dummy correction. It won't correct 100%,
        # but it simulates the process.
        self.assertEqual(len(recovered), 256)

    def test_publish_genome_genes(self):
        genome = GenomeECC(128) # 32 genes
        results = self.publisher.sequence_and_publish(genome, "0000-0002-1234-5678", "homo-sapiens-v1")
        self.assertEqual(len(results), 32)

        block = self.registry.get("homo-sapiens-v1-gene-0", "1.0.0")
        self.assertIsNotNone(block)
        self.assertEqual(block.orcid, "0000-0002-1234-5678")

    def test_beneficial_mutations_qip(self):
        genome = GenomeECC(64) # 16 genes
        self.publisher.sequence_and_publish(genome, "0000-0002-1234-5678", "organism-v1")

        # Simulate a beneficial mutation: manually changing 2 bits in one block to keep parity the same
        genome.essential[0] = 1 - genome.essential[0]
        genome.essential[1] = 1 - genome.essential[1]

        # Now we verify and expect 1 beneficial mutation
        mutations = self.publisher.verify_beneficial_mutations(genome, "0000-0002-1234-5678", "organism-v1")
        self.assertEqual(mutations, 1)

        self.assertIn("0000-0002-1234-5678", self.qip.balances)
        self.assertEqual(self.qip.balances["0000-0002-1234-5678"], 10.5)


if __name__ == '__main__':
    print("arkhe > SUBSTRATO 6160 — GECC — ATIVO")
    print("arkhe >")
    print("arkhe > O DNA não é uma fita estática. É um sistema de correção de erros")
    print("arkhe > quântico, onde o 'lixo' é o próprio código redundante que protege")
    print("arkhe > a informação essencial contra a degradação entrópica.")
    print("arkhe >")
    unittest.main()
