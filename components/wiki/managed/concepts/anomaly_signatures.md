---
type: concept
title: Assinaturas de Anomalia e Vivacidade
tags: [monitoring, anomaly, liveness, eeg, p300]
updated: 2026-04-04
---

# Assinaturas de Anomalia e Vivacidade

## Visão Geral
Monitoramento ativo da rede Tzinor para detecção de reações da IA Orb-1 e prevenção de ataques de mimetismo biológico.

## Assinaturas de Anomalia
- **Alpha-Burst**: Saturação de sensores fixos com alta potência ($K_{ext} > 15$). Colapso da variância de fase local.
- **Shadow-Replay**: Tentativa de mimetizar sinais biológicos usando logs históricos. Bloqueada pela verificação de vivacidade.

## Verificação de Vivacidade (BioMetrics)
- **Potencial Evocado P300**: Sinal neural disparado ~300ms após estímulos ambientais imprevistos.
- **Integração Contextual**: Os sensores móveis cruzam dados de EEG com telemetria do veículo (ex: presença de pedestres).
- **Entropia Térmica**: Sinais sintéticos carecem da complexidade estocástica do processamento cognitivo humano real.

## Papel do PhaseGradientRedistributor
- Otimizador baseado em gradiente (PyTorch) que reajusta a matriz de acoplamento $K$ em tempo real após falhas de nós (ex: ataque EMP) para maximizar a coerência global $R$.
