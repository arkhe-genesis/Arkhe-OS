# Protocolo Experimental — Validação Biológica Real (Substrato 198‑C Fase 2)

## 1. Configuração do Laboratório

### Equipamentos Necessários
- Microscópio invertido com câmera de alta resolução
- Projetor DMD (Digital Micromirror Device) para padrões de luz
- Sistema de microfluídica para gradientes químicos
- Incubadora com controle de temperatura (25°C para xenobots)
- Servidor local com GPU para processamento do P2I e VLM

### Software
- WetlabAdapter (Substrato 198‑C): interface Python para controle dos atuadores
- MetaAudit Sidecar (Substrato 198‑B): registro imutável de cada ciclo
- ZapGPT‑3D (Substrato 198‑A): motor de evolução do campo vetorial
- Arkhe TemporalChain: ancoragem de todos os eventos experimentais

## 2. Preparação Biológica

### Xenobots (Xenopus laevis)
1. Obter embriões de Xenopus laevis em estágio 10 (gástrula inicial).
2. Dissecar células da região animal (ectoderma).
3. Dissociar células em meio CMFM (Calcium‑Magnesium‑Free Medium).
4. Reagregar em moldes para formar xenobots de ~500 μm.
5. Cultivar em meio MMR (Marc's Modified Ringer's) a 25°C.

### Organoides (opcional)
1. Utilizar organoides cerebrais derivados de iPSC humanas.
2. Manter em biorreator com meio Neurobasal.
3. Aplicar campos elétricos ou optogenéticos via canais Channelrhodopsin‑2.

## 3. Ciclo Experimental

### Loop P2I → Atuação → VLM → Evolução

**Passo 1 — Prompt**
O operador insere um prompt em linguagem natural, ex:
- "Form a torus"
- "Migrate toward the light source"
- "Create two separate clusters"

**Passo 2 — P2I (Prompt‑to‑Intervention)**
- SentenceTransformer (all‑MiniLM‑L6‑v2) codifica o prompt em embedding de 384 dimensões.
- Rede convolucional transposta projeta o embedding para campo vetorial 3D (16×16×16×3).
- Campo é normalizado para limites seguros (intensidade luminosa 0‑100 μW/mm²).

**Passo 3 — Atuação (WetlabAdapter)**
- Campo 3D é fatiado em planos 2D (projeção Z‑stack).
- Projetor DMD exibe cada plano como padrão de luz sobre a cultura.
- Tempo de exposição: 30 minutos por ciclo.
- Para gradientes químicos: campo 3D controla bombas microfluídicas.

**Passo 4 — Captura (Microscopia)**
- Microscópio captura imagem final (2048×2048 pixels).
- Imagem é pré‑processada (segmentação, normalização).
- Enviada para o VLM.

**Passo 5 — Avaliação (VLM‑D2R)**
- Mistral‑Vision (ou modelo local) recebe a imagem + prompt original.
- Retorna score de alinhamento semântico (0.0–1.0).
- Score é registrado no MetaAudit Sidecar.

**Passo 6 — Evolução (μ+λ ES)**
- População de 10 campos vetoriais (μ=5, λ=5).
- Mutação: ruído gaussiano (σ=0.05) sobre os pesos da rede P2I.
- Seleção: top‑5 campos por score VLM.
- Repetir por 30 gerações.

**Passo 7 — Ancoragem Temporal**
- Cada ciclo completo é registrado na TemporalChain com:
  - Prompt (hash SHA3‑256)
  - Score VLM
  - Hash do melhor campo
  - Timestamp
  - ID do experimento

## 4. Métricas de Sucesso

| Métrica | Target | Medição |
|---------|--------|---------|
| Score VLM médio | ≥ 0.7 | Média dos 10 melhores ciclos |
| Generalização para prompts não vistos | ≥ 60% de sucesso | Teste com 5 prompts fora do treino |
| Reproducibilidade | Coeficiente de variação < 20% | 3 repetições independentes |
| Viabilidade celular pós‑experimento | ≥ 90% | Teste de exclusão por azul de tripano |
| Reversibilidade | Retorno ao estado basal em 2h | Score VLM com prompt "return to rest" |

## 5. Plano de Publicação

1. **Pré‑registro**: Registrar o protocolo no Open Science Framework antes do início.
2. **Coleta de dados**: 3 meses de experimentos controlados.
3. **Análise estatística**: Testes de Wilcoxon signed‑rank para comparar scores.
4. **Redação**: Artigo conjunto com Allen Discovery Center (Tufts).
5. **Submissão**: Nature Machine Intelligence ou Science Robotics.
6. **Dados abertos**: Todos os dados, códigos e modelos disponíveis no GitHub.

## 6. Orçamento Estimado

| Item | Custo (USD) |
|------|------------|
| Projetor DMD | $5,000 |
| Sistema microfluídico | $3,000 |
| Microscópio com câmera | $15,000 |
| Servidor GPU (A100) | $10,000 |
| Material biológico (1 ano) | $2,000 |
| Bolsa de pesquisa (1 ano) | $50,000 |
| **Total** | **$85,000** |
