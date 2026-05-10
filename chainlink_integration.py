class ChainlinkResourceOracle:
    def __init__(self, rpc_url, contract_address, private_key, chain_id=80001):
        self.rpc_url = rpc_url
        self.contract_address = contract_address
        self.chain_id = chain_id

    def get_price(self, resource):
        return 100.0
