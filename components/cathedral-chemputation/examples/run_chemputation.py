#!/usr/bin/env python3
"""
run_chemputation.py — Demonstração end-to-end do módulo FS-97
"""

import asyncio
import json
import hashlib
from pathlib import Path

from cathedral_chemputation.intent.parser import ArkheMolecularParser
from cathedral_chemputation.quantum.evaluator import QuantumPhysicalEvaluator, QuantumBackend
from cathedral_chemputation.receipt.scientific_receipt import ScientificReceiptBuilder, ConsentRef

async def main():
    print("🧬 Iniciando Chemputation Soberana (FS-97 Prototype)")

    arkhe_code = """
    molecule {
      target: "covalent_inhibitor",
      protein_target: "KRAS_G12D",
      constraints: {
        IC50_max: "10nM",
        synthetic_steps_max: 5
      }
    }
    """

    intent = ArkheMolecularParser.parse(arkhe_code, intent_id="kras_demo")
    print(f"✅ Intent: {intent.intent_id}")

    evaluator = QuantumPhysicalEvaluator(backend=QuantumBackend.PENNYLANE_SIMULATOR)
    quantum_result = await evaluator.evaluate_molecule(smiles="LiH", properties=["ground_state_energy"])
    print(f"✅ Avaliação quântica concluída")

    synthesis_info = {"synthesizability_score": 0.88}

    consent_ref = ConsentRef(
        consent_hash="h1", citizen_did_hash="d1", scope_hash="s1",
        hierarchical=True, block_id_hash="b1"
    )

    class Codex:
        async def store_artifact(self, artifact_id, content_hash, metadata):
            return {}

    receipt_builder = ScientificReceiptBuilder(codex_client=Codex())
    receipt = await receipt_builder.build_molecule_discovery_receipt(
        intent=intent, molecule_smiles="LiH", quantum_result=quantum_result,
        synthesis_info=synthesis_info, consent_ref=consent_ref
    )

    print(f"✅ Receipt gerado: {receipt.receipt_id}")
    print(f"🔗 Codex URL: {receipt.codex_anchor['verification_url']}")

if __name__ == "__main__":
    asyncio.run(main())
