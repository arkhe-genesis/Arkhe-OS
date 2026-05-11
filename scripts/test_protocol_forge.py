# test_protocol_forge.py — Teste do Gerador de Geradores

import asyncio
import json
from protocol_forge import ProtocolForge

INTENTION_CODE = """
// intenção: enxame_anonimo_drones.arkhe
protocol "Enxame Anônimo" {
  description: "Consensus BFT para enxames de drones com anonimato quântico"

  entities: [drone, enxame, regulador, operador]

  privacy: {
    drone: {
      anonymity: "full",
      dp_epsilon: 0.3
    },
    enxame: {
      aggregation_privacy: "homomorphic",
      consensus_anonymity: true
    }
  }

  consensus: {
    type: "bft",
    fault_tolerance: 1/3,
    finality_time_ms: 500,
    verifiable: true
  }

  regulation: ["LGPD", "GDPR", "ITAR"]

  performance: {
    max_latency_ms: 200,
    min_throughput_ops_sec: 100,
    scalability_nodes: 1000
  }

  integrates_with: [
    "cathedral::consensus::bft_core",
    "cathedral::privacy::quantum_dp",
    "cathedral::audit::cross_jurisdiction"
  ]
}
"""

async def run_test():
    print("🜏 Iniciando Teste do ProtocolForge (Substrato 83)...")
    forge = ProtocolForge()

    try:
        substrate = await forge.generate_from_intention(INTENTION_CODE)

        print("\n" + "="*60)
        print(f"SUBSTRATO GERADO: {substrate.name}")
        print(f"ID: {substrate.substrate_id}")
        print(f"Coerência Ω: {substrate.coherence_score}")
        print(f"Status: {'CANONIZADO' if substrate.canonized else 'PENDENTE'}")
        print("="*60)

        print("\nCOMPONENTES:")
        for comp_type, spec in substrate.components.items():
            print(f"- [{comp_type.upper()}]: {list(spec.keys()) if isinstance(spec, dict) else spec}")

        print("\nVERIFICAÇÃO INDEPENDENTE:")
        verification = await forge.verify_generated_substrate(substrate, INTENTION_CODE)
        print(f"Válido: {verification['valid']}")
        print(f"Coerência: {verification['coherence_score']}")

        print("\n🜏 TESTE CONCLUÍDO COM SUCESSO.")

    except Exception as e:
        print(f"❌ ERRO NO TESTE: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_test())
