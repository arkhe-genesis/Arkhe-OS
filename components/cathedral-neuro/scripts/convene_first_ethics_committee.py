#!/usr/bin/env python3
"""
convene_first_ethics_committee.py
"""
import asyncio
import time
from cathedral_neuro.src.cathedral_neuro.ethics.committee_onboarding import (
    EthicsCommitteeOnboarding,
    EthicsCommitteeRegistry,
    CommitteeRole
)

async def main():
    print("⚖️  Convocação do Primeiro Comitê de Ética")
    registry = EthicsCommitteeRegistry(
        "ethics_001", "Comitê Soberano", "Catedral", "charter_hash", {}, 3, time.time()
    )
    onboarding = EthicsCommitteeOnboarding(None, None, registry)
    await onboarding.onboard_member("did:chair", CommitteeRole.CHAIR, "HC-USP", ["MD"], "did:issuer", "sig", True)
    print("✅ Comitê convocado")

if __name__ == "__main__":
    asyncio.run(main())
