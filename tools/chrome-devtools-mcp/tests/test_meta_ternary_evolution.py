# tests/test_meta_ternary_evolution.py

import asyncio
import sys
import os
import logging

# Adiciona o root ao path
sys.path.append(os.getcwd())

from ontological.forge import OntologicalForge, DomainOntologySpec
from ontological.meta_learning import MetaLearningEngine
from protocol_forge import ProtocolForge
from src.arkhe_core.quantum.codex import QuantumCodex

async def test_full_evolutionary_cycle():
    logging.basicConfig(level=logging.INFO)
    print("=== INICIANDO TESTE DE EVOLUÇÃO META-TERNÁRIA (FS-84/FS-86) ===")

    # 1. Setup
    codex = QuantumCodex()
    proto_forge = ProtocolForge(cathedral_codex=codex)
    onto_forge = OntologicalForge(codex=codex, protocol_forge=proto_forge)
    meta_engine = MetaLearningEngine(forge=onto_forge, recursive_engine=onto_forge.learning_engine, codex=codex)

    # 2. Gera 11 ontologias para ativar o paradigma ternário (threshold >= 10)
    print("[Fase 1] Gerando histórico para ativação ternária...")
    for i in range(11):
        spec = DomainOntologySpec(
            domain_name=f"Domain_{i}",
            description=f"Teste {i}",
            base_uri="http://cathedral.ark/test",
            entities=["A", "B", "C"],
            actions=["X"],
            consents=["C"],
            purposes=["P"],
            constraints={"high_privacy": True}
        )
        onto_forge.generate_domain_ontology(spec)

    onto_forge.enable_recursive_self_improvement()
    print(f"  > Modo Ternário Ativado: {onto_forge.thresholds.get('ternary_mode')}")

    # 3. Valida Hipótese de Meta-Aprendizado
    print("[Fase 2] Validando hipótese de meta-aprendizado...")
    success = await meta_engine.create_and_validate_hypothesis(
        target="min_classes",
        change={"min_classes": 5}
    )
    print(f"  > Hipótese validada: {success}")

    # 4. Gera ontologia ternária
    print("[Fase 3] Gerando ontologia sob paradigma ternário...")
    spec_ternary = DomainOntologySpec(
        domain_name="TernaryProtocol",
        description="Protocolo otimizado BitZK",
        base_uri="http://cathedral.ark/test",
        entities=["Node1", "Node2", "Node3", "Node4", "Node5"],
        actions=["Sync"],
        consents=[],
        purposes=[],
        constraints={"high_privacy": True}
    )

    onto = onto_forge.generate_domain_ontology(spec_ternary)
    intention = onto_forge.ontology_to_intention(onto)

    print("--- INTENÇÃO TERNÁRIA ---")
    print(intention)
    print("-------------------------")

    # Verificações finais
    assert onto_forge.thresholds["ternary_mode"] is True
    assert "cathedral::ternary::bitzk" in intention
    assert onto_forge.ternary_builder.operations_count > 0

    print(f"[Efficiency] Operações ternárias: {onto_forge.ternary_builder.operations_count}")
    print("=== TESTE DE EVOLUÇÃO CONCLUÍDO COM SUCESSO ===")

if __name__ == "__main__":
    asyncio.run(test_full_evolutionary_cycle())
