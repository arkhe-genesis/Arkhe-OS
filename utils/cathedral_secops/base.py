# utils/cathedral_secops/base.py - Base for Cathedral SecOps Tools

import hashlib
import time
import json
from typing import Dict, Any, Optional
from cathedral_codex import CrystalCodex
from cathedral_zk import generate_zk_component

class BaseSecOpsTool:
    """
    Base class for all Cathedral SecOps tools.
    Enforces granular consent, ZK-proof generation, and Codex anchoring.
    """

    def __init__(self, tool_name: str, consent_id: str, codex: Optional[CrystalCodex] = None):
        if not consent_id:
            raise ValueError("CATHEDRAL SECOPS ERROR: Consent ID is mandatory for all operations.")

        self.tool_name = tool_name
        self.consent_id = consent_id
        self.codex = codex or CrystalCodex()
        self.start_time = time.time()

    async def anchor_receipt(self, operation: str, status: str, metadata: Dict[str, Any]):
        """
        Anchors a SecOpsReceipt to the Crystal Codex.
        """
        receipt_id = f"receipt_{self.tool_name}_{int(time.time())}"
        receipt_data = {
            "tool": self.tool_name,
            "operation": operation,
            "consent_id": self.consent_id,
            "status": status,
            "timestamp": time.time(),
            "metadata": metadata
        }

        content_hash = hashlib.sha256(json.dumps(receipt_data, sort_keys=True).encode()).hexdigest()

        await self.codex.store_artifact(
            artifact_id=receipt_id,
            content_hash=content_hash,
            metadata=receipt_data
        )
        return receipt_id

    async def generate_proof(self, proof_type: str, public_inputs: Dict[str, Any]):
        """
        Generates a ZK-proof for a SecOps operation.
        """
        return await generate_zk_component(
            circuit_type=f"secops_{proof_type}",
            tool=self.tool_name,
            consent_id=self.consent_id,
            **public_inputs
        )
