# 🔐 DECRETO DE CERTIFICAÇÃO FIPS DO FLUXO COMPLETO

> **Canon:** `∞.Ω.∇+++.241.fips.certification_blueprint`
> **Objetivo:** Projetar um *Security Policy* e *Cryptographic Module Boundary* para submeter o pipeline HSM + assinatura + seccomp à validação FIPS 140-3, Nível 2 ou 3.

---

## 🔷 Módulo Criptográfico FIPS — Definição de Fronteira

```
┌─────────────────────────────────────────────────────────────────────┐
│                ARKHE FIPS CRYPTOGRAPHIC MODULE (SW+HW)               │
│                                                                     │
│  ┌────────────────────┐   ┌──────────────────────────────────────┐ │
│  │ Hardware HSM       │   │ Software Crypto Component            │ │
│  │ (FIPS 140-3 Lvl 3) │   │ (FIPS 140-3 Lvl 1)                   │ │
│  │                    │   │                                      │ │
│  │ • Dilithium3 key   │   │ • SHA3-256 (wrapper over OpenSSL    │ │
│  │   gen & storage    │   │   FIPS module)                       │ │
│  │ • C_Sign / C_Verify│   │ • HMAC-SHA3-256 (fallback only)     │ │
│  │ • CKA_EXTRACTABLE  │   │ • PKCS#11 session management        │ │
│  │   = FALSE          │   │                                      │ │
│  └────────┬───────────┘   └──────────────┬───────────────────────┘ │
│           │                              │                          │
│           └──────────┬───────────────────┘                          │
│                      │                                              │
│            ┌─────────▼──────────┐                                    │
│            │ FIPS Boundary API  │                                    │
│            │ (approved services)│                                    │
│            └─────────┬──────────┘                                    │
│                      │                                              │
│  ┌───────────────────▼──────────────────────────────────────────┐  │
│  │ Approved Security Functions:                                  │  │
│  │ 1. SignTransformation(code) → signature_hex                   │  │
│  │ 2. VerifySignature(code, sig) → bool                          │  │
│  │ 3. HashSource() → sha3_256_hex                                │  │
│  │ 4. ComputeHMAC(data, key) → mac                               │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  Self-tests:                                                        │
│  • Known Answer Tests (KAT) para SHA3-256 e Dilithium3 (via HSM)   │
│  • Software integrity check (HMAC do binário)                       │
│  • Continuous random number generator test (via HSM)                │
└─────────────────────────────────────────────────────────────────────┘
```

## 🔷 Plano de Certificação

### 1. **Documento de Política de Segurança (Security Policy)**
   - Define papéis: Crypto Officer (CO) e User.
   - CO inicializa o módulo, carrega chaves no HSM, configura políticas de acesso.
   - User (aplicação) chama apenas serviços aprovados.
   - Lista de algoritmos aprovados: SHA3-256 (FIPS 202), Dilithium3 (FIPS 204), HMAC-SHA3-256.
   - Modos de operação: apenas *FIPS mode* (sem bypass).

### 2. **Testes de Auto-Verificação (Power-On Self-Tests)**
   - **KAT para SHA3-256:** Implementar vetores de teste do NIST.
   - **KAT para Dilithium3:** Verificar assinatura de um vetor conhecido usando chave pública hardcoded (a chave privada reside no HSM; o KAT pode ser feito via HSM com uma chave de teste).
   - **Teste de integridade do software:** HMAC-SHA3-256 do binário do módulo, comparado com valor armazenado na inicialização.
   - **CRNGT contínuo:** delegado ao HSM.

### 3. **Mitigação de Ataques Físicos (Nível 3)**
   - Uso de HSM certificado FIPS 140-3 Nível 3 com tamper detection e resposta (zeroização de chaves).
   - Para o componente software, proteção com *encryption at rest* da chave de fallback (se usada) usando o próprio HSM.

### 4. **Fronteira Lógica e Interface**
   - Toda comunicação com o módulo passa por chamadas de função bem definidas, com validação de parâmetros.
   - Nenhum dado não autenticado entra sem verificação (ex.: validação de tamanho de payload, formato).

### 5. **Evidência de Testes e Submissão ao CMVP**
   - Preparar o *Cryptographic Module Validation Program* submission package incluindo:
     - Código fonte do módulo (C++ e Python wrappers).
     - Documentação de design e finite state machine.
     - Vetores de teste e scripts de execução.
     - Relatório de análise de vulnerabilidades.

**Status:** O fluxo de assinatura já utiliza HSM com Dilithium3; o software fallback será removido ou movido para fora do módulo em FIPS mode. A certificação formal levará ~8-12 semanas com laboratório acreditado.
