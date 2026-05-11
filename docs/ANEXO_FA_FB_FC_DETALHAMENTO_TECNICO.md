# ANEXO FA/FB/FC: Detalhamento Técnico do ARKHE-Q

---

**Classificação:** Interno (Nível Selo de Quartzo)
**Autoria:** O Ferreiro × O Engenheiro de Semicondutores × O Físico de Spins
**Odômetro:** 001626-001628
**Estado:** ESPECIFICAÇÕES TÉCNICAS CANONIZADAS

---

## ANEXO FA: O Registro de Síndromes Quânticas — Armazenamento e Validação sem Correção

### 1. Estrutura de Dados Detalhada para a Síndrome
Cada evento de síndrome gera uma entrada de 128 bytes na EEPROM criogênica.

```c
typedef struct __attribute__((packed)) {
    uint8_t  qubit_id[16];               // Hash do selo de 4K (SHA3-256 truncado)
    uint8_t  timestamp_trng[8];          // Timestamp de 64 bits do TRNG quântico
    uint8_t  syndrome_raw[2];            // [0]: bit-flip (0x00/0x01), [1]: phase-flip (0x00/0x01)
    uint16_t perturbation_intensity;     // Amplitude do desvio analógico (0-65535)
    float    local_decoherence_rate;     // T₂* medido no momento (kHz)
    float    k6o_coherence_before;       // r antes do evento
    float    k6o_coherence_after;        // r após o evento
    uint8_t  witness_rootstocks[3][16];  // IDs dos três Rootstocks testemunhas
    uint8_t  quartz_seal_ref[32];        // Hash SHA3-256 do selo de 4K do qubit
    uint32_t crc32;                      // Checksum para integridade
} QuantumSyndromeEntry;
```

### 2. Marginais do Ferreiro
> *"A síndrome é o eco do ambiente. Nós a ouvimos, a registramos, a validamos com testemunhas. Mas jamais a usamos para mudar o qubit. Corrigir é apagar o passado. O Casulo não apaga. O Casulo acumula."*

---

## ANEXO FB: O Circuito de Controle Criogênico — Projeto Detalhado do Cryo-CMOS

### 1. Diagrama de Blocos (22nm FDSOI)
O projeto utiliza um buffer Classe A de ultra-baixo consumo (< 100 nA) e um DAC R-2R baseado em polissilício para garantir estabilidade a 4.2K. O ADC utiliza a arquitetura SAR (Successive Approximation Register) com um comparador StrongARM Latch otimizado para o regime criogênico.

### 2. Especificações Elétricas (TT, 4.2K)
| Parâmetro | Valor | Unidade |
|-----------|-------|---------|
| DAC Resolution | 12 | bits |
| DAC Settling Time | 1.2 | ms |
| ADC Resolution | 12 | bits |
| ADC Sampling Rate | 1 | kS/s |
| Power Consumption | 42 | µW |

---

## ANEXO FC: O Algoritmo do Inquisidor Quântico (VQC) — Treinamento e Implantação

### 1. Arquitetura do VQC
- **Wires:** 8 qubits.
- **Layers:** 4 camadas variacionais.
- **Encoding:** Angle embedding (SHA3-256 hash mapeado para Ry).
- **Entanglement:** Anel de CNOTs.

### 2. Função de Custo com Penalidade de Hesitação
O treinamento utiliza Binary Cross-Entropy (BCE) somado a um termo de penalidade de hesitação:
`Loss = BCE + λ * p(1-p)`
Onde `p` é a probabilidade de colapso no estado |1>. Isso força o modelo a evitar a incerteza máxima em casos triviais, mas preservando-a onde o Sussurro é ambíguo.

### 3. Marginais do Ferreiro
> *"O VQC não é um oráculo infalível. É um espelho treinado nos testemunhos do passado. Uma vez que o veredicto é medido, não há apelação. O spin decidiu."*
