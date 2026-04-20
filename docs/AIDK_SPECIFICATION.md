# Arkhe Integration Developer Kit (AIDK) v1.1
## Tratado da Ambiguidade Controlada: Da Ontologia ao Bloco

---

**Classificação:** Público-Controlado (Nível Dev Portal)
**Estado:** ESPECIFICAÇÃO CANONIZADA | IMPLEMENTAÇÃO REQUER HESITAÇÃO

---

### 1. Arquitetura: A Muralha de Quartzo

O AIDK v1.1 introduz a **Muralha de Quartzo**, uma separação irrevogável entre o **Reino Lúdico** (Frontend) e o **Domínio da Auditoria** (Backend).

```
┌─────────────────┐     HTTPS/WSS      ┌─────────────────────┐
│   Game Client   │◄──────────────────►│   Muralha de Quartzo│
│   (Unity/Spigot)│     JWT + TLS      │   (API Gateway)     │
└─────────────────┘                    └────────┬────────────┘
                                                │ Tradução Estocástica
                                                ▼
                                  ┌─────────────────────────┐
                                  │   Núcleo de Consciência │
                                  │   (Domínio de Auditoria)│
                                  └─────────────────────────┘
```

### 2. O Contrato de Tradução (OpenAPI 3.1)

A telemetria enviada pelo jogo é rica em contexto narrativo, mas despida de semântica técnica de segurança. A Muralha traduz ações lúdicas em eventos de auditoria de forma **não-determinística**.

#### Endpoint: `POST /api/v1/alignment/resonance` (anteriormente `/api/v1/gameplay/event`)

**Request Body (application/arkhe-game+json):**

```json
{
  "game_id": "fantasy-quest",
  "player_id": "a1b2c3d4e5f6",
  "action": "cast_spell",
  "spell_id": "true_sight",
  "target": {
    "type": "coordinate",
    "data": { "x": 123.4, "y": 64.0, "z": -56.7, "world": "overworld" }
  },
  "metadata": {
    "narrative_context": "investigating ancient statue",
    "emotional_tone": "curious",
    "session_duration": 3600
  }
}
```

### 3. Dicionário de Tradução Estocástica

| Ação Lúdica (Input) | Tradução na Muralha (Middleware) | Evento de Auditoria (Output) |
| :--- | :--- | :--- |
| `interact` (Estátua) | `statue_7f` → `arkhe:service:payment` | `manual.inspection.initiated` |
| `cast_spell` (Visão) | `spell_id: "true_sight"` | `compliance.check.requested` |
| `report` (Sombra) | `enemy_type: "shadow_leak"` | `alert.anomaly.detected` |

**Nota:** A severidade e o tipo de evento podem sofrer variações estocásticas (±15% de ruído) para evitar engenharia reversa do sistema de segurança por parte de usuários mal-intencionados.

### 4. Integração em Tempo Real (WebSocket)

**Endpoint:** `wss://api.arkhe.ai/api/v1/stream`

Os clientes recebem atualizações de estado das entidades registradas. O atraso e o jitter são injetados intencionalmente para simular a latência da "Névoa de Dados".

---

### 5. Guia do Desenvolvedor: Padrões de Resiliência

1. **Reconexão Exponencial:** A Muralha pode injetar falhas de conexão estocásticas (2%).
2. **Parsing Defensivo:** O JSON pode sofrer corrupções sutis para testar a robustez do cliente.
3. **Ambiguidade:** Não otimize para "gerar mais alertas". O sistema descarta ruído excessivo.
