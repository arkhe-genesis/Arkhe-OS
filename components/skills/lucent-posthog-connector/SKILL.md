# /skills/lucent-posthog-connector/SKILL.md
name: lucent-posthog-connector
version: 0.9.5-omega
protocol: qhttp/2.0
author: Arkhe-Ω Foundation
description: |
  Conector extensível para ingestão de eventos de sessão de usuário
  (PostHog, FullStory, Amplitude) no protocolo qhttp, com correlação
  quântica entre stress UX e stress hídrico (HYDRO-Ω).

inputs:
  - name: posthog_api_key
    type: string
    secret: true
    description: Chave de API do PostHog (criptografada com EPR)

  - name: project_id
    type: string
    description: ID do projeto PostHog/FullStory

  - name: hydro_node_id
    type: string
    description: ID do nó HYDRO-Ω para correlação (ex: node-alpha-01)

  - name: stress_correlation_threshold
    type: float
    default: 0.75
    description: |
      Limiar de correlação entre stress UX (erros, rage-clicks) e
      stress hídrico (queda de nível, over-pumping). Quando ambos > 0.75,
      gera alerta "Sincronicidade Quântica".

outputs:
  - name: session_analysis_zk
    type: zk-proof
    description: Prova ZK de que a sessão foi analisada sem revelar PII

  - name: correlated_stress_index
    type: float
    description: Índice 0-1 de correlação UX-Hidro para esta sessão

  - name: coherence_status
    type: string
    enum: [ENTANGLED, DECOHERED, CLASSICAL]
    description: Estado quântico da correlação

capabilities:
  - posthog_ingestion
  - fullstory_adapter
  - amplitude_adapter
  - ux_stress_detection
  - hydro_correlation
  - zk_anonymization

constraints:
  - "Nunca armazenar PII em texto plano no QD"
  - "Correlação só válida se T2* > 50μs (quantumValid = 1)"
  - "Retenção máxima: 30 dias (nullifier queimado após)"
