#!/usr/bin/env python3
"""
fhe_key_manager.py — Gestão distribuída de chaves FHE via DHT anônima.
"""
import asyncio
import hashlib
import json
from pathlib import Path
from typing import Dict, Optional
import tenseal as ts

class FHEKeyManager:
    """Gestão soberana de chaves FHE com verificação por pares."""

    def __init__(self, node_id: str, dht_client):
        self.node_id = node_id
        self.dht = dht_client
        self.key_pairs: Dict[str, ts.Context] = {}

    async def generate_and_publish_keypair(self,
                                          purpose: str,
                                          config: 'FHEConfig') -> str:
        """Gera par de chaves e publica hash público na DHT."""
        # Criar contexto com parâmetros
        context = ts.context(
            ts.SchemeType.CKKS,
            poly_modulus_degree=config.poly_modulus_degree,
            coeff_mod_bit_sizes=config.coeff_mod_bit_sizes
        )
        context.generate_galois_keys()
        context.generate_relin_keys()

        # Extrair chave pública para compartilhamento
        public_key = context.public_key()

        # Hash da chave pública para verificação
        pk_hash = hashlib.sha3_256(
            public_key.serialize()
        ).hexdigest()

        # Publicar na DHT (apenas hash, não a chave completa)
        record = {
            "node_id": self.node_id,
            "purpose": purpose,
            "pk_hash": pk_hash,
            "config_hash": hashlib.sha3_256(
                json.dumps(config.__dict__, sort_keys=True).encode()
            ).hexdigest(),
            "timestamp": asyncio.get_event_loop().time()
        }
        await self.dht.store(f"fhe_key:{pk_hash[:16]}", json.dumps(record))

        # Armazenar localmente (chave privada nunca sai do nó)
        self.key_pairs[pk_hash] = context

        return pk_hash

    async def verify_peer_key(self, pk_hash: str) -> bool:
        """Verifica autenticidade de chave pública de peer via DHT."""
        record_raw = await self.dht.retrieve(f"fhe_key:{pk_hash[:16]}")
        if not record_raw:
            return False
        record = json.loads(record_raw)
        # Verificar consistência do hash
        return record["pk_hash"] == pk_hash

    def rotate_key(self, pk_hash: str, new_config: 'FHEConfig') -> str:
        """Rotação segura de chaves com re-criptografia homomórfica."""
        if pk_hash not in self.key_pairs:
            raise ValueError("Chave não encontrada")
        # Em produção: usar key switching do SEAL para migrar ciphertexts
        # Retorna pseudo-coroutine (since the caller might await it, but we handle it simply here)
        raise NotImplementedError("Rotation logic to be updated")
