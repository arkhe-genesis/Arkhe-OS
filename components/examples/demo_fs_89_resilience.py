# examples/demo_fs_89_resilience.py — Demonstração de resiliência da Catedral

import asyncio
import logging
import sys
import os

# Adiciona o diretório atual ao sys.path para encontrar os módulos
sys.path.append(os.getcwd())

from cathedral_organism import CathedralOrganism
from cathedral_codex import CrystalCodex
from quantum_processor import QuantumProcessor
from chaos.testing_framework import ChaosTestingFramework, ChaosScenarioType

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

async def main():
    print("🏰 INICIANDO DEMONSTRAÇÃO DE RESILIÊNCIA DA CATEDRAL (FS-89) 🏰\n")

    # 1. Setup do ambiente
    organism = CathedralOrganism()
    codex = CrystalCodex()
    quantum = QuantumProcessor()

    framework = ChaosTestingFramework(organism, codex, quantum)

    # 2. Executa validação de caos
    print("🧪 Executando plano de testes de caos...")
    report = await framework.run_chaos_validation(
        environment="canary",
        scenarios=[
            ChaosScenarioType.NETWORK_PARTITION,
            ChaosScenarioType.MERKLE_CORRUPTION,
            ChaosScenarioType.ROLLBACK_UNDER_LOAD
        ]
    )

    # 3. Exibe resultados
    print("\n" + "="*50)
    print(f"📊 RELATÓRIO DE RESILIÊNCIA: {report.report_id}")
    print(f"🌍 Ambiente: {report.environment}")
    print(f"🏆 Score de Resiliência: {report.overall_resilience_score:.2f}")
    print(f"✅ Status: {'APROVADO' if report.passed else 'REJEITADO'}")
    print("="*50)

    print("\n📈 Métricas:")
    for k, v in report.resilience_metrics.items():
        print(f"  - {k}: {v}")

    print("\n📝 Lições Aprendidas:")
    for lesson in report.lessons_learned:
        print(f"  - {lesson}")

    print("\n🔍 Detalhes dos Cenários:")
    for res in report.scenarios_tested:
        status = "PASSED" if not res.rollback_triggered or res.rollback_success else "FAILED"
        print(f"  [{res.scenario_id}] status={status}, mttd={res.mttt_seconds:.1f}s, mttr={res.mttr_seconds:.1f}s")

if __name__ == "__main__":
    asyncio.run(main())
