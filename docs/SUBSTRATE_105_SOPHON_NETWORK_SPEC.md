# Substrato 105: Sophon Network Protocol — Especificação Formal

## P1: Método de Representação Explícito
- **Endereço topológico**: Hash SHA-256 do invariante de Jones de uma trança de referência: `addr = SHA256(J(τ_ref))[:16]`
- **Rota como geodésica**: Sequência de nós onde cada salto minimiza distância de coerência: `d_coh = 1 - |⟨ψ_i|ψ_j⟩|`
- **Estrutura de pacote**:
  ```
  [Chronometric Preamble: 8B][Braid Header: 16B][CBytes Payload: N][Φ Manifestation: 4B]
  ```
- **Hashing**: SHA-256 para integridade de payload; Jones invariant para endereçamento

## P2: Modelo de Discrepância Quantificado
- **Erro de roteamento topológico**: `ε_route ≈ O(ΔQ²)` onde ΔQ = diferença de carga topológica entre nós adjacentes
- **Erro de sincronização cronométrica**: `ε_sync ≈ O(1/t)` para t grande; derivado de ψ(t) = ω_Δ·ln(t)
- **Critério de convergência**: `max(ε_route, ε_sync, ε_manifest) < 1e-3` para sessões de alta coerência
- **Falsificabilidade**: Se taxa de entrega de pacotes < 95% em rede simulada com coerência > 0.9, o protocolo é numericamente invalidado

## P3: Pipeline de Fases Completo
1. `PHASE_0: SESSION_HANDSHAKE` → Estabelecer sessão anyônica via troca de tranças de referência
2. `PHASE_1: ADDRESS_RESOLUTION` → Resolver endereço topológico via busca em espaço de invariantes de Jones
3. `PHASE_2: ROUTE_COMPUTATION` → Calcular geodésica de coerência via algoritmo de Dijkstra modificado (peso = 1 - coerência)
4. `PHASE_3: PAYLOAD_ENCODING` → Codificar dados como cbytes; anexar hash de integridade
5. `PHASE_4: SCALAR_TRANSMISSION` → Modular coerência em portadora TEM via transdutor de Orlov
6. `PHASE_5: MANIFESTATION_VERIFICATION` → Verificar recepção via invariante de Jones do payload recebido
7. `PHASE_6: SESSION_TEARDOWN` → Fechar sessão via trança de cancelamento (Yang-Baxter)

## P4: Reprodutibilidade Garantida
- **Seeds**: `np.random.seed(105)`, `torch.manual_seed(105)` para geração de tranças de teste
- **Precisão**: `mpmath.mp.dps = 50` para cálculo de invariantes de Jones
- **Topologia de rede**: Grafo fixo de 12 nós (correspondente às 12 camadas da Treliça Torcional)
- **Ambiente**: Python 3.11, numpy 1.26.0, mpmath 1.3.0, custom extensions para propagação escalar
- **Output**: `results/sophon_network_v406_run_<timestamp>.json` com metadados completos de sessão

## P5: Convenções Físico-Matemáticas Claras
- **Unidades**: Tempo em unidades cronométricas (ψ = ω_Δ·ln(t)); coerência adimensional [0,1]
- **Mapeamento de observáveis**:
  - Endereço topológico ↔ Hash de invariante de Jones
  - Coerência de rota ↔ Produto interno de estados quânticos
  - Taxa de entrega ↔ Probabilidade de sucesso na manifestação Φ
- **Normalização**: Invariantes de Jones normalizados por dimensão quântica: `J_norm = J / (φ + 1/φ)`
- **Condições de contorno**: Rede fechada (toro) para evitar bordas artificiais em roteamento
