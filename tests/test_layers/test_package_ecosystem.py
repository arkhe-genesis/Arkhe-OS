import unittest
from pathlib import Path
import tempfile
from src.arkhe.layers.package_ecosystem import (
    parse_semver,
    DependencyCache,
    PluggableAuditor,
    AuditLevel,
    AuditReport,
    ArkToml,
    MythosGateIntegration,
    EBPFMetricsMonitor,
    MultiverseRouter,
    PackageRegistry,
    ArtBlock
)

class TestPackageEcosystem(unittest.TestCase):
    def test_parse_semver(self):
        self.assertEqual(parse_semver('1.2.3'), (1, 2, 3))
        with self.assertRaises(ValueError):
            parse_semver('1.2')

    def test_dependency_cache(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = DependencyCache(Path(tmpdir))
            cache.set('test-pkg', '1.0.0', b'dummy content')
            path = cache.get('test-pkg', '1.0.0')
            self.assertIsNotNone(path)
            if path:
                self.assertEqual(path.read_bytes(), b'dummy content')

            self.assertIsNone(cache.get('test-pkg', '2.0.0'))

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
        gate = MythosGateIntegration()
        self.assertTrue(gate.evaluate_ethical_context("pkg1", "good code"))
        self.assertFalse(gate.evaluate_ethical_context("pkg2", "this is malicious code"))

    def test_ebpf_metrics_monitor(self):
        monitor = EBPFMetricsMonitor()
        monitor.record_build()
        monitor.record_publish()
        monitor.record_publish()
        metrics = monitor.get_metrics()
        self.assertEqual(metrics["builds"], 1)
        self.assertEqual(metrics["publishes"], 2)

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
