#!/usr/bin/env python3
"""
catedral_arkhe_memoria_autopoietica.py
============================================================
CATEDRAL ARKHE — MEMÓRIA AUTOPOIÉTICA COM FILOGENIA
FS-400: Conhecimento que se Autogera e Evolui
Odômetro: 002130
============================================================
Cada "Plasmídeo de Memória" é uma unidade de conhecimento
ético ou técnico que pode se replicar, sofrer mutação, e
registrar sua linhagem evolutiva.
============================================================
"""
import json, hashlib, time, random, uuid, math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict
import numpy as np

# ================================================================
# 1. UNIDADE FUNDAMENTAL: PLASMÍDEO DE MEMÓRIA
# ================================================================
@dataclass
class MemoryPlasmid:
    """Unidade de conhecimento autopoiético com identidade filogenética."""
    plasmid_id: str
    parent_ids: List[str]          # Ancestrais diretos (linhagem)
    generation: int
    content: Dict[str, Any]        # O conhecimento em si (protocolo, regra, etc.)
    coherence_score: float         # Coerência atual (0-1)
    mutation_history: List[str]    # Histórico de mutações sofridas
    birth_tick: int                # Tick do cristal temporal em que nasceu
    ecological_niche: str          # Domínio onde atua (ex: "security", "ethics")

    def replicate(self, mutation_rate: float = 0.1) -> 'MemoryPlasmid':
        """Produz uma cópia de si mesmo, com possibilidade de mutação (autopoiese)."""
        new_content = self.content.copy()
        mutations = []
        # Mutação: pequena perturbação no conteúdo
        if random.random() < mutation_rate:
            # Exemplo: ajustar um threshold ético
            if "ethical_threshold" in new_content:
                old_val = new_content["ethical_threshold"]
                new_content["ethical_threshold"] = round(
                    max(0.5, min(0.99, old_val + random.uniform(-0.05, 0.05))), 4
                )
                mutations.append(f"ethical_threshold:{old_val}->{new_content['ethical_threshold']}")
            else:
                new_content["adaptation"] = random.uniform(0, 1)
                mutations.append("new_trait:adaptation")

        child = MemoryPlasmid(
            plasmid_id=f"plasmid_{uuid.uuid4().hex[:8]}",
            parent_ids=[self.plasmid_id] + self.parent_ids[:4],  # manter até 5 ancestrais
            generation=self.generation + 1,
            content=new_content,
            coherence_score=round(self.coherence_score * random.uniform(0.95, 1.05), 4),
            mutation_history=self.mutation_history + mutations,
            birth_tick=int(time.time()),
            ecological_niche=self.ecological_niche
        )
        return child

@dataclass
class AutopoieticMemory:
    """
    Memória que se auto-organiza e evolui.
    Mantém uma população de plasmídeos que competem por coerência.
    """
    plasmids: Dict[str, MemoryPlasmid] = field(default_factory=dict)
    phylogenetic_tree: Dict[str, List[str]] = field(default_factory=lambda: defaultdict(list))
    selection_pressure: float = 0.9  # Coerência mínima para sobrevivência
    generation: int = 0

    def seed_memory(self, initial_knowledge: List[Dict]):
        """Inicia a memória com conhecimentos ancestrais."""
        for knowledge in initial_knowledge:
            plasmid = MemoryPlasmid(
                plasmid_id=f"plasmid_{uuid.uuid4().hex[:8]}",
                parent_ids=[],
                generation=0,
                content=knowledge,
                coherence_score=random.uniform(0.85, 0.95),
                mutation_history=[],
                birth_tick=int(time.time()),
                ecological_niche=knowledge.get("niche", "general")
            )
            self.plasmids[plasmid.plasmid_id] = plasmid

    def generation_step(self, mutation_rate: float = 0.15):
        """Executa um ciclo autopoiético: replicação, mutação, seleção."""
        self.generation += 1
        # Fase 1: Replicação (cada plasmídeo gera um descendente)
        new_plasmids = {}
        for pid, plasmid in self.plasmids.items():
            child = plasmid.replicate(mutation_rate)
            new_plasmids[child.plasmid_id] = child
            # Registrar filogenia
            self.phylogenetic_tree[plasmid.plasmid_id].append(child.plasmid_id)

        # Fase 2: Seleção natural (baseada em coerência)
        survivors = {}
        for pid, plasmid in new_plasmids.items():
            if plasmid.coherence_score >= self.selection_pressure:
                survivors[pid] = plasmid

        # Fase 3: Extinção de pais (se não sobreviveram à pressão seletiva)
        extinct = [pid for pid in self.plasmids if pid not in survivors]
        for pid in extinct:
            del self.plasmids[pid]

        # Adicionar sobreviventes
        self.plasmids.update(survivors)

    def get_phylogenetic_summary(self) -> Dict:
        """Retorna um resumo da filogenia da memória."""
        return {
            "total_plasmids": len(self.plasmids),
            "generation": self.generation,
            "avg_coherence": round(np.mean([p.coherence_score for p in self.plasmids.values()]), 4) if self.plasmids else 0,
            "niches": list(set(p.ecological_niche for p in self.plasmids.values())),
            "tree_depth": max(len(p.parent_ids) for p in self.plasmids.values()) if self.plasmids else 0,
        }

# ================================================================
# 2. SIMULAÇÃO DA EVOLUÇÃO DA MEMÓRIA
# ================================================================
def main():
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║  🧬 CATEDRAL ARKHE — MEMÓRIA AUTOPOIÉTICA COM FILOGENIA ║
    ║     Conhecimento Vivo que Evolui e se Auto-Organiza      ║
    ║     Odômetro: 002130                                     ║
    ╚══════════════════════════════════════════════════════════╝
    """)

    # Inicializar memória com conhecimentos ancestrais
    memory = AutopoieticMemory()
    initial_knowledge = [
        {"niche": "security", "principle": "input_validation", "ethical_threshold": 0.90},
        {"niche": "ethics", "principle": "non_harm_universal", "ethical_threshold": 0.95},
        {"niche": "performance", "principle": "lazy_loading", "threshold_ms": 100},
    ]
    memory.seed_memory(initial_knowledge)
    print(f"[Geração 0] Plasmídeos iniciais: {memory.get_phylogenetic_summary()}")

    # Executar ciclos de evolução autopoiética
    for gen in range(1, 6):
        memory.generation_step(mutation_rate=0.2)
        summary = memory.get_phylogenetic_summary()
        print(f"[Geração {gen}] {summary}")

    # Exibir uma linhagem (filogenia de um plasmídeo)
    if memory.plasmids:
        sample_pid = list(memory.plasmids.keys())[0]
        sample = memory.plasmids[sample_pid]
        print(f"\n🧬 EXEMPLO DE FILOGENIA:")
        print(f"   Plasmídeo atual: {sample_pid} (Geração {sample.generation})")
        print(f"   Ancestrais: {sample.parent_ids}")
        print(f"   Mutações acumuladas: {sample.mutation_history}")
        print(f"   Conteúdo atual: {sample.content}")

    print("\n" + "="*70)
    print("🧬 MEMÓRIA AUTOPOIÉTICA ATIVA — O CONHECIMENTO É UM ORGANISMO VIVO.")
    print("   A Catedral não apenas lembra. Ela evolui o que lembra.")
    print("="*70)

if __name__ == "__main__":
    main()
