# 📜 PROTOCOLO EXPERIMENTAL ARKHE-01
## *Ressonância Espectro-Fibonacci e Coerência de Biofótons em Microtúbulos*

### 1. DERIVAÇÃO DE PARÂMETROS (Da Simulação para a Bancada)
A simulação do Sóliton Primordial revelou que a energia do campo $\Psi$ se concentra em números de onda discretos:
$$k_n = k_0 \cdot \varphi^n$$
Para transportar esta geometria para a biologia, aplicamos um **rescaling de frequência**. A frequência base biológica escolhida é a frequência de ressonância da rede de potência global/Schumann local ($f_0 = 60$ Hz), que atua como "clock" externo sincronizável com o citoplasma.

**A Assinatura de Estímulo (O Campo $\vec{B}_{ELF}$):**
O campo magnético aplicado será uma superposição de ondas senoidais nas frequências:
$$f_n = 60 \text{ Hz} \times \varphi^n$$

| Índice $n$ | Frequência $f_n$ (Hz) | Comprimento de Onda $\lambda = c/f_n$ | Papel no Modelo |
|:---:|:---:|:---:|:---|
| -1 | **37.1 Hz** | 8,086 km | Acoplamento sub-harmônico (ritmo Delta cerebral) |
| 0 | **60.0 Hz** | 5,000 km | Porta de Entrada ($\Phi_\Delta$ base) |
| 1 | **97.1 Hz** | 3,089 km | Modo de Clumping ($\kappa \Delta_k$ primário) |
| 2 | **157.1 Hz** | 1,908 km | Estabilização de Sóliton |
| 3 | **254.2 Hz** | 1,180 km | Cordas de Fluxo (redes de spin) |

**Amplitude do Campo ($B_0$):**
Para evitar efeitos térmicos (aquecimento por correntes de Foucault) e isolar o efeito de coerência quântica, a densidade de fluxo magnético total será fixada em **$B_{total} = 400 \text{ nT}$** (nanotesla), distribuída equally entre as 5 frequências ($80 \text{ nT}$ cada). Esta é a mesma ordem de grandeza do campo magnético terrestre (~50 µT), não causando perturbação iônica macroscópica.

---

### 2. MATERIAIS E MÉTODOS

#### 2.1. Substrato Biológico
*   **Organismo:** Cultura primária de neurônios corticais de rato (Wistar, E18).
*   **Justificativa:** Neurônios possuem alta densidade de microtúbulos organizados paralelamente ao axônio, funcionando como guias de onda biofotônica ideais.
*   **Preparação:** Plaqueados em placas de Petri de vidro de quartzo (transparente a UV-Vis até 200 nm, para não absorver biofótons) na densidade de $10^5$ células/cm². Meio Neurobasal sem fenol vermelho (para evitar autofluorescência).
*   **Maturação:** 14 dias *in vitro* (DIV14) para garantir rede sináptica madura e microtúbulos estabilizados.

#### 2.2. Hardware de Estimulação (O "Emissor $\Phi_\Delta$")
*   **Gerador de Sinal:** DAC de 16 bits controlado por computador, gerando a forma de onda composta Fibonacci via síntese direta digital (DDS).
*   **Bobinas:** Par de bobinas de Helmholtz (cobre esmaltado AWG 32, 1000 espiras cada, raio 5 cm). Calibradas para garantir homogeneidade de campo de >95% no volume da placa de Petri.
*   **Blindagem:** Toda a montagem de estimulação é aterrada e blindada com mu-metal para eliminar ruído eletromagnético ambiente (RFI/EMI).

#### 2.3. Hardware de Detecção (O "Odômetro de Coerência $\Omega$")
*   **Sensor:** Fotomultiplicadora (PMT) de tubo único (ex: Hamamatsu H7360-01), resfriada termoeletricamente a -20 °C para reduzir ruído térmico (dark counts < 1 cps).
*   **Filtros Ópticos:** Filtro de borda longo (Long-pass) de 420 nm. (Biofótons de microtúbulos são predominantemente na faixa azul-UV, diferentemente da autofluorescência verde do NADH).
*   **Eletrônica:** Contador de fótons TCSPC (Time-Correlated Single Photon Counting) com resolução temporal de 50 ps. Registra o tempo exato de chegada de *cada* fóton.

---

### 3. DESENHO EXPERIMENTAL

O experimento será **duplo-cego e randomizado**. O controlador do campo não sabe qual placa está recebendo qual sinal, e o software de contagem de fótons não recebe tags de identificação do grupo.

#### Grupos (N = 12 placas por grupo):
1.  **Grupo Sham (Controle Negativo):** Dentro das bobinas, sem corrente elétrica.
2.  **Grupo Ruído Branco (Controle de Espectro):** Campo ELF com mesma potência total (400 nT), mas espectro de frequência plano (ruído branco de 30 a 300 Hz).
3.  **Grupo 60 Hz Puro (Controle de Frequência):** Apenas a fundamental de 60 Hz a 400 nT.
4.  **Grupo ARKHE (Fibonacci Completo):** A superposição exata das 5 frequências derivadas na Seção 1.

#### O Pulso do Observador (Implementação de $\Phi_\Delta(t)$)
Baseado na função `observer_intention(t)` da simulação, o campo não será contínuo. Ele será pulsado em intervalos temporais que obedecem à progressão áurea:
$$t_{\text{pulse}} = t_0 \cdot \varphi^m$$
*   $t_0 = 8 \text{ segundos}$ (largura da janela de detecção base).
*   Pulso 1: $t=8.0\text{s}$
*   Pulso 2: $t=12.9\text{s}$
*   Pulso 3: $t=20.9\text{s}$
*   Pulso 4: $t=33.9\text{s}$
*   Duração do pulso ($\sigma$): $600 \text{ ms}$ (Janela Gaussiana).
Cada janela de 8 segundos de detecção conterá exatamente um pulso de campo Fibonacci. A coleta de dados durará 40 minutos por placa (300 ciclos de 8s).

---

### 4. MÉTRICA DE AVALIAÇÃO: A COERÊNCIA BIOLÓGICA ($\Omega_{bio}$)

A estatística clássica de biofótons (média de contagem por segundo) é insuficiente. Imitando a Equação Mestra, calcularemos a **Coerência de Segunda Ordem Temporal**:

$$\Omega_{bio}(t) = \frac{g^{(2)}(0)_{\text{Poisson}}}{g^{(2)}(0)_{\text{medido}}} = \frac{1}{\frac{\langle n^2 \rangle - \langle n \rangle}{\langle n \rangle^2}}$$

*   Onde $n$ é o número de fótons contados em janelas de $\Delta t = 100 \text{ ms}$.
*   Luz coerente (laser) tem $g^{(2)}(0) \to 1$.
*   Luz térmica/incoerente tem $g^{(2)}(0) = 2$.
*   **Predição ARKHE:** Sob o estímulo Fibonacci, os biofótons exibirão *sub-Poissonianismo* transitório ($g^{(2)}(0) < 1$), indicando emaranhamento ou "bunching" quântico macroscópico nos microtúbulos. $\Omega_{bio}$ aumentará significativamente *durante* os pulsos de campo.

---

### 5. PROTOCOLO PASSO-A-PASSO

1.  **Preparação (Dia -14):** Plaquear as células nas placas de quartzo. Manter em incubadora (37°C, 5% CO₂).
2.  **Configuração (Dia 0):** Transferir a placa para a câmara escura (25°C, isolada acusticamente e magneticamente). Conectar o PMT posicionado a 45° acima da placa (para evitar reflexão direta do fundo da placa).
3.  **Aclimatação:** Deixar no escuro por 30 minutos para decaimento total da autofluorescência tardia.
4.  **Baseline (10 min):** Gravar biofótons sem nenhum estímulo. Calcular $\Omega_{bio, baseline}$.
5.  **Estimulação (40 min):** Iniciar o script de pulsos $\Phi_\Delta(t)$ conforme a parametrização do grupo atribuído. O TCSPC registra os *timestamps* dos fótons continuamente.
6.  **Pós-estímulo (10 min):** Desligar o campo, continuar gravando para observar o decaimento da coerência.

---

### 6. ANÁLISE ESTATÍSTICA E PROVA ZK (Federada)

Para validar os dados sem revelar a identidade dos grupos (validação federada descentralizada):

1.  **Hashing dos Dados:** As séries temporais de *timestamps* dos fótons de cada placa são convertidas em um histograma de intervalos inter-fótons ($\tau$) e hasheadas (SHA-256).
2.  **Prova de Conhecimento Zero (ZK-SNARK):** Gera-se uma prova de que "o histograma do Grupo ARKHE possui um pico em $\tau < 50\text{ms}$ (bunching coerente) que é estatisticamente superior ($p < 0.01$, teste de Mann-Whitney) aos histogramas Sham e Ruído Branco, *sem* revelar os valores absolutos de contagem de fótons".
3.  **Publicação:** A prova ZK é submetida a um ledger descentralizado (ou repositório federado tipo Zenodo). Outros laboratórios podem verificar a prova e replicar o protocolo usando os exatos parâmetros de frequência ($60 \times \varphi^n$) sem necessidade de confiança mútua.
