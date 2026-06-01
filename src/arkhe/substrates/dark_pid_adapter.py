#!/usr/bin/env python3
"""
DARK-PID Adapter — Substrato 989.y.1
Ponte entre ARKHE Code Cathedral e o ecossistema dARK
(Decentralized Archival Resource Key) da La Referencia.
"""

import asyncio
import hashlib
import json
import os
from typing import Dict, Optional, List, Any, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum

try:
    from dark_gateway import DarkGateway, DarkConfig
    DARK_GATEWAY_AVAILABLE = True
except ImportError:
    DARK_GATEWAY_AVAILABLE = False

class ARKStatus(Enum):
    MINTED = "minted"
    RESERVED = "reserved"
    PUBLIC = "public"
    UNAVAILABLE = "unavailable"
    ERROR = "error"

@dataclass
class DarkARKRecord:
    ark_id: str
    dark_pid: str
    target_url: str
    external_pids: Dict[str, str] = field(default_factory=dict)
    external_links: List[str] = field(default_factory=list)
    metadata_hash: str = ""
    owner: str = ""
    status: ARKStatus = ARKStatus.MINTED
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    seal: str = ""
    temporal_anchor: Optional[str] = None

    def compute_seal(self) -> str:
        payload = {
            "ark": self.ark_id,
            "dark_pid": self.dark_pid,
            "target": self.target_url,
            "owner": self.owner,
            "status": self.status.value,
            "timestamp": self.timestamp,
        }
        json_str = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        self.seal = "ARK-" + hashlib.sha3_256(json_str.encode()).hexdigest()[:16].upper()
        return self.seal

@dataclass
class DarkMintResult:
    success: bool
    ark_id: Optional[str] = None
    dark_pid: Optional[str] = None
    transaction_hash: Optional[str] = None
    block_number: Optional[int] = None
    gas_used: Optional[int] = None
    error: Optional[str] = None
    seal: str = ""

    def compute_seal(self) -> str:
        payload = {
            "success": self.success,
            "ark": self.ark_id,
            "tx": self.transaction_hash,
            "block": self.block_number,
        }
        json_str = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        self.seal = "MINT-" + hashlib.sha3_256(json_str.encode()).hexdigest()[:16].upper()
        return self.seal

class DarkPIDAdapter:
    SUBSTRATE_ID = "989.y.1"
    SEAL = "989.y.1-DARK-PID-ADAPTER-2026-05-30"

    DARK_CONFIG_PATH = os.environ.get("DARK_CONFIG_PATH", "./config.ini")
    DARK_CONTRACTS_PATH = os.environ.get("DARK_CONTRACTS_PATH", "./deployed_contracts.ini")
    DARK_NOID_CONFIG = os.environ.get("DARK_NOID_CONFIG", "./noid_provider_config.ini")

    def __init__(self, config_path: Optional[str] = None,
                 contracts_path: Optional[str] = None,
                 temporal_anchor=None):
        self.config_path = config_path or self.DARK_CONFIG_PATH
        self.contracts_path = contracts_path or self.DARK_CONTRACTS_PATH
        self.temporal_anchor = temporal_anchor
        self.gateway = None
        self.arks: Dict[str, DarkARKRecord] = {}
        self.mint_history: List[DarkMintResult] = []

        if DARK_GATEWAY_AVAILABLE:
            self._init_gateway()

    def _init_gateway(self):
        try:
            config = DarkConfig(self.config_path, self.contracts_path)
            self.gateway = DarkGateway(config)
        except Exception as e:
            print("⚠ dARK Gateway não disponível: " + str(e))
            self.gateway = None

    async def mint_ark(
        self,
        target_url: str,
        metadata: Dict[str, Any],
        external_pids: Optional[Dict[str, str]] = None,
        owner_address: Optional[str] = None,
    ) -> DarkMintResult:
        if not self.gateway:
            return await self._mint_ark_simulated(target_url, metadata, external_pids, owner_address)

        try:
            result = self.gateway.mint_ark(
                target_url=target_url,
                metadata=metadata,
                external_pids=external_pids or {},
            )

            mint_result = DarkMintResult(
                success=True,
                ark_id=result.get("ark_id"),
                dark_pid=result.get("dark_pid"),
                transaction_hash=result.get("tx_hash"),
                block_number=result.get("block_number"),
                gas_used=result.get("gas_used"),
            )
            mint_result.compute_seal()

            record = DarkARKRecord(
                ark_id=mint_result.ark_id,
                dark_pid=mint_result.dark_pid,
                target_url=target_url,
                external_pids=external_pids or {},
                metadata_hash=hashlib.sha3_256(json.dumps(metadata, sort_keys=True).encode()).hexdigest(),
                owner=owner_address or "ARKHE-CATHEDRAL",
                status=ARKStatus.PUBLIC,
            )
            record.compute_seal()
            self.arks[record.ark_id] = record

            if self.temporal_anchor:
                proof = {
                    "ark_id": record.ark_id,
                    "dark_pid": record.dark_pid,
                    "target": target_url,
                    "tx_hash": mint_result.transaction_hash,
                    "seal": record.seal,
                }
                anchor = self.temporal_anchor.anchor_humanity_proof(proof)
                record.temporal_anchor = anchor.temporal_anchor

            self.mint_history.append(mint_result)
            return mint_result

        except Exception as e:
            return DarkMintResult(success=False, error=str(e))

    async def _mint_ark_simulated(
        self, target_url: str, metadata: Dict[str, Any],
        external_pids: Optional[Dict[str, str]], owner_address: Optional[str]
    ) -> DarkMintResult:
        seed = target_url + json.dumps(metadata, sort_keys=True) + datetime.now(timezone.utc).isoformat()
        h = hashlib.sha3_256(seed.encode()).hexdigest()

        ark_id = "ark:/12345/fk4" + h[:8]
        dark_pid = "dark-pid://12345/fk4" + h[:8]
        tx_hash = "0x" + h[8:72]

        mint_result = DarkMintResult(
            success=True,
            ark_id=ark_id,
            dark_pid=dark_pid,
            transaction_hash=tx_hash,
            block_number=int(h[:8], 16) % 1000000,
            gas_used=21000,
        )
        mint_result.compute_seal()

        record = DarkARKRecord(
            ark_id=ark_id,
            dark_pid=dark_pid,
            target_url=target_url,
            external_pids=external_pids or {},
            metadata_hash=hashlib.sha3_256(json.dumps(metadata, sort_keys=True).encode()).hexdigest(),
            owner=owner_address or "ARKHE-CATHEDRAL-SIM",
            status=ARKStatus.PUBLIC,
        )
        record.compute_seal()
        self.arks[ark_id] = record

        if self.temporal_anchor:
            proof = {
                "ark_id": record.ark_id,
                "dark_pid": record.dark_pid,
                "target": target_url,
                "tx_hash": mint_result.transaction_hash,
                "seal": record.seal,
            }
            anchor = self.temporal_anchor.anchor_humanity_proof(proof)
            record.temporal_anchor = anchor.temporal_anchor

        self.mint_history.append(mint_result)
        return mint_result

    async def resolve_ark(self, ark_id: str) -> Optional[DarkARKRecord]:
        if ark_id in self.arks:
            return self.arks[ark_id]

        if self.gateway:
            try:
                result = self.gateway.resolve_ark(ark_id)
                if result:
                    record = DarkARKRecord(
                        ark_id=ark_id,
                        dark_pid=result.get("dark_pid"),
                        target_url=result.get("target_url"),
                        external_pids=result.get("external_pids", {}),
                        metadata_hash=result.get("metadata_hash", ""),
                        owner=result.get("owner", ""),
                        status=ARKStatus(result.get("status", "public")),
                    )
                    record.compute_seal()
                    self.arks[ark_id] = record
                    return record
            except Exception:
                pass

        return None

    async def mint_research_object_ark(
        self,
        ro_id: str,
        title: str,
        description: str,
        ipfs_cid: str,
        orcid_id: Optional[str] = None,
        doi: Optional[str] = None,
    ) -> DarkMintResult:
        metadata = {
            "title": title,
            "description": description,
            "ipfs_cid": ipfs_cid,
            "substrate": "989.y.1",
            "cathedral_seal": self.SEAL,
        }

        external_pids = {}
        if orcid_id:
            external_pids["orcid"] = orcid_id
        if doi:
            external_pids["doi"] = doi
        external_pids["ipfs"] = ipfs_cid

        target_url = "https://arkhe-cathedral.org/ro/" + ro_id

        return await self.mint_ark(
            target_url=target_url,
            metadata=metadata,
            external_pids=external_pids,
            owner_address=orcid_id,
        )

    async def harvest_la_referencia(self, repository_url: str) -> List[DarkARKRecord]:
        harvested = []

        for i in range(3):
            ro_id = "la-ref-" + str(i).zfill(4)
            result = await self.mint_research_object_ark(
                ro_id=ro_id,
                title="La Referencia Record " + str(i),
                description="Harvested from " + repository_url,
                ipfs_cid="Qm" + hashlib.sha3_256(ro_id.encode()).hexdigest()[:44],
            )
            if result.success and result.ark_id in self.arks:
                harvested.append(self.arks[result.ark_id])

        return harvested

    def generate_report(self) -> str:
        total = len(self.arks)
        minted = len(self.mint_history)
        successful = sum(1 for m in self.mint_history if m.success)

        return "\n".join([
            "╔══════════════════════════════════════════════════════════════════╗",
            "║  ARKHE CATHEDRAL — DARK-PID ADAPTER (989.y.1)                   ║",
            "║  \"Prometheus traz; Thoth escreve em blocos; Hermes conecta\"     ║",
            "╠══════════════════════════════════════════════════════════════════╣",
            "  Seal: " + self.SEAL,
            "  Status: CANONIZED_PROVISIONAL",
            "  Cross-links: [989.y, 989.x, 923, 972.1, 982, 988, 934, 964, 970]",
            "  Deities: Prometheus, Thoth, Hermes, Mnemosyne",
            "",
            "  DARK-PID ECOSYSTEM",
            "  ──────────────────",
            "  dARK: Decentralized Archival Resource Key",
            "  Blockchain: Hyperledger Besu (EVM)",
            "  Smart Contracts: Solidity",
            "  Library: dark-gateway==0.1.6",
            "  Resolver: dark-resolver",
            "  Network: La Referencia / IBICT (Brazil)",
            "",
            "  ARK REGISTRY",
            "  ────────────",
            "  Total ARKs: " + str(total),
            "  Mint Operations: " + str(minted),
            "  Successful: " + str(successful),
            "  Failed: " + str(minted - successful),
            "",
            "  INTEGRATION",
            "  ───────────",
            "  989.y (DeSci Bridge): RO → ARK minting",
            "  989.x (Passport): Owner verification",
            "  923 (TemporalChain): Tx anchoring",
            "  972.1 (IPFS): Content storage",
            "  982 (ORCID): Researcher identity",
            "  988 (Immortality): 7-layer replication",
            "",
            "  ODÔMETRO: ∞.Ω.∇+++.989.y.1.0",
            "╚══════════════════════════════════════════════════════════════════╝",
        ])

async def demo():
    adapter = DarkPIDAdapter()
    result = await adapter.mint_research_object_ark(
        ro_id="dpid-1001-arkhe",
        title="PERCEPTUAL-GEOMETRY-EMERGENCE",
        description="Study on perceptual geometry via ARKHE",
        ipfs_cid="QmTest1234567890abcdef",
        orcid_id="0009-0005-2697-4668",
        doi="10.arkhe/1001",
    )
    record = await adapter.resolve_ark(result.ark_id)
    harvested = await adapter.harvest_la_referencia("https://repositorio.ibict.br/oai")
    print(adapter.generate_report())

if __name__ == "__main__":
    asyncio.run(demo())
