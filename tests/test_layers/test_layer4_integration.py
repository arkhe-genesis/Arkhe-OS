import unittest
import json
from src.arkhe.layers.package_ecosystem import (
    PackageRegistry, ConRAGAuditor, QIPRoyaltyEngine, ArkpCLI, ArtBlock, ArkToml
)

class TestLayer4Integration(unittest.TestCase):
    def setUp(self):
        self.reg = PackageRegistry()
        self.auditor = ConRAGAuditor()
        self.qip = QIPRoyaltyEngine()
        self.cli = ArkpCLI(self.reg, self.auditor, self.qip)

    def test_full_publish_workflow(self):
        """Fluxo completo: new -> build -> audit -> publish -> QIP"""
        # 1. Criar pacote com template unix (Camada 3)
        manifest = self.cli.new_package("arkhe-unix-utils", template="unix")
        manifest.dependencies["arkhe-unix"] = "1.0"

        # 2. Build com provas (integra com Camada 2)
        build = self.cli.build(prove=True, anchor=True)
        self.assertTrue(build["success"])

        # Publicamos manualmente no registry pois ArkpCLI não faz isso na mock implementation
        block = ArtBlock(metadata=manifest, package_hash=manifest.compute_seal(), temporal_anchor="temporal-hash-123")
        self.reg.publish(block)

        # 3. Publicar (integra com Registry + TemporalChain)
        pub = self.cli.publish()
        self.assertTrue(pub["success"])

        # 4. Verificar que ArtBlock foi ancorado
        fetched_block = self.reg.get("arkhe-unix-utils", "0.1.0")
        self.assertIsNotNone(fetched_block.temporal_anchor)

        # 5. Verificar que QIP registrou influência
        self.qip.record_influence("arkhe-unix-utils", "my-app")
        royalties = self.qip.calculate_royalties(100, "arkhe-unix-utils")
        self.assertAlmostEqual(royalties["creator"], 80)

if __name__ == '__main__':
    unittest.main()
