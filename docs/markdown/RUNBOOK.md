## 🚀 EXECUÇÃO DO SISTEMA

### Modo 1: Nó de Desenvolvimento Local

```bash
# Iniciar todos os serviços em background
$ arkhe services start \
    --mode development \
    --mrc-daemon \
    --parser-node \
    --validation-harness \
    --dashboard-webgpu \
    --log-level debug

# Verificar logs em tempo real
$ arkhe logs tail --follow --substrates 284,287,290

# Executar parsing local de um repositório
$ arkhe parser scan ./my-project \
    --output ./results/scan.json \
    --substrates 283,284 \
    --generate-proof

# Visualizar resultados no dashboard
$ xdg-open http://localhost:3000/coherence?project=my-project
```

### Modo 2: Nó Federado em Cluster (Produção)

```bash
# Iniciar como nó de parsing federado (Substrato 285)
$ arkhe services start \
    --mode federated-parser \
    --node-id parser-br-001 \
    --federation-id quantum-materials-2026 \
    --stake-phi 50.0 \
    --mrc-profile ecmp-cluster \
    --log-level info

# Registrar nó no consórcio federado
$ arkhe federation register \
    --node-id parser-br-001 \
    --capabilities parsing,zk-proving,fhe-aggregation \
    --phi-stake 50.0 \
    --endpoint https://parser-br-001.arkhe.local:8443

# Monitorar recompensas e métricas
$ arkhe federation metrics --node-id parser-br-001 --watch
✓ Parsers executados: 127
✓ Φ‑tokens ganhos: 1,143.2
✓ Coerência média: 0.914
✓ Uptime: 99.97%
```

### Modo 3: Edge Device para Streaming Adaptativo

```bash
# Configurar dispositivo edge (Substrato 294)
$ arkhe edge register \
    --device-id edge-lab-br-001 \
    --capabilities cpu:4,ram:8GB,storage:512GB \
    --latency-budget-ms 50 \
    --criticality-threshold 0.85 \
    --zk-verification snark,stark

# Iniciar streaming de métricas de coerência
$ arkhe edge stream start \
    --source coherence-metrics \
    --target edge-lab-br-001 \
    --adaptive-routing true \
    --cache-proofs true \
    --priority critical

# Verificar latência e entrega
$ arkhe edge metrics --device-id edge-lab-br-001 --window 5m
✓ Latência p50: 23ms | p95: 41ms | p99: 48ms
✓ Taxa de entrega: 99.94%
✓ Proofs verificados localmente: 1,247
```

### Modo 4: Dashboard de Monitoramento Global

```bash
# Iniciar dashboard em modo produção com autenticação
$ arkhe ui dashboard start \
    --mode production \
    --host 0.0.0.0 \
    --port 443 \
    --tls-cert /etc/arkhe/certs/fullchain.pem \
    --tls-key /etc/arkhe/certs/privkey.pem \
    --auth-provider octra \
    --nostr-relays wss://relay.damus.io,wss://relay.snort.social

# Acessar dashboard (autenticação via Nostr)
# URL: https://seu-dominio.arkhe.local
# Login: assinar mensagem com sua chave npub

# Painéis disponíveis:
# • /coherence/global — Mapa de calor de Φ_C global
# • /substrates/graph — Grafo de dependências transversal
# • /marketplace/trade — Interface de trading de ativos de coerência
# • /evolution/population — Visualização de populações evolutivas
# • /edge/devices — Monitoramento de dispositivos edge
# • /dao/proposals — Governança e votação de propostas
```

---

## 🔄 ATUALIZAÇÃO E MANUTENÇÃO

### Atualizar para Nova Versão

```bash
# 1. Fazer backup da configuração atual
$ arkhe config backup --output ./backup/arkhe-config-$(date +%Y%m%d).tar.gz

# 2. Atualizar pacote Python
$ pip install --upgrade arkhe-os-web3-complete[all]

# 3. Recompilar componentes nativos se necessário
$ cd arkhe_os/crypto/zinc_plus && cargo build --release
$ cd arkhe_os/ui/dashboard && npm run build:prod

# 4. Reiniciar serviços com zero downtime (rolling update)
$ arkhe services restart --rolling --batch-size 2 --health-check-timeout 30s

# 5. Verificar integridade pós-atualização
$ arkhe health check --post-upgrade --verbose
```

### Backup e Recuperação

```bash
# Backup completo do estado do nó
$ arkhe backup create \
    --include keys,config,ledger-cache,proofs \
    --encrypt --passphrase-file ~/.arkhe/backup.key \
    --output ./backups/full-$(date +%Y%m%d-%H%M).enc

# Restaurar de backup
$ arkhe backup restore \
    --input ./backups/full-20260507-1430.enc \
    --passphrase-file ~/.arkhe/backup.key \
    --verify-signature

# Replicar configuração para múltiplos nós
$ arkhe config sync \
    --source ~/.arkhe/config \
    --targets node-002,node-003,node-004 \
    --via mrc \
    --verify-after-sync
```