#!/usr/bin/env python3
"""
cosmicdao_client.py — Cliente Python para submissão de provas à CosmicDAO
Integra: geração de prova ZK + assinatura + submissão on-chain + monitoramento
"""

import os
import json
import time
import hashlib
from pathlib import Path
from typing import Dict, Optional, List
from dataclasses import dataclass, asdict
from web3 import Web3, Account
from web3.middleware import geth_poa_middleware
from eth_account.messages import encode_defunct
import requests

@dataclass
class BlockchainConfig:
    """Configuração para conexão com blockchain"""
    rpc_url: str = "https://sepolia.infura.io/v3/YOUR_PROJECT_ID"  # ou local node
    chain_id: int = 11155111  # Sepolia testnet
    contract_address: str = "0x0000000000000000000000000000000000000000"  # Endereço do CosmicDAOVerifier
    relayer_private_key: Optional[str] = None  # Para transações patrocinadas
    gas_price_gwei: float = 20.0
    gas_limit: int = 500000
    confirmation_blocks: int = 3


class CosmicDAOClient:
    """
    Cliente para interagir com o contrato CosmicDAOVerifier.
    """

    def __init__(self, config: BlockchainConfig):
        self.config = config

        # Inicializar Web3
        self.w3 = Web3(Web3.HTTPProvider(config.rpc_url))
        try:
            if self.w3.eth.chain_id == 11155111:  # Sepolia
                self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        except:
            pass

        # Carregar contrato
        abi_path = Path(__file__).parent / "CosmicDAO.json"
        if abi_path.exists():
            with open(abi_path, 'r') as f:
                abi = json.load(f)['abi']
        else:
            # Minimal ABI if file missing
            abi = [
                {"inputs":[{"internalType":"uint256","name":"_omegaScaled","type":"uint256"},{"internalType":"bytes32","name":"_signalHash","type":"bytes32"},{"internalType":"bytes32","name":"_metadataHash","type":"bytes32"},{"components":[{"internalType":"uint256[2]","name":"pi_a","type":"uint256[2]"},{"internalType":"uint256[2][2]","name":"pi_b","type":"uint256[2][2]"},{"internalType":"uint256[2]","name":"pi_c","type":"uint256[2]"},{"internalType":"uint256[]","name":"public_signals","type":"uint256[]"}],"internalType":"struct IGroth16Verifier.Groth16Proof","name":"_proof","type":"tuple"}],"name":"submitCoherenceProof","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},
                {"inputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"name":"proofs","outputs":[{"internalType":"uint256","name":"proofId","type":"uint256"},{"internalType":"address","name":"prover","type":"address"},{"internalType":"uint256","name":"omegaScaled","type":"uint256"},{"internalType":"uint256","name":"timestamp","type":"uint256"},{"internalType":"bytes32","name":"signalHash","type":"bytes32"},{"internalType":"bytes32","name":"metadataHash","type":"bytes32"},{"internalType":"bool","name":"isValid","type":"bool"},{"internalType":"uint256","name":"gasUsed","type":"uint256"}],"stateMutability":"view","type":"function"}
            ]

        self.contract = self.w3.eth.contract(address=Web3.to_checksum_address(config.contract_address), abi=abi)

        # Configurar conta para transações
        if config.relayer_private_key:
            self.account = Account.from_key(config.relayer_private_key)
            self.w3.eth.default_account = self.account.address
            print(f"✅ Relayer account: {self.account.address[:10]}...")
        else:
            self.account = None
            print("⚠️ No relayer key; transactions require user signature")

    def prepare_proof_submission(
        self,
        omega: float,
        signal_data: bytes,
        metadata: Dict,
        zk_proof: Dict
    ) -> Dict:
        omega_scaled = int(omega * 1e6)
        signal_hash = Web3.keccak(signal_data)
        metadata_hash = Web3.keccak(text=json.dumps(metadata, sort_keys=True))

        solidity_proof = {
            'pi_a': [int(zk_proof['pi_a'][0], 16) if isinstance(zk_proof['pi_a'][0], str) else zk_proof['pi_a'][0],
                     int(zk_proof['pi_a'][1], 16) if isinstance(zk_proof['pi_a'][1], str) else zk_proof['pi_a'][1]],
            'pi_b': [
                [int(zk_proof['pi_b'][0][0], 16) if isinstance(zk_proof['pi_b'][0][0], str) else zk_proof['pi_b'][0][0],
                 int(zk_proof['pi_b'][0][1], 16) if isinstance(zk_proof['pi_b'][0][1], str) else zk_proof['pi_b'][0][1]],
                [int(zk_proof['pi_b'][1][0], 16) if isinstance(zk_proof['pi_b'][1][0], str) else zk_proof['pi_b'][1][0],
                 int(zk_proof['pi_b'][1][1], 16) if isinstance(zk_proof['pi_b'][1][1], str) else zk_proof['pi_b'][1][1]]
            ],
            'pi_c': [int(zk_proof['pi_c'][0], 16) if isinstance(zk_proof['pi_c'][0], str) else zk_proof['pi_c'][0],
                     int(zk_proof['pi_c'][1], 16) if isinstance(zk_proof['pi_c'][1], str) else zk_proof['pi_c'][1]],
            'public_signals': [
                omega_scaled,
                700000,
                int(zk_proof.get('salt', '0x0'), 16) if isinstance(zk_proof.get('salt', 0), str) else zk_proof.get('salt', 0)
            ]
        }

        message = f"I attest that coherence Ω={omega:.6f} was measured for signal {signal_hash.hex()[:16]}..."
        signed_message = encode_defunct(text=message)

        if self.account:
            signature = self.account.sign_message(signed_message)
            signature_hex = signature.signature.hex()
        else:
            signature_hex = None

        return {
            'omega_scaled': omega_scaled,
            'signal_hash': signal_hash.hex(),
            'metadata_hash': metadata_hash.hex(),
            'proof': solidity_proof,
            'message': message,
            'signature': signature_hex,
            'prover_address': self.account.address if self.account else None
        }

    async def submit_proof_async(
        self,
        prepared_proof: Dict,
        wait_for_confirmation: bool = True
    ) -> Dict:
        if not self.account:
             return {"success": False, "error": "Signature required: No relayer account configured"}

        tx_params = {
            'from': self.account.address,
            'gas': self.config.gas_limit,
            'gasPrice': self.w3.to_wei(self.config.gas_price_gwei, 'gwei'),
            'chainId': self.config.chain_id,
            'nonce': self.w3.eth.get_transaction_count(self.account.address)
        }

        tx = self.contract.functions.submitCoherenceProof(
            prepared_proof['omega_scaled'],
            Web3.to_bytes(hexstr=prepared_proof['signal_hash']),
            Web3.to_bytes(hexstr=prepared_proof['metadata_hash']),
            prepared_proof['proof']
        ).build_transaction(tx_params)

        signed_tx = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)

        tx_hash_hex = tx_hash.hex()
        print(f"📤 Proof submitted: tx_hash={tx_hash_hex}")

        if wait_for_confirmation:
            receipt = self.w3.eth.wait_for_transaction_receipt(
                tx_hash,
                timeout=120,
                poll_latency=2
            )

            if receipt['status'] == 1:
                return {
                    'success': True,
                    'tx_hash': tx_hash_hex,
                    'block_number': receipt['blockNumber'],
                    'gas_used': receipt['gasUsed'],
                    'omega_on_chain': prepared_proof['omega_scaled'] / 1e6
                }
            else:
                return {
                    'success': False,
                    'tx_hash': tx_hash_hex,
                    'error': 'Transaction reverted',
                    'gas_used': receipt['gasUsed']
                }

        return {
            'success': 'pending',
            'tx_hash': tx_hash_hex,
            'estimated_confirmation_sec': 15 * self.config.confirmation_blocks
        }
