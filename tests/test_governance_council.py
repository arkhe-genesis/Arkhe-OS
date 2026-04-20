
import asyncio
from src.arkhe_core.governance_council import governance_app

async def test_governance_workflow():
    print("\n--- TESTANDO WORKFLOW DE GOVERNANÇA ---")
    initial_state = {
        "evento": "Detecção de Vulnerabilidade Crítica",
        "sistema": "Core-Banking",
        "cve": "CVE-2024-1234",
        "cvss": 9.8,
        "iteration_count": 0,
        "historico": []
    }

    result = await governance_app.ainvoke(initial_state)

    print("\nRESULTADO FINAL:")
    print(f"Status: {result['status_final']}")
    print(f"Ticket Jira: {result['ticket_jira']}")
    print(f"Iterações do ISSO: {result['iteration_count']}")
    print("\nHISTÓRICO:")
    for entry in result['historico']:
        print(f"- {entry}")

    # Verificações básicas
    assert result['status_final'] == "ENCAMINHADO"
    assert "SEC-" in result['ticket_jira']
    assert result['iteration_count'] > 1  # Deve ter tido pelo menos uma rejeição do DPO conforme simulado
    assert any("REJEITOU" in entry for entry in result['historico'])
    assert any("APROVOU" in entry for entry in result['historico'])

if __name__ == "__main__":
    asyncio.run(test_governance_workflow())
