#!/usr/bin/env python3
"""
merkle_aggregation_debug.py
Investiga comportamento de root_hash constante na cadeia de coerência.
"""
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional

class MerkleAggregationDebugger:
    """
    Diagnostica estratégia de agregação Merkle para identificar causa de root_hash constante.
    """

    def __init__(self, chain_path: str):
        self.chain_path = Path(chain_path)
        if self.chain_path.exists():
            self.chain_data = self._load_chain()
        else:
            self.chain_data = {}

    def _load_chain(self) -> Dict:
        """Carrega dados da cadeia de provas."""
        with open(self.chain_path) as f:
            return json.load(f)

    def analyze_root_hash_behavior(self) -> Dict:
        """
        Analisa padrão de root_hash ao longo da cadeia.

        Returns:
            diagnóstico com possíveis causas e recomendações
        """
        blocks = {k: v for k, v in self.chain_data.items() if k != 'block_0'}

        if not blocks:
            return {'error': 'No blocks found after genesis'}

        # Extrair root_hashes
        root_hashes = [blocks[k].get('root_hash') for k in sorted(blocks.keys()) if 'root_hash' in blocks[k]]
        unique_roots = set(root_hashes)

        analysis = {
            'total_blocks': len(blocks),
            'unique_root_hashes': len(unique_roots),
            'root_hash_pattern': 'constant' if len(unique_roots) <= 1 else 'varying',
            'first_root': root_hashes[0] if root_hashes else None,
            'parent_hash_chain_valid': self._verify_parent_chain(),
            'possible_causes': [],
            'recommendations': []
        }

        if analysis['root_hash_pattern'] == 'constant':
            analysis['possible_causes'] = [
                '1. Fixed-depth Merkle tree with sliding window (depth=8)',
                '2. Root hash computed over static metadata, not block content',
                '3. Aggregation policy: root updates only on full window completion',
                '4. Bug: root_hash not recomputed after new block addition'
            ]

            analysis['recommendations'] = [
                '✓ Implementar root_hash dinâmico: hash(content + previous_root + timestamp)',
                '✓ Expor estratégia de agregação nos metadados do bloco',
                '✓ Adicionar campo "aggregation_window_position" para rastrear progresso',
                '✓ Considerar Merkle Mountain Range (MMR) para crescimento incremental'
            ]

        # Verificar integridade da cadeia de parent_hash
        if not analysis['parent_hash_chain_valid']:
            analysis['possible_causes'].append(
                '5. parent_hash chain broken: blocks not properly linked'
            )
            analysis['recommendations'].append(
                '✓ Validar que cada block_id tem parent_hash = hash do bloco anterior'
            )

        return analysis

    def _verify_parent_chain(self) -> bool:
        """Verifica se parent_hash forma cadeia válida."""
        blocks = {k: v for k, v in self.chain_data.items()
                 if k != 'block_0' and isinstance(k, str) and k.startswith('block_')}

        sorted_blocks = sorted(blocks.items(), key=lambda x: int(x[0].split('_')[1]))

        for i in range(1, len(sorted_blocks)):
            prev_id, prev_data = sorted_blocks[i-1]
            curr_id, curr_data = sorted_blocks[i]

            # Calcular hash esperado do bloco anterior
            prev_content = {k: v for k, v in prev_data.items() if k != 'block_hash'}
            expected_parent = hashlib.sha256(
                json.dumps(prev_content, sort_keys=True).encode()
            ).hexdigest()

            if curr_data.get('parent_hash') != expected_parent:
                print(f"⚠️  Chain break: {curr_id} expects parent {expected_parent[:16]}..., "
                      f"got {curr_data.get('parent_hash', 'N/A')[:16]}...")
                return False

        return True

    def suggest_aggregation_strategy(self) -> str:
        """Sugere estratégia de agregação baseada na análise."""
        analysis = self.analyze_root_hash_behavior()

        if analysis.get('error'):
            return analysis['error']

        if analysis['root_hash_pattern'] == 'constant':
            return """
            🔄 STRATEGY RECOMMENDATION: Dynamic Merkle Root with Incremental Updates

            Current behavior suggests fixed-window aggregation. Recommended approach:

            1. Root Hash Formula:
               root_hash = SHA256(
                 block_content_hash +
                 previous_root_hash +
                 window_position +
                 timestamp_ns
               )

            2. Aggregation Metadata per Block:
               {
                 "aggregation": {
                   "strategy": "incremental_mmr",  // or "sliding_window"
                   "window_size": 8,
                   "position_in_window": 3,  // 0-indexed
                   "root_update_policy": "on_position_0"  // or "every_block"
                 }
               }

            3. Verification:
               - Verifier can recompute root_hash from public block data
               - Chain integrity via parent_hash + root_hash cross-check
            """
        else:
            return "✅ Root hash varies as expected — no aggregation strategy change needed."
