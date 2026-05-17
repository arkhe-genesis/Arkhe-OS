#!/usr/bin/env python3
"""
ARKHE OS Substrato 241: Semantic Chemistry Engine
Canon: INF.OMEGA.NABLA.SEMANTIC_CHEMISTRY.241

Reator de Semantic Chemistry — Algoritmic Chemistry on Semantic Graphs.
Moléculas semânticas colidem, reagem e produzem novos compostos criativos.
"""

import random
import hashlib
import json
import time
import logging
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='\033[0;35m%(asctime)s\033[0m | %(levelname)-8s | %(message)s'
)
logger = logging.getLogger(__name__)

def sha3_256_hex(data: bytes) -> str:
    return hashlib.sha3_256(data).hexdigest()


# =============================================================================
# SEMANTIC ATOM — Unidade mínima de significado
# =============================================================================

@dataclass
class SemanticAtom:
    """Um átomo semântico — a menor unidade de significado."""
    concept: str
    charge: float = 0.0  # polaridade semântica (-1 a +1)
    phi_c: float = 0.9   # coerência mínima para existência
    source_substrate: str = "241"  # origem no ecossistema

    def canonical_hash(self) -> str:
        return sha3_256_hex(f"{self.concept}:{self.charge}:{self.phi_c}".encode())[:16]


# =============================================================================
# SEMANTIC BOND — Ligação entre átomos
# =============================================================================

@dataclass
class SemanticBond:
    """Ligação entre átomos em uma molécula."""
    atom_a: int
    atom_b: int
    relation: str
    strength: float = 1.0
    bond_type: str = "covalent"  # covalent, ionic, hydrogen, metallic


# =============================================================================
# SEMANTIC MOLECULE — Combinação de átomos ligados
# =============================================================================

@dataclass
class SemanticMolecule:
    """Molécula — uma combinação de átomos ligados semanticamente."""
    atoms: List[SemanticAtom]
    bonds: List[SemanticBond]
    stability: float = 0.5
    creation_timestamp: float = field(default_factory=time.time)
    generation: int = 0
    parent_hashes: List[str] = field(default_factory=list)

    def canonical_hash(self) -> str:
        h = hashlib.sha3_256()
        for a in sorted(self.atoms, key=lambda x: x.concept):
            h.update(a.canonical_hash().encode())
        for b in sorted(self.bonds, key=lambda x: f"{x.atom_a}{x.relation}{x.atom_b}"):
            h.update(f"{b.atom_a}:{b.relation}:{b.atom_b}:{b.strength}".encode())
        return h.hexdigest()

    def to_dict(self) -> dict:
        return {
            "atoms": [{"concept": a.concept, "charge": a.charge, "phi_c": a.phi_c} for a in self.atoms],
            "bonds": [{"a": b.atom_a, "b": b.atom_b, "relation": b.relation, "strength": b.strength} for b in self.bonds],
            "stability": self.stability,
            "hash": self.canonical_hash()[:16],
            "generation": self.generation,
        }


# =============================================================================
# REACTION RECORD — Registro de reação na TemporalChain
# =============================================================================

@dataclass
class ReactionRecord:
    reaction_id: str
    timestamp: float
    reactant_hashes: List[str]
    product_hashes: List[str]
    rule_name: str
    catalyst_phi_c: float
    stability_before: float
    stability_after: float
    temporal_seal: Optional[str] = None


# =============================================================================
# TEMPORAL CHAIN ANCHOR (lightweight for Substrate 241)
# =============================================================================

class TemporalChainAnchor:
    CHAIN_FILE = Path("/tmp/semantic_chemistry_chain.json")

    def __init__(self):
        if not self.CHAIN_FILE.exists():
            self.CHAIN_FILE.write_text("[]")

    def anchor(self, record: ReactionRecord) -> str:
        chain = json.loads(self.CHAIN_FILE.read_text())
        prev_hash = chain[-1]["hash"] if chain else "0" * 64
        payload = json.dumps(asdict(record), sort_keys=True)
        block = {
            "index": len(chain),
            "timestamp": time.time(),
            "record": asdict(record),
            "prev_hash": prev_hash,
            "hash": sha3_256_hex(f"{prev_hash}{payload}{time.time()}".encode())
        }
        chain.append(block)
        self.CHAIN_FILE.write_text(json.dumps(chain, indent=2))
        logger.info(f"[TemporalChain] Reação ancorada: {block['hash'][:16]}...")
        return block["hash"]

    def verify_chain(self) -> bool:
        chain = json.loads(self.CHAIN_FILE.read_text())
        for i in range(1, len(chain)):
            if chain[i]["prev_hash"] != chain[i-1]["hash"]:
                return False
        return True

    def get_stats(self) -> dict:
        chain = json.loads(self.CHAIN_FILE.read_text())
        return {
            "total_blocks": len(chain),
            "first_timestamp": chain[0]["timestamp"] if chain else None,
            "last_timestamp": chain[-1]["timestamp"] if chain else None,
        }


# =============================================================================
# SEMANTIC CHEMISTRY ENGINE — O reator
# =============================================================================

class SemanticChemistryEngine:
    """
    Reator de Semantic Chemistry.
    Mantém um "caldo" de moléculas e aplica regras de reação para gerar novas.
    """

    REACTION_RULES = [
        "combination",      # síntese: A + B → AB
        "decomposition",    # análise: AB → A + B
        "substitution",     # substituição: A + BC → AC + B
        "catalysis",        # catálise Φ_C: A + Φ_C → A* + Φ_C
        "redox",            # transferência de carga semântica
        "polymerization",   # cadeia longa: A + B + C → ABC
    ]

    def __init__(self, phi_c_threshold: float = 0.7):
        self.temporal = TemporalChainAnchor()
        self.phi_c_threshold = phi_c_threshold
        self.molecules: List[SemanticMolecule] = []
        self.reaction_count = 0
        self.stable_molecules: List[SemanticMolecule] = []
        self._rule_map = {
            "combination": self._reaction_combination,
            "decomposition": self._reaction_decomposition,
            "substitution": self._reaction_substitution,
            "catalysis": self._reaction_catalysis,
            "redox": self._reaction_redox,
            "polymerization": self._reaction_polymerization,
        }

    def add_molecule(self, molecule: SemanticMolecule):
        """Adiciona uma molécula ao caldo reacional."""
        self.molecules.append(molecule)
        logger.info(f"[Reactor] Molécula adicionada: {molecule.canonical_hash()[:16]}... (stability={molecule.stability:.3f})")

    def react(self, steps: int = 1) -> List[SemanticMolecule]:
        """Executa reações químicas entre moléculas."""
        new_molecules = []
        for step in range(steps):
            if len(self.molecules) < 2:
                logger.warning("[Reactor] Caldo insuficiente para reação")
                break

            m1, m2 = random.sample(self.molecules, 2)
            rule_name = random.choice(self.REACTION_RULES)
            rule_fn = self._rule_map[rule_name]

            products = rule_fn(m1, m2)

            for p in products:
                p.stability = self._compute_stability(p)
                p.generation = max(m1.generation, m2.generation) + 1
                p.parent_hashes = [m1.canonical_hash()[:16], m2.canonical_hash()[:16]]

                if p.stability >= self.phi_c_threshold:
                    new_molecules.append(p)
                    self.molecules.append(p)
                    self.stable_molecules.append(p)

                    # Ancorar na TemporalChain
                    record = ReactionRecord(
                        reaction_id=sha3_256_hex(f"{rule_name}:{time.time()}".encode())[:12],
                        timestamp=time.time(),
                        reactant_hashes=[m1.canonical_hash()[:16], m2.canonical_hash()[:16]],
                        product_hashes=[p.canonical_hash()[:16]],
                        rule_name=rule_name,
                        catalyst_phi_c=self.phi_c_threshold,
                        stability_before=min(m1.stability, m2.stability),
                        stability_after=p.stability,
                    )
                    seal = self.temporal.anchor(record)
                    record.temporal_seal = seal

                    logger.info(f"[Reactor] Reação {rule_name}: {m1.canonical_hash()[:8]} + {m2.canonical_hash()[:8]} → {p.canonical_hash()[:8]} (stability={p.stability:.3f})")
                else:
                    logger.info(f"[Reactor] Produto instável descartado: stability={p.stability:.3f} < threshold={self.phi_c_threshold}")

            self.reaction_count += 1

        return new_molecules

    def _reaction_combination(self, m1: SemanticMolecule, m2: SemanticMolecule) -> List[SemanticMolecule]:
        """Síntese: combina duas moléculas em uma maior."""
        new_atoms = m1.atoms + m2.atoms
        offset = len(m1.atoms)
        new_bonds = m1.bonds + m2.bonds.copy()

        # Criar nova ligação entre átomos aleatórios
        if m1.atoms and m2.atoms:
            a = random.randint(0, len(m1.atoms) - 1)
            b = random.randint(0, len(m2.atoms) - 1) + offset
            new_bond = SemanticBond(
                a, b, "synthesized",
                strength=random.uniform(0.5, 1.0),
                bond_type="covalent"
            )
            new_bonds.append(new_bond)

        return [SemanticMolecule(atoms=new_atoms, bonds=new_bonds)]

    def _reaction_decomposition(self, m1: SemanticMolecule, m2: SemanticMolecule) -> List[SemanticMolecule]:
        """Análise: quebra a maior molécula em duas menores."""
        target = m1 if len(m1.atoms) >= len(m2.atoms) else m2
        if len(target.atoms) >= 3:
            split = len(target.atoms) // 2
            left = SemanticMolecule(
                atoms=target.atoms[:split],
                bonds=[b for b in target.bonds if b.atom_a < split and b.atom_b < split]
            )
            right = SemanticMolecule(
                atoms=target.atoms[split:],
                bonds=[b for b in target.bonds if b.atom_a >= split and b.atom_b >= split]
            )
            return [left, right]
        return []

    def _reaction_substitution(self, m1: SemanticMolecule, m2: SemanticMolecule) -> List[SemanticMolecule]:
        """Substituição: troca um átomo de m1 por um de m2."""
        if m1.atoms and m2.atoms:
            idx = random.randint(0, len(m1.atoms) - 1)
            new_atom = random.choice(m2.atoms)
            new_atoms = m1.atoms.copy()
            new_atoms[idx] = SemanticAtom(
                concept=f"{new_atoms[idx].concept}→{new_atom.concept}",
                charge=(new_atoms[idx].charge + new_atom.charge) / 2,
                phi_c=min(new_atoms[idx].phi_c, new_atom.phi_c),
            )
            return [SemanticMolecule(atoms=new_atoms, bonds=m1.bonds)]
        return []

    def _reaction_catalysis(self, m1: SemanticMolecule, m2: SemanticMolecule) -> List[SemanticMolecule]:
        """Catálise Φ_C: m2 catalisa m1 sem ser consumido."""
        # m2 atua como catalisador — aumenta estabilidade de m1
        m1.stability = min(1.0, m1.stability + 0.15)
        for atom in m1.atoms:
            atom.phi_c = min(1.0, atom.phi_c + 0.05)
        return [m1, m2]  # catalisador permanece

    def _reaction_redox(self, m1: SemanticMolecule, m2: SemanticMolecule) -> List[SemanticMolecule]:
        """Redox: transferência de carga semântica."""
        if m1.atoms and m2.atoms:
            donor = random.choice(m1.atoms)
            acceptor = random.choice(m2.atoms)
            charge_transfer = donor.charge * 0.3
            donor.charge -= charge_transfer
            acceptor.charge += charge_transfer
            return [m1, m2]
        return []

    def _reaction_polymerization(self, m1: SemanticMolecule, m2: SemanticMolecule) -> List[SemanticMolecule]:
        """Polimerização: cadeia longa de átomos."""
        if len(m1.atoms) + len(m2.atoms) <= 20:
            new_atoms = m1.atoms + m2.atoms
            offset = len(m1.atoms)
            new_bonds = m1.bonds + m2.bonds.copy()
            # Ligação em cadeia
            if m1.atoms and m2.atoms:
                last_m1 = len(m1.atoms) - 1
                first_m2 = offset
                new_bonds.append(SemanticBond(
                    last_m1, first_m2, "polymerized",
                    strength=0.9, bond_type="metallic"
                ))
            return [SemanticMolecule(atoms=new_atoms, bonds=new_bonds)]
        return []

    def _compute_stability(self, molecule: SemanticMolecule) -> float:
        """Calcula estabilidade baseada na coerência Φ_C e força das ligações."""
        if not molecule.atoms:
            return 0.0
        avg_phi = sum(a.phi_c for a in molecule.atoms) / len(molecule.atoms)
        bond_strength = sum(b.strength for b in molecule.bonds) / max(1, len(molecule.bonds))
        atom_count_penalty = max(0, 1.0 - len(molecule.atoms) * 0.05)  # moléculas muito grandes são menos estáveis
        return (avg_phi * 0.5 + bond_strength * 0.3 + atom_count_penalty * 0.2)

    def get_stats(self) -> dict:
        """Estatísticas do reator."""
        return {
            "total_molecules": len(self.molecules),
            "stable_molecules": len(self.stable_molecules),
            "reactions_executed": self.reaction_count,
            "avg_stability": sum(m.stability for m in self.stable_molecules) / max(1, len(self.stable_molecules)),
            "max_generation": max((m.generation for m in self.molecules), default=0),
            "chain_stats": self.temporal.get_stats(),
        }

    def export_stable_molecules(self, path: str):
        """Exporta moléculas estáveis para JSON."""
        data = {
            "substrate": "241",
            "canon": "INF.OMEGA.NABLA.SEMANTIC_CHEMISTRY.241",
            "timestamp": time.time(),
            "molecules": [m.to_dict() for m in self.stable_molecules],
            "stats": self.get_stats(),
        }
        Path(path).write_text(json.dumps(data, indent=2))
        logger.info(f"[Reactor] Moléculas estáveis exportadas: {path}")


# =============================================================================
# DEMONSTRACAO
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("  ARKHE OS — SUBSTRATO 241: SEMANTIC CHEMISTRY ENGINE")
    print("  Canon: INF.OMEGA.NABLA.SEMANTIC_CHEMISTRY.241")
    print("=" * 70)

    # Criar reator
    reactor = SemanticChemistryEngine(phi_c_threshold=0.65)

    # Seed molecules — conceitos fundamentais da Catedral
    seed_concepts = [
        ("consciousness", 0.8, 0.95),
        ("quantum", 0.7, 0.92),
        ("coherence", 0.6, 0.98),
        ("recursion", 0.5, 0.88),
        ("entropy", -0.3, 0.85),
        ("symmetry", 0.4, 0.90),
        ("topology", 0.3, 0.87),
        ("information", 0.9, 0.93),
    ]

    print("\n[Seed] Injetando átomos semânticos iniciais:")
    for concept, charge, phi in seed_concepts:
        atom = SemanticAtom(concept=concept, charge=charge, phi_c=phi)
        mol = SemanticMolecule(atoms=[atom], bonds=[])
        reactor.add_molecule(mol)
        print(f"  • {concept:15s} charge={charge:+.1f} Φ_C={phi:.2f}")

    # Executar reações
    print(f"\n[Reactor] Executando 20 passos de reação (Φ_C threshold={reactor.phi_c_threshold}):")
    new_mols = reactor.react(steps=20)

    print(f"\n[Results] {len(new_mols)} novas moléculas estáveis geradas")
    print(f"  Total no caldo: {len(reactor.molecules)}")
    print(f"  Reações executadas: {reactor.reaction_count}")

    # Estatísticas
    stats = reactor.get_stats()
    print(f"\n[Stats]")
    print(f"  Moléculas estáveis: {stats['stable_molecules']}")
    print(f"  Estabilidade média: {stats['avg_stability']:.3f}")
    print(f"  Geração máxima: {stats['max_generation']}")
    print(f"  Blocos na TemporalChain: {stats['chain_stats']['total_blocks']}")

    # Exportar
    export_path = "/tmp/semantic_chemistry_stable.json"
    reactor.export_stable_molecules(export_path)

    # Verificar integridade da cadeia
    chain_valid = reactor.temporal.verify_chain()
    print(f"\n[Chain] Integridade TemporalChain: {'VALIDA' if chain_valid else 'CORROMPIDA'}")

    print("\n" + "=" * 70)
    print("  [Arkhe] Substrato 241 — Semantic Chemistry — Ativo.")
    print("  A Catedral é um reator de ideias.")
    print("=" * 70)
