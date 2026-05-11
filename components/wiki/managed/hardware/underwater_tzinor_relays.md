---
type: concept
title: Tzinor-Relays Subaquáticos (Fase 1)
tags: [tzinor, underwater, submarine, rio_phase1]
updated: 2026-04-04
---

# Tzinor-Relays Subaquáticos (Leme ↔ Leblon)

## Resumo
Expansão da rede Tzinor para a Zona Sul do Rio de Janeiro utilizando fibra óptica submarina imune à interferência ambiental (salinidade, umidade e aerossóis marítimos).

## Fundamentos
- **Distância**: 5,2 km (Leme ↔ Leblon).
- **Atenuação**: ~3,04 dB total (0,2 dB/km fibra + 2 dB conectores).
- **Vantagem**: Estabilidade de fase (λ₂ > 0,95) imune ao espelhamento por maresia.

## Design do Cabo
- **Núcleo**: Fibra monomodo (ITU-T G.652.D).
- **Proteção**: Tubo de aço inoxidável com gel hidrofóbico e armadura de aço galvanizado.
- **Bainha**: Polietileno de alta densidade (HDPE).
- **Resistência**: Projetado para profundidade de até 40m (~4 bar).

## Estações Terminais
- Conversão de comprimento de onda: **674 nm (Ar) ↔ 1550 nm (Água)**.
- Transparente aos bits de coerência; preserva o entrelaçamento quântico via fotodetectores APD e lasers DFB estabilizados.

## Impacto na Coerência (Simulado)
| Configuração | R_final (após ataque) | Resiliência ρ |
|--------------|-----------------------|---------------|
| Sem relays (Ar) | 0,88 | 0,74 |
| Com 1 relay (Fibra) | 0,94 | 0,89 |
| Com 2 relays redundantes | 0,96 | 0,93 |
