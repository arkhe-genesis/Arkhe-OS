#!/usr/bin/env python3
"""
DeSci Nodes Bridge — Substrato 989.y
Ponte entre DeSci Labs (FAIR research objects, IPFS, dPID) e ARKHE Code Cathedral.
"""

import asyncio
import hashlib
import json
from typing import Dict, Optional, List, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

class ResearchObjectType(Enum):
    PUBLICATION = "publication"
    DATASET = "dataset"
    CODE = "code"
    PROTOCOL = "protocol"
    MODEL = "model"
    HYPOTHESIS = "hypothesis"
    REVIEW = "review"

@dataclass
class FAIRMetadata:
    dpid: str
    doi: Optional[str] = None
    orcid_id: Optional[str] = None
    title: str = ""
    description: str = ""
    keywords: List[str] = field(default_factory=list)

    access_protocol: str = "https"
    access_level: str = "public"
    license: str = "CC-BY-4.0"

    data_format: str = "json"
    ontology: str = "schema.org"
    cross_references: List[str] = field(default_factory=list)

    provenance: str = ""
    version: str = "1.0.0"
    creation_date: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def compute_fair_score(self) -> float:
        score = 0.0
        if self.dpid: score += 0.0625
        if self.doi: score += 0.0625
        if self.title and self.description: score += 0.0625
        if self.keywords: score += 0.0625
        if self.access_protocol: score += 0.125
        if self.license: score += 0.125
        if self.data_format: score += 0.125
        if self.ontology: score += 0.125
        if self.provenance: score += 0.125
        if self.version: score += 0.125
        return score

@dataclass
class ResearchObject:
    ro_id: str
    ro_type: ResearchObjectType

    cid: str
    manifest_cid: str
    content_hash: str

    fair: FAIRMetadata

    cathedral_substrates: List[int] = field(default_factory=list)
    cathedral_seals: List[str] = field(default_factory=list)

    is_published: bool = False
    is_peer_reviewed: bool = False
    review_count: int = 0

    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    temporal_anchor: Optional[str] = None
    seal: str = ""

    def compute_seal(self) -> str:
        payload = {
            "ro_id": self.ro_id,
            "cid": self.cid,
            "type": self.ro_type.value,
            "fair_score": round(self.fair.compute_fair_score(), 4),
            "timestamp": self.timestamp,
        }
        json_str = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        self.seal = "RO-" + hashlib.sha3_256(json_str.encode()).hexdigest()[:16].upper()
        return self.seal

class DeSciNodesBridge:
    SUBSTRATE_ID = "989.y"
    SEAL = "989.y-DESCI-NODES-BRIDGE-A1B2C3D4E5F67890"

    def __init__(self, temporal_anchor=None, ipfs_client=None):
        self.research_objects: Dict[str, ResearchObject] = {}
        self.temporal_anchor = temporal_anchor
        self.ipfs_client = ipfs_client
        self.dpid_counter = 1000

    def generate_dpid(self) -> str:
        self.dpid_counter += 1
        return "dpid-" + str(self.dpid_counter).zfill(6) + "-arkhe"

    async def create_research_object(
        self,
        ro_type: ResearchObjectType,
        content: bytes,
        title: str,
        description: str,
        orcid_id: Optional[str] = None,
        keywords: List[str] = None,
        cathedral_substrates: List[int] = None,
    ) -> ResearchObject:
        dpid = self.generate_dpid()

        content_hash = hashlib.sha3_256(content).hexdigest()

        cid = await self._publish_to_ipfs(content)

        manifest = {
            "dpid": dpid,
            "type": ro_type.value,
            "title": title,
            "description": description,
            "content_hash": content_hash,
            "cid": cid,
            "orcid_id": orcid_id,
            "keywords": keywords or [],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "substrate": self.SUBSTRATE_ID,
            "cathedral_seal": self.SEAL,
        }
        manifest_json = json.dumps(manifest, sort_keys=True, ensure_ascii=False).encode()
        manifest_cid = await self._publish_to_ipfs(manifest_json)

        fair = FAIRMetadata(
            dpid=dpid,
            orcid_id=orcid_id,
            title=title,
            description=description,
            keywords=keywords or [],
            license="CC-BY-4.0",
            provenance="Created via ARKHE DeSci Bridge " + self.SUBSTRATE_ID,
        )

        ro = ResearchObject(
            ro_id=dpid,
            ro_type=ro_type,
            cid=cid,
            manifest_cid=manifest_cid,
            content_hash=content_hash,
            fair=fair,
            cathedral_substrates=cathedral_substrates or [],
            cathedral_seals=[self.SEAL],
        )
        ro.compute_seal()

        if self.temporal_anchor:
            proof = {
                "ro_id": ro.ro_id,
                "cid": ro.cid,
                "manifest_cid": ro.manifest_cid,
                "seal": ro.seal,
                "fair_score": ro.fair.compute_fair_score(),
            }
            humanity_anchor = self.temporal_anchor.anchor_humanity_proof(proof)
            ro.temporal_anchor = humanity_anchor.temporal_anchor

        self.research_objects[dpid] = ro
        return ro

    async def _publish_to_ipfs(self, content: bytes) -> str:
        if self.ipfs_client:
            return await self.ipfs_client.add(content)
        return "Qm" + hashlib.sha3_256(content).hexdigest()[:44]

    def link_to_substrate(self, dpid: str, substrate_id: int, substrate_seal: str) -> bool:
        if dpid not in self.research_objects:
            return False
        ro = self.research_objects[dpid]
        if substrate_id not in ro.cathedral_substrates:
            ro.cathedral_substrates.append(substrate_id)
        if substrate_seal not in ro.cathedral_seals:
            ro.cathedral_seals.append(substrate_seal)
        return True

    def get_fair_report(self, dpid: str) -> Optional[Dict[str, Any]]:
        if dpid not in self.research_objects:
            return None
        ro = self.research_objects[dpid]
        return {
            "dpid": dpid,
            "type": ro.ro_type.value,
            "fair_score": ro.fair.compute_fair_score(),
            "findable": {
                "dpid": ro.fair.dpid,
                "doi": ro.fair.doi,
                "title": ro.fair.title,
                "keywords": ro.fair.keywords,
            },
            "accessible": {
                "protocol": ro.fair.access_protocol,
                "license": ro.fair.license,
                "level": ro.fair.access_level,
            },
            "interoperable": {
                "format": ro.fair.data_format,
                "ontology": ro.fair.ontology,
                "cross_refs": ro.fair.cross_references,
            },
            "reusable": {
                "provenance": ro.fair.provenance,
                "version": ro.fair.version,
                "creation_date": ro.fair.creation_date,
            },
            "cathedral_links": {
                "substrates": ro.cathedral_substrates,
                "seals": ro.cathedral_seals,
            },
            "seal": ro.seal,
            "temporal_anchor": ro.temporal_anchor,
        }

    def generate_report(self) -> str:
        total = len(self.research_objects)
        by_type = {}
        for ro in self.research_objects.values():
            by_type[ro.ro_type.value] = by_type.get(ro.ro_type.value, 0) + 1

        avg_fair = sum(ro.fair.compute_fair_score() for ro in self.research_objects.values()) / total if total > 0 else 0

        return "\n".join([
            "╔══════════════════════════════════════════════════════════════════╗",
            "║  ARKHE CATHEDRAL — DESCI NODES BRIDGE (989.y)                   ║",
            "║  \"Prometheus traz; Athena organiza; Mnemosyne lembra\"           ║",
            "╠══════════════════════════════════════════════════════════════════╣",
            "  Seal: " + self.SEAL,
            "  Status: CANONIZED_PROVISIONAL",
            "  Cross-links: [989.x, 988, 972.1, 923, 982, 934, 964, 970]",
            "  Deities: Prometheus, Athena, Mnemosyne, Thoth",
            "",
            "  RESEARCH OBJECTS",
            "  ────────────────",
            "  Total: " + str(total),
            "  By Type: " + json.dumps(by_type, indent=2),
            "  Avg FAIR Score: " + format(avg_fair, '.2%'),
            "",
            "  FAIR PRINCIPLES",
            "  ───────────────",
            "  Findable:     dPID + DOI + ORCID + rich metadata",
            "  Accessible:   HTTPS + CC-BY-4.0 + public/restricted/private",
            "  Interoperable: JSON + schema.org + cross-references",
            "  Reusable:     Provenance + versioning + Cathedral seals",
            "",
            "  INTEGRATION",
            "  ───────────",
            "  IPFS:    Content-addressed storage (CID)",
            "  dPID:    DeSci Persistent Identifier",
            "  ORCID:   Researcher identity (982)",
            "  TemporalChain: Immutable anchoring (923)",
            "  Axiarchy: Ethical validation (954)",
            "",
            "  ODÔMETRO: ∞.Ω.∇+++.989.y.0",
            "╚══════════════════════════════════════════════════════════════════╝"
        ])

async def demo():
    bridge = DeSciNodesBridge()

    ro = await bridge.create_research_object(
        ro_type=ResearchObjectType.PUBLICATION,
        content=b"PERCEPTUAL-GEOMETRY-EMERGENCE: A Cathedral Study",
        title="PERCEPTUAL-GEOMETRY-EMERGENCE",
        description="Study on perceptual geometry emergence via ARKHE",
        orcid_id="0009-0005-2697-4668",
        keywords=["perception", "geometry", "consciousness", "AI"],
        cathedral_substrates=[934, 964, 970],
    )
    bridge.link_to_substrate(ro.ro_id, 989, "989-PASSPORT-GATEWAY-4B3CB68C02D21E5A")
    report = bridge.get_fair_report(ro.ro_id)
    print(bridge.generate_report())

if __name__ == "__main__":
    asyncio.run(demo())
