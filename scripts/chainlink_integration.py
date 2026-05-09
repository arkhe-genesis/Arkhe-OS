from web3 import Web3
from eth_account import Account
import requests
import json

class ChainlinkResourceOracle:
    """Cliente Python para consultar preços via Chainlink Oracle."""

    def __init__(
        self,
        rpc_url: str,
        contract_address: str,
        private_key: str,
        chain_id: int = 80001  # Mumbai testnet
    ):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.account = Account.from_key(private_key)
        self.contract = self.w3.eth.contract(
            address=contract_address,
            abi=self._load_abi()  # carregar ABI do contrato
        )
        self.chain_id = chain_id

    def _load_abi(self) -> list:
        """Carrega ABI do contrato (simplificado)."""
        return [
            {
                "inputs": [{"name": "resource", "type": "string"}],
                "name": "getPrice",
                "outputs": [{"name": "", "type": "uint256"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [
                    {"name": "resource", "type": "string"},
                    {"name": "source", "type": "string"}
                ],
                "name": "requestResourcePrice",
                "outputs": [{"name": "", "type": "bytes32"}],
                "stateMutability": "nonpayable",
                "type": "function"
            }
        ]

    def get_price(self, resource: str) -> float:
        """Consulta preço atual de recurso (leitura)."""
        price_wei = self.contract.functions.getPrice(resource).call()
        return price_wei / 1e18  # converter de wei para unidade base

    def request_price_update(self, resource: str, source_code: str) -> str:
        """Solicita atualização de preço via Chainlink Functions."""
        tx = self.contract.functions.requestResourcePrice(
            resource, source_code
        ).build_transaction({
            'from': self.account.address,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
            'chainId': self.chain_id,
            'gas': 300000
        })

        signed = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed.rawTransaction)

        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        return tx_hash.hex()

    def use_in_negotiation(self, negotiator, zone: str, resource: str):
        """Integra preços Chainlink na negociação de recursos."""
        price = self.get_price(resource)
        # Ajustar valuation com preço de mercado
        # base_valuation = negotiator.zone_valuations[zone].base
        # adjusted = ResourceBundle(
        #     energy_gj=base_valuation.energy_gj / price if resource == "energy_gj" else base_valuation.energy_gj,
        #     # ... ajustar outros recursos ...
        # )
        # return adjusted
        return None
