#!/usr/bin/env python3
"""
_key_rotation.py — Rotação automática de chaves de integridade para o ARKHE OS.
Gerencia ciclo de vida das chaves, geração, armazenamento e verificação.
"""

import os
import json
import time
import struct
import secrets
import hashlib
import hmac
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict

# ============================================================================
# Estruturas de Dados
# ============================================================================

@dataclass
class IntegrityKey:
    """Uma chave de integridade com metadados de ciclo de vida."""
    key_id: str               # Identificador único (ex: "20260505_120000")
    key_hex: str              # Chave secreta em hexadecimal
    valid_from: float         # Timestamp Unix de quando se torna ativa
    valid_until: Optional[float] = None  # Timestamp de expiração (None = sem expiração)
    is_active: bool = True    # Se a chave está ativa para assinatura
    created_by: str = "auto"  # Identificador de quem criou a chave
    comment: str = ""         # Comentário opcional

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'IntegrityKey':
        return cls(**data)

    def is_valid_at(self, timestamp: float = None) -> bool:
        """Verifica se a chave é válida em um dado timestamp."""
        if timestamp is None:
            timestamp = time.time()
        if not self.is_active:
            return False
        if timestamp < self.valid_from:
            return False
        if self.valid_until is not None and timestamp > self.valid_until:
            return False
        return True

    def compute_signature(self, content_hash: str) -> str:
        """Computa assinatura HMAC-SHA256 usando esta chave."""
        from ._integrity import ARKHE_MAGIC  # Import local para evitar circular
        payload = ARKHE_MAGIC + content_hash.encode('ascii')
        key_bytes = bytes.fromhex(self.key_hex)
        return hmac.new(key_bytes, payload, 'sha256').hexdigest()


# ============================================================================
# Gerenciador de Chaves
# ============================================================================

class KeyManager:
    """
    Gerencia o ciclo de vida das chaves de integridade.
    Armazena chaves em arquivo JSON com permissões restritas.
    """

    def __init__(self, storage_path: Optional[Path] = None):
        if storage_path is None:
            storage_path = Path(__file__).parent / "_integrity_keys.json"
        self.storage_path = storage_path
        self.keys: Dict[str, IntegrityKey] = {}
        self._load_keys()

    def _load_keys(self):
        """Carrega chaves do arquivo de armazenamento."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                self.keys = {
                    k: IntegrityKey.from_dict(v)
                    for k, v in data.get('keys', {}).items()
                }
            except (json.JSONDecodeError, KeyError):
                # Arquivo corrompido ou formato antigo — iniciar vazio
                self.keys = {}
        else:
            self.keys = {}

    def _save_keys(self):
        """Salva chaves no arquivo de armazenamento com permissões restritas."""
        data = {
            'version': 1,
            'keys': {k: v.to_dict() for k, v in self.keys.items()},
            'last_modified': time.time(),
        }
        # Escrever atomicamente
        tmp_path = self.storage_path.with_suffix('.tmp')
        with open(tmp_path, 'w') as f:
            json.dump(data, f, indent=2)
        os.replace(tmp_path, self.storage_path)
        # Restringir permissões no Unix
        if os.name == 'posix':
            os.chmod(self.storage_path, 0o600)

    def generate_key(
        self,
        valid_from: Optional[float] = None,
        valid_until: Optional[float] = None,
        comment: str = "",
        created_by: str = "auto"
    ) -> IntegrityKey:
        """
        Gera uma nova chave de integridade.

        Args:
            valid_from: timestamp de início de validade (None = agora)
            valid_until: timestamp de expiração (None = sem expiração)
            comment: comentário descritivo
            created_by: identificador do criador

        Returns:
            IntegrityKey gerada e armazenada
        """
        if valid_from is None:
            valid_from = time.time()

        # Gerar chave aleatória de 32 bytes (256 bits)
        key_bytes = secrets.token_bytes(32)
        key_hex = key_bytes.hex()

        # Criar identificador único baseado no timestamp
        from datetime import datetime
        key_id = datetime.fromtimestamp(valid_from).strftime("%Y%m%d_%H%M%S_") + secrets.token_hex(4)

        key = IntegrityKey(
            key_id=key_id,
            key_hex=key_hex,
            valid_from=valid_from,
            valid_until=valid_until,
            is_active=True,
            created_by=created_by,
            comment=comment
        )

        self.keys[key_id] = key
        self._save_keys()
        return key

    def deactivate_key(self, key_id: str) -> bool:
        """Desativa uma chave (não a remove, apenas marca como inativa)."""
        if key_id in self.keys:
            self.keys[key_id].is_active = False
            self._save_keys()
            return True
        return False

    def get_active_keys(self, timestamp: float = None) -> List[IntegrityKey]:
        """Retorna todas as chaves ativas e válidas no timestamp dado."""
        if timestamp is None:
            timestamp = time.time()
        return [k for k in self.keys.values() if k.is_valid_at(timestamp)]

    def get_signing_key(self) -> Optional[IntegrityKey]:
        """Retorna a chave mais recente para assinar novos selos."""
        active = self.get_active_keys()
        if not active:
            return None
        # Retornar a chave com valid_from mais recente
        return max(active, key=lambda k: k.valid_from)

    def verify_signature(
        self,
        content_hash: str,
        signature: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Verifica uma assinatura contra todas as chaves ativas.
        Retorna (True, key_id) se alguma chave válida assinou,
        ou (False, None) se nenhuma chave corresponde.
        """
        valid_keys = self.get_active_keys()
        for key in valid_keys:
            expected_sig = key.compute_signature(content_hash)
            if hmac.compare_digest(signature, expected_sig):
                return True, key.key_id
        return False, None

    def rotate_key(
        self,
        transition_period_seconds: float = 3600.0,  # 1 hora de transição
        comment: str = "Rotação automática programada"
    ) -> Tuple[IntegrityKey, IntegrityKey]:
        """
        Executa uma rotação completa de chave:
        1. Gera uma nova chave com valid_from = agora
        2. Define valid_until da chave anterior para agora + transition_period

        Returns:
            (nova_chave, chave_anterior)
        """
        now = time.time()
        old_key = self.get_signing_key()

        # Definir expiração da chave anterior (período de transição)
        if old_key is not None and old_key.valid_until is None:
            old_key.valid_until = now + transition_period_seconds
            # Não desativar ainda — continua ativa durante transição

        # Gerar nova chave
        new_key = self.generate_key(
            valid_from=now,
            comment=comment,
            created_by="rotation_script"
        )

        # Persistir alterações
        self._save_keys()

        return new_key, old_key

    def list_keys(self) -> List[dict]:
        """Lista todas as chaves com informações de status."""
        now = time.time()
        result = []
        for key in sorted(self.keys.values(), key=lambda k: k.valid_from, reverse=True):
            result.append({
                'key_id': key.key_id,
                'valid_from': key.valid_from,
                'valid_until': key.valid_until,
                'is_active': key.is_active,
                'is_valid_now': key.is_valid_at(now),
                'created_by': key.created_by,
                'comment': key.comment,
                'is_current_signing_key': key == self.get_signing_key(),
            })
        return result

    def get_rotation_status(self) -> dict:
        """Retorna status completo da rotação de chaves."""
        signing_key = self.get_signing_key()
        return {
            'total_keys': len(self.keys),
            'active_keys': len(self.get_active_keys()),
            'current_signing_key_id': signing_key.key_id if signing_key else None,
            'keys': self.list_keys(),
            'storage_path': str(self.storage_path),
        }


# ============================================================================
# Singleton para acesso global (inicializado sob demanda)
# ============================================================================

_key_manager_instance: Optional[KeyManager] = None

def get_key_manager() -> KeyManager:
    """Retorna a instância singleton do KeyManager."""
    global _key_manager_instance
    if _key_manager_instance is None:
        _key_manager_instance = KeyManager()
    return _key_manager_instance
