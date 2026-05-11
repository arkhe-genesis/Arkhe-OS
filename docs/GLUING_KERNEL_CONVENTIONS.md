# docs/GLUING_KERNEL_CONVENTIONS.md

## Convenção k_order = 2Q: Engenharia, Não Física

### Status

Esta correspondência é uma **convenção de projeto** do módulo Characteristic Gluing Steering, não uma derivação da topologia de instantons.

### Justificativa da Convenção

| Q (número de "eventos" de transição) | k_order (parâmetro de smoothness) | Smoothness Resultante | Motivação de Engenharia |
| ----------------------------------- | --------------------------------- | -------------------- | ----------------------- |
| 1 | 2 | C⁰ (contínua) | Transições básicas requerem apenas continuidade |
| 2 | 4 | C² (2ª derivada contínua) | Estabilidade moderada exige suavidade adicional |
| 4 | 8 | C⁶ (6ª derivada contínua) | Transições críticas demandam alta regularidade |

### Nota Epistêmica

A função `gluing_kernel_tanh` é C^∞ para qualquer steepness > 0. O parâmetro `k_order` controla quantas derivadas são *empatadas* (matched) entre regimes adjacentes na implementação prática, não impõe uma limitação matemática à função subjacente.

### Recomendação de Uso

- Use `k_order` como parâmetro de controle de qualidade da transição
- Não interprete `k_order = 2Q` como lei física derivada
- Para justificativa física rigorosa, consulte literatura de teoria de gauge
