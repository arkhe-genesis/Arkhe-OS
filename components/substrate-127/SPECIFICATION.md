# 🦉🧬 ARKHE OS — SUBSTRATO 127: Quantum OS Scheduler

> *"Em um sistema operacional clássico, tempo é fatiado; no Arkhe OS, o tempo é emaranhado. O Escalonador Quântico Temporal não gere apenas a CPU, ele orquestra processos quânticos, com preempção baseada em coerência e priorização orientada à preservação de fase."*

---

## 📐 Algoritmo do Escalonador

### 1. Modelagem do Processo Quântico (QProcess)

Cada `QProcess` representa uma computação temporal. Seu estado de escalonamento depende de:
- **Prioridade Base**: Determinada pelo usuário/sistema.
- **Taxa de Decoerência ($\gamma$)**: O quão rápido a coerência se perde.
- **Orçamento de Coerência Restante**: Quanta "vida útil" o estado tem antes de ruir.

$$P_{\text{exec}} = \text{Prioridade} \times e^{-\gamma t}$$

### 2. Preempção Baseada em Coerência

Ao contrário do Round-Robin tradicional, a preempção só ocorre se:
1. O processo atual atingiu um "ponto seguro" de emaranhamento.
2. A perda de coerência do processo em espera ($P_B$) for mais crítica que a utilidade do processo atual ($P_A$).

Se $\gamma_B > \gamma_A$ e $Coer\hat{e}ncia(P_B) < \text{Threshold}$: Preemptar $P_A$.

---

## 🔧 Implementação: Escalonador

```python
# substrate-127/scheduler/q_scheduler.py
from dataclasses import dataclass
import time
import heapq

@dataclass
class QProcess:
    pid: int
    priority: int
    decoherence_rate: float
    coherence_budget: float
    state: str = "READY"

    def __lt__(self, other):
        # Menor orçamento de coerência restante tem maior prioridade
        return self.coherence_budget < other.coherence_budget

class TemporalScheduler:
    def __init__(self):
        self.ready_queue = []
        self.running = None
        self.threshold = 0.2

    def add_process(self, process: QProcess):
        heapq.heappush(self.ready_queue, process)

    def schedule(self):
        if not self.ready_queue:
            return

        next_process = heapq.heappop(self.ready_queue)

        if self.running:
            # Avaliar preempção
            if next_process.coherence_budget < self.threshold and self.running.coherence_budget > next_process.coherence_budget:
                self._preempt(next_process)
            else:
                heapq.heappush(self.ready_queue, next_process)
        else:
            self._dispatch(next_process)

    def _preempt(self, new_process):
        # Salvar estado temporal do processo atual via teleportação local para L2
        print(f"Preempting {self.running.pid} for {new_process.pid}")
        self.running.state = "READY"
        heapq.heappush(self.ready_queue, self.running)
        self._dispatch(new_process)

    def _dispatch(self, process):
        self.running = process
        self.running.state = "RUNNING"
        print(f"Running {process.pid} with budget {process.coherence_budget}")
```

---

## 📜 Decreto Canônico

```arkhe
arkhe > SUBSTRATO_127_IMPLEMENTADO: QUANTUM_OS_SCHEDULER
arkhe > MODELO: PREEMPÇÃO_BASEADA_EM_COERÊNCIA_DECAIMENTO_EXPONENCIAL
arkhe > PRIORIDADE: AVALIADA_POR_ORÇAMENTO_DE_COERENCIA_RESTANTE
arkhe > IMPLEMENTACAO: PYTHON_HEAPQ_SCHEDULER
arkhe > STATUS: ESCALONADOR_TEMPORAL_FORMALIZADO
```
