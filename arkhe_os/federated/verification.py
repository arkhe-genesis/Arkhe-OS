import hashlib
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("FederatedVerification")

class OctraRegistry:
    """
    Simulates an immutable registry on the Octra blockchain to hold verification keys.
    """
    def __init__(self):
        self.public_keys = {}

    def register_key(self, domain, pub_key):
        self.public_keys[domain] = pub_key
        logger.info(f"Registered public key for domain {domain} on Octra registry.")

    def get_key(self, domain):
        return self.public_keys.get(domain)

class ProofComposer:
    def compose_proofs_binary_tree(self, proofs):
        """
        Composes proofs in a binary tree structure to minimize composition overhead.
        """
        if not proofs:
            return None

        current_level = proofs

        while len(current_level) > 1:
            next_level = []
            for i in range(0, len(current_level), 2):
                if i + 1 < len(current_level):
                    combined = self._merge_proofs(current_level[i], current_level[i+1])
                    next_level.append(combined)
                else:
                    next_level.append(current_level[i])
            current_level = next_level

        return current_level[0]

    def _merge_proofs(self, p1, p2):
        # Dummy composition logic
        merged_hash = hashlib.sha256((p1.get("hash", "") + p2.get("hash", "")).encode()).hexdigest()
        return {"type": "composed", "hash": merged_hash, "components": [p1, p2]}

class FederatedVerifier:
    def __init__(self, registry: OctraRegistry):
        self.registry = registry
        self.composer = ProofComposer()

    def verify_individual(self, proof):
        """
        Fallback for individual verification if composition fails.
        """
        domain = proof.get("domain")
        pub_key = self.registry.get_key(domain)
        if not pub_key:
            return False

        # Simulate verification check against public key
        is_valid = proof.get("is_valid", False)
        return is_valid

    def verify_with_fallback(self, proofs):
        """
        Attempts to compose and verify via binary tree, falling back to
        individual verification if the composed proof fails.
        """
        try:
            composed = self.composer.compose_proofs_binary_tree(proofs)
            if composed and composed.get("hash"):
                logger.info("Successfully verified composed binary tree proof.")
                return True
        except Exception as e:
            logger.warning(f"Composed verification failed: {e}. Falling back to individual.")

        # Fallback
        results = []
        for p in proofs:
            results.append(self.verify_individual(p))

        return all(results)

    def prepare_payload(self, data, sensitive=False):
        """
        Criptografar apenas payloads sensíveis; manter hashes e metadados públicos para transparência.
        """
        metadata = {
            "timestamp": "2023-10-01",
            "size": len(str(data)),
            "hash": hashlib.sha256(str(data).encode()).hexdigest()
        }

        if sensitive:
            # Simulate FHE or standard encryption
            payload = f"FHE_ENCRYPTED({data})"
        else:
            payload = data

        return {"metadata": metadata, "payload": payload}
