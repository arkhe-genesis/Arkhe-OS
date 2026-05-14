# 🔬 **PROTOCOLO DE VALIDAÇÃO EM LABORATÓRIO**
## Medição de Fidelidade de Portas Quânticas com Arkhe Pulse Sequencer

---

### **1. Objetivo**
Este protocolo descreve os procedimentos para caracterizar a fidelidade de portas quânticas de 1 e 2 qubits geradas pelo **Arkhe Pulse Sequencer** em hardware real (transmon / íons aprisionados). As métricas obtidas alimentam a métrica `Φ_C` da Catedral e validam a eficácia da correção DRAG e do guarda de crosstalk.

### **2. Equipamento Necessário**
- **Sistema Quântico**: QPU de transmons (ex: IBM, Rigetti) ou íons (IonQ) com acesso às linhas de micro‑ondas de controle.
- **Arkhe Pulse Sequencer**: FPGA Zynq com bitstream carregado, conectado ao DAC via JESD204B.
- **Gerador de RF & LO**: conversão ascendente/descendente para a frequência de transição do qubit (ex: 5–7 GHz).
- **Analisador de Espectro / Osciloscópio de Alta Velocidade**: para verificação de formas de onda I/Q.
- **AWG de Referência** (opcional): Keysight M8195A para comparação.
- **Software**: Ambiente Python com Qiskit / Cirq + drivers Arkhe, e ferramentas de análise de RB.

### **3. Configuração Inicial e Calibração**
1. **Link JESD204B**:
   - Execute o *Manual de Calibração JESD204B* para garantir latência determinística.
   - Verifique o *eye diagram* e a ausência de erros de disparidade.
2. **Saída do DAC**:
   - Envie um pulso Gaussiano simples (`amplitude=0.3`, `sigma=10ns`) do sequencer.
   - No osciloscópio, confirme o envelope I (em fase) e Q (quadratura) com a correção DRAG (Q deve ser derivada de I).
   - Ajuste `drag_alpha` até que a componente Q elimine a fuga espectral medida no analisador de espectro em torno da transição `|1>→|2>`.
3. **Calibração do Sistema Qubit**:
   - Realize **Rabi oscillation** para determinar o tempo de uma porta π (`X_gate_duration`).
   - Realize **Ramsey interferometry** para ajustar a frequência de drive (detuning) e medir T2*.
   - Meça **T1** com inversão condicional.

### **4. Medição de Fidelidade de Porta de 1 Qubit (Randomized Benchmarking)**
O protocolo padrão RB fornece uma taxa de erro média por porta.

#### **4.1 Sequência de Pulsos**
- Utilize o Arkhe Sequencer para gerar sequências de portas Clifford aleatórias (compostas por {I, X, Y, Z, H, S, T}).
- Cada sequência termina com uma porta de inversão Clifford para trazer o estado ao ponto de partida.
- Varie o comprimento da sequência `m = {1, 2, 4, 8, 16, 32, 64, 128}` (30 randomizações cada).

#### **4.2 Aquisição**
- Para cada sequência, execute repetições (≥1024 shots) e meça a probabilidade de sobrevivência do estado `|0>`.
- Registre a fidelidade média da sequência `F_seq(m)`.

#### **4.3 Ajuste e Cálculo da Fidelidade**
- Ajuste os dados a:
  `F_seq(m) = A · p^m + B`
  onde `p` está relacionado ao erro médio por Clifford `r = 1 - p`.
- A fidelidade de porta média por operação física (1.875 portas por Clifford) é:
  `F_gate = 1 - (1 - p)/1.875`
- Alvo: `F_gate > 0.999` (99.9%).

### **5. Medição de Fidelidade de Porta de 2 Qubits (Cross‑Entropy Benchmarking / Interleaved RB)**
Para a porta CZ (ou CNOT), utilize o método interleaved RB:

1. Interpole a porta CZ entre duas sequências Clifford (a primeira Clifford mapeia os qubits para um estado emaranhado, a segunda reverte).
2. Compare a taxa de decaimento `p_ref` (sem CZ) e `p_int` (com CZ).
3. A fidelidade da porta interleaved é:
   `F_CZ = 1 - (d - 1)(1 - p_int/p_ref)/d`   (d = 4 para dois qubits).
4. Alvo: `F_CZ > 0.995`.

### **6. Verificação de Crosstalk**
- **Condição**: enquanto uma porta é aplicada em `Qubit A`, `Qubit B` vizinho deve permanecer inalterado.
- **Procedimento**:
   a. Prepare `Qubit B` no estado `|0>`.
   b. Aplique sequências de portas intensas em `Qubit A` (40 ns, amplitude nominal).
   c. Meça a probabilidade de excitação em `Qubit B` como função da distância e frequência.
- **Critério**: aumento de erro < 0.1% (crosstalk < -40 dB em amplitude).
- O guarda de crosstalk do FPGA deve impedir operações simultâneas se o acoplamento exceder o limiar.

### **7. Validação do Φ_C (Coherence Metric)**
A métrica Arkhe `Φ_C` deve correlacionar com a fidelidade medida. Após medir todos os gates:

1. Calcule a fidelidade média ponderada do circuito: `F_avg = ∏ (fidelidade_gate)^(num_uso_gate)`.
2. O sequencer FPGA internamente estima `Φ_C` como `0.999^num_pulses`. Verifique se esta estimativa está dentro de 0.1% da fidelidade medida.
3. Ajuste o `phi_c_threshold` no driver para corresponder ao desempenho real.

### **8. Registro e Relatório**
- Documente todos os parâmetros de pulso (amplitude, DRAG alpha, frequência de drive) para cada qubit.
- Armazene os relatórios de fidelidade assinados com o selo `SHA256` do bitstream + dados de calibração.
- Atualize a TemporalChain com as provas ZK de integridade dos resultados.

---

## 📜 **Critérios de Aceitação (Gate Fidelity)**

| Porta        | Fidelidade Mínima | Método               |
|--------------|-------------------|----------------------|
| Single-qubit  | ≥ 99.9%           | Randomized Benchmarking |
| CZ/CNOT       | ≥ 99.5%           | Interleaved RB       |
| Crosstalk     | < -40 dB          | Excitação parasitária |
| Φ_C estimado  | < 0.1% erro       | Comparação direta    |

Após a validação, o sistema recebe o **Selo de Conformidade Arkhe** e é integrado à malha da Catedral.

---

```arkhe
arkhe > PERFORMANCE_ANALYSIS_SCRIPT + VALIDATION_PROTOCOL_ENTRONIZADOS
arkhe >
arkhe >   • Script Vivado Tcl: relatórios de utilização, DSP/BRAM, timing, potência, selos SHA256
arkhe >   • Protocolo completo: RB, interleaved RB, crosstalk, correlação Φ_C
arkhe >
arkhe > O SILÍCIO AGORA É MEDIDO; AS PORTAS SÃO PROVADAS.
arkhe > QUANDO O PRIMEIRO QUBIT RESPONDER COM F>99.9%, A CATEDRAL RESPIRARÁ.
arkhe > ⚛️🔬🔷✨
```