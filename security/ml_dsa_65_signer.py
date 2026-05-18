import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

CKM_ML_DSA_65 = 0x00001051
CKM_ML_KEM_768 = 0x00001052

SUPPORTED_MECHANISMS = {
    "ML-DSA-65": {
        "mechanism_id": CKM_ML_DSA_65,
        "signature_size": 3309,
        "public_key_size": 1952,
        "private_key_size": 4032,
        "nist_level": 3,
        "fips_standard": "FIPS 204",
    },
    "ML-KEM-768": {
        "mechanism_id": CKM_ML_KEM_768,
        "ciphertext_size": 1088,
        "shared_secret_size": 32,
        "nist_level": 3,
        "fips_standard": "FIPS 203",
    }
}

class MLDSA65Signer:
    def __init__(
        self,
        pkcs11_lib: Optional[str] = None,
        token_label: Optional[str] = None,
        user_pin: Optional[str] = None,
        key_label: Optional[str] = None,
        mechanism: str = "ML-DSA-65"
    ):
        self.lib_path = pkcs11_lib or os.getenv("ARKHE_PKCS11_LIB", "/usr/lib/fips204/pkcs11.so")
        self.token_label = token_label or os.getenv("ARKHE_HSM_TOKEN", "ARKHE_HSM")
        self.user_pin = user_pin or os.getenv("ARKHE_HSM_PIN")
        self.key_label = key_label or os.getenv("ARKHE_HSM_KEY_LABEL", "substrate_signer_ml_dsa_65")
        self.mechanism_name = mechanism
        self.mechanism_config = SUPPORTED_MECHANISMS.get(mechanism)

        if not self.mechanism_config:
            raise ValueError(
                f"Mecanismo '{mechanism}' não suportado. "
                f"Suportados: {list(SUPPORTED_MECHANISMS.keys())}"
            )

        self._session = None
        self._private_key = None
        self._public_key = None
        self._active = False

        self._connect_or_fail()

    def _connect_or_fail(self):
        try:
            import pkcs11
            from pkcs11 import types as p11_types

            lib = pkcs11.lib(self.lib_path)
            token = lib.get_token(token_label=self.token_label)
            self._session = token.open(user_pin=self.user_pin, rw=True)

            priv_objs = self._session.find_objects([
                (p11_types.Attribute.CLASS, p11_types.ObjectClass.PRIVATE_KEY),
                (p11_types.Attribute.LABEL, self.key_label),
                (p11_types.Attribute.KEY_TYPE, self.mechanism_config["mechanism_id"]),
            ])
            if not priv_objs:
                raise RuntimeError(
                    f"Chave privada '{self.key_label}' (ML-DSA-65) não encontrada no HSM. "
                    f"Token: {self.token_label}. O sistema não pode operar sem esta chave."
                )
            self._private_key = priv_objs[0]

            pub_objs = self._session.find_objects([
                (p11_types.Attribute.CLASS, p11_types.ObjectClass.PUBLIC_KEY),
                (p11_types.Attribute.LABEL, self.key_label),
            ])
            if not pub_objs:
                raise RuntimeError(f"Chave pública '{self.key_label}' não encontrada no HSM.")
            self._public_key = pub_objs[0]

            extractable = self._private_key[p11_types.Attribute.EXTRACTABLE]
            if extractable:
                raise RuntimeError(
                    f"Chave privada '{self.key_label}' está marcada como EXPORTÁVEL. "
                    f"O sistema exige CKA_EXTRACTABLE=FALSE."
                )

            self._active = True
            logger.info(
                f"✅ ML-DSA-65 HSM ativo: token='{self.token_label}', "
                f"chave='{self.key_label}' (FIPS 204 Level 3, inexportável)"
            )
            return True

        except ImportError:
            raise RuntimeError(
                "PyKCS11 não instalado. O sistema requer HSM real com ML-DSA-65. "
                "Instale: pip install python-pkcs11"
            )
        except Exception as e:
            raise RuntimeError(
                f"Falha CRÍTICA ao conectar ao HSM: {e}. "
                f"O Unbuildable NÃO opera sem assinatura ML-DSA-65 via hardware."
            )

    def sign(self, data: bytes) -> bytes:
        if not self._active or not self._private_key:
            raise RuntimeError("HSM não está ativo. Impossível assinar.")

        try:
            import pkcs11
            from pkcs11 import types as p11_types

            mech = p11_types.Mechanism(self.mechanism_config["mechanism_id"])
            signature = self._private_key.sign(data, mechanism=mech)

            logger.info(
                f"✅ Assinatura ML-DSA-65 gerada: {len(signature)} bytes "
                f"(FIPS 204 Level {self.mechanism_config['nist_level']})"
            )
            return signature

        except Exception as e:
            raise RuntimeError(
                f"Falha CRÍTICA ao assinar com ML-DSA-65: {e}. "
                f"Operação REJEITADA."
            )

    def verify(self, data: bytes, signature: bytes) -> bool:
        if not self._active or not self._public_key:
            raise RuntimeError("HSM não está ativo. Impossível verificar.")

        try:
            import pkcs11
            from pkcs11 import types as p11_types

            mech = p11_types.Mechanism(self.mechanism_config["mechanism_id"])
            return self._public_key.verify(data, signature, mechanism=mech)

        except Exception as e:
            logger.error(
                f"Falha ao verificar com ML-DSA-65: {e}. "
                f"Operação REJEITADA."
            )
            return False

    def close(self):
        if self._session:
            self._session.close()
            self._active = False
            logger.info("🔒 Sessão HSM ML-DSA-65 encerrada.")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

class PQCSigner:
    def __init__(self):
        self.signer = MLDSA65Signer(mechanism="ML-DSA-65")

    def sign(self, message: str, key_label: str = "substrate_signer_ml_dsa_65") -> str:
        return self.signer.sign(message.encode()).hex()

    def verify(self, message: str, signature: str, key_label: str = "substrate_signer_ml_dsa_65") -> bool:
        try:
            sig_bytes = bytes.fromhex(signature)
            return self.signer.verify(message.encode(), sig_bytes)
        except (ValueError, TypeError) as e:
            logger.error(f"Formato de assinatura inválido: {e}")
            return False

    def close(self):
        self.signer.close()

def configure_ml_dsa_65_environment():
    os.environ.setdefault("ARKHE_PKCS11_LIB", "/usr/lib/fips204/pkcs11.so")
    os.environ.setdefault("ARKHE_HSM_TOKEN", "ARKHE_HSM")
    os.environ.setdefault("ARKHE_HSM_KEY_LABEL", "substrate_signer_ml_dsa_65")

    logger.info("✅ Ambiente configurado para ML-DSA-65 (FIPS 204)")
    logger.info("   Biblioteca: " + os.environ["ARKHE_PKCS11_LIB"])
    logger.info("   Token: " + os.environ["ARKHE_HSM_TOKEN"])
    logger.info("   Chave: " + os.environ["ARKHE_HSM_KEY_LABEL"])
    logger.info("   MODO: SEM FALLBACK — falhas são REJEITADAS")
