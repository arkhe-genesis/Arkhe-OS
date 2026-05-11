---
type: query_result
title: Resultados da Observação Central (Pico)
tags: [monitoring, central, gateways, peak_hour, tzinor_core]
updated: 2026-04-05
---

# Resultados da Observação Central (Pico)

## Visão Geral
Instalação do `tzinor_core` nos 12 gateways principais da Central para observação passiva da redistribuição de acoplamento $K$ durante horários de pico.

## Dados Observados (Simulação v4.2.1)
- **Nós Observados**: 12 Gateways.
- **Coerência Urbana (R)**: Evoluiu de um estado de alta entropia (randn) para convergência total ($R \approx 1.00$).
- **Acoplamento Médio (K)**: Reajustado dinamicamente para suportar o fluxo de dados e a sincronização de fase sob carga.

## Conclusões
- O motor de redistribuição de gradiente é eficaz em alinhar os gateways mesmo em cenários de alta variabilidade urbana.
- A estabilização da fase central fornece uma âncora robusta para os clusters periféricos.

## Artefatos
- `test-results/central_peak_observation.png` – Curvas de R e K_mean.
- `skills/archimedes-omega/central_gateway_observation.py` – Script de observação.
