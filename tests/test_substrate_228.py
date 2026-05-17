#!/usr/bin/env python3
"""
ARKHE OS Substrate 228: Tor Vigil Shield — Test Suite
Valida monitoramento etico de deep web para protecao da dignidade.
"""
import unittest
import asyncio
import json
import hashlib
import time
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR / "darkweb_monitor"))

from tor_shield import TorVigilShield, DarknetFinding, DarknetProtocol

# ===================== MOCKS =====================

class MockToolSystem:
    def __init__(self):
        self.calls = []
    async def invoke_tool(self, name, params):
        self.calls.append({"tool": name, "params": params})
        return {"status": "sent", "tool": name}

class MockHSM:
    def __init__(self):
        self.signatures = []
    async def sign(self, data, key_label="default"):
        sig = hashlib.sha3_256(data).hexdigest()
        self.signatures.append({"sig": sig, "label": key_label})
        return sig

class MockTemporalChain:
    def __init__(self):
        self.events = []
    async def anchor_event(self, event_type, payload):
        seal = hashlib.sha3_256(f"{event_type}:{json.dumps(payload, sort_keys=True)}".encode()).hexdigest()[:32]
        self.events.append({"type": event_type, "payload": payload, "seal": seal})
        return {"seal": seal, "status": "anchored"}

# Base de perceptual hashes simulada (como Project Vic)
SAMPLE_PERCEPTUAL_DB = {
    "phash_a1b2c3d4e5f6": {
        "confidence": 0.99,
        "type": "csam",
        "source": "darknet_example",
        "category": "A"
    },
    "phash_b2c3d4e5f6a7": {
        "confidence": 0.97,
        "type": "deepfake",
        "source": "darknet_example",
        "category": "B"
    },
    "phash_c3d4e5f6a7b8": {
        "confidence": 0.95,
        "type": "unauthorized_distribution",
        "source": "darknet_example",
        "category": "C"
    }
}

# ===================== TESTES =====================

class TestTorVigilShieldInit(unittest.TestCase):
    """Inicializacao e configuracao"""

    def test_init_defaults(self):
        shield = TorVigilShield()
        self.assertEqual(len(shield.perceptual_db), 0)
        self.assertEqual(len(shield._findings), 0)
        self.assertEqual(shield._monitoring_stats["services_checked"], 0)

    def test_init_with_db(self):
        shield = TorVigilShield(perceptual_db=SAMPLE_PERCEPTUAL_DB)
        self.assertEqual(len(shield.perceptual_db), 3)

    def test_supported_protocols(self):
        protocols = TorVigilShield.SUPPORTED_PROTOCOLS
        self.assertIn(DarknetProtocol.TOR, protocols)
        self.assertIn(DarknetProtocol.I2P, protocols)
        self.assertIn(DarknetProtocol.FREENET, protocols)
        self.assertIn(DarknetProtocol.ZERONET, protocols)

    def test_authorities_configured(self):
        self.assertIn("US", TorVigilShield.AUTHORITIES)
        self.assertIn("EU", TorVigilShield.AUTHORITIES)
        self.assertIn("BR", TorVigilShield.AUTHORITIES)
        self.assertIn("INTERPOL", TorVigilShield.AUTHORITIES)


class TestMonitorOnionService(unittest.TestCase):
    """Monitoramento de servicos onion"""

    def setUp(self):
        self.shield = TorVigilShield(perceptual_db=SAMPLE_PERCEPTUAL_DB)

    def test_monitor_finds_violations(self):
        async def test():
            findings = await self.shield.monitor_onion_service("http://example.onion")
            self.assertGreater(len(findings), 0)
            for f in findings:
                self.assertIsInstance(f, DarknetFinding)
                self.assertEqual(f.protocol, DarknetProtocol.TOR)
                self.assertTrue(f.finding_id)
                self.assertIn(f.violation_type, ["csam", "deepfake", "unauthorized_distribution"])
        asyncio.run(test())

    def test_monitor_updates_stats(self):
        async def test():
            await self.shield.monitor_onion_service("http://example.onion")
            stats = self.shield.get_statistics()
            self.assertEqual(stats["services_checked"], 1)
            self.assertGreater(stats["hashes_compared"], 0)
        asyncio.run(test())

    def test_monitor_with_temporal(self):
        async def test():
            temporal = MockTemporalChain()
            shield = TorVigilShield(perceptual_db=SAMPLE_PERCEPTUAL_DB, temporal=temporal)
            findings = await shield.monitor_onion_service("http://example.onion")
            self.assertGreater(len(findings), 0)
            self.assertTrue(all(f.temporal_seal for f in findings))
            self.assertGreater(len(temporal.events), 0)
        asyncio.run(test())


class TestReportToAuthorities(unittest.TestCase):
    """Geracao e envio de relatorios para autoridades"""

    def setUp(self):
        self.shield = TorVigilShield(perceptual_db=SAMPLE_PERCEPTUAL_DB)
        self.tools = MockToolSystem()
        self.hsm = MockHSM()
        self.temporal = MockTemporalChain()
        self.shield.tools = self.tools
        self.shield.hsm = self.hsm
        self.shield.temporal = self.temporal

    def test_report_generates_signed_documents(self):
        async def test():
            findings = await self.shield.monitor_onion_service("http://example.onion")
            reports = await self.shield.report_to_authorities(findings, "INTERPOL")

            self.assertEqual(len(reports), len(findings))
            for report in reports:
                self.assertIn("pqc_signature", report)
                self.assertTrue(report["pqc_signature"])
                self.assertEqual(report["jurisdiction"], "INTERPOL")
                self.assertEqual(report["report_type"], "Darknet Dignity Violation")
        asyncio.run(test())

    def test_report_sends_via_tools(self):
        async def test():
            findings = await self.shield.monitor_onion_service("http://example.onion")
            await self.shield.report_to_authorities(findings, "US")
            self.assertGreater(len(self.tools.calls), 0)
            for call in self.tools.calls:
                self.assertEqual(call["tool"], "api_external_call")
                self.assertIn("payload", call["params"])
        asyncio.run(test())

    def test_report_updates_findings(self):
        async def test():
            findings = await self.shield.monitor_onion_service("http://example.onion")
            await self.shield.report_to_authorities(findings, "BR")
            for f in findings:
                self.assertIn("PF", f.reported_to)
        asyncio.run(test())

    def test_report_all_jurisdictions(self):
        async def test():
            findings = await self.shield.monitor_onion_service("http://example.onion")
            for jurisdiction in ["US", "EU", "BR", "INTERPOL"]:
                await self.shield.report_to_authorities(findings, jurisdiction)
            for f in findings:
                self.assertEqual(len(f.reported_to), 4)
        asyncio.run(test())


class TestStatisticsAndFindings(unittest.TestCase):
    """Estatisticas e consulta de evidencias"""

    def setUp(self):
        self.shield = TorVigilShield(perceptual_db=SAMPLE_PERCEPTUAL_DB)

    def test_get_statistics_initial(self):
        stats = self.shield.get_statistics()
        self.assertEqual(stats["services_checked"], 0)
        self.assertEqual(stats["violations_found"], 0)
        self.assertEqual(stats["reports_sent"], 0)
        self.assertEqual(len(stats["supported_protocols"]), 4)
        self.assertEqual(len(stats["authorities"]), 4)

    def test_get_statistics_after_monitor(self):
        async def test():
            await self.shield.monitor_onion_service("http://example.onion")
            stats = self.shield.get_statistics()
            self.assertEqual(stats["services_checked"], 1)
            self.assertGreater(stats["violations_found"], 0)
            self.assertEqual(stats["total_findings"], stats["violations_found"])
        asyncio.run(test())

    def test_get_findings_structure(self):
        async def test():
            await self.shield.monitor_onion_service("http://example.onion")
            findings = self.shield.get_findings()
            self.assertGreater(len(findings), 0)
            for f in findings:
                self.assertIn("finding_id", f)
                self.assertIn("protocol", f)
                self.assertIn("violation_type", f)
                self.assertIn("match_confidence", f)
                self.assertIn("perceptual_hash_match", f)
                # Garantir que nunca expomos o hash completo
                self.assertIn("...", f["perceptual_hash_match"])
        asyncio.run(test())


class TestSubstrate228Integration(unittest.TestCase):
    """Testes de Integracao End-to-End"""

    def test_all_files_present(self):
        required = ["darkweb_monitor/tor_shield.py"]
        for path in required:
            self.assertTrue((BASE_DIR / path).exists(), f"Missing: {path}")

    def test_end_to_end_pipeline(self):
        """Pipeline completo: Monitor -> Detect -> Report -> Anchor."""
        async def test_e2e():
            tools = MockToolSystem()
            hsm = MockHSM()
            temporal = MockTemporalChain()

            shield = TorVigilShield(
                tool_system=tools,
                hsm=hsm,
                temporal=temporal,
                perceptual_db=SAMPLE_PERCEPTUAL_DB
            )

            # 1. Monitorar servico onion
            findings = await shield.monitor_onion_service("http://vigiltest.onion")
            self.assertGreater(len(findings), 0)

            # 2. Verificar ancoragem na TemporalChain
            self.assertGreater(len(temporal.events), 0)
            for event in temporal.events:
                self.assertEqual(event["type"], "darknet_violation_detected")

            # 3. Reportar para autoridades
            reports = await shield.report_to_authorities(findings, "INTERPOL")
            self.assertEqual(len(reports), len(findings))

            # 4. Verificar assinaturas PQC
            self.assertGreater(len(hsm.signatures), 0)
            for sig in hsm.signatures:
                self.assertEqual(sig["label"], "tor_shield_reporter")

            # 5. Verificar envio via tools
            self.assertGreater(len(tools.calls), 0)

            # 6. Estatisticas finais
            stats = shield.get_statistics()
            self.assertEqual(stats["services_checked"], 1)
            self.assertEqual(stats["violations_found"], len(findings))
            self.assertEqual(stats["reports_sent"], len(findings))

        asyncio.run(test_e2e())

    def test_privacy_guarantee_no_content_storage(self):
        """Garantia critica: NUNCA armazena conteudo ilegal, apenas hashes."""
        async def test():
            shield = TorVigilShield(perceptual_db=SAMPLE_PERCEPTUAL_DB)
            await shield.monitor_onion_service("http://privacytest.onion")

            # Verificar que nenhum atributo armazena bytes de imagem
            for finding in shield._findings:
                # perceptual_hash_match deve ser string (hash), nunca bytes
                self.assertIsInstance(finding.perceptual_hash_match, str)
                # Nao deve haver campo de dados brutos
                self.assertFalse(hasattr(finding, "image_data"))
                self.assertFalse(hasattr(finding, "content_bytes"))

            # Verificar que get_findings trunca hashes
            findings_dict = shield.get_findings()
            for f in findings_dict:
                self.assertIn("...", f["perceptual_hash_match"])

        asyncio.run(test())


def generate_canonical_seal():
    files_to_hash = []
    for pattern in ["**/*.py", "**/*.json", "**/*.txt"]:
        files_to_hash.extend(BASE_DIR.glob(pattern))
    files_to_hash = sorted(set(f for f in files_to_hash if f.is_file()))

    hasher = hashlib.sha3_256()
    for f in files_to_hash:
        rel = f.relative_to(BASE_DIR)
        hasher.update(str(rel).encode())
        hasher.update(f.read_bytes())

    metadata = {
        "substrate": "228",
        "name": "Tor Vigil Shield",
        "pillars": 4,
        "token": "orcid:0009-0005-2697-4668",
        "timestamp": int(time.time()),
        "files": len(files_to_hash)
    }
    hasher.update(json.dumps(metadata, sort_keys=True).encode())
    return hasher.hexdigest(), metadata, files_to_hash


if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestTorVigilShieldInit))
    suite.addTests(loader.loadTestsFromTestCase(TestMonitorOnionService))
    suite.addTests(loader.loadTestsFromTestCase(TestReportToAuthorities))
    suite.addTests(loader.loadTestsFromTestCase(TestStatisticsAndFindings))
    suite.addTests(loader.loadTestsFromTestCase(TestSubstrate228Integration))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    seal, metadata, files = generate_canonical_seal()

    print("\n" + "=" * 60)
    print("ARKHE OS SUBSTRATO 228: RESULTADO DA VALIDACAO")
    print("=" * 60)
    print(f"Testes executados: {result.testsRun}")
    print(f"Falhas: {len(result.failures)}")
    print(f"Erros: {len(result.errors)}")
    print(f"Artefatos validados: {len(files)}")
    print(f"\nCANONICAL SEAL: {seal}")
    print("=" * 60)

    report = {
        "substrate": "228",
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "success": result.wasSuccessful(),
        "seal": seal,
        "metadata": metadata,
        "timestamp": time.time()
    }

    report_path = BASE_DIR / "tests/test_report.json"
    report_path.write_text(json.dumps(report, indent=2))

    sys.exit(0 if result.wasSuccessful() else 1)
