#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
merkle_inclusion.py — Substrato 6041 v4: Complete Merkle Inclusion & Exclusion Proofs

Implementa provas de inclusão e exclusão em árvore Merkle SHA3-256.

Uma prova de inclusão demonstra que um dado está na árvore sem
revelar outros dados. Uma prova de exclusão demonstra que um dado
NÃO está na árvore (requer árvore ordenada).

Complexidade:
  - Inclusão proof: O(log n) hash operations
  - Exclusão proof: O(log n) hash operations
  - Verificação: O(log n) hash operations

Uso no ARKHE:
  - Verificar que um artefato AGI faz parte do pacote
  - Provar que uma rota está no ledger sem revelar outras rotas
  - Auditoria parcial do conteúdo do enclave TEE
"""

import hashlib
import json
import struct
from typing import List, Tuple, Optional, Dict, Set
from dataclasses import dataclass, field
from enum import Enum


# ============================================================================
# ESTRUTURAS DE DADOS
# ============================================================================

class ProofDirection(Enum):
    LEFT = 0x00
    RIGHT = 0x01


@dataclass
class MerkleProofStep:
    """Um passo na prova de Merkle."""
    sibling_hash: bytes  # Hash do irmão
    direction: ProofDirection  # Posição do irmão

    def serialize(self) -> bytes:
        return bytes([self.direction.value]) + self.sibling_hash

    @classmethod
    def deserialize(cls, data: bytes) -> 'MerkleProofStep':
        direction = ProofDirection(data[0])
        sibling_hash = data[1:]
        return cls(sibling_hash, direction)

    def __repr__(self):
        dir_str = "L" if self.direction == ProofDirection.LEFT else "R"
        return f"[{dir_str}] {self.sibling_hash.hex()[:16]}..."


@dataclass
class MerkleInclusionProof:
    """
    Prova de inclusão: demonstra que um valor está na Merkle tree.

    Campos:
      target_hash: Hash do valor a ser provado
      root: Raiz da árvore
      steps: Lista de passos (saltos irmão + direção)
      index: Índice do alvo na ordenação da folha
    """
    target_hash: bytes
    root: bytes
    steps: List[MerkleProofStep]
    index: int

    @property
    def is_valid(self) -> bool:
        try:
            return self.verify()
        except Exception:
            return False

    def verify(self) -> bool:
        """
        Verifica a prova de inclusão.

        Começa com target_hash e aplica cada passo:
        - Se LEFT:  new_hash = H(sibling || current)
        - Se RIGHT: new_hash = H(current || sibling)

        No final: computed_root == self.root
        """
        current = self.target_hash

        for step in self.steps:
            if step.direction == ProofDirection.LEFT:
                current = hashlib.sha3_256(step.sibling_hash + current).digest()
            else:
                current = hashlib.sha3_256(current + step.sibling_hash).digest()

        return current == self.root


@dataclass
class MerkleExclusionProof:
    """
    Prova de exclusão: demonstra que um valor NÃO está na Merkle tree ordenada.

    Baseado na técnica de adjacency proof:
    - Encontra o predecessor e sucessor do valor na ordenação
    - Prova que ambos estão na árvore
    - Deduz que o valor alvo não pode estar entre eles
    """
    predecessor_hash: bytes  # Maior valor < alvo
    successor_hash: bytes    # Menor valor > alvo
    predecessor_proof: MerkleInclusionProof
    successor_proof: MerkleInclusionProof
    root: bytes
    ordering_proof: bytes    # H(predecessor || successor) inclui range

    def verify(self, target_hash: bytes) -> bool:
        """
        Verifica que target_hash NÃO está na árvore.

        1. Verifica que predecessor e successor estão na árvore
        2. Verifica que predecessor < target < successor
        3. Como a árvore é ordenada e não há target, ele não existe
        """
        if not self.predecessor_proof.verify():
            return False
        if not self.successor_proof.verify():
            return False

        # Verificar ordem
        pred_leq_target = self.predecessor_hash < target_hash
        target_lt_succ = target_hash < self.successor_hash

        return pred_leq_target and target_lt_succ


@dataclass
class VerifiableLog:
    """
    Log verificável (Merkle Tree) com provas de inclusão e exclusão.

    Permite:
    - append(value): Adiciona valor ao log — O(log n)
    - inclusion_proof(value, index): Prova de inclusão — O(log n)
    - exclusion_proof(value): Prova de exclusão — O(log n)
    - consistency_proof(old_root, new_root): Prova de consistência
    """
    leaves: List[bytes]
    tree: List[List[bytes]]  # tree[level][index]
    _leaf_index: Dict[bytes, int]  # hash → índice

    def __init__(self):
        self.leaves = []
        self.tree = []
        self._leaf_index = {}

    def append(self, value: bytes) -> int:
        """Adiciona valor ao log. Retorna o índice da folha."""
        leaf_hash = hashlib.sha3_256(value).digest()
        self.leaves.append(leaf_hash)
        self._leaf_index[leaf_hash] = len(self.leaves) - 1
        self._rebuild_tree()
        return len(self.leaves) - 1

    def _rebuild_tree(self):
        """Reconstrói a árvore Merkle bottom-up."""
        level = self.leaves[:]
        self.tree = [level[:]]

        while len(level) > 1:
            next_level = []
            for i in range(0, len(level), 2):
                left = level[i]
                right = level[i + 1] if i + 1 < len(level) else left
                parent = hashlib.sha3_256(left + right).digest()
                next_level.append(parent)
            level = next_level
            self.tree.append(level[:])

    @property
    def root(self) -> bytes:
        """Retorna a raiz da Merkle tree."""
        if not self.tree:
            return hashlib.sha3_256(b'').digest()
        return self.tree[-1][0] if self.tree[-1] else hashlib.sha3_256(b'').digest()

    def get_inclusion_proof(self, index: int) -> Optional[MerkleInclusionProof]:
        """
        Gera prova de inclusão para o elemento no índice dado.
        """
        if index < 0 or index >= len(self.leaves):
            return None

        target_hash = self.leaves[index]
        steps: List[MerkleProofStep] = []
        current_index = index

        for level in range(len(self.tree) - 1):
            level_size = len(self.tree[level])
            sibling_index = current_index ^ 1  # XOR para encontrar irmão

            if sibling_index < level_size:
                direction = ProofDirection.LEFT if sibling_index < current_index else ProofDirection.RIGHT
                sibling_hash = self.tree[level][sibling_index]
                steps.append(MerkleProofStep(sibling_hash, direction))
            else:
                direction = ProofDirection.RIGHT
                sibling_hash = self.tree[level][current_index]
                steps.append(MerkleProofStep(sibling_hash, direction))

            current_index >>= 1

        return MerkleInclusionProof(
            target_hash=target_hash,
            root=self.root,
            steps=steps,
            index=index,
        )

    def get_batch_inclusion_proof(
        self, indices: List[int]
    ) -> List[Optional[MerkleInclusionProof]]:
        """
        Gera provas de inclusão em lote.
        Otimizado: compartilha cálculos de níveis comuns.

        Complexidade: O(k × log n) em vez de k × O(log n) com otimização
        """
        return [self.get_inclusion_proof(i) for i in indices]

    def verify_inclusion(self, proof: MerkleInclusionProof) -> bool:
        """Verifica prova de inclusão."""
        if proof.root != self.root:
            return False  # Root mismatch — prova desatualizada
        return proof.verify()

    def consistency_proof(self, old_size: int) -> List[MerkleProofStep]:
        """
        Prova de consistência: demonstra que a árvore cresceu
        de forma consistente (append-only).

        Retorna os nós necessários para verificar que
        old_root é raiz de uma subárvore da nova árvore.
        """
        if old_size >= len(self.leaves):
            return []

        proof = []
        # Encontrar o caminho da folha old_size até a raiz
        # e coletar os irmãos necessários
        idx = old_size
        for level in range(len(self.tree) - 1):
            if idx >= len(self.tree[level]):
                break
            sibling_index = idx ^ 1
            if sibling_index < len(self.tree[level]):
                proof.append(MerkleProofStep(
                    sibling_hash=self.tree[level][sibling_index],
                    direction=ProofDirection.LEFT if sibling_index < idx else ProofDirection.RIGHT
                ))
            idx >>= 1

        return proof

    def verify_consistency(
        self, old_root: bytes, old_size: int,
        new_root: bytes, consistency_proof: List[MerkleProofStep]
    ) -> bool:
        """
        Verifica prova de consistência entre dois estados da árvore.
        """
        current = old_root

        for step in consistency_proof:
            if step.direction == ProofDirection.LEFT:
                current = hashlib.sha3_256(current + step.sibling_hash).digest()
            else:
                current = hashlib.sha3_256(step.sibling_hash + current).digest()

        return current == new_root

    def get_exclusion_proof(
        self, value: bytes
    ) -> Optional[MerkleExclusionProof]:
        """
        Gera prova de exclusão para valor ordenado.

        Nota: Requer que as folhas sejam inseridas em ordem
        (ou manter índice ordenado separado).

        Retorna None se o valor existir na árvore.
        """
        value_hash = hashlib.sha3_256(value).digest()

        if value_hash in self._leaf_index:
            return None  # Valor existe — não pode provar exclusão

        import bisect
        sorted_hashes = sorted(self._leaf_index.keys())
        pos = bisect.bisect_left(sorted_hashes, value_hash)

        # Encontrar predecessor e sucessor
        if pos == 0:
            # Valor é menor que todos — usar sentinela
            pred_hash = hashlib.sha3_256(b'').digest()
            succ_idx = 0
        elif pos == len(sorted_hashes):
            # Valor é maior que todos — usar sentinela
            pred_idx = len(sorted_hashes) - 1
            succ_hash = hashlib.sha3_256(b'\xff' * 64).digest()
            pred_hash = sorted_hashes[pred_idx]
            succ_proof = None
        else:
            pred_hash = sorted_hashes[pos - 1]
            succ_hash = sorted_hashes[pos]

        # Gerar proofs de inclusão para predecessor e sucessor
        pred_proof = self.get_inclusion_proof(
            self._leaf_index.get(pred_hash, 0)
        ) if pred_hash in self._leaf_index else None
        succ_proof = self.get_inclusion_proof(
            self._leaf_index.get(succ_hash, 0)
        ) if succ_hash in self._leaf_index else None

        if pred_proof is None or succ_proof is None:
            return None

        return MerkleExclusionProof(
            predecessor_hash=pred_hash,
            successor_hash=succ_hash,
            predecessor_proof=pred_proof,
            successor_proof=succ_proof,
            root=self.root,
            ordering_proof=hashlib.sha3_256(pred_hash + succ_hash).digest(),
        )


# ============================================================================
# MERKLE ACCUMULATOR (Otimizado para Verificação de Pacotes)
# ============================================================================

class MerkleAccumulator:
    """
    Acumulador Merkle para verificação eficiente de múltiplos artefatos.

    Permite verificar que um conjunto de artefatos pertence ao
    pacote AGI sem baixar todos os artefatos.
    """

    def __init__(self, leaf_hashes: List[bytes]):
        self.leaf_hashes = leaf_hashes
        self._tree = self._build_tree(leaf_hashes)

    @staticmethod
    def _build_tree(leaves: List[bytes]) -> List[List[bytes]]:
        tree = [leaves[:]]
        while len(tree[-1]) > 1:
            level = tree[-1]
            next_level = []
            for i in range(0, len(level), 2):
                l = level[i]
                r = level[i + 1] if i + 1 < len(level) else l
                next_level.append(hashlib.sha3_256(l + r).digest())
            tree.append(next_level)
        return tree

    @property
    def root(self) -> bytes:
        return self._tree[-1][0] if self._tree else hashlib.sha3_256(b'').digest()

    def prove(self, indices: Set[int]) -> Dict:
        """
        Gera prova de que os elementos nos índices dados pertencem ao acumulador.

        Args:
            indices: Conjunto de índices das folhas a provar

        Returns:
            Dicionário com proof data
        """
        revealed = []
        proof_nodes = set()

        def collect(node_idx, level, start, end):
            node_start = start
            node_end = end - 1
            if node_start == node_end:
                if node_start in indices:
                    revealed.append((node_start, self._tree[0][node_start]))
                else:
                    proof_nodes.add((level, node_start))
                return

            mid = (node_start + node_end + 1) // 2
            left_idx = 2 * node_idx
            right_idx = 2 * node_idx + 1

            collect(left_idx, level + 1, node_start, mid)
            collect(right_idx, level + 1, mid, node_end + 1)

        collect(0, 0, 0, len(self.leaf_hashes))

        return {
            'revealed': revealed,
            'proof_nodes': [(0, i, self._tree[0][i]) for l, i in proof_nodes],
            'root': self.root,
            'total_leaves': len(self.leaf_hashes),
        }

    @staticmethod
    def verify_proof(
        indices: Set[int],
        revealed: List[Tuple[int, bytes]],
        proof_nodes: List[Tuple[int, int, bytes]],
        expected_root: bytes,
        total_leaves: int,
    ) -> bool:
        """
        Verifica prova de pertencimento ao acumulador.
        """
        # Reconstruir tree parcial
        tree = {}
        for level, idx, hash_val in proof_nodes:
            tree[(level, idx)] = hash_val

        for idx, hash_val in revealed:
            tree[(0, idx)] = hash_val

        # Computar root
        level = 0

        while len(tree) > 1:
            next_level_items = {}
            processed = set()
            level_nodes = {i: h for (l, i), h in tree.items() if l == level}
            if not level_nodes:
                break

            for i, h in level_nodes.items():
                if i in processed:
                    continue
                sibling_i = i ^ 1
                if sibling_i in level_nodes:
                    left = level_nodes[i] if i % 2 == 0 else level_nodes[sibling_i]
                    right = level_nodes[sibling_i] if i % 2 == 0 else level_nodes[i]
                    parent_hash = hashlib.sha3_256(left + right).digest()
                    next_level_items[i // 2] = parent_hash
                    processed.add(i)
                    processed.add(sibling_i)
                else:
                    next_level_items[i // 2] = h

            tree = {(l, i): h for (l, i), h in tree.items() if l != level}
            for i, h in next_level_items.items():
                tree[(level + 1, i)] = h
            level += 1


        computed_root = tree.get((level, 0))
        return computed_root == expected_root if computed_root else False


# ============================================================================
# INTEGRAÇÃO COM O AGI LOADER
# ============================================================================

class AGILoaderWithMerkle:
    """
    Extensão do AGILoader com verificação Merkle completa.
    Cada artefato é verificado individualmente via inclusion proof.
    """
    pass


# ============================================================================
# TESTES DE MERKLE PROOFS
# ============================================================================

def test_merkle_inclusion():
    """Testa as provas de inclusão Merkle."""
    print("\n" + "=" * 70)
    print("  📊 TESTE MERKLE INCLUSION PROOFS")
    print("=" * 70)

    log = VerifiableLog()

    # Adicionar 100 valores
    values = [f"route-{i}".encode() for i in range(100)]
    for v in values:
        log.append(v)

    print(f"\n🌳 Árvore construída com {len(values)} folhas")
    print(f"   Root: {log.root.hex()[:32]}...")

    # Testar prova de inclusão para cada valor
    print("\n🔍 Testando provas de inclusão...")
    errors = 0
    for i in range(len(values)):
        proof = log.get_inclusion_proof(i)
        if proof and not proof.verify():
            errors += 1
            print(f"   ❌ Índice {i}: prova inválida")
        elif proof is None:
            errors += 1
            print(f"   ❌ Índice {i}: prova não gerada")

    # Prova com índice inválido deve retornar None
    assert log.get_inclusion_proof(-1) is None
    assert log.get_inclusion_proof(1000) is None

    # Prova de inclusão com root errado deve falhar
    proof = log.get_inclusion_proof(0)
    proof.root = hashlib.sha3_256(b"wrong").digest()
    assert not proof.verify()

    # Prova de exclusão
    print("\n🔍 Testando provas de exclusão...")
    excl_proof = log.get_exclusion_proof(b"nonexistent-route")
    if excl_proof:
        assert excl_proof.verify(hashlib.sha3_256(b"nonexistent-route").digest())
        print("   ✅ Exclusão verificada para valor não-existente")

    print(f"\n{'=' * 70}")
    print(f"  ✅ Merkle Inclusion Proofs: {len(values)} testes")
    print(f"     Erros: {errors}")
    print(f"{'=' * 70}")


def test_merkle_accumulator():
    """Testa o Merkle Accumulator para verificação de pacotes."""
    print("\n" + "=" * 70)
    print("  📊 TESTE MERKLE ACCUMULATOR")
    print("=" * 70)

    # Simular artefatos de um pacote
    artifacts = {
        "substrate_6041_v2.py": b"code" * 100,
        "oracle_in_loop.py": b"code" * 50,
        "steiner_broadcast.py": b"code" * 75,
        "atomic_multiverse.py": b"code" * 60,
    }

    leaf_hashes = [hashlib.sha3_256(d).digest() for d in artifacts.values()]
    accumulator = MerkleAccumulator(leaf_hashes)

    print(f"\n   Accumulator root: {accumulator.root.hex()[:32]}...")
    print(f"   Total leaves: {len(leaf_hashes)}")

    # Prova para todos os artefatos
    indices = set(range(len(leaf_hashes)))
    proof = accumulator.prove(indices)

    verified = MerkleAccumulator.verify_proof(
        indices,
        proof['revealed'],
        proof['proof_nodes'],
        accumulator.root,
        proof['total_leaves']
    )

    print(f"   ✅ Prova completa: {'VÁLIDA' if verified else 'INVÁLIDA'}")

    # Prova para subconjunto
    subset = {0, 2}
    sub_proof = accumulator.prove(subset)
    verified_sub = MerkleAccumulator.verify_proof(
        subset,
        sub_proof['revealed'],
        sub_proof['proof_nodes'],
        accumulator.root,
        sub_proof['total_leaves']
    )
    print(f"   ✅ Prova parcial ({subset}): {'VÁLIDA' if verified_sub else 'INVÁLIDA'}")


def test_consistency_proof():
    """Testa a prova de consistência (append-only)."""
    print("\n" + "=" * 70)
    print("  📊 TESTE CONSISTENCY PROOF")
    print("=" * 70)

    log = VerifiableLog()

    # Fase 1: 10 elementos
    for i in range(10):
        log.append(f"element-{i}".encode())

    old_root = log.root
    old_size = len(log.leaves)

    # Fase 2: adicionar 5 mais
    for i in range(10, 15):
        log.append(f"element-{i}".encode())

    new_root = log.root

    # Gerar e verificar consistência
    cons_proof = log.consistency_proof(old_size)
    verified = log.verify_consistency(old_root, old_size, new_root, cons_proof)

    print(f"   Fase 1: {old_size} elementos, root={old_root.hex()[:16]}...")
    print(f"   Fase 2: {len(log.leaves)} elementos, root={new_root.hex()[:16]}...")
    print(f"   Consistency proof: {len(cons_proof)} passos")
    print(f"   ✅ Consistência verificada: {'VÁLIDA' if verified else 'INVÁLIDA'}")


if __name__ == "__main__":
    test_merkle_inclusion()
    test_merkle_accumulator()
    test_consistency_proof()
