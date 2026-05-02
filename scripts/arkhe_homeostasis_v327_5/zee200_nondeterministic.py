#!/usr/bin/env python3
"""
zee200_nondeterministic.py
Adiciona entropia não-determinística ao processo de geração de provas ZEE200.
"""
import hashlib
import time
import os
from typing import Optional

class NonDeterministicProofSeed:
    """
    Gera sementes de prova com entropia não-determinística para garantir
    que cada prova seja única mesmo para inputs idênticos.
    """

    def __init__(self,
                 entropy_sources: list = None,
                 chain_binding: bool = True):
        """
        Args:
            entropy_sources: lista de fontes de entropia
                - 'time': timestamp de alta resolução
                - 'pid': ID do processo
                - 'memory': hash de região de memória aleatória
                - 'hardware': informações de hardware (se disponível)
            chain_binding: se True, vincula semente ao hash do bloco anterior
        """
        self.entropy_sources = entropy_sources or ['time', 'pid', 'memory']
        self.chain_binding = chain_binding
        self.previous_proof_hash: Optional[str] = None

    def generate_seed(self,
                     proof_content: dict,
                     parent_hash: Optional[str] = None) -> str:
        """
        Gera semente não-determinística para uma prova.

        Args:
            proof_content: conteúdo da prova para hashing
            parent_hash: hash do bloco anterior (para encadeamento)

        Returns:
            seed_hex: semente hexadecimal de 64 caracteres
        """
        entropy_components = []

        # 1. Conteúdo da prova (determinístico)
        content_hash = hashlib.sha256(
            hashlib.md5(str(proof_content).encode()).digest()
        ).hexdigest()
        entropy_components.append(f"content:{content_hash}")

        # 2. Fontes de entropia não-determinística
        if 'time' in self.entropy_sources:
            # Timestamp de alta resolução + jitter do sistema
            t = time.perf_counter_ns()
            entropy_components.append(f"time:{t}:{os.urandom(4).hex()}")

        if 'pid' in self.entropy_sources:
            entropy_components.append(f"pid:{os.getpid()}:{os.urandom(2).hex()}")

        if 'memory' in self.entropy_sources:
            # Hash de buffer aleatório na memória
            mem_sample = os.urandom(16)
            entropy_components.append(f"memory:{hashlib.sha256(mem_sample).hexdigest()[:16]}")

        if 'hardware' in self.entropy_sources:
            # Informações de hardware (se disponível)
            try:
                import platform
                hw_info = f"{platform.node()}:{platform.machine()}"
                entropy_components.append(f"hw:{hashlib.sha256(hw_info.encode()).hexdigest()[:16]}")
            except:
                pass

        # 3. Vinculação à cadeia (se habilitado)
        if self.chain_binding and parent_hash:
            entropy_components.append(f"chain:{parent_hash}")
        elif self.chain_binding and self.previous_proof_hash:
            entropy_components.append(f"chain:{self.previous_proof_hash}")

        # 4. Combinar e hash final
        combined = "|".join(entropy_components)
        seed = hashlib.sha256(combined.encode()).hexdigest()

        # Atualizar hash anterior para próximo bloco
        self.previous_proof_hash = seed

        return seed

    def inject_into_proof(self,
                         proof: dict,
                         parent_hash: Optional[str] = None) -> dict:
        """
        Injeta semente não-determinística nos metadados da prova.

        Args:
            proof: dicionário de prova gerado pelo ZEE200
            parent_hash: hash do bloco anterior

        Returns:
            proof_com enriched: prova com metadados de entropia
        """
        seed = self.generate_seed(proof, parent_hash)

        proof['entropy_metadata'] = {
            'seed': seed,
            'timestamp_ns': time.perf_counter_ns(),
            'entropy_sources': self.entropy_sources,
            'chain_bound': self.chain_binding,
            'previous_hash': parent_hash or self.previous_proof_hash
        }

        # Recalcular proof_hash incluindo entropia
        proof['proof_hash'] = hashlib.sha256(
            str(proof).encode()
        ).hexdigest()[:16]

        return proof
