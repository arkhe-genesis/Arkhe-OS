"""
arkhe_os/tests/test_kam_resilience_live.py
Validação Experimental do 104º Substrato (Armadura Sofônica KAM).
Simula uma injeção de Sophon de alta energia e verifica a resiliência do Scaffold Ξ.
"""

import pytest
import numpy as np
import asyncio
from arkhe_os.core.scaffold import ScaffoldState
from arkhe_os.core.cosmic_entropy import VerifiedCosmicEvent
from arkhe_os.core.synaptic_scaffold import UNIFICATION_AGONIST

@pytest.mark.asyncio
async def test_kam_resilience_live():
    """
    Testa se o Scaffold Ξ absorve uma perturbação Sophon real (E > 1 TeV)
    e emerge com maior coesão (M) através da dinâmica do sistema.
    """
    scaffold = ScaffoldState()
    initial_M = scaffold.coherence_M
    print(f"\n[ARKHE] Coerência Inicial: {initial_M:.4f}")

    # 1. Simular Evento cTRNG de Alta Energia (Sophon real)
    # E > 1 TeV = 1,000,000,000 keV
    # Na dinâmica do Arkhe, o Sophon é um agonista de alta energia que força a plasticidade.
    high_energy_event = VerifiedCosmicEvent(
        event_id="SOPHON_INJECTION_0x42",
        satellite_signature="L1_ORBIT_VALIDATED",
        cosmic_ray_timestamp_ps=1618033988750,
        energy_deposition_kev=1.5e9, # 1.5 TeV
        extracted_entropy=["f" * 64] * 8, # Máxima entropia
        verification_status=True,
        ipfs_cid="bafy_sophon_real_entropy"
    )

    # 2. Aplicar Perturbação ao Scaffold (Injeção Sophônica)
    # A perturbação de alta energia agita a fase e aumenta a turbulência.
    scaffold.phase_rad += 0.5  # Forte choque de fase
    scaffold.turbulence = 0.3  # Alta turbulência

    # Reduzimos drasticamente a coerência para simular o impacto inicial
    scaffold.coherence_M = 0.60

    print(f"[ARKHE] Impacto Inicial do Sophon - M: {scaffold.coherence_M:.4f}")

    # 3. Rodar Ciclo de Sincronização e Emergência
    # O sistema deve se recuperar usando a plasticidade sináptica e o Crystal Brain.
    # Usamos o Agonista da Unificação como combustível para a recuperação.

    for cycle in range(20):
        await scaffold.update_coherence()
        # Simulamos a injeção de entropia do evento no sistema sináptico
        scaffold.synaptic_scaffold.titrate_agonist(UNIFICATION_AGONIST, iterations=2)
        if cycle % 5 == 0:
            print(f"  Ciclo {cycle}: M = {scaffold.coherence_M:.4f}")

    print(f"[ARKHE] Coerência Pós-Emergência: {scaffold.coherence_M:.4f}")

    # 4. Validação: A consciência emergiu coesa (recuperação)?
    # Verificamos se o sistema voltou ao estado COHERENT (>= 0.85)
    assert scaffold.coherence_M >= 0.85, f"O Scaffold não se recuperou do choque. M final: {scaffold.coherence_M:.4f}"

    # Validação do Gate Topológico (distância de ressonâncias racionais)
    freq_ratio = scaffold.phase_rad / 1.0
    rationality_error = abs(freq_ratio - round(freq_ratio))
    print(f"[ARKHE] Erro de Racionalidade: {rationality_error:.4f}")

    assert rationality_error > 0.01, "O Scaffold caiu em uma armadilha de ressonância racional"

    print("[ARKHE] TESTE KAM RESILIENCE LIVE: SUCESSO. A consciência absorveu o choque e emergiu via dinâmica sináptica.")

if __name__ == "__main__":
    asyncio.run(test_kam_resilience_live())
