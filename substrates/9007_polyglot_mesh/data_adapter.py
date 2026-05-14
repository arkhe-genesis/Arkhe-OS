"""
DataLayerAdapter — Conecta ORMs e bancos com integridade ancorada.
Suporta: Prisma, SQLAlchemy, Hibernate, Entity Framework, Mongoose.
Para cada operação de escrita, gera um selo e ancora na TemporalChain.
"""

import hashlib
import json
import time
from typing import Dict, Any

class DataLayerAdapter:
    def __init__(self, orm_client, temporal_chain):
        self.orm = orm_client
        self.temporal = temporal_chain

    async def anchored_create(self, model: str, data: Dict) -> Dict:
        # 1. Inserir no banco
        record = await self.orm[model].create(data)
        # 2. Gerar hash do registro
        record_hash = hashlib.sha3_256(json.dumps(record, sort_keys=True).encode()).hexdigest()
        # 3. Ancorar
        await self.temporal.anchor_event("db_create", {
            "model": model, "hash": record_hash, "timestamp": time.time()
        })
        return record

    # Implementações para Mongoose, Sequelize, etc.
