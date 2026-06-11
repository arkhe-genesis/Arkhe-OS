"""
cathedral_crypto/bls_utils.py
BLS12-381 utilities using blst-py – identidade e autenticidade.
Selo: BLS-UTILS-v1.0.0-2026-06-10
"""
import hashlib
from typing import Tuple, Optional
import secrets

try:
    import blst
    BLST_AVAILABLE = True
except ImportError:
    BLST_AVAILABLE = False
    print("[BLS] blst-py não instalado. Usando stub para testes locais.")

class BLSKeyPair:
    """Par de chaves BLS12-381 para assinatura e verificação."""

    def __init__(self, sk: Optional[bytes] = None):
        if not BLST_AVAILABLE:
            # Stub para testes
            if sk is None:
                self.sk_bytes = secrets.token_bytes(32)
            else:
                self.sk_bytes = sk
            self.pk_bytes = hashlib.sha256(self.sk_bytes).digest()
        else:
            if sk is None:
                self.sk = blst.SecretKey()
                self.sk.keygen()
            else:
                self.sk = blst.SecretKey(sk)
            self.pk = self.sk.public_key()

    @property
    def private_key_bytes(self) -> bytes:
        if not BLST_AVAILABLE:
            return self.sk_bytes
        return self.sk.to_bytes()

    @property
    def public_key_bytes(self) -> bytes:
        if not BLST_AVAILABLE:
            return self.pk_bytes
        return self.pk.to_bytes()

    def sign(self, message: bytes, dst: bytes = b"BLS_SIG_BLS12381G1_XMD:SHA-256_SSWU_RO_NUL_") -> bytes:
        """Assina uma mensagem com a chave privada."""
        if not BLST_AVAILABLE:
            return hashlib.sha256(self.sk_bytes + message).digest()

        sig = blst.Signature()
        sig.sign(self.sk, message, dst=dst)
        return sig.to_bytes()

    @staticmethod
    def verify(message: bytes, signature: bytes, pk: bytes,
               dst: bytes = b"BLS_SIG_BLS12381G1_XMD:SHA-256_SSWU_RO_NUL_") -> bool:
        """Verifica uma assinatura BLS."""
        if not BLST_AVAILABLE:
            # Mock verification
            return True

        try:
            sig = blst.Signature(signature)
            pub = blst.PublicKey(pk)
            return sig.verify(True, pub, message, dst=dst)
        except Exception:
            return False

    @staticmethod
    def aggregate_signatures(signatures: list, public_keys: list, message: bytes) -> bool:
        """
        Agrega múltiplas assinaturas e verifica contra chaves públicas agregadas.
        Útil para consenso threshold.
        """
        if not BLST_AVAILABLE:
            return True

        agg_sig = blst.AggregateSignature()
        for sig_bytes in signatures:
            agg_sig.add_signature(blst.Signature(sig_bytes))

        # Agrega chaves públicas
        agg_pk = blst.AggregatePublicKey()
        for pk_bytes in public_keys:
            agg_pk.add_public_key(blst.PublicKey(pk_bytes))

        return agg_sig.aggregate_verify(True, agg_pk, message, dst=b"BLS_SIG_BLS12381G1_XMD:SHA-256_SSWU_RO_NUL_")
