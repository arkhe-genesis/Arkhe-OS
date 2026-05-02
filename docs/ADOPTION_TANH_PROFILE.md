# Adoção do Perfil Tanh no Characteristic Gluing Steering

**Versão**: v∞.370.2
**Data**: 3 de Maio de 2026
**Autor**: Rafael Oliveira (ORCID: 0009-0005-2697-4668)
**Referência**: Simulação de instantons em `core/instanton_simulator.py`

## Resumo Executivo

O perfil da função tanh com steepness $k = \frac{\pi}{4} \sqrt{Q}$ foi validado como aproximação numérica do perfil de ação do instanton BPST, com erro L² < 0.02 para $Q \in [1, 8]$. Esta aproximação é agora adotada como padrão no módulo `Characteristic Gluing Steering` (Substrato 92).

## Parâmetros Validados

| Parâmetro | Valor | Fonte |
| ----------- | ------- | ------- |
| `base_steepness` | π/4 ≈ 0.7854 | Minimização L² em `instanton_simulator.py` |
| `scaling_exponent` | 0.5 | Ajuste empírico para multi-instanton |
| `max_L2_error` | 0.02 | Limiar de aceitação para uso em produção |
| `k_order_per_instanton` | 2 | Correspondência com smoothness C^{k-2} |

## Fórmula de Colagem Adotada

$$\sigma(t; Q) = \frac{1}{2} \left[ 1 + \tanh\left( \frac{\pi}{4} \sqrt{Q} \cdot (t - t_0) \right) \right]$$

onde:

- $t \in [0, 1]$: tempo normalizado da transição
- $Q \in \mathbb{Z}^+$: número de instantons (número de Chern da transição)
- $t_0$: ponto central da transição (default: 0.5)

## Correspondência com Smoothness

| Q | k_order | Smoothness | Aplicação Típica |
| --- | --------- | ------------ | ----------------- |
| 1 | 2 | C⁰ | Transições básicas de regime |
| 2 | 4 | C² | Transições com estabilidade moderada |
| 4 | 8 | C⁶ | Transições críticas do Crystal Brain |
| 8 | 16 | C¹⁴ | Transições de alta precisão (futuro) |

## Integração com o Pipeline ARKHE

1. **SPSA Adaptive**: Usa `compute_gluing_steepness(Q)` para ajustar parâmetro de colagem durante otimização
2. **Characteristic Gluing**: Usa `tanh_gluing_function()` como kernel de transição entre regimes
3. **ZEE200 Proofs**: Registra `k_order` como metadado de prova para verificação de smoothness

## Validação Contínua

O módulo `validate_gluing_quality(Q)` deve ser executado periodicamente para garantir que alterações futuras não degradem a aproximação tanh. Limiares de alerta:

- ⚠️ Warning: L² > 0.015
- ❌ Error: L² > 0.02 (requer revisão da aproximação)

## Referências

1. Crump, Gadioux, Reall & Santos, *Phys. Rev. Lett.* **136**, 171405 (2026) — Instantons em Yang-Mills
2. `core/instanton_simulator.py` — Código de validação numérica
3. `core/characteristic_gluing.py` — Implementação adotada

## Histórico de Revisões

| Versão | Data | Mudança |
| -------- | ------ | --------- |
| v∞.370.2 | 2026-05-03 | Adoção inicial do perfil tanh validado |
