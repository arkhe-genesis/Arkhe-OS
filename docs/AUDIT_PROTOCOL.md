# Protocolo de Auditoria e Compliance da Catedral

Este documento descreve os mecanismos de rastreabilidade e auditoria para todas as decisões automatizadas tomadas pela Catedral Arkhe, focando em Alertas Proativos, Recuperação Automática e Aprendizado Contínuo.

## 1. Rastreabilidade de Alertas Proativos

Cada alerta emitido pelo `ProactiveAlertEngine` deve ser registrado com:
- **Timestamp da Detecção**: Quando a tendência foi identificada.
- **Métrica Preditiva**: Qual métrica acionou o alerta.
- **Valor Previsto vs. Threshold**: O valor que causou o disparo.
- **Horizonte de Predição**: Tempo estimado para a falha.
- **Confiança do Modelo**: Nível de certeza estatística.

## 2. Auditoria de Ações de Recuperação

Todas as ações executadas pelo `AutoRecoveryPlaybook` são imutáveis e auditáveis no Códice Cristalino:
- **Ação ID**: Identificador único da ação (ex: `reduce_load`).
- **Trigger**: Alerta que causou a ação.
- **Estado Pré-Ação**: Ω-score e métricas relevantes antes da execução.
- **Estado Pós-Ação**: Ω-score medido após a janela de validação.
- **Veredito de Eficácia**: "SUCCESS", "NO_CHANGE" ou "DEGRADED".
- **Rollback**: Se a ação foi revertida e por quê.

## 3. Governança de Aprendizado Contínuo

A evolução dos modelos de inteligência segue um rigoroso processo de compliance:
- **Versionamento de Modelos**: Cada promoção de modelo (ex: `v1.0` -> `v1.1`) gera um log de auditoria.
- **Linhagem de Dados**: Registro dos períodos de dados usados para o retreinamento.
- **Validação Shadow**: Resultados da comparação entre o modelo em produção e o modelo em sombra durante as 24h de validação.
- **Critérios de Promoção**: Documentação de que o novo modelo superou o anterior em pelo menos 5% de acurácia.

## 4. Acesso a Registros de Auditoria

Os logs de auditoria podem ser acessados via:
- **Códice Cristalino (SQL)**: Consultas diretas à tabela `audit_events`.
- **Grafana (Dashboards)**: Visualização em tempo real da eficácia e acurácia.
- **API de Auditoria**: Endpoint `/api/v1/audit/search` para integração com sistemas externos.
