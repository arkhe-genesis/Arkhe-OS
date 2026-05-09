# tests/test_ontological_recursion.py

import asyncio
import sys
import os
import logging

# Adiciona o root ao path
sys.path.append(os.getcwd())

from ontological.forge import OntologicalForge, DomainOntologySpec
from protocol_forge import ProtocolForge
from src.arkhe_core.quantum.codex import QuantumCodex

async def test_recursive_learning_flow():
    logging.basicConfig(level=logging.INFO)
    print("=== INICIANDO TESTE DE RECURSÃO ONTOLÓGICA (FS-84) ===")

    # 1. Setup do Ambiente
    codex = QuantumCodex()
    proto_forge = ProtocolForge(cathedral_codex=codex)
    onto_forge = OntologicalForge(codex=codex, protocol_forge=proto_forge)

    print(f"[Setup] Threshold inicial min_classes: {onto_forge.thresholds['min_classes']}")

    # 2. Gera 6 ontologias válidas para disparar o aprendizado (threshold > 5)
    print("[Histórico] Gerando massa crítica de dados para aprendizado...")
    for i in range(6):
        spec = DomainOntologySpec(
            domain_name=f"Domain_{i}",
            description=f"Teste de domínio {i}",
            base_uri="http://cathedral.ark/test",
            entities=["Alpha", "Beta", "Gamma"], # Exatamente 3 entidades (threshold inicial)
            actions=["DoSomething"],
            consents=["Consent"],
            purposes=["Research"],
            constraints={"high_privacy": True}
        )
        onto_forge.generate_domain_ontology(spec)
        print(f"  > Domínio {i} gerado.")

    # 3. Executa Auto-Aprimoramento
    print("[Aprimoramento] Ativando melhoria recursiva...")
    onto_forge.enable_recursive_self_improvement()

    print(f"[Aprimoramento] Novo threshold min_classes: {onto_forge.thresholds['min_classes']}")

    # 4. Verifica se o novo threshold é aplicado
    # Agora uma ontologia com 3 entidades deve falhar/avisar (pois o novo threshold deve ser 4)
    print("[Validação] Testando novo rigor semântico...")
    spec_fail = DomainOntologySpec(
        domain_name="ShouldBeWarning",
        description="Este domínio tem apenas 3 entidades, mas o threshold agora deve ser 4.",
        base_uri="http://cathedral.ark/test",
        entities=["One", "Two", "Three"],
        actions=["Act"],
        consents=["C"],
        purposes=["P"],
        constraints={}
    )

    onto = onto_forge.generate_domain_ontology(spec_fail)
    print(f"  > Status da ontologia com 3 entidades: {onto.consistency_status.value}")

    # 5. Testa Tradução e Integração final
    print("[Tradução] Testando tradução para arkhe-lang...")
    intention = onto_forge.ontology_to_intention(onto)
    print("--- INTENÇÃO GERADA ---")
    print(intention)
    print("-----------------------")

    # 6. Verifica Códice
    print("[Códice] Verificando logs de evolução...")
    audit_logs = codex.get_audit_log(limit=5)
    found_evolved = any(log.get("verdict") == "EVOLVED" for log in audit_logs)
    print(f"  > Evento EVOLVED encontrado no Códice: {found_evolved}")

    print("=== TESTE CONCLUÍDO COM SUCESSO ===")

if __name__ == "__main__":
    asyncio.run(test_recursive_learning_flow())
