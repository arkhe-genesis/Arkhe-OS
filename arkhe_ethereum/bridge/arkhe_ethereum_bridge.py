import json
import asyncio
from web3 import Web3
from web3.exceptions import ContractLogicError

class ArkheEthereumBridge:
    def __init__(self, rpc_url: str, private_key: str):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.private_key = private_key
        if self.private_key:
            self.account = self.w3.eth.account.from_key(private_key)
            self.w3.eth.default_account = self.account.address
        else:
            self.account = None

        self.identity_contract = None
        self.bridge_contract = None
        self.payment_contract = None
        self.governance_contract = None

    def connect_contracts(self, identity_address, identity_abi,
                          bridge_address, bridge_abi,
                          payment_address, payment_abi,
                          governance_address, governance_abi):
        self.identity_contract = self.w3.eth.contract(address=identity_address, abi=identity_abi)
        self.bridge_contract = self.w3.eth.contract(address=bridge_address, abi=bridge_abi)
        self.payment_contract = self.w3.eth.contract(address=payment_address, abi=payment_abi)
        self.governance_contract = self.w3.eth.contract(address=governance_address, abi=governance_abi)

    def _send_transaction(self, tx):
        if not self.account:
            raise Exception("No private key provided for transaction signing.")

        tx['nonce'] = self.w3.eth.get_transaction_count(self.account.address)
        signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        return receipt

    def register_identity_on_chain(self, orcid: str, pqc_public_key: bytes):
        if not self.account:
            raise Exception("No private key provided for transaction signing.")
        tx = self.identity_contract.functions.registerIdentity(
            orcid, pqc_public_key
        ).build_transaction({
            'from': self.account.address,
            'gas': 2000000,
            'gasPrice': self.w3.eth.gas_price
        })
        return self._send_transaction(tx)

    def anchor_seal_to_ethereum(self, seal_hash: bytes, phi_c_score: int, metadata_uri: str):
        if not self.account:
            raise Exception("No private key provided for transaction signing.")
        # seal_hash must be exactly 32 bytes for bytes32
        tx = self.bridge_contract.functions.anchorSeal(
            seal_hash, phi_c_score, metadata_uri
        ).build_transaction({
            'from': self.account.address,
            'gas': 2000000,
            'gasPrice': self.w3.eth.gas_price
        })
        return self._send_transaction(tx)

    async def oracle_loop(self, event_queue: asyncio.Queue):
        """Continuously consumes verified propositions from Token Arkhe Bus and anchors to Ethereum"""
        print("Starting Oracle Loop...")
        while True:
            event = await event_queue.get()
            print(f"Oracle Loop picked up event: {event}")
            try:
                seal_hash = event.get('seal_hash')
                phi_c_score = event.get('phi_c_score')
                metadata_uri = event.get('metadata_uri')

                receipt = await asyncio.to_thread(self.anchor_seal_to_ethereum, seal_hash, phi_c_score, metadata_uri)
                print(f"Anchored seal {seal_hash.hex()} to Ethereum! Tx Hash: {receipt.transactionHash.hex()}")
            except Exception as e:
                print(f"Failed to anchor event: {e}")
            finally:
                event_queue.task_done()
