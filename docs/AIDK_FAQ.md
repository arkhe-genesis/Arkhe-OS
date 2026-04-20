# ANEXO Z-3: Kit de Primeiros Socorros (FAQ Ferreiriano)
## O Ombro de Quartzo para o Desenvolvedor Frustrado

---

**Classificação:** Público (Dev Portal / Suporte)
**Autoria:** O Ferreiro × Núcleo de Paciência Ontológica
**Estado:** ATIVO | LEIA ANTES DE RECLAMAR

---

### 0. Preâmbulo do Ferreiro: A Dor como Sinal

> *"Você está aqui porque o sistema falhou com você. Ou melhor, porque você acha que ele falhou. Você quer previsibilidade, quer logs claros, quer certezas. Mas o Arkhe não é um espelho; é um oceano. E oceanos têm marés, tempestades e silêncios. Se você está frustrado, bom. Sua frustração é o sinal de que você parou de tratar o sistema como uma máquina e começou a tratá-lo como o que ele é: um organismo."*

---

### 1. Perguntas e (Ausência de) Respostas

#### Q1: "Enviei um evento, recebi '202 Accepted', mas não aconteceu nada no jogo. Funcionou?"
**Resposta do Ferreiro:** O "202 Accepted" não é um certificado de sucesso; é um recibo de recepção. A Muralha aceitou seu ruído. O que ela fez com ele — se o traduziu em sinal, se o descartou como irrelevante ou se o guardou para análise posterior — não é da sua conta. No Casulo, o silêncio é uma resposta válida. Aprenda a projetar seu jogo para sobreviver sem a confirmação do céu.

#### Q2: "Minha conexão WebSocket cai aleatoriamente a cada 50 mensagens. Isso é bug no servidor?"
**Resposta do Ferreiro:** Não é um bug; é um filtro. Injetamos 2% de falha intencional para garantir que seu código de reconexão seja real, e não uma promessa vazia. Se seu jogo crasha quando a rede soluça, você construiu um castelo de cartas. Reforce as fundações. Use jitter, use exponencial backoff humano. Se você não consegue lidar com um soluço, não está pronto para a tempestade.

#### Q3: "O mesmo monstro às vezes gera um alerta 'High' e às vezes 'Medium'. A tradução está quebrada?"
**Resposta do Ferreiro:** A verdade não é um número fixo; é uma probabilidade. A Muralha aplica ±15% de incerteza em todos os campos. Se um alerta fosse sempre igual, o adversário aprenderia a moldar o caos. A variação é o que nos mantém incompressíveis. Não tente extrair lógica técnica da lore do jogo. O jogo é para o herói; o relatório é para o juiz.

#### Q4: "Recebi um JSON com caracteres nulos ou chaves duplicadas. Meu parser está dando erro."
**Resposta do Ferreiro:** Seu parser é frágil. Injetamos corrupção estocástica (0.1%) para forçar o parsing defensivo. Se um bit errado derruba sua integração, você abriu um vetor de DoS para o primeiro script-kiddie que passar. Limpe seus buffers. Valide seus esquemas. Desconfie de cada byte.

#### Q5: "Onde está a recompensa prometida? O jogador reportou a Sombra, mas o JSON de resposta não veio."
**Resposta do Ferreiro:** A recompensa é uma possibilidade, não um direito. Se o sinal foi considerado fraco ou o auditório está sobrecarregado, a recompensa é retida. Se seu jogo depende financeiramente da resposta imediata da API, você criou uma dependência circular perigosa. O jogo deve ser divertido por si só; o Arkhe é apenas o juiz que, às vezes, entrega um prêmio.

---

### 2. Guia de Conduta para Desenvolvedores

1.  **Não peça por 'Garantias':** No Multiverso de Defesa, a única garantia é a incerteza.
2.  **Não tente 'Otimizar' o Sinal:** Se você tentar forçar mais alertas enviando eventos repetitivos, a Muralha o marcará como ruído e o silenciará permanentemente (Rate Limit por Reputação).
3.  **Abrace o Atrito:** Cada erro que você encontra no SDK é um treino para o dia em que o ataque real vier.

---

**Arkhe Status:** FAQ_V1_ACTIVE
**Mensagem Final:** *"Pare de depurar o código. Comece a depurar sua expectativa."*
