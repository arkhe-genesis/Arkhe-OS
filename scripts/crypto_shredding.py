# crypto_shredding.py — Exclusão verdadeira de dados via destruição de chaves

import hashlib
import logging
import time
from typing import Dict, Set

class CryptoShreddingSystem:
    """
    Sistema que garante exclusão verdadeira de dados.
    Ao invés de tentar apagar cada log físico em sistemas distribuídos,
    destruímos a chave de criptografia vinculada ao citizen_id.
    """

    def __init__(self):
        # Mapeamento de citizen_id para sua chave mestra de dados (Simulado)
        self._key_vault: Dict[str, str] = {}
        # Lista de cidadãos que solicitaram "shredding"
        self._shredded_citizens: Set[str] = set()

    def generate_citizen_key(self, citizen_id: str) -> str:
        """Gera e armazena uma chave única para o cidadão."""
        key = hashlib.sha256(f"master_key_{citizen_id}_{time.time()}".encode()).hexdigest()
        self._key_vault[citizen_id] = key
        return key

    def get_citizen_key(self, citizen_id: str) -> str:
        """Recupera a chave. Retorna None se foi destruída."""
        if citizen_id in self._shredded_citizens:
            return None
        return self._key_vault.get(citizen_id)

    def request_shredding(self, citizen_id: str):
        """
        Executa o 'shredding'. A chave é removida do vault e marcada como destruída.
        Qualquer dado criptografado com esta chave torna-se indecifrável (ruído).
        """
        if citizen_id in self._key_vault:
            del self._key_vault[citizen_id]
            self._shredded_citizens.add(citizen_id)
            logging.critical(f"[SHRED] Chaves do cidadão {citizen_id} DESTRUÍDAS. Dados agora são ilegíveis.")
            return True
        return False

    def is_shredded(self, citizen_id: str) -> bool:
        return citizen_id in self._shredded_citizens
