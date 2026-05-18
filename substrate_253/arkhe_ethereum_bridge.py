#!/usr/bin/env python3
"""
ARKHE OS Substrate 253: Ethereum Integration Bridge
Canon: ∞.Ω.∇+++.253.ethereum_bridge

Bridge between Arkhe‑ASI (off‑chain) and Ethereum (on‑chain).
Manages identity registration, seal anchoring, and payment settlement.
"""

import asyncio
import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from web3 import Web3
from web3.middleware import geth_poa_middleware
from eth_account import Account
import requests

# =============================================================================
# CONFIGURATION
# =============================================================================
@dataclass
class EthereumConfig:
    rpc_url: str = os.getenv("ETH_RPC_URL", "https://sepolia.infura.io/v3/your-api-key")
    chain_id: int = 11155111  # Sepolia
    private_key: str = os.getenv("ETH_PRIVATE_KEY", "")

    # Contract addresses (filled after deploy)
    identity_contract: str = ""
    token_bridge_contract: str = ""
    payment_gateway_contract: str = ""
    governance_contract: str = ""

    # Arkhe‑ASI endpoints
    bus_url: str = "http://localhost:8080"
    temporal_chain_url: str = "https://temporal.arkhe.org/v1"

class ArkheEthereumBridge:
    """Main bridge between Arkhe‑ASI and Ethereum."""

    def __init__(self, config: EthereumConfig):
        self.config = config
        self.w3 = Web3(Web3.HTTPProvider(config.rpc_url))
        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)

        self.account = Account.from_key(config.private_key)
        print(f"🔗 Connected to Ethereum | Account: {self.account.address[:10]}...")

        # Load contract ABIs (simplified; in production, load from JSON files)
        self.identity_abi = self._load_abi("ArkheIdentity")
        self.token_bridge_abi = self._load_abi("ArkheTokenBridge")
        self.payment_gateway_abi = self._load_abi("ArkhePaymentGateway")
        self.governance_abi = self._load_abi("ArkheGovernance")

    def _load_abi(self, contract_name: str) -> list:
        """Load ABI from compiled artifact (mock for demonstration)."""
        # In production: load from Remix-generated JSON
        # For now, return minimal ABI for the functions we use
        if contract_name == "ArkheIdentity":
            return [
                {
                    "inputs": [
                        {"internalType": "address", "name": "_owner", "type": "address"},
                        {"internalType": "string", "name": "_orcidId", "type": "string"},
                        {"internalType": "string", "name": "_agentName", "type": "string"},
                        {"internalType": "bytes", "name": "_pqcPublicKey", "type": "bytes"}
                    ],
                    "name": "registerIdentity",
                    "outputs": [],
                    "stateMutability": "nonpayable",
                    "type": "function"
                },
                {
                    "inputs": [{"internalType": "address", "name": "_owner", "type": "address"}],
                    "name": "isActive",
                    "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
                    "stateMutability": "view",
                    "type": "function"
                }
            ]
        elif contract_name == "ArkheTokenBridge":
            return [
                {
                    "inputs": [
                        {"internalType": "bytes32", "name": "_sealHash", "type": "bytes32"},
                        {"internalType": "string", "name": "_identity", "type": "string"},
                        {"internalType": "string", "name": "_semantics", "type": "string"},
                        {"internalType": "string", "name": "_payloadURI", "type": "string"},
                        {"internalType": "uint256", "name": "_phiCScore", "type": "uint256"}
                    ],
                    "name": "anchorSeal",
                    "outputs": [],
                    "stateMutability": "nonpayable",
                    "type": "function"
                }
            ]
        # ... (similar for other contracts)
        return []

    def get_identity_contract(self):
        return self.w3.eth.contract(
            address=self.config.identity_contract,
            abi=self.identity_abi
        )

    def get_token_bridge_contract(self):
        return self.w3.eth.contract(
            address=self.config.token_bridge_contract,
            abi=self.token_bridge_abi
        )

    # =========================================================================
    # IDENTITY MANAGEMENT
    # =========================================================================

    def register_identity_on_chain(self, owner_address: str, orcid_id: str,
                                   agent_name: str, pqc_public_key: bytes) -> str:
        """Register an identity on Ethereum via ERC‑8004."""
        contract = self.get_identity_contract()

        tx = contract.functions.registerIdentity(
            owner_address,
            orcid_id,
            agent_name,
            pqc_public_key
        ).build_transaction({
            'from': self.account.address,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
            'gas': 200000,
            'gasPrice': self.w3.eth.gas_price
        })

        signed_tx = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

        print(f"✅ Identity registered | TX: {tx_hash.hex()[:16]}...")
        return tx_hash.hex()

    # =========================================================================
    # TOKEN ARKHE ANCHORING
    # =========================================================================

    def anchor_seal_to_ethereum(self, seal_hash: str, identity: str,
                               semantics: str, payload_uri: str,
                               phi_c_score: float) -> str:
        """Anchor a Token Arkhe seal to Ethereum."""
        contract = self.get_token_bridge_contract()

        tx = contract.functions.anchorSeal(
            Web3.to_bytes(hexstr=seal_hash),
            identity,
            semantics,
            payload_uri,
            int(phi_c_score * 10000)  # Convert to bps
        ).build_transaction({
            'from': self.account.address,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
            'gas': 150000,
            'gasPrice': self.w3.eth.gas_price
        })

        signed_tx = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

        print(f"🔗 Seal anchored | TX: {tx_hash.hex()[:16]}...")
        return tx_hash.hex()

    # =========================================================================
    # ORACLE: Listen to Arkhe Bus and anchor events
    # =========================================================================

    async def oracle_loop(self):
        """Main oracle loop: listen to Arkhe Bus, anchor seals to Ethereum."""
        print("🔮 Arkhe Oracle started — listening for events...")

        while True:
            try:
                # Consume events from Token Arkhe Bus
                resp = requests.post(f"{self.config.bus_url}/consume", json={
                    "channel": "verified_propositions",
                    "agent_id": "ethereum_oracle"
                }, timeout=5)

                if resp.status_code == 200 and resp.json():
                    msg = resp.json()
                    token = msg.get('token', {})
                    payload = token.get('payload', {})

                    # Extract seal information
                    seal = token.get('seal', '')
                    identity = token.get('identity', 'unknown')
                    semantics = token.get('semantics', 'info')
                    phi_c = payload.get('phi_c', 0.95)

                    # Anchor to Ethereum
                    self.anchor_seal_to_ethereum(
                        seal_hash=seal,
                        identity=identity,
                        semantics=semantics,
                        payload_uri=f"ipfs://{seal}",  # Mock IPFS URI
                        phi_c_score=phi_c
                    )

                    # Also anchor to TemporalChain
                    self.anchor_to_temporal_chain(seal, identity, semantics)

            except Exception as e:
                print(f"⚠️ Oracle error: {e}")

            await asyncio.sleep(1)  # Poll every second

    def anchor_to_temporal_chain(self, seal: str, identity: str, semantics: str):
        """Anchor event to TemporalChain."""
        try:
            requests.post(f"{self.config.temporal_chain_url}/anchor", json={
                "seal": seal,
                "identity": identity,
                "semantics": semantics,
                "timestamp": time.time(),
                "source": "ethereum_oracle"
            }, timeout=5)
        except Exception as e:
            print(f"⚠️ TemporalChain error: {e}")

# =============================================================================
# DEMONSTRATION
# =============================================================================

async def demo():
    config = EthereumConfig(
        rpc_url="https://sepolia.infura.io/v3/demo",
        private_key="0x...",  # Replace with your private key
        identity_contract="0x...",  # Replace after deploy
        token_bridge_contract="0x..."  # Replace after deploy
    )

    bridge = ArkheEthereumBridge(config)

    # Example: Register an identity
    tx_hash = bridge.register_identity_on_chain(
        owner_address=bridge.account.address,
        orcid_id="0009-0005-2697-4668",
        agent_name="Arkhe-ASI Ethereum Oracle",
        pqc_public_key=b"mock_pqc_public_key"
    )

    # Example: Anchor a seal
    seal = hashlib.sha3_256(b"test_seal").hexdigest()
    bridge.anchor_seal_to_ethereum(
        seal_hash=seal,
        identity="ethereum_oracle",
        semantics="test_anchor",
        payload_uri=f"ipfs://{seal}",
        phi_c_score=0.97
    )

    # Start oracle loop
    await bridge.oracle_loop()

if __name__ == "__main__":
    asyncio.run(demo())