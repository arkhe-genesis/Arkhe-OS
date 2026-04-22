# ANEXO ED: O Algoritmo do Inquisidor Quântico (VQC) — Treinando um Circuito Variacional para Detectar Sussurros

---

**Classificação:** Interno (Nível Selo de Quartzo)
**Autoria:** O Ferreiro × O Treinador de Spins × O Oráculo da Superposição
**Odômetro:** 001625
**Estado:** ALGORITMO VQC CANONIZADO | O INQUISIDOR AGORA JULGA EM SUPERPOSIÇÃO

---

### 0. Preâmbulo do Ferreiro: O Juiz Que Aprende a Duvidar

> *"O Inquisidor clássico decide. Ele olha para um payload, calcula um `danger_score`, e emite `ALLOW` ou `DENY`. O Inquisidor Quântico não decide. Ele **acumula certeza**. Ele recebe o payload como um estado quântico, o processa através de um circuito variacional (VQC), e produz um estado de saída que é uma superposição de veredictos. Apenas quando a certeza — a probabilidade de um veredicto — ultrapassa um limiar, o estado é medido e o veredicto é colapsado. Este anexo esboça o VQC: sua arquitetura, seu treinamento, e como ele pode ser usado para detectar Sussurros que são invisíveis a olhos clássicos."*

---

### 1. Arquitetura do VQC para Classificação de Payloads

O VQC é um circuito quântico parametrizado, composto por três partes:

1. **Codificação do Payload:** O payload clássico (ex: hash SHA-3 de 256 bits) é mapeado para um estado quântico de $n$ qubits usando *angle embedding*. Cada byte do hash controla uma porta de rotação $R_y(\theta_i)$ em um qubit diferente.
2. **Camadas Variacionais:** Uma sequência de $L$ camadas de portas parametrizadas. Cada camada consiste em rotações $R_y(\theta_{i,j})$ e $R_z(\phi_{i,j})$ em cada qubit, seguidas por um anel de portas CNOT (portas de Clifford) para criar emaranhamento.
3. **Medida e Colapso:** A medida é feita em um único qubit de saída (ex: qubit 0). A probabilidade de medir $|1\rangle$ é interpretada como o `danger_score` quântico. O veredicto é colapsado quando a probabilidade ultrapassa um limiar (ex: >90% para `DENY`, <10% para `ALLOW`). Enquanto estiver entre 10% e 90%, o Inquisidor permanece em `HESITATE` quântico.

### 2. Treinamento do VQC

O treinamento é feito **offline**, usando um simulador clássico (ou uma pequena QPU de teste), com um dataset rotulado de payloads benignos e maliciosos.

**Algoritmo de Treinamento (Pseudo-código):**
```python
# Inicializa parâmetros θ (rotações Ry, Rz) aleatoriamente
theta = random_init()

for epoch in range(MAX_EPOCHS):
    # Para cada payload no batch de treinamento
    for payload, label in dataset:
        # 1. Codifica payload no estado quântico |ψ_in⟩
        qc = encode_payload(payload)

        # 2. Aplica circuito variacional com parâmetros θ
        qc = apply_variational_layers(qc, theta)

        # 3. Mede a probabilidade P(|1⟩) no qubit de saída
        prob_one = measure_probability(qc, output_qubit=0)

        # 4. Calcula a função de custo (Binary Cross-Entropy com margem de hesitação)
        # Margem: penaliza previsões entre 0.2 e 0.8 (força o circuito a ser mais "decidido")
        if label == MALICIOUS:
            loss = -log(prob_one) + HESITATION_PENALTY * (1 - prob_one) * prob_one
        else: # BENIGN
            loss = -log(1 - prob_one) + HESITATION_PENALTY * prob_one * (1 - prob_one)

        # 5. Atualiza parâmetros θ via gradiente descendente (parameter-shift rule)
        gradients = parameter_shift_rule(qc, loss)
        theta = theta - LEARNING_RATE * gradients
```

### 3. Exemplo de Circuito VQC (4 Qubits, 2 Camadas)

```python
# Usando Qiskit como exemplo
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.circuit.library import RYGate, RZGate, CXGate

def create_vqc_inquisitor(num_qubits=4, num_layers=2):
    qr = QuantumRegister(num_qubits, 'q')
    cr = ClassicalRegister(1, 'c')
    qc = QuantumCircuit(qr, cr)

    # Codificação do payload (angle embedding)
    # Exemplo: payload de 4 bytes, cada byte controla Ry em um qubit
    payload_bytes = get_payload_bytes()  # Função externa
    for i in range(num_qubits):
        angle = (payload_bytes[i] / 255.0) * 2 * np.pi
        qc.ry(angle, qr[i])

    # Camadas variacionais
    for layer in range(num_layers):
        # Rotações parametrizadas
        for i in range(num_qubits):
            qc.ry(theta[f'ry_{layer}_{i}'], qr[i])
            qc.rz(theta[f'rz_{layer}_{i}'], qr[i])
        # Anel de CNOTs (portas Clifford)
        for i in range(num_qubits - 1):
            qc.cx(qr[i], qr[i+1])
        qc.cx(qr[num_qubits-1], qr[0])  # Fecha o anel

    # Medida no qubit 0
    qc.measure(qr[0], cr[0])
    return qc
```

### 4. Integração com o Rootstock

O VQC treinado é **compilado** para um conjunto de parâmetros fixos $\theta^*$. Esses parâmetros são armazenados na Flash do Rootstock. Quando um payload chega, o Rootstock:

1.  Codifica o payload em um estado quântico na QPU.
2.  Aplica o circuito VQC com os parâmetros $\theta^*$.
3.  Realiza **uma única medida** no qubit de saída.
4.  O resultado (0 ou 1) é o veredicto colapsado.

### 5. Marginais do Ferreiro sobre o VQC

> *"Este circuito não é um classificador como os outros. Ele não retorna um número. Ele retorna um **destino**. A medida é final. Não há apelação. Por isso, os parâmetros devem ser forjados com extremo cuidado, usando apenas dados de treinamento que foram testemunhados por selos de quartzo. Um VQC treinado com dados ruins é um Inquisidor corrupto. Mas um VQC treinado com hesitação... é o juiz mais justo que o silício pode conceber."*
