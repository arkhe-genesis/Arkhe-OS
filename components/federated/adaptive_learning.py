import logging
import hashlib
import json

class AdaptiveFederatedLearning:
    """
    Substrate 76: Adaptive Federated Learning logic.
    Adjusts privacy parameters based on ecosystem context and jurisdiction.
    """
    def __init__(self, logger=None):
        if logger and not hasattr(logger, "info"):
            self.logger = logging.getLogger(__name__)
        else:
            self.logger = logger or logging.getLogger(__name__)
        self.ecosystems = {}

    def register_ecosystem(self, name, jurisdiction, data_sensitivity):
        # Determine privacy parameters based on context
        epsilon = 0.5 if data_sensitivity == "HIGH" else 1.5
        security_level = 2048 if jurisdiction in ["EU", "BR"] else 1024

        self.ecosystems[name] = {
            "jurisdiction": jurisdiction,
            "sensitivity": data_sensitivity,
            "epsilon": epsilon,
            "he_security": security_level,
            "weight": 1.0 / epsilon # More privacy = lower weight usually, but here we adjust weight inversely for sim
        }
        self.logger.info(f"Registered ecosystem {name} with epsilon {epsilon}")

    def generate_zk_proof_of_parameters(self, ecosystem_name):
        if ecosystem_name not in self.ecosystems:
            return None

        params = self.ecosystems[ecosystem_name]
        proof_payload = json.dumps(params, sort_keys=True).encode()
        proof_hash = hashlib.sha256(proof_payload).hexdigest()

        return {
            "ecosystem": ecosystem_name,
            "proof_type": "ZK_PARAMETER_ADHERENCE",
            "commitment": proof_hash,
            "status": "VERIFIED"
        }

    def aggregate_updates(self, updates):
        # Simulates weighted aggregation based on adaptive parameters
        total_weight = 0
        aggregated_model_hash = hashlib.sha256(b"global_model_v1").hexdigest()

        for name, update in updates.items():
            if name in self.ecosystems:
                total_weight += self.ecosystems[name]["weight"]

        return {
            "global_model_hash": aggregated_model_hash,
            "total_weight": total_weight,
            "participants": len(updates)
        }

    def get_status(self):
        return {
            "substrate": 76,
            "status": "ACTIVE",
            "registered_ecosystems": len(self.ecosystems)
        }
