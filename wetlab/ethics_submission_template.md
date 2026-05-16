# Protocolo de Pesquisa — Controle por Linguagem Natural em Sistemas Biológicos
## Substrato 198‑C: Validação do "Verbo‑Campo" em Matéria Viva

### 1. Resumo
Este protocolo descreve a extensão do framework ZapGPT para sistemas biológicos
reais (xenobots, organoides), utilizando linguagem natural como único mecanismo
de controle sobre o comportamento coletivo celular, sem recompensas engenheiradas.

### 2. Objetivos
- Demonstrar que prompts linguísticos podem influenciar o comportamento de
  sistemas biológicos via campos físicos (luz, gradientes químicos).
- Validar a generalização do loop P2I → Atuação → VLM → Evolução para matéria viva.
- Estabelecer as bases para uma nova classe de interfaces cérebro‑máquina
  baseadas exclusivamente em linguagem.

### 3. Metodologia
1. **Preparação**: Xenobots ou organoides são cultivados em meio controlado.
2. **Interface**: Um WetlabAdapter traduz campos vetoriais 3D do P2I em padrões
   de luz (optogenética) ou gradientes químicos no meio de cultura.
3. **Ciclo Fechado**:
   - Prompt linguístico → embedding → campo vetorial 3D
   - Campo projetado como luz/químico sobre a cultura
   - Imagem microscópica capturada após período de exposição
   - VLM avalia alinhamento semântico (score 0‑1)
   - Evolução (μ+λ ES) otimiza o mapeador P2I
4. **Controles**: Culturas não expostas ao campo, ou expostas a campos aleatórios.

### 4. Considerações Éticas
- **Origem celular**: Xenobots derivados de células‑tronco embrionárias de Xenopus
  laevis, seguindo protocolos estabelecidos (Kriegman et al., 2020).
- **Bem‑estar**: Não há sistema nervoso; os xenobots são aglomerados celulares
  sem capacidade de dor ou sofrimento.
- **Reversibilidade**: Campos aplicados são removíveis; o sistema retorna ao
  estado basal após interrupção.
- **Confinamento**: Todos os experimentos são realizados em ambiente de contenção
  biológica nível 1 (BSL‑1).

### 5. Colaborações Propostas
- Allen Discovery Center (Tufts University) — expertise em xenobots
- Levin Lab (Wyss Institute) — biologia sintética e bioeletricidade
- Laboratório de Optogenética (Stanford) — controle por luz

### 6. Cronograma
| Fase | Duração | Entregável |
|------|---------|-----------|
| Simulação Biofísica (198‑C Fase 1) | 3 meses | WetlabAdapter validado em simulação |
| Submissão a Comitês de Ética | 1 mês | Protocolo aprovado |
| Experimentos Controlados (198‑C Fase 2) | 6 meses | Dados experimentais |
| Publicação | 3 meses | Artigo conjunto submetido |

### 7. Referências
- Le, Erickson, Zhang, Levin & Bongard (2025). ZapGPT: Free‑form Language
  Prompting for Simulated Cellular Control. arXiv:2509.10660.
- Kriegman et al. (2020). A scalable pipeline for designing reconfigurable
  organisms. PNAS, 117(4), 1853‑1859.
