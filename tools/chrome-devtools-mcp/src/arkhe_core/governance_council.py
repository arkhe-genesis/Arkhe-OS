
from typing import List, Dict, Any, Optional, TypedDict, Literal
from langgraph.graph import StateGraph, END
from . import council_tools

class IncidentState(TypedDict, total=False):
    evento: str
    sistema: str
    cve: Optional[str]
    cvss: float
    decisao_ciso: Optional[str]
    parecer_cio: Optional[str]
    plano_tecnico: Optional[str]
    parecer_dpo: Optional[str]
    status_revisao: Optional[Literal["Aprovado", "Rejeitado", "Requer_Alteracao"]]
    feedback_dpo: Optional[str]
    iteration_count: int
    ticket_jira: Optional[str]
    status_final: Optional[str]
    historico: List[str]
    seguranca_dominios: List[str] # Lista de domínios afetados (1-6)

def no_ciso(state: IncidentState) -> Dict[str, Any]:
    print("--- NÓ CISO ---")
    historico = state.get("historico", [])
    historico.append("CISO: Alinhamento com NIST CSF 2.0. Foco em Identidade e Proteção de Dados.")

    dominios = ["Domínio 1 (IAM)", "Domínio 4 (Dados)"]
    if state["cvss"] > 9.0:
        return {"decisao_ciso": "ExigirMitigacao", "historico": historico, "seguranca_dominios": dominios}
    return {"decisao_ciso": "Acompanhar", "historico": historico, "seguranca_dominios": dominios}

def no_cio(state: IncidentState) -> Dict[str, Any]:
    print("--- NÓ CIO ---")
    historico = state.get("historico", [])
    historico.append("CIO: Avaliando SLA e janelas de manutenção IaC.")
    cmdb = council_tools.consultar_cmdb(state["sistema"])
    return {"parecer_cio": f"SLA: {cmdb['sla']}. Janela disponível via pipeline CI/CD.", "historico": historico}

def no_isso(state: IncidentState) -> Dict[str, Any]:
    print("--- NÓ ISSO ---")
    historico = state.get("historico", [])
    iteration = state.get("iteration_count", 0) + 1

    cve = state.get("cve", "CVE-Generica")
    playbook = council_tools.obter_playbook(cve)

    plano = f"Plano v{iteration} (Zero Trust): {playbook}"

    # Implementação técnica de Defesa em Profundidade
    plano += "\n- Aplicar NetworkPolicy L4 (Domínio 2)"
    plano += "\n- Validar assinatura de imagem via Cosign (Domínio 3)"

    if state.get("status_revisao") == "Rejeitado":
        plano += "\n- ADENDA: Mascaramento de PII no ACL (Domínio 4) incluído conforme DPO."
        historico.append(f"ISSO: Plano atualizado com controles do Domínio 4 (iteração {iteration}).")
    else:
        historico.append(f"ISSO: Plano inicial focado em Domínios 2 e 3 (iteração {iteration}).")

    return {"plano_tecnico": plano, "iteration_count": iteration, "historico": historico}

def no_dpo(state: IncidentState) -> Dict[str, Any]:
    print("--- NÓ DPO ---")
    historico = state.get("historico", [])
    plano = state["plano_tecnico"]

    # Exigência do Domínio 4 (Privacidade)
    if "Mascaramento" not in plano and state.get("iteration_count", 0) == 1:
        historico.append("DPO: REJEITOU por falta de Mascaramento de PII (Domínio 4).")
        return {
            "status_revisao": "Rejeitado",
            "feedback_dpo": "Necessário incluir Mascaramento de PII no Anti-Corruption Layer.",
            "historico": historico
        }

    historico.append("DPO: APROVOU os controles de privacidade.")
    return {"status_revisao": "Aprovado", "historico": historico}

def no_issm(state: IncidentState) -> Dict[str, Any]:
    print("--- NÓ ISSM ---")
    historico = state.get("historico", [])
    ticket = council_tools.criar_ticket_jira(
        titulo=f"SEC-PILOT: Mitigar {state.get('cve', 'Vulnerabilidade')} em {state['sistema']}",
        descricao=state["plano_tecnico"],
        responsavel="Equipa-Seguranca-Operativa",
        prazo="24h (SLO Crítico)"
    )
    historico.append(f"ISSM: Orquestração concluída. Ticket Jira: {ticket}")
    return {"ticket_jira": ticket, "status_final": "ENCAMINHADO", "historico": historico}

def roteador_dpo(state: IncidentState) -> Literal["isso", "issm"]:
    if state["status_revisao"] == "Rejeitado" and state["iteration_count"] < 3:
        return "isso"
    return "issm"

# Construção do Grafo
workflow = StateGraph(IncidentState)

workflow.add_node("ciso", no_ciso)
workflow.add_node("cio", no_cio)
workflow.add_node("isso", no_isso)
workflow.add_node("dpo", no_dpo)
workflow.add_node("issm", no_issm)

workflow.set_entry_point("ciso")
workflow.add_edge("ciso", "cio")
workflow.add_edge("cio", "isso")
workflow.add_edge("isso", "dpo")

workflow.add_conditional_edges(
    "dpo",
    roteador_dpo,
    {
        "isso": "isso",
        "issm": "issm"
    }
)

workflow.add_edge("issm", END)

# Compilação
governance_app = workflow.compile()
