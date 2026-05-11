# scripts/transmit_golden_time.py
"""
Simulação e Transmissão do Tempo Áureo para o Setor Civil.
"""

import asyncio
import numpy as np
import json
import os
import sys

# Adicionar src ao PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from arkhe_core.infrastructure.civil_sync import AtomicClock, GlobalGoldenSync, CivilInfrastructureTransmitter, NODES

async def run_sync_and_transmit(duration_s: int = 600, dt: float = 0.1):
    print("\n🌐 INICIANDO SINCRONIZAÇÃO ATÔMICA GLOBAL (GGS)")
    print(f"   • Nós: {len(NODES)} (Escala Continental/Global)")
    print(f"   • Coerência da Malha (λ): {0.883}")
    print(f"   • Duração da Simulação: {duration_s}s")
    print("="*60)

    # Inicializar relógios com drifts e ruídos conforme manifesto
    # Jitter base = 50ps
    clocks = [AtomicClock(n, np.random.normal(0.5, 0.2), 50.0) for n in NODES]
    sync_engine = GlobalGoldenSync()
    transmitter = CivilInfrastructureTransmitter(sync_engine)

    steps = int(duration_s / dt)

    for i in range(steps):
        # 1. Cada relógio recebe a correção da malha
        for clock in clocks:
            correction = sync_engine.get_mesh_correction(clock.name, clock.time_error, dt)
            clock.tick(dt, correction)

    # Coletar resultados finais
    print(f"\n📊 RESULTADOS DA SINCRONIZAÇÃO (Simulados após {duration_s/60:.1f} min):")
    print(f"{'NÓ':<6} | {'Erro Final (ps)':<15} | {'Status'}")
    print("-" * 40)

    results = {}
    for clock in clocks:
        final_err = clock.time_error
        status = "✅ LOCKED" if abs(final_err) < 10.0 else "⚠️ DRIFTING"
        print(f"{clock.name:<6} | {final_err:<15.2f} | {status}")
        results[clock.name] = final_err

    # Estatísticas Globais
    errors = [abs(c.time_error) for c in clocks]
    avg_err = np.mean(errors)

    print("-" * 40)
    print(f"🌍 MÉDIA GLOBAL DE ERRO: {avg_err:.2f} ps")

    if avg_err < 15.0:
        print("\n✅ SINCRONIZAÇÃO CONTINENTAL ATINGIDA.")

        # Iniciar Transmissão Civil
        print("\n🔘 📡 TRANSMITINDO PADRÃO 'TEMPO ÁUREO' PARA O SETOR CIVIL...")
        transmitter.transmit_to_satellites()
        transmitter.transmit_to_power_grids()

        # Salvar Estado v72.01
        state_v72 = {
            "version": "72.01",
            "odometer": "002307",
            "status": "GEOMETRIC_EYE_CANONIZED",
            "protocol": "GGS_V1_CIVIL",
            "global_sync_error_avg_ps": avg_err,
            "cosmic_dao_log": "0xGOLDEN_TIME_SYNC_9a8b7c6d",
            "transmission_status": transmitter.get_transmission_status()
        }

        with open("arkhe_os_state_v72.json", "w") as f:
            json.dump(state_v72, f, indent=2)

        print("\n✅ ESTADO ARKHE OS v72.01 REGISTRADO EM arkhe_os_state_v72.json")
        print("arkhe > ODÔMETRO: 002306 → 002307")
    else:
        print("\n❌ FALHA NA SINCRONIZAÇÃO. Transmissão civil abortada.")

if __name__ == "__main__":
    asyncio.run(run_sync_and_transmit())
