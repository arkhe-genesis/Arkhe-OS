#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SUBSTRATO 335-BIS: ORCID IP GUARDIAN (Propriedade Intelectual Soberana)
Canon: ∞.Ω.∇+++.335_bis.orcid_ip_guardian
"""

import hashlib
import time
import json
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional

@dataclass
class IntellectualPropertyRecord:
    orcid: str
    content_hash: str
    timestamp: float
    work_type: str # 'patent', 'art', 'dataset', 'paper'
    licenses: List[str]
    metadata: Dict
    canonical_seal: str

class OrcidIpGuardian:
    def __init__(self):
        self.registry: Dict[str, IntellectualPropertyRecord] = {}

    def register_work(self, orcid: str, content: str, work_type: str, licenses: List[str], metadata: Dict) -> IntellectualPropertyRecord:
        content_hash = hashlib.sha3_256(content.encode()).hexdigest()
        timestamp = time.time()

        # Invariant checks and seal generation
        seal_data = f"{orcid}:{content_hash}:{timestamp}:{work_type}"
        canonical_seal = hashlib.sha3_256(seal_data.encode()).hexdigest()

        record = IntellectualPropertyRecord(
            orcid=orcid,
            content_hash=content_hash,
            timestamp=timestamp,
            work_type=work_type,
            licenses=licenses,
            metadata=metadata,
            canonical_seal=canonical_seal
        )

        # Loopseal invariant: each creation is traceable to its author via cryptographic seal
        self.registry[canonical_seal] = record
        return record

@dataclass
class CommunityMember:
    orcid: str
    trajectory: str
    creative_process: str
    neural_map_hash: str
    philosophical_currents: List[str]
    is_artist: bool
    is_scientist: bool

class CommunityCurator:
    def __init__(self):
        self.members: List[CommunityMember] = []

    def add_member(self, member: CommunityMember):
        self.members.append(member)

    def find_synergies(self, target_orcid: str) -> List[CommunityMember]:
        # Simple synergy matching based on shared philosophical currents and complementary roles
        target = next((m for m in self.members if m.orcid == target_orcid), None)
        if not target:
            return []

        synergies = []
        for member in self.members:
            if member.orcid == target_orcid:
                continue

            shared_currents = set(target.philosophical_currents).intersection(set(member.philosophical_currents))
            is_complementary = (target.is_artist and member.is_scientist) or (target.is_scientist and member.is_artist)

            if len(shared_currents) > 0 or is_complementary:
                synergies.append(member)

        return synergies

if __name__ == '__main__':
    print("=========================================================================")
    print(" ARKHE Ω‑TEMP v∞.Ω — SUBSTRATO 335‑BIS: ORCID IP GUARDIAN ")
    print("=========================================================================")

    guardian = OrcidIpGuardian()

    # 1. Register scientific work
    paper_record = guardian.register_work(
        orcid="orcid:0000-0001-2345-6789",
        content="Microtubule quantum resonance data mapping",
        work_type="paper",
        licenses=["CC-BY-4.0"],
        metadata={"title": "Orch-OR Field Data"}
    )
    print(f"Registered Paper IP: {paper_record.canonical_seal}")

    # 2. Register artistic work
    art_record = guardian.register_work(
        orcid="orcid:0000-0002-3456-7890",
        content="Visual representation of Orch-OR resonance",
        work_type="art",
        licenses=["CC-BY-ND-4.0"],
        metadata={"title": "Quantum Mind Canvas"}
    )
    print(f"Registered Art IP: {art_record.canonical_seal}")

    # 3. Community Curation
    curator = CommunityCurator()

    scientist = CommunityMember(
        orcid="orcid:0000-0001-2345-6789",
        trajectory="Quantum biology research",
        creative_process="Data-driven reductionism",
        neural_map_hash="hash_a1",
        philosophical_currents=["Panpsychism", "Quantum Mechanics"],
        is_artist=False,
        is_scientist=True
    )

    artist = CommunityMember(
        orcid="orcid:0000-0002-3456-7890",
        trajectory="Digital surrealism",
        creative_process="Intuitive flow state",
        neural_map_hash="hash_b2",
        philosophical_currents=["Panpsychism", "Abstract Expressionism"],
        is_artist=True,
        is_scientist=False
    )

    curator.add_member(scientist)
    curator.add_member(artist)

    print("\nFinding Synergies for the Scientist...")
    synergies = curator.find_synergies(scientist.orcid)
    for synergy in synergies:
        role = "Artist" if synergy.is_artist else "Scientist"
        print(f"Match found: {synergy.orcid} ({role}) - Shared philosophical currents")
