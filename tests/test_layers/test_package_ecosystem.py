import unittest
from pathlib import Path
import tempfile
from src.arkhe.layers.package_ecosystem import (
    parse_semver,
    DependencyCache,
    DependencyKey,

    PluggableAuditor,
    AuditLevel,
    AuditReport,
    ArkToml,
    MythosGatePublisher,
    EthicalRiskAssessor,
    PublicationDecision,


    EBPFMetricsMonitor,
    MultiverseRouter,
    PackageRegistry,
    ArtBlock,
    QIPRoyaltyEngine,
    RegistryDashboard,
    ConRAGAuditor
)

class TestPackageEcosystem(unittest.TestCase):
    def test_parse_semver(self):
        self.assertEqual(parse_semver('1.2.3'), (1, 2, 3))
        with self.assertRaises(ValueError):
            parse_semver('1.2')

    def test_dependency_cache(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = DependencyCache(str(tmpdir))
            key1 = DependencyKey("test-pkg", "1.0.0", "hash1")
            cache.put(key1, b'dummy content')
            content = cache.get(key1)
            self.assertIsNotNone(content)
            if content:
                self.assertEqual(content, b'dummy content')

            key2 = DependencyKey("test-pkg", "2.0.0", "hash2")
            self.assertIsNone(cache.get(key2))

    def test_pluggable_auditor(self):
        auditor = PluggableAuditor()

        def dummy_plugin(manifest: ArkToml, source: str) -> AuditReport:
            if "bad" in source:
                return AuditReport(passed=False, issues=["Bad word found"])
            return AuditReport(passed=True, issues=[])

        auditor.register_plugin(dummy_plugin)

        manifest = ArkToml("test", "1.0.0")

        report1 = auditor.audit(manifest, "good code")
        self.assertTrue(report1.passed)

        report2 = auditor.audit(manifest, "bad code")
        self.assertFalse(report2.passed)
        self.assertIn("Bad word found", report2.issues)

    def test_mythos_gate_integration(self):
        publisher = MythosGatePublisher(assessor=EthicalRiskAssessor())
        manifest_safe = {
            "package": {"name": "pkg1", "version": "1.0.0", "description": "Safe package", "license": "MIT"},
            "dependencies": {}
        }
        source_files_safe = [("main.py", "def hello(): pass")]
        can_publish, message, assessment = publisher.evaluate_for_publication(
            manifest_safe, source_files_safe, [], "ORCID:123"
        )
        self.assertTrue(can_publish)
        self.assertEqual(assessment.decision, PublicationDecision.APPROVED)

        manifest_unsafe = {
            "package": {"name": "pkg2", "version": "1.0.0", "description": "Undetectable exploit backdoor", "license": "MIT"},
            "dependencies": {}
        }
        source_files_unsafe = [("backdoor.py", "import os, eval, subprocess\ndef exploit(target):\n    eval(f'os.system(\"{target}\")')\n    subprocess.call(['rm', '-rf', '/'])\n    return 'weaponized'")]
        can_publish2, message2, assessment2 = publisher.evaluate_for_publication(
            manifest_unsafe, source_files_unsafe, [], "ORCID:123"
        )
        self.assertFalse(can_publish2)
        self.assertIn(assessment2.decision, [PublicationDecision.REJECTED, PublicationDecision.REQUIRES_REVIEW])

    def test_ebpf_metrics_monitor(self):
        monitor = EBPFMetricsMonitor()
        monitor.attach_hooks()
        monitor.record_build(latency_ms=150.0, cache_hit_rate=0.8)
        monitor.record_publish()
        monitor.record_publish()
        metrics = monitor.get_metrics()
        self.assertEqual(metrics["builds"], 1)
        self.assertEqual(metrics["publishes"], 2)
        self.assertEqual(metrics["build_latency_ms"], 150.0)
        self.assertEqual(metrics["kernel_cache_hit_rate"], 0.8)

    def test_resolve_tree(self):
        registry = PackageRegistry()

        dep_manifest = ArkToml("dep-pkg", "1.0.0", {})
        dep_block = ArtBlock(metadata=dep_manifest, package_hash=dep_manifest.compute_seal())
        registry.publish(dep_block)

        main_manifest = ArkToml("main-pkg", "1.0.0", {"dep-pkg": "1.0.0"})
        main_block = ArtBlock(metadata=main_manifest, package_hash=main_manifest.compute_seal())
        registry.publish(main_block)

        resolved = registry.resolve_tree("main-pkg", "1.0.0")
        self.assertEqual(resolved, {"main-pkg": "1.0.0", "dep-pkg": "1.0.0"})

    def test_artblock_signature(self):
        manifest = ArkToml("test-pkg", "1.0.0", {})
        block = ArtBlock(metadata=manifest, package_hash=manifest.compute_seal())
        block.sign_with_orcid("0000-0000-0000-0000", "dummy-private-key")
        self.assertEqual(block.orcid, "0000-0000-0000-0000")
        self.assertIsNotNone(block.signature)

    def test_qip_royalty_engine(self):
        monitor = EBPFMetricsMonitor()
        monitor.record_build(cache_hit_rate=0.5)
        engine = QIPRoyaltyEngine(metrics_monitor=monitor)

        royalties = engine.calculate_royalties(100.0, "test-pkg")
        # Base 100 * (1.0 + 0.5) = 150
        # Creator 150 * 0.8 = 120
        # Cathedral 150 * 0.2 = 30
        self.assertEqual(royalties["creator"], 120.0)
        self.assertEqual(royalties["cathedral"], 30.0)

    def test_registry_dashboard(self):
        registry = PackageRegistry()
        manifest = ArkToml("test-pkg", "1.0.0", {})
        block = ArtBlock(metadata=manifest, package_hash=manifest.compute_seal())
        block.sign_with_orcid("1234-5678", "dummy-key")
        registry.publish(block)

        auditor = ConRAGAuditor()
        dashboard = RegistryDashboard(registry, auditor)
        html = dashboard.render_html()
        self.assertIn("test-pkg@1.0.0", html)
        self.assertIn("ORCID: 1234-5678", html)

    def test_multiverse_router(self):
        registry = PackageRegistry()
        router = MultiverseRouter(registry)

        manifest = ArkToml("multiverse-pkg", "1.0.0")
        block = ArtBlock(metadata=manifest, package_hash=manifest.compute_seal())

        router.publish_to_branch(block, "main")
        router.publish_to_branch(block, "dev")

        self.assertIn("multiverse-pkg@1.0.0", router.get_packages_in_branch("main"))
        self.assertIn("multiverse-pkg@1.0.0", router.get_packages_in_branch("dev"))
        self.assertEqual(len(router.get_packages_in_branch("feature")), 0)

if __name__ == '__main__':
    unittest.main()
