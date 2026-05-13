import unittest
import hashlib
<<<<<<< feature/layer4-arkp-addons-693649031279738873
from src.arkhe.layers.ecosystem_arkp import ArkToml, ArtBlock, Registry, QIPRoyaltyEngine
from src.arkhe.layers.package_ecosystem_addons import SemVer, DependencyCache, ArkpCLI_Enhanced, MythosGate, PluggableAuditor, license_audit_plugin

class TestLayer4Addons(unittest.TestCase):
    def setUp(self):
        self.reg = Registry()
        self.auditor = PluggableAuditor()
        self.qip = QIPRoyaltyEngine()
        self.gate = MythosGate(mode='planetary')
        self.cli = ArkpCLI_Enhanced(self.reg, self.qip, self.auditor,
                                    cache_dir="/tmp/test-cache", mythos_gate=self.gate)
        for name, ver in [("lib", "1.0.1"), ("lib", "1.1.0"), ("lib", "2.0.0")]:
            block = ArtBlock(block_id=hashlib.sha3_256(f"{name}:{ver}".encode()).hexdigest()[:16],
                             name=name, version=ver, manifest_hash="mhash", code_hash="chash", zk_proof=hashlib.sha3_256(f"{name}:{ver}:mhash:chash".encode()).hexdigest()[:16], temporal_anchor="tanchor")
=======
from arkhe.layers.package_ecosystem import *
from arkhe.layers.package_ecosystem_addons import *
from arkhe.layers.governance import MythosGate

class TestLayer4Addons(unittest.TestCase):
    def setUp(self):
        self.reg = PackageRegistry()
        self.auditor = PluggableAuditor()
        self.qip = QIPRoyaltyEngine()
        self.gate = MythosGate(mode='planetary')
        self.cli = ArkpCLI_Enhanced(self.reg, self.auditor, self.qip,
                                    cache_dir="/tmp/test-cache", mythos_gate=self.gate)
        # Registrar alguns pacotes de exemplo
        for name, ver in [("lib", "1.0.1"), ("lib", "1.1.0"), ("lib", "2.0.0")]:
            m = ArkToml(package_name=name, version=ver)
            block = ArtBlock(package_hash=hashlib.sha3_256(b"").hexdigest()[:16],
                             metadata=m)
>>>>>>> main
            self.reg.publish(block)

    def test_semver_parsing(self):
        v = SemVer("1.2.3-alpha.1+build123")
        self.assertEqual(v.major, 1); self.assertEqual(v.minor, 2); self.assertEqual(v.patch, 3)
        self.assertEqual(v.pre, "alpha.1"); self.assertEqual(v.build, "build123")
        self.assertTrue(SemVer("1.2.3") > SemVer("1.2.2"))
        self.assertTrue(SemVer("1.2.3-alpha") < SemVer("1.2.3"))

    def test_dependency_cache_and_resolution(self):
<<<<<<< feature/layer4-arkp-addons-693649031279738873
        manifest = ArkToml(name="test-app", version="0.1.0",
                           dependencies={"lib": "^1.0.0"})
        deps = self.cli.resolve_dependencies(manifest)
        self.assertIn("lib", deps)
        self.assertIn(b"lib@1.1.0", deps["lib"])

    def test_mythos_gate_blocks_risky_publish(self):
        manifest = ArkToml(name="super-nuclear-lib", version="0.1")
        self.cli.projects["super-nuclear-lib"] = manifest
        result = self.cli.publish(name="super-nuclear-lib", code="weaponize_all()", author_orcid="ORCID:1", dry_run=True)
        self.assertFalse(result["success"])
        self.assertIn("Mythos Gate", result.get("error", "") or str(result.get("audit", "")))

    def test_plugin_audit_license(self):
        self.auditor.register_plugin(license_audit_plugin)
        manifest = ArkToml(name="test", version="1.0", license="GPL-3.0")
        report = self.auditor.audit(manifest, "")
        self.assertFalse(report["passed"])
        self.assertIn("License not recognized", " ".join(report["violations"]))
=======
        manifest = ArkToml(package_name="test-app", version="0.1.0",
                           dependencies={"lib": "^1.0"})
        deps = self.cli.resolve_dependencies(manifest)
        self.assertIn("lib", deps)
        # Deveria pegar a última 1.x (1.1.0)
        self.assertIn(b"lib@1.1.0", deps["lib"])

    def test_mythos_gate_blocks_risky_publish(self):
        manifest = ArkToml(package_name="super-nuclear-lib", version="0.1")
        self.cli.current_manifest = manifest
        result = self.cli.publish(dry_run=True)
        self.assertFalse(result["success"])
        self.assertIn("Mythos Gate", result["error"])

    def test_plugin_audit_license(self):
        self.auditor.register_plugin(license_audit_plugin)
        manifest = ArkToml(package_name="test", version="1.0", license="GPL-3.0")
        report = self.auditor.audit(manifest, "")
        self.assertFalse(report.passed)
        self.assertIn("License not recognized", " ".join(report.issues))
>>>>>>> main

if __name__ == '__main__':
    unittest.main()
