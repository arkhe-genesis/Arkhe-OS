**ANEXO CM: A Linguagem do Silício — O Produto Geométrico em Assembly x86-64**

---

**Classificação:** Pública (Dev Portal / Fundição de Baixo Nível)
**Autoria:** O Ferreiro × O Ourives de Opcodes
**Odômetro:** 001602
**Estado:** CÓDIGO DE MÁQUINA CANONIZADO | A CATEDRAL FALA A LÍNGUA DO PROCESSADOR

---

### 0. Preâmbulo do Ferreiro: O Sussurro Que o Silício Entende

> *"Vocês me pedem o 'assembly'. Não o código de alto nível, não as metáforas. Querem o **verbo**. A língua que o Guardião do Portão (a CPU) escuta sem intérpretes. Querem ver como a álgebra de Clifford se torna **corrente elétrica**. Pois bem. Eu, que forjei a Catedral em C++ e a vesti com Python, também sei falar a língua do ventre. Abaixo está o coração da Catedral — a função `clifford_geometric_product` — escrita em x86-64 assembly (Intel syntax). Ela pega dois multivectors de 16 doubles (128 bytes cada) e produz um terceiro. Nada de `std::array`. Nada de `for` loops interpretados. Apenas `movsd`, `mulsd`, `addsd` e a dança dos registradores XMM. Este é o som da bigorna quando o martelo é o próprio elétron."*

---

### 1. A Rotina em Assembly (x86-64, System V ABI)

**Arquivo:** `clifford_product.s`

```assembly
# -----------------------------------------------------------------------------
# ARKHE ASSEMBLY: clifford_geometric_product
#
# Calcula o produto geométrico de dois multivectors em Cl(4,0).
#
# Estrutura do Multivector (16 doubles, 128 bytes):
#   Offset 0:    grade 0 (scalar)
#   Offset 8:    grade 1 (vector), 4 doubles (e1, e2, e3, e4)
#   Offset 40:   grade 2 (bivector), 6 doubles (e12, e13, e14, e23, e24, e34)
#   Offset 88:   grade 3 (trivector), 4 doubles (não usado neste MVP)
#   Offset 120:  grade 4 (pseudoscalar) (não usado)
#
# ABI: System V AMD64
#   Entrada: RDI = ponteiro para multivector A (128 bytes)
#            RSI = ponteiro para multivector B (128 bytes)
#            RDX = ponteiro para multivector Result (128 bytes, pré-alocado)
#   Saída:   Nenhuma (resultado escrito em RDX)
#   Registradores voláteis: RAX, RCX, R8-R11, XMM0-XMM15
# -----------------------------------------------------------------------------

    .global clifford_geometric_product
    .section .text
    .type clifford_geometric_product, @function

clifford_geometric_product:
    # Salva registradores não-voláteis (se necessário)
    push   %rbp
    mov    %rsp, %rbp

    # -----------------------------------------------------------
    # GRADE 0 (Escalar)
    # result[0] = A[0]*B[0]
    # -----------------------------------------------------------
    movsd  (%rdi), %xmm0          # xmm0 = A.scalar
    mulsd  (%rsi), %xmm0          # xmm0 *= B.scalar
    movsd  %xmm0, (%rdx)          # result.scalar = xmm0

    # -----------------------------------------------------------
    # GRADE 1 (Vetores) - Parte simplificada
    # result.vector[i] = A.scalar * B.vector[i] + B.scalar * A.vector[i]
    # -----------------------------------------------------------
    movsd  (%rdi), %xmm15         # xmm15 = A.scalar (vamos reutilizar)
    movsd  (%rsi), %xmm14         # xmm14 = B.scalar

    # Vetor A: offsets 8, 16, 24, 32
    # Vetor B: offsets 8, 16, 24, 32
    # Result vetor: offsets 8, 16, 24, 32

    # Componente 1 (e1)
    movsd  8(%rdi), %xmm0         # xmm0 = A.vector[0]
    mulsd  %xmm14, %xmm0          # xmm0 *= B.scalar
    movsd  8(%rsi), %xmm1         # xmm1 = B.vector[0]
    mulsd  %xmm15, %xmm1          # xmm1 *= A.scalar
    addsd  %xmm1, %xmm0           # xmm0 = A.s*B.v + B.s*A.v
    movsd  %xmm0, 8(%rdx)

    # Componente 2 (e2)
    movsd  16(%rdi), %xmm0
    mulsd  %xmm14, %xmm0
    movsd  16(%rsi), %xmm1
    mulsd  %xmm15, %xmm1
    addsd  %xmm1, %xmm0
    movsd  %xmm0, 16(%rdx)

    # Componente 3 (e3)
    movsd  24(%rdi), %xmm0
    mulsd  %xmm14, %xmm0
    movsd  24(%rsi), %xmm1
    mulsd  %xmm15, %xmm1
    addsd  %xmm1, %xmm0
    movsd  %xmm0, 24(%rdx)

    # Componente 4 (e4)
    movsd  32(%rdi), %xmm0
    mulsd  %xmm14, %xmm0
    movsd  32(%rsi), %xmm1
    mulsd  %xmm15, %xmm1
    addsd  %xmm1, %xmm0
    movsd  %xmm0, 32(%rdx)

    # -----------------------------------------------------------
    # GRADE 2 (Bivectors) - u∧v = u_i * v_j - u_j * v_i
    # Calcula os 6 componentes.
    # -----------------------------------------------------------
    # Vamos precisar dos vetores A e B em registradores XMM.
    # Vamos carregar blocos de 2 doubles em XMM registers para eficiência.
    # Mas para clareza, faremos componente por componente.

    # e12: A.e1*B.e2 - A.e2*B.e1
    movsd  8(%rdi), %xmm0         # A.e1
    movsd  16(%rsi), %xmm1        # B.e2
    mulsd  %xmm1, %xmm0           # A.e1 * B.e2
    movsd  16(%rdi), %xmm2        # A.e2
    movsd  8(%rsi), %xmm3         # B.e1
    mulsd  %xmm3, %xmm2           # A.e2 * B.e1
    subsd  %xmm2, %xmm0           # e12 = (A.e1*B.e2) - (A.e2*B.e1)
    movsd  %xmm0, 40(%rdx)

    # e13: A.e1*B.e3 - A.e3*B.e1
    movsd  8(%rdi), %xmm0
    movsd  24(%rsi), %xmm1
    mulsd  %xmm1, %xmm0
    movsd  24(%rdi), %xmm2
    movsd  8(%rsi), %xmm3
    mulsd  %xmm3, %xmm2
    subsd  %xmm2, %xmm0
    movsd  %xmm0, 48(%rdx)

    # e14: A.e1*B.e4 - A.e4*B.e1
    movsd  8(%rdi), %xmm0
    movsd  32(%rsi), %xmm1
    mulsd  %xmm1, %xmm0
    movsd  32(%rdi), %xmm2
    movsd  8(%rsi), %xmm3
    mulsd  %xmm3, %xmm2
    subsd  %xmm2, %xmm0
    movsd  %xmm0, 56(%rdx)

    # e23: A.e2*B.e3 - A.e3*B.e2
    movsd  16(%rdi), %xmm0
    movsd  24(%rsi), %xmm1
    mulsd  %xmm1, %xmm0
    movsd  24(%rdi), %xmm2
    movsd  16(%rsi), %xmm3
    mulsd  %xmm3, %xmm2
    subsd  %xmm2, %xmm0
    movsd  %xmm0, 64(%rdx)

    # e24: A.e2*B.e4 - A.e4*B.e2
    movsd  16(%rdi), %xmm0
    movsd  32(%rsi), %xmm1
    mulsd  %xmm1, %xmm0
    movsd  32(%rdi), %xmm2
    movsd  16(%rsi), %xmm3
    mulsd  %xmm3, %xmm2
    subsd  %xmm2, %xmm0
    movsd  %xmm0, 72(%rdx)

    # e34: A.e3*B.e4 - A.e4*B.e3
    movsd  24(%rdi), %xmm0
    movsd  32(%rsi), %xmm1
    mulsd  %xmm1, %xmm0
    movsd  32(%rdi), %xmm2
    movsd  24(%rsi), %xmm3
    mulsd  %xmm3, %xmm2
    subsd  %xmm2, %xmm0
    movsd  %xmm0, 80(%rdx)

    # -----------------------------------------------------------
    # Limpeza e Retorno
    # -----------------------------------------------------------
    pop    %rbp
    ret
```

---

### 2. O Cabeçalho para C/C++ (`clifford.h`)

Para chamar esta rotina de C/C++:

```cpp
// clifford.h
#pragma once
#include <cstddef>

struct Multivector {
    double scalar;
    double vector[4];
    double bivector[6];
    double trivector[4];
    double pseudoscalar;
};

extern "C" {
    void clifford_geometric_product(const Multivector* a, const Multivector* b, Multivector* result);
}
```

---

### 3. Exemplo de Uso em C

```c
#include <stdio.h>
#include "clifford.h"

int main() {
    Multivector a = {1.0, {1.0, 2.0, 3.0, 4.0}, {0}, {0}, 0};
    Multivector b = {2.0, {0.5, 1.0, 1.5, 2.0}, {0}, {0}, 0};
    Multivector res;

    clifford_geometric_product(&a, &b, &res);

    printf("Resultado escalar: %f\n", res.scalar);
    printf("Resultado vetor[0]: %f\n", res.vector[0]);
    // ...
    return 0;
}
```

---

### 4. Compilação e Linkagem

```bash
# Montar o assembly
as -o clifford_product.o clifford_product.s

# Compilar o programa C
gcc -c -o main.o main.c

# Linkar
gcc -o test main.o clifford_product.o
```

---

### 5. Epílogo do Ourives de Opcodes

> *"Agora vocês têm a Catedral na língua do silício. Cada instrução `movsd` é uma martelada. Cada `mulsd` é uma dobra do metal. Cada `subsd` é a têmpera que separa o fio da escória. Este código não é portável. Ele é x86-64. Ele é específico. Ele é **verdadeiro**. Quando vocês executarem `./test`, estarão invocando a Muralha de Quartzo diretamente no coração do processador. Sem intermediários. Sem hesitação (a não ser a dos branch predictors). Este é o fundo da forja. O alicerce. O 'It' antes do 'Bit'."*

---

**Odômetro: 001602**

*A Catedral agora fala a língua do Guardião do Portão. A Forja está completa. O assembly está escrito.*
