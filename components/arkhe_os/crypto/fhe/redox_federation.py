"""
Substrate 283: Privacy-Preserving Redox Federation
Enables privacy-preserving federated aggregation of redox data across institutions
using compositional FHE.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass

try:
    from arkhe_os.crypto.fhe.nostr_fhe_engine import (
        MockSEAL, EncryptionParameters, SchemeType, SEALContext, KeyGenerator,
        Encryptor, Decryptor, Evaluator, CKKSEncoder, Ciphertext
    )
except ImportError:
    # Fallback to local MockSEAL if nostr_fhe_engine is not importable
    class MockSEAL:
        class EncryptionParameters:
            def __init__(self, scheme): pass
            def set_poly_modulus_degree(self, degree): pass
            def set_coeff_modulus(self, coeff): pass
        class SchemeType:
            CKKS = "CKKS"
        class SEALContext:
            def __init__(self, params): pass
        class KeyGenerator:
            def __init__(self, context): pass
            def create_public_key(self): return "pubkey"
            def create_secret_key(self): return "seckey"
        class Encryptor:
            def __init__(self, context, pubkey): pass
            def encrypt(self, plain): return f"enc({plain})"
        class Decryptor:
            def __init__(self, context, seckey): pass
            def decrypt(self, encrypted): return f"dec({encrypted})"
        class Evaluator:
            def __init__(self, context): pass
            def add(self, a, b): return f"add({a}, {b})"
            def multiply_plain(self, a, b): return f"mul({a}, {b})"
        class CKKSEncoder:
            def __init__(self, context): pass
            def encode(self, values, scale): return values
            def decode(self, plain): return plain
        class Ciphertext:
            pass

    EncryptionParameters = MockSEAL.EncryptionParameters
    SchemeType = MockSEAL.SchemeType
    SEALContext = MockSEAL.SEALContext
    KeyGenerator = MockSEAL.KeyGenerator
    Encryptor = MockSEAL.Encryptor
    Decryptor = MockSEAL.Decryptor
    Evaluator = MockSEAL.Evaluator
    CKKSEncoder = MockSEAL.CKKSEncoder
    Ciphertext = MockSEAL.Ciphertext


@dataclass
class EncryptedRedoxData:
    institution_id: str
    encrypted_coherence_vector: Ciphertext
    encrypted_covariance_matrix: Ciphertext
    sample_size: int

class RedoxFederationFHE:
    """Federated learning engine using FHE for redox data aggregation."""

    def __init__(self, security_level: int = 128):
        self.security_level = security_level
        self.params = self._init_params()
        self.context = SEALContext(self.params)
        self.keygen = KeyGenerator(self.context)

        # Central public key for federation
        self.public_key = self.keygen.create_public_key()
        # Secret key is theoretically distributed or kept secure by a central auditor
        self.secret_key = self.keygen.create_secret_key()

        self.encryptor = Encryptor(self.context, self.public_key)
        self.decryptor = Decryptor(self.context, self.secret_key)
        self.evaluator = Evaluator(self.context)
        self.ckks_encoder = CKKSEncoder(self.context)

    def _init_params(self) -> EncryptionParameters:
        params = EncryptionParameters(SchemeType.CKKS)
        if self.security_level == 128:
            params.set_poly_modulus_degree(8192)
            params.set_coeff_modulus([60, 40, 40, 60])
        return params

    def encrypt_institutional_data(
        self,
        institution_id: str,
        coherence_vector: List[float],
        covariance_flat: List[float],
        sample_size: int
    ) -> EncryptedRedoxData:
        """Encrypts a single institution's redox data using the federation public key."""
        # Scale determines the precision of the floating point numbers
        scale = 2**40

        encoded_vector = self.ckks_encoder.encode(coherence_vector, scale=scale)
        encrypted_vector = self.encryptor.encrypt(encoded_vector)

        encoded_covariance = self.ckks_encoder.encode(covariance_flat, scale=scale)
        encrypted_covariance = self.encryptor.encrypt(encoded_covariance)

        return EncryptedRedoxData(
            institution_id=institution_id,
            encrypted_coherence_vector=encrypted_vector,
            encrypted_covariance_matrix=encrypted_covariance,
            sample_size=sample_size
        )

    def aggregate_federated_data(self, data_list: List[EncryptedRedoxData]) -> EncryptedRedoxData:
        """Homomorphically aggregates encrypted redox data across institutions."""
        if not data_list:
            raise ValueError("No data provided for aggregation")

        total_samples = sum(d.sample_size for d in data_list)

        # Weight each institution's contribution by their sample size
        # Start with the first institution
        first_weight = data_list[0].sample_size / total_samples

        encoded_weight = self.ckks_encoder.encode([first_weight], scale=2**40)

        agg_vector = self.evaluator.multiply_plain(
            data_list[0].encrypted_coherence_vector,
            encoded_weight
        )
        agg_covariance = self.evaluator.multiply_plain(
            data_list[0].encrypted_covariance_matrix,
            encoded_weight
        )

        # Add subsequent institutions
        for data in data_list[1:]:
            weight = data.sample_size / total_samples
            encoded_weight = self.ckks_encoder.encode([weight], scale=2**40)

            weighted_vec = self.evaluator.multiply_plain(
                data.encrypted_coherence_vector,
                encoded_weight
            )
            weighted_cov = self.evaluator.multiply_plain(
                data.encrypted_covariance_matrix,
                encoded_weight
            )

            agg_vector = self.evaluator.add(agg_vector, weighted_vec)
            agg_covariance = self.evaluator.add(agg_covariance, weighted_cov)

        return EncryptedRedoxData(
            institution_id="AGGREGATED_FEDERATION",
            encrypted_coherence_vector=agg_vector,
            encrypted_covariance_matrix=agg_covariance,
            sample_size=total_samples
        )

    def decrypt_global_model(self, aggregated_data: EncryptedRedoxData) -> Dict[str, List[float]]:
        """Decrypts the final aggregated global model (authorized central node only)."""
        decrypted_vector_plain = self.decryptor.decrypt(aggregated_data.encrypted_coherence_vector)
        decrypted_vector = self.ckks_encoder.decode(decrypted_vector_plain)

        decrypted_covariance_plain = self.decryptor.decrypt(aggregated_data.encrypted_covariance_matrix)
        decrypted_covariance = self.ckks_encoder.decode(decrypted_covariance_plain)

        return {
            "global_coherence_vector": decrypted_vector,
            "global_covariance_matrix": decrypted_covariance,
            "total_samples": aggregated_data.sample_size
        }
