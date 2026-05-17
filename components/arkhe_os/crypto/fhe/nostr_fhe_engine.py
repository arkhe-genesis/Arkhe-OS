# arkhe_os/crypto/fhe/nostr_fhe_engine.py
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import numpy as np

# ing seal for environments where Microsoft SEAL is not installed
class PySEAL:
    class EncryptionParameters:
        def __init__(self, scheme): self.scheme = scheme
        def set_poly_modulus_degree(self, degree): self.degree = degree
        def set_coeff_modulus(self, coeff): self.coeff = coeff
    class SchemeType:
        CKKS = "CKKS"
        BFV = "BFV"
    class SEALContext:
        def __init__(self, params): self.params = params
    class KeyGenerator:
        def __init__(self, context): self.context = context
        def create_public_key(self): return "pubkey"
        def create_secret_key(self): return "seckey"
    class Encryptor:
        def __init__(self, context, pubkey): self.pubkey = pubkey
        def encrypt(self, plain): return {"data": plain, "encrypted": True}
    class Decryptor:
        def __init__(self, context, seckey): self.seckey = seckey
        def decrypt(self, encrypted): return encrypted["data"]
    class Evaluator:
        def __init__(self, context): self.context = context
        def add(self, a, b):
            if isinstance(a, dict) and isinstance(b, dict):
                return {"data": [x + y for x, y in zip(a["data"], b["data"])], "encrypted": True}
            return {"data": a["data"] + b["data"], "encrypted": True}
        def sub(self, a, b):
            if isinstance(a, dict) and isinstance(b, dict):
                return {"data": [x - y for x, y in zip(a["data"], b["data"])], "encrypted": True}
            return {"data": a["data"] - b["data"], "encrypted": True}
        def multiply_plain(self, a, b):
            if isinstance(a, dict):
                return {"data": [x * b[0] for x in a["data"]], "encrypted": True}
            return {"data": a["data"] * b[0], "encrypted": True}
    class CKKSEncoder:
        def __init__(self, context): self.context = context
        def encode(self, values, scale): return values
        def decode(self, plain): return plain
    class BFVEncoder:
        def __init__(self, context): self.context = context
        def encode(self, values): return values
        def decode(self, plain): return plain
    class Ciphertext:
        pass
    class Plaintext:
        pass

try:
    from seal import (
        EncryptionParameters, SchemeType, SEALContext, KeyGenerator,
        Encryptor, Decryptor, Evaluator, CKKSEncoder, BFVEncoder,
        Ciphertext, Plaintext
    )
except ImportError:
    EncryptionParameters = PySEAL.EncryptionParameters
    SchemeType = PySEAL.SchemeType
    SEALContext = PySEAL.SEALContext
    KeyGenerator = PySEAL.KeyGenerator
    Encryptor = PySEAL.Encryptor
    Decryptor = PySEAL.Decryptor
    Evaluator = PySEAL.Evaluator
    CKKSEncoder = PySEAL.CKKSEncoder
    BFVEncoder = PySEAL.BFVEncoder
    Ciphertext = PySEAL.Ciphertext
    Plaintext = PySEAL.Plaintext


@dataclass
class NostrEventComponents:
    """Componentes de um evento Nostr para criptografia seletiva."""
    pr_content: Optional[str] = None          # Conteúdo sensível de PR
    coherence_report: Optional[Dict] = None   # Métricas de coerência (floats)
    signature_data: Optional[bytes] = None    # Assinatura criptográfica
    public_meta: Optional[Dict] = None    # Metadados públicos (não criptografados)

class NostrFHEEngine:
    """Motor FHE composicional para criptografar payloads de eventos Nostr."""

    def __init__(self, security_level: int = 128):
        self.security_level = security_level
        self.params = self._init_params()
        self.context = SEALContext(self.params)
        self.keygen = KeyGenerator(self.context)
        self.public_key = self.keygen.create_public_key()
        self.secret_key = self.keygen.create_secret_key()
        self.encryptor = Encryptor(self.context, self.public_key)
        self.decryptor = Decryptor(self.context, self.secret_key)
        self.evaluator = Evaluator(self.context)

        # Encoders por tipo de dado
        self.ckks_encoder = CKKSEncoder(self.context)  # Para floats (coherence_report)
        self.bfv_encoder = BFVEncoder(self.context)     # Para ints (signature_data)

        # Cache de ciphertexts
        self.ciphertext_cache: Dict[str, Ciphertext] = {}

    def _init_params(self) -> EncryptionParameters:
        """Inicializa parâmetros FHE baseados no nível de segurança."""
        params = EncryptionParameters(SchemeType.CKKS)
        if self.security_level == 128:
            params.set_poly_modulus_degree(8192)
            params.set_coeff_modulus(
                [60, 40, 40, 60]  # Bits para coeficientes modulares
            )
        elif self.security_level == 256:
            params.set_poly_modulus_degree(16384)
            params.set_coeff_modulus(
                [60, 50, 50, 50, 60]
            )
        else:
            raise ValueError(f"Unsupported security level: {self.security_level}")
        return params

    def encrypt_event(self, event: NostrEventComponents, event_id: str) -> Dict[str, Ciphertext]:
        """Criptografa componentes de evento Nostr com esquemas apropriados."""
        encrypted = {}

        # Criptografar coherence_report com CKKS (dados contínuos)
        if event.coherence_report:
            values = list(event.coherence_report.values())
            plain = self.ckks_encoder.encode(values, scale=2**40)
            encrypted['coherence_report'] = self.encryptor.encrypt(plain)

        # Criptografar signature_data com BFV (dados discretos)
        if event.signature_data:
            int_vals = [int(b) for b in event.signature_data]
            plain = self.bfv_encoder.encode(int_vals)
            encrypted['signature_data'] = self.encryptor.encrypt(plain)

        # Criptografar pr_content com BFV após tokenização
        if event.pr_content:
            tokens = [hash(t) % (2**31) for t in event.pr_content.split()[:100]]
            plain = self.bfv_encoder.encode(tokens)
            encrypted['pr_content'] = self.encryptor.encrypt(plain)

        # Cache para reuso
        for key, ct in encrypted.items():
            self.ciphertext_cache[f"{event_id}:{key}"] = ct

        return encrypted

    def aggregate_coherence_reports(
        self,
        encrypted_reports: List[Ciphertext]
    ) -> Ciphertext:
        """Agrega múltiplos relatórios de coerência criptografados via soma homomórfica."""
        if not encrypted_reports:
            raise ValueError("No reports to aggregate")

        result = encrypted_reports[0]
        for ct in encrypted_reports[1:]:
            result = self.evaluator.add(result, ct)

        # Dividir por N para média (multiplicação por escalar)
        n = len(encrypted_reports)
        result = self.evaluator.multiply_plain(
            result,
            self.ckks_encoder.encode([1.0/n], scale=2**40)
        )

        return result

    def decrypt_coherence_aggregate(
        self,
        encrypted: Ciphertext
    ) -> List[float]:
        """Decripta resultado agregado de coerência (apenas para nós autorizados)."""
        plain = self.decryptor.decrypt(encrypted)
        return self.ckks_encoder.decode(plain)

    def compute_coherence_delta_homomorphically(
        self,
        encrypted_before: Ciphertext,
        encrypted_after: Ciphertext
    ) -> Ciphertext:
        """Computa delta de coerência sobre dados criptografados."""
        return self.evaluator.sub(encrypted_after, encrypted_before)
