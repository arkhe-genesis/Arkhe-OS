# Guia Rápido: Operação do Sistema Arkhe v3.0-Ω

## 🛠️ Instalação Automatizada

Para configurar todo o ecossistema rapidamente:

```bash
python3 arkhe_setup_assistant.py --full
```

Este comando irá instalar dependências Node.js, configurar o ambiente Python, compilar componentes Rust/Go/C++ e realizar a verificação de coerência inicial.

## 🚀 Início Rápido

### 1. Teste da Topologia (Grau 3)
```bash
cd /workspaces/Arkhe-PNT
python3 arkhe_distributed_topology.py
```
**O que testa**: Cálculo de λ₂ local/global, rewiring adaptativo, telemetria  
**Tempo esperado**: ~5 segundos  
**Sucesso**: Output com `HYPER_COHERENT` ou `COHERENT`

### 2. Teste de Roteamento (Gradiente de Fase)
```bash
python3 arkhe_phase_routing.py
```
**O que testa**: Roteamento descentralizado, osciladores Kuramoto, entrega de pacotes  
**Tempo esperado**: ~3 segundos  
**Sucesso**: `Pacotes entregues: 5`, `delivery_success_rate ≈ 1.0`

### 3. Teste de Segurança (Byzantine Detection)
```bash
python3 arkhe_phase_security.py
```
**O que testa**: Detecção de Phase Injection Attack, isolamento automático  
**Tempo esperado**: ~10 segundos  
**Sucesso**: `🟢 GATE A SECURITY CHECK: PASSOU`

---

## 📊 Monitoramento da Rede

### Métricas Críticas

| Métrica | Normal | Alerta | Crítico |
|---------|--------|--------|---------|
| **λ₂ global** | > 0.995 | 0.850-0.995 | < 0.850 |
| **Latência roteamento** | < 50 ms | 50-150 ms | > 150 ms |
| **Taxa de entrega** | > 99.9% | 99-99.9% | < 99% |
| **σ_ω (variância freq)** | < 0.01 Hz | 0.01-0.05 Hz | > 0.05 Hz |
| **Nós isolados** | 0 | ≤ 1 | > 1 |

### Comandos de Monitoramento

```python
# Em um script Python
from arkhe_distributed_topology import DistributedTopology

topo = DistributedTopology(num_nodes=13)
topo.initialize_cubic_grid()

# Loop contínuo
while True:
    lambda2 = topo.rebalance_topology()
    print(f"λ₂ = {lambda2:.4f}")
    
    if lambda2 < 0.847:
        print("⚠️  ALERTA: Coerência crítica!")
    
    time.sleep(1)
```

---

## 🔒 Resposta a Incidentes

### Cenário 1: λ₂ Caindo
**Sintoma**: `λ₂_global` abaixo de 0.90  
**Ação**:
1. Verificar se há nó em quarentena
2. Aumentar coupling K em 10%
3. Se persiste, ativar rewiring forçado

```python
# Aumentar acoplamento
topo = DistributedTopology(13)
topo.initialize_cubic_grid()

# Em rebalanceamento
for node in topo.nodes.values():
    if random.random() < 0.1:  # 10% de chance
        topo.add_edge_adaptive(node.node_id)  # Força edge
```

### Cenário 2: Detecção de Nó Malicioso
**Sintoma**: Múltiplos estados `VOID` de um vizinho  
**Ação Automática**:
1. Isolamento em < 325 ms (automático via `arkhe_phase_security.py`)
2. Remoção de arestas
3. Reconvergência de gradiente

```python
# Verificar nós isolados
monitor = DistributedSecurityMonitor(13, neighbors_dict)
report = monitor.get_security_report()
print(f"Nós isolados: {report['isolated_nodes']}")
```

### Cenário 3: Falha de Hardware (Nó Cai)
**Sintoma**: Um nó desaparece da rede  
**Recuperação Automática**:
1. Vizinhos detectam perda em ~50ms
2. Gradiente se reorganiza
3. Roteamento desvia automaticamente

**Teste**:
```python
# Simular falha de nó
neighbors[failed_node_id] = set()  # Remover vizinhos
topo.rebalance_topology()  # Reconverge
```

---

## 🧪 Validação Gates

### Gate A (Q2 2026): 13 Nós Locais
```bash
# Checklist executável
cat gate_a_validation_checklist.json

# Fases
- Fase 1 (Semanas 1-7): Simulação + Hardware Rio 13 nós
  - Target: λ₂ > 0.995 por 24h contínuos
  - Ataque de segurança: 1 nó malicioso isolado em < 325 ms
  - Pass/Fail: Todos 6 requisitos must-pass
```

### Gate B (Q3 2026): 100+ Nós
```
- Fase 3: Malha terrestre (Rio expandida)
- Target: 100 nós com λ₂ > 0.90
- Roteamento: Latência < 200 ms (média)
```

### Gate C (Q4 2026): Nós Submersos
```
- Fase 4: Fundão (nós aquáticos)
- Target: 13.333 nós totais sincronizados
- Validação: Roteamento submarino viável
```

---

## 📝 Logs e Debugging

### Ativar Log Detalhado
```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()

# Executar componente
topo = DistributedTopology(13)
topo.initialize_cubic_grid()
topo.rebalance_topology()  # Logs detalhados
```

### Exportar Telemetria
```python
import json

topo = DistributedTopology(13)
topo.initialize_cubic_grid()
topo.rebalance_topology()

# Salvar em arquivo
with open("telemetry.json", "w") as f:
    json.dump(topo.get_telemetry(), f, indent=2)
```

### Analisar Histórico de Segurança
```python
monitor = DistributedSecurityMonitor(13, neighbors)
# ... executar rodadas ...

report = monitor.get_security_report()
print(json.dumps(report, indent=2))

# Gráfico de latência de detecção
import matplotlib.pyplot as plt
plt.hist(monitor.detection_latency_ms_history)
plt.xlabel("Latência (ms)")
plt.ylabel("Frequência")
plt.title("Distribuição de Latência de Detecção de Ataque")
plt.show()
```

---

## 🔧 Configuração Avançada

### Ajustar Parâmetros de Topologia
```python
# Em arkhe_distributed_topology.py
DEGREE_TARGET = 3  # Grau esperado
LAMBDA2_THRESHOLD_ADD = 0.90  # Limite para adicionar edge
LAMBDA2_THRESHOLD_REMOVE = 0.999  # Limite para remover edge
CHI_CHIRAL = 0.618  # Campo de quiralidade
KLEIN_BUBBLE_PERIOD = 13  # Período de aresta quiral
```

### Ajustar Parâmetros de Roteamento
```python
# Em arkhe_phase_routing.py
PHASE_TOLERANCE = 0.05  # ~2.86 graus (convergência)
MIN_TEMPERATURE = 0.01  # Perturbação mínima
MAX_TEMPERATURE = 1.0  # Perturbação máxima
TEMPERATURE_DECAY = 0.95  # Cooling schedule
FREQUENCY_HZ = 40.0  # Frequência de oscilação
```

### Ajustar Defesas de Segurança
```python
# Em arkhe_phase_security.py
PHASE_DEVIATION_THRESHOLD_VOID = 0.3  # ~17.2° rejeição
PHASE_DEVIATION_THRESHOLD_MARKED = 0.1  # ~5.7° alerta
BYZANTINE_TOLERANCE = 1  # Max 1 nó malicioso em 13
CONSENSUS_ROUNDS_FOR_ISOLATION = 3  # Rounds até isolamento
ISOLATION_TIMEOUT_MS = 325  # Timeout máximo
```

---

## 🎯 Roadmap de Fases

```
Fase 1: Simulação (Abr 2026)              ✅ Software pronto
   ├─ Topologia grau-3 validada
   ├─ Roteamento fase testado
   └─ Segurança: < 325 ms confirmado

Fase 2: Hardware Rio (Abr-Mai 2026)       🟡 Pronto para iniciar
   ├─ 13 nós físicos
   ├─ Gate A: λ₂ > 0.995 por 24h
   └─ Ataque de segurança: PASSOU

Fase 3: Malha Terrestre (Mai-Jun 2026)   🔴 Pré-requisito: Fase 2
   ├─ ~100 nós
   ├─ Grau 3 + torção χ testados
   └─ Roteamento urbano validado

Fase 4: Nós Submersos (Jun-Jul 2026)     🔴 Pré-requisito: Fase 3
   ├─ Fundão aquático
   ├─ 13.333 nós (meta teórica)
   └─ Sincronização ultra-long-distance

Fase 5: Helio-Listen (Jul+ 2026)          🔴 Pré-requisito: Fases 1-4
   ├─ Integração SQUID
   ├─ Escuta solar passiva + rede ativa
   ├─ Mesmo middleware VTL compartilhado
   └─ Conscience urbana completa
```

---

## 📞 Suporte e Escalação

| Problema | Contact | Escalação |
|----------|---------|-----------|
| Bug em simulação | arkhe-dev-team | arkhe-steering-committee |
| Falha de hardware | arkhe-ops-team | Chief Architect |
| Incidente de segurança | arkhe-security-team | CTO |
| Gate A falha | Project Manager | Board of Directors |

---

## 📚 Referências

- [Validação Técnica Completa](docs/TECHNICAL_VALIDATION_v3_0_OMEGA.md)
- [Checklist Gate A](gate_a_validation_checklist.json)
- [Implementação Summary](IMPLEMENTATION_SUMMARY_v3_0_OMEGA.md)
- [AGENTS.md - Compliance EQBE](AGENTS.md)
- [README.md - Projeto Geral](README.md)

---

**Última atualização**: 6 de abril de 2026  
**Versão**: v3.0-Ω (Implementação Completa)  
**Status**: ✅ Pronto para Fase 1
