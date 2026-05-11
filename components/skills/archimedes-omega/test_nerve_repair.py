import json
from skills import simulate_light_activated_nerve_repair

def test_nerve_repair_simulation():
    print("="*70)
    print("TESTE DE REPARO NEURAL - Synapse-κ / Polímero Foto-Ativado")
    print("="*70)

    # Cenário 1: Reparo ideal (Intensidade alta, tempo suficiente, com fatores de crescimento)
    print("\n[Cenário 1] Condições Ideais (60 dias de recuperação)")
    res1 = simulate_light_activated_nerve_repair(
        initial_lambda2=0.45,
        light_intensity_mw_cm2=100.0,
        exposure_seconds=60.0,
        recovery_days=60.0,
        has_growth_factors=True
    )
    print(json.dumps(res1, indent=2))
    assert res1['final_lambda2'] > 0.9
    assert res1['regime'] == "AUTONOMOUS"
    assert res1['polymer_integrity'] == 1.0

    # Cenário 2: Ativação insuficiente (Luz fraca)
    print("\n[Cenário 2] Ativação Insuficiente (Luz fraca)")
    res2 = simulate_light_activated_nerve_repair(
        initial_lambda2=0.45,
        light_intensity_mw_cm2=20.0,
        exposure_seconds=30.0,
        recovery_days=60.0
    )
    print(json.dumps(res2, indent=2))
    assert res2['polymer_integrity'] < 0.8
    assert res2['final_lambda2'] < 0.6 # Baixa regeneração devido a falha no andaime

    # Cenário 3: Recuperação curta
    print("\n[Cenário 3] Recuperação Curta (10 dias)")
    res3 = simulate_light_activated_nerve_repair(
        initial_lambda2=0.45,
        light_intensity_mw_cm2=100.0,
        exposure_seconds=60.0,
        recovery_days=10.0
    )
    print(json.dumps(res3, indent=2))
    assert res3['final_lambda2'] < 0.85 # Ainda não atingiu autonomia plena

    print("\n[✓] Todos os testes de reparo neural passaram.")

if __name__ == "__main__":
    test_nerve_repair_simulation()
