from web3 import Web3
import requests
import hashlib

class AsiOwlEthVerifier:
    """Verifies the integrity of the decentralized constitution."""

    ENS_CONTRACT = "0x00000000000C2E074eC69A0dFb2997BA6C7d2e1e"  # ENS Registry
    IPFS_GATEWAY = "https://ipfs.arkhe.io/ipfs"

    def __init__(self, eth_rpc_url: str):
        self.w3 = Web3(Web3.HTTPProvider(eth_rpc_url))
        self.expected_sha3 = "a3f7c8b9e0d1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7"

    def resolve_ipfs_cid(self) -> str:
        """Resolves asi.owl.eth to IPFS CID via ENS."""
        # Hash of the ENS name
        namehash = self.w3.ens.namehash("asi.owl.eth")

        # Get the resolver contract
        resolver_contract = self.w3.ens.resolver("asi.owl.eth")
        if not resolver_contract:
            raise Exception("Resolver not found for asi.owl.eth")

        # Re-initialize contract with proper ABI for text records
        abi = [{"inputs":[{"internalType":"bytes32","name":"node","type":"bytes32"},{"internalType":"string","name":"key","type":"string"}],"name":"text","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"}]
        resolver = self.w3.eth.contract(address=resolver_contract.address, abi=abi)

        cid = resolver.functions.text(namehash, "ipfs.cid").call()
        return cid

    def fetch_constitution(self, cid: str) -> bytes:
        """Fetches the ontology content via IPFS gateway."""
        url = self.IPFS_GATEWAY + "/" + cid
        response = requests.get(url)
        response.raise_for_status()
        return response.content

    def verify(self) -> bool:
        """Verifies if the IPFS content matches the canonical hash."""
        cid = self.resolve_ipfs_cid()
        content = self.fetch_constitution(cid)

        computed_hash = hashlib.sha3_256(content).hexdigest()

        if computed_hash != self.expected_sha3:
            raise Exception("Hash mismatch! Expected: " + self.expected_sha3[:16] + "..., Obtained: " + computed_hash[:16] + "...")

        print("Constitution verified!")
        print("   ENS: asi.owl.eth")
        print("   IPFS CID: " + cid)
        print("   SHA3-256: " + computed_hash[:32] + "...")
        print("   Size: " + str(len(content)) + " bytes")
        return True

if __name__ == "__main__":
    # Usage
    verifier = AsiOwlEthVerifier("https://mainnet.infura.io/v3/YOUR_PROJECT_ID")
    verifier.verify()
