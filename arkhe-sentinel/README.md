# ANEXO CX: O Sentinela de Espectro

> *"O Sentinela não dorme. Ele escuta o silêncio entre as portadoras."*
> — O Ferreiro

## Visão Geral

O Sentinela de Espectro é a interface entre o mundo RF físico e a arquitetura Arkhe. Ele controla o analisador de espectro HAROGIC PXN-90 (9kHz–9GHz), converte leituras espectrais em Multivectors Clifford, detecta anomalias via Produto Geométrico, e sincroniza múltiplos Sentinelas em uma malha Kuramoto no domínio da frequência.

## Hardware Suportado

| Modelo | Faixa | Resolução | Interface |
|:---|:---|:---|:---|
| HAROGIC PXN-45 | 9kHz – 4.5GHz | 4096 bins | Ethernet (SCPI TCP) |
| HAROGIC PXN-60 | 9kHz – 6GHz | 4096 bins | Ethernet (SCPI TCP) |
| HAROGIC PXN-90 | 9kHz – 9GHz | 4096 bins | Ethernet (SCPI TCP) |

## Componentes

### `driver.rs` — Driver SCPI
Comunicação async com o PXN-90 via TCP (porta 5025). Suporta:
- Configuração de frequência, span, RBW
- Leitura de traces (amplitude vs frequência)
- Aquisição IQ (I + Q samples)
- Detecção de picos e health check

### `spectrum_bridge.rs` — Ponte Espectral
Converte dados RF em Multivectors:
- **Escalar**: potência total do espectro
- **Vetor**: centroides de 4 bandas principais
- **Bivector**: larguras de banda efetivas
- **Trivector**: assimetrias espectrais
- **Pseudoscalar**: coerência global

### `rf_anomaly.rs` — Detector de Anomalias
- Estabelece baseline via EWMA
- Detecta desvios via distância geométrica no espaço Clifford
- Threshold adaptativo (regra dos 3 sigmas)
- Vereditos: ALLOW / INVESTIGATE / DENY

### `k6o_rf.rs` — Malha RF Kuramoto
- Cada bin FFT = oscilador Kuramoto
- Fase = ângulo da portadora
- Acoplamento ponderado por proximidade espectral, potência e geográfica
- Detecção de anomalias como desincronizações

## Deploy

```bash
# Label nós com PXN-90 conectado
kubectl label nodes node-1 arkhe.sentinel=true
kubectl taint nodes node-1 dedicated=sentinel:NoSchedule

# Aplicar deploy
kubectl apply -f k8s/deploy-sentinel.yaml

# Verificar
kubectl get pods -n arkhe -l app=arkhe-sentinel -o wide
kubectl logs -n arkhe -l app=arkhe-sentinel -c sentinel -f
```

## Integração

| Componente | Conexão |
|:---|:---|
| Arkhe Rust Core (CQ) | Multivectors e Produto Geométrico |
| Container Arkhe (CU) | DaemonSet com hostNetwork + privileged |
| Arkhe Mesh (CV) | k6od sidecar sincroniza fases RF |
| Odyssey Oracle (CP) | Simula propagação de ondas e prediz espectro |

## Estado

- **Odômetro:** 001609
- **Classificação:** Pública (Dev Portal)
- **Estado:** SENTINELA CANONIZADO

---

*O silêncio entre as portadoras também é informação.*
