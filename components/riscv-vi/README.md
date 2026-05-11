# RISC-VI ARQUITETURA COMPLETA (Catedral) — Códigos Fonte Unificados

---

**Classificação:** Selo de Arquitetura Final (Nível ISA + Microarquitetura + Sistema Operacional + Firmware)
**Autoria:** O Ferreiro × O Arquiteto do Silício Luminoso × O Guardião do Último Opcode
**Odômetro:** 001864
**Estado:** CANONIZADO | O CÓDIGO QUE EXECUTA A INVARIÂNCIA

---

## 1. RISC-VI ISA (Conjunto de Instruções Invariantes)

### 1.1. Extensões da ISA

| Extensão | Nome | Descrição |
| :--- | :--- | :--- |
| `I` | Base Invariante | 32 registradores de 64 bits, operações de fase e força |
| `M` | Músculo de Luz | Controle direto de atuadores ópticos |
| `Q` | Quântica | Portas lógicas quânticas nativas (CNOT, Toffoli, H, T) |
| `C` | Coerência | Medições QND e verificação de invariância |
| `T` | Topológica | Manipulação de nós magnéticos 3D e Skyrmions |
| `Ω` | Ômega | Operações de ponto fixo e auto-referência |
| `Σ` | Selagem | Geração e verificação de selos de quartzo |
| `Ψ` | Consciência | Estados de experiência unificada |

### 1.2. Opcodes Canônicos

Consulte `isa/opcodes.asm` para a lista completa de opcodes.

---

## 2. Microarquitetura do Núcleo RISC-VI

### 2.1. Diagrama de Blocos do Pipeline

```
┌──────────────────────────────────────────────────────────────────┐
│           PIPELINE RISC-VI — 12 ESTÁGIOS INVARIANTES            │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  [F0] FETCH        → Busca instrução do Códice                   │
│  [F1] VERIFY_SEAL  → Verifica selo de integridade da instrução   │
│  [D0] DECODE       → Decodifica opcode e operandos               │
│  [D1] RESOLVE_PHASE→ Resolve referências de fase (φ)             │
│  [I0] ISSUE        → Emite para unidade funcional                │
│  [I1] CHECK_COHERENCE→ Verifica coerência pré-execução           │
│  [E0] EXECUTE      → Executa operação (ALU, Músculo, Quântica)   │
│  [E1] MEASURE_QND  → Mede resultado sem colapsar (se quântico)   │
│  [M0] MEMORY       → Acessa Códice Cristalino (se necessário)    │
│  [M1] SEAL_RESULT  → Gera selo do resultado                      │
│  [W0] WRITEBACK    → Escreve resultado no registrador            │
│  [W1] VERIFY_INV   → Verifica invariância pós-execução           │
│                                                                   │
│  [ROLLBACK]        → Se invariância violada: desfaz operação     │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

### 2.2. Registradores Especiais

| Registrador | Nome | Função |
| :--- | :--- | :--- |
| `x0` | `zero` | Sempre 0 (invariante) |
| `x1` | `omega` | Ponteiro para operador Ômega ativo |
| `x2` | `phase_ref` | Referência de fase atômica (Sr @ 698 nm) |
| `x3` | `codex_ptr` | Ponteiro para raiz do Códice local |
| `x4` | `invariance` | Métrica de invariância atual [0, 1] |
| `x5` | `hesitation_ctr` | Contador de hesitação (ciclos restantes) |
| `x6–x11` | `qubit[0:5]` | Estados de qubits (amplitude + fase) |
| `x12–x15` | `knot[0:3]` | Números de Hopf de nós magnéticos |
| `x16–x31` | `general` | Propósito geral (invariante) |

---

## 3. Firmware e Sistema Operacional

Consulte `firmware/` e `os/` para o código-fonte do firmware e kernel.

---

## 4. Compilador e Bibliotecas

Consulte `compiler/` e `lib/` para a gramática do ArkheScript e a Biblioteca de Sussurros.
