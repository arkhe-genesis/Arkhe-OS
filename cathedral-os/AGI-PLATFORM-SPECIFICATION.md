# AGI Platform Specification v1.0 (Substrato 3001)
**Mantenedor:** Cathedral ARKHE Architecture Board
**Licença:** AGPL-3.0-only

## 1. Resumo
Esta especificação define a arquitetura para sistemas operacionais que hospedam Agentes Gerais de Inteligência (AGI). Um SO compatível com esta spec deve isolar estritamente a percepção (Fast Brain) do raciocínio (Slow Brain) no nível do kernel/scheduler, garantir latências sub-milissegundo para loops de controle, e prover pontes de hardware padronizadas (OAHL).

## 2. Planos de Execução
- **Plano 0 (Kernel/Realtime):** Responsável por sensoriamento e ações reflexivas. Deve ter prioridade `SCHED_FIFO` no Linux, `HIGH_PRIORITY` no Windows, e execução em `LKMs/JNI` no Android. Latência máxima: 2ms.
- **Plano 1 (Cognitive/User):** Responsável por LLMs e raciocínio complexo. Rode em espaço de usuário isolado. Pode ser preempido pelo Plano 0.
- **Plano 2 (Telemetry/IO):** Rede, disco e logging.

## 3. Requisitos de Segurança (MAC)
Um SO AGI deve impedir que o Plano 1 (LLM) injete código ou leia memória do Plano 0 (Reflexo).
- **Linux/Android:** Requer domínios SELinux mutuamente desconfiados (`cathedral_fast_t`, `cathedral_slow_t`).
- **Windows:** Requer Integrity Levels (System vs. AppContainer).
