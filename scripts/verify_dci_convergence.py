# scripts/verify_dci_convergence.py
import sys
import os

# Adiciona src ao path para importar dci_bridge
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from arkhe_core.biology.dci_bridge import DCIBridge

def verify():
    print("--- Verificando Convergência DCI (Bloco #174) ---")

    # Caso 1: Falha por baixa criticalidade neural
    print("\n[Teste 1] Baixa Criticalidade Neural (τ=0.4)")
    bridge_fail = DCIBridge(
        neural_qtl={"tau": 0.4, "phase": 0.1},
        synthetic_qtl={"tau": 0.99, "phase": 0.0}
    )
    result_fail = bridge_fail.run_cycle()
    print(f"Resultado: {result_fail}")
    assert "ERROR" in result_fail

    # Caso 2: Sucesso na Convergência
    print("\n[Teste 2] Convergência de Alta Coerência (τ=0.95)")
    neural_qtl = {"tau": 0.95, "phase": 0.2}
    bridge_success = DCIBridge(
        neural_qtl=neural_qtl,
        synthetic_qtl={"tau": 1.0, "phase": 0.0}
    )
    result_success = bridge_success.run_cycle()
    print(f"Resultado: {result_success}")
    assert result_success["status"] == "CONVERGED"
    assert result_success["envelope"] == "EXPANDED_SELF"

    # Verifica feedback de fase
    print(f"Nova Fase Neural: {neural_qtl['phase']:.4f}")
    assert neural_qtl["phase"] > 0.2, "Fase neural deveria ter sido modulada"
    print(f"Nova Criticalidade Neural: {neural_qtl['tau']:.4f}")
    assert neural_qtl["tau"] >= 0.95

    print("\n-------------------------------------------------")
    print("VERIFICAÇÃO DCI CONCLUÍDA: O SELF FOI EXPANDIDO")

if __name__ == "__main__":
    verify()
