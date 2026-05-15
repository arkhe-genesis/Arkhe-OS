# 🛠️ Runbook SRE — ARKHE Broadcast Mesh

**Versão:** 1.0.0
**Substrato:** 9047‑A
**Público:** Operadores N1/N2, Engenheiros de Confiabilidade
**Selo Canônico:** `a3f2b8c9d1e4f5a6`

---

## 📋 Índice de Playbooks

| ID | Cenário | Severidade | SLA |
|----|---------|-----------|-----|
| INC‑001 | Queda de Φ_C abaixo de 0.95 | P1‑Crítico | 5 min |
| INC‑002 | Perda de conectividade com plataforma (Twitch/YT/TikTok) | P1‑Crítico | 10 min |
| INC‑003 | Latência de processamento Spark > 30s | P2‑Alto | 30 min |
| INC‑004 | Ataque de view‑botting detectado | P1‑Crítico | 5 min |
| INC‑005 | Falha na ancoragem TemporalChain | P1‑Crítico | 5 min |
| INC‑006 | Saturação de Kafka (lag > 10.000 mensagens) | P2‑Alto | 15 min |
| INC‑007 | Vazamento de credenciais detectado | P0‑Emergência | Imediato |

---

## INC‑001: Queda de Φ_C abaixo de 0.95

### Sintomas
- Alerta `ArkheMeshPhiCLow` disparado no Prometheus
- Dashboard Grafana mostra Φ_C em declínio
- Canais Twitch mostram mensagem automática de baixa coerência

### Diagnóstico (5 passos)
1. **Verificar métricas agregadas**
   ```bash
   curl -s http://mesh-orchestrator:8053/api/v1/mesh/status | jq '.mesh_phi_c'
   ```
2. **Identificar streams com baixa coerência**
   ```bash
   curl -s http://mesh-orchestrator:8053/api/v1/mesh/phi_c_snapshot | jq '.[] | select(.phi_c < 0.95)'
   ```
3. **Verificar Guardian Attractor**
   ```bash
   kubectl logs -l app=guardian --tail=50 | grep -i "threat\|anomaly"
   ```
4. **Verificar conectividade com APIs das plataformas**
   ```bash
   curl -s http://mesh-orchestrator:8053/health | jq '.connectors'
   ```
5. **Verificar logs do orquestrador**
   ```bash
   kubectl logs -l app=mesh-orchestrator --tail=100 | grep -i "error\|warning"
   ```

### Resolução
- **Causa comum 1:** API de plataforma retornando erro → **Ação:** Executar playbook INC‑002
- **Causa comum 2:** Guardian bloqueando mensagens em massa → **Ação:** Verificar regras de exorcismo; ajustar threshold temporariamente
- **Causa comum 3:** Sobrecarga do Spark → **Ação:** Executar playbook INC‑003
- **Causa comum 4:** Ataque de view‑botting → **Ação:** Executar playbook INC‑004

### Rollback
Se a coerência não se recuperar em 15 minutos:
1. Ativar modo de contingência: `curl -X POST http://mesh-orchestrator:8053/api/v1/mesh/contingency`
2. Reduzir frequência de polling das APIs para 5 minutos
3. Desabilitar validação Guardian para mensagens (apenas log)
4. Notificar equipe de engenharia via PagerDuty

---

## INC‑002: Perda de Conectividade com Plataforma

### Sintomas
- Streams da plataforma X marcados como offline
- Métrica `arkhe_connector_online{platform="X"}` = 0
- Erro 401/403/500 nas chamadas de API

### Diagnóstico
1. **Verificar status do conector**
   ```bash
   curl -s http://mesh-orchestrator:8053/health | jq '.connectors[] | select(.platform=="twitch")'
   ```
2. **Testar API manualmente**
   ```bash
   # Twitch
   curl -H "Client-Id: $TWITCH_CLIENT_ID" -H "Authorization: Bearer $TWITCH_TOKEN" \
     https://api.twitch.tv/helix/streams?user_login=tvglobo
   ```
3. **Verificar validade do token OAuth2**
   ```bash
   kubectl exec -it deployment/vault-agent -- vault read secret/twitch
   ```
4. **Verificar rate limiting**
   ```bash
   kubectl logs -l app=mesh-orchestrator --tail=100 | grep "429\|Rate limit"
   ```

### Resolução
- **Token expirado →** Renovar automaticamente (já implementado) ou manualmente:
  ```bash
  curl -X POST http://mesh-orchestrator:8053/api/v1/connectors/twitch/refresh_token
  ```
- **Rate limit →** Reduzir frequência de polling temporariamente:
  ```bash
  curl -X PATCH http://mesh-orchestrator:8053/api/v1/config \
    -d '{"poll_interval_seconds": 300}'
  ```
- **API outage →** Ativar modo de contingência; os dados daquela plataforma serão interpolados a partir do último snapshot

---

## INC‑004: Ataque de View‑Botting Detectado

### Sintomas
- Contagem de viewers anômala (ex.: 100.000 viewers em um canal que normalmente tem 500)
- Φ_C caindo devido a dados inconsistentes
- Logs do Guardian mostram padrões de spam no chat

### Diagnóstico
1. **Identificar canal suspeito**
   ```bash
   curl -s http://mesh-orchestrator:8053/api/v1/audience/globo | jq '.channels[] | select(.viewers > 50000)'
   ```
2. **Verificar métricas de chat para o canal**
   ```bash
   curl -s http://spark-master:4040/api/v1/applications | jq '.[] | select(.name=="chat_processor")'
   ```
3. **Analisar padrão de crescimento de viewers (Grafana)**

### Resolução
1. **Isolar canal suspeito**
   ```bash
   curl -X POST http://mesh-orchestrator:8053/api/v1/connectors/twitch/blacklist \
     -d '{"channel": "suspect_channel", "reason": "view_botting", "duration_minutes": 60}'
   ```
2. **Excluir métricas anômalas do cálculo de Φ_C**
3. **Reportar à plataforma (ex.: Twitch Trust & Safety)**
4. **Ancorar incidente na TemporalChain para auditoria futura**

---

## 📞 Contatos de Escalonamento

| Nível | Equipe | Contato | SLA |
|-------|--------|---------|-----|
| N1 | NOC Broadcast | noc@broadcast.arkhe.org | 5 min |
| N2 | Engenharia ARKHE | sre@arkhe.org | 15 min |
| N3 | Especialista Plataforma | platform-eng@arkhe.org | 30 min |
| N4 | ARKHE Observatory | observatory@arkhe.org | 2 horas |
| Emergência | Security Incident | security-emergency@arkhe.org (PGP: 0xARKHE) | Imediato |