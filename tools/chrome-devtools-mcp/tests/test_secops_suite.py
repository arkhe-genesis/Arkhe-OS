# tests/test_secops_suite.py - Integration tests for Cathedral SecOps

import asyncio
import unittest
import json
import os
import sys

# Ensure root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.cathedral_secops.crypto import CathedralCryptoKit
from utils.cathedral_secops.lab import SovereignLab
from utils.cathedral_secops.sniffer import SovereignShark
from utils.cathedral_secops.headi import SovereignHeadi
from utils.cathedral_secops.gno_auditor import SovereignGnoAuditor
from cathedral_codex import CrystalCodex

class TestSecOpsSuite(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.consent_id = "test_consent_2026"
        self.codex = CrystalCodex()

    async def test_crypto_kit(self):
        kit = CathedralCryptoKit(self.consent_id)
        result = await kit.encrypt("sensitive data", "test_encryption")
        self.assertEqual(result["receipt_id"][:8], "receipt_")
        self.assertIn("proof", result)
        print(f"[OK] CryptoKit: {result['ciphertext']}")

    async def test_lab_instantiation(self):
        lab = SovereignLab(self.consent_id)
        result = await lab.create_lab("PentestLab", "isolated_net", ["nmap", "kali"])
        self.assertEqual(result["status"], "Lab Active")
        self.assertIn("receipt_id", result)
        print(f"[OK] SovereignLab: {result['lab_id']} instantiated.")

    async def test_sniffer_privacy(self):
        shark = SovereignShark(self.consent_id)
        result = await shark.capture("eth0", 10, "audit")
        self.assertEqual(result["stats_summary"]["https_ratio"], 0.85)
        self.assertIn("proof", result)
        print(f"[OK] SovereignShark: Protocol distribution proven via ZK.")

    async def test_headi_injection(self):
        headi = SovereignHeadi(self.consent_id)
        result = await headi.inject("http://target.local")
        self.assertIn("Injection Test Complete", result["status"])
        self.assertIn("receipt_id", result)
        print(f"[OK] SovereignHeadi: Header injection anchored.")

    async def test_gno_auditor(self):
        auditor = SovereignGnoAuditor(self.consent_id)
        result = await auditor.audit_contract("./test.gno")
        self.assertEqual(result["status"], "Audit Complete")
        self.assertIn("receipt_id", result)
        print(f"[OK] SovereignGnoAuditor: Gno contract audited.")

    async def test_mandatory_consent(self):
        with self.assertRaises(ValueError):
            CathedralCryptoKit(consent_id="")

if __name__ == "__main__":
    unittest.main()
