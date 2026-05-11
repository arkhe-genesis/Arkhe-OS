# demo_recursive_learning_implementation.py
import asyncio
import logging
import sys
import os

# Adiciona diretório atual ao path para importação dos módulos locais
sys.path.append(os.getcwd())

from ontological.forge import OntologicalForge, DomainOntologySpec, OntologyConsistency
from ontological.recursive_learning import RecursiveLearningEngine, FeedbackType

async def run_demo():
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    print("🜏 Iniciando Demonstração do Aprendizado Recursivo (FS-84.1)...")

    forge = OntologicalForge()
    engine = RecursiveLearningEngine(forge)

    domain = "SaudeDigital"

    # 1. Simulação de 10 gerações para coleta de dados
    print("\n[Fase 1] Coleta de Histórico (10 gerações)...")
    for i in range(10):
        spec = DomainOntologySpec(
            domain_name=domain,
            description=f"Ontologia de Saúde v{i}",
            base_uri="http://cathedral.ark/health",
            entities=["Paciente", "Doutor"] + ([f"Entidade_{j}" for j in range(i*2)] if i > 5 else []),
            constraints={"high_privacy": i % 2 == 0}
        )

        result = await forge.forge_from_ontology(spec)
        ontology = result["ontology"]

        engine.record_generation(
            spec=spec,
            ontology=ontology,
            intention=result["intention_code"],
            substrate=result["substrate"],
            metrics={"generation_time": 0.5, "coherence": 0.96}
        )

        # Feedback automático baseado na consistência
        sentiment = 1.0 if ontology.consistency_status == OntologyConsistency.VALID else -0.5
        engine.add_feedback(
            generation_id=ontology.ontology_id,
            feedback_type=FeedbackType.VALIDATION,
            sentiment=sentiment,
            details={"msg": f"Status: {ontology.consistency_status.value}"},
            source="Validator_v1"
        )

    # 2. Extração de Padrões
    print("\n[Fase 2] Extração de Padrões do Histórico...")
    patterns = engine.extract_patterns(min_support=3)
    for p in patterns:
        print(f" - Padrão Aprendido: {p.description} (Confiança: {p.confidence})")

    # 3. Otimização de Parâmetros
    print("\n[Fase 3] Otimização de Parâmetros por Domínio...")
    optimized = engine.optimize_parameters(domain)
    print(f" - Parâmetros Otimizados para {domain}: {optimized.parameters}")

    # 4. Aplicação de Aprendizado em Nova Geração
    print("\n[Fase 4] Aplicação do Aprendizado em Nova Geração...")
    new_spec = DomainOntologySpec(
        domain_name=domain,
        description="Geração Aprimorada",
        base_uri="http://cathedral.ark/health",
        entities=["Paciente", "Doutor", "Prontuario"],
        constraints={"high_privacy": True}
    )

    # Antes da aplicação (padrão)
    print(f" - Threshold Original: {new_spec.constraints.get('consistency_threshold', 'Default')}")

    # Aplica padrões
    enhanced_spec = engine.apply_learned_patterns(new_spec)
    print(f" - Threshold Aprimorado: {enhanced_spec.constraints.get('consistency_threshold')}")

    # 5. Meta-Aprendizado
    print("\n[Fase 5] Meta-Aprendizado: Forge aprimora a si mesmo...")
    success = await engine.enable_meta_learning()
    print(f" - Meta-Aprendizado aplicado: {success}")

    # Relatório Final
    print("\n[Fase 6] Relatório de Aprendizado Acumulado...")
    report = engine.generate_learning_report()
    print(f" - Total de Gerações: {report['total_generations']}")
    print(f" - Padrões no Códice: {report['patterns_count']}")

    print("\n🜏 Demonstração concluída. A Catedral agora aprende a criar.")

if __name__ == "__main__":
    asyncio.run(run_demo())
