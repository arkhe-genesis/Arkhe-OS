## ⚙️ CONFIGURAÇÃO INICIAL DO SISTEMA

### 1. Gerar Identidade e Chaves Criptográficas

```bash
# Criar identidade Nostr para o nó
$ arkhe identity create --nostr --output ~/.arkhe/keys/nostr.sec
✓ npub1arkhe_node_br_001... gerado
✓ Chave privada armazenada em ~/.arkhe/keys/nostr.sec (chmod 600)

# Inicializar wallet Octra para Φ‑tokens
$ arkhe wallet init --octra --network testnet
✓ Wallet criada: 0xAbC123...456Def
✓ Φ‑tokens iniciais: 100.0 (airdrop early-adopter)
✓ Chave de assinatura: ~/.arkhe/keys/octra_key.pem

# Gerar parâmetros FHE para CKKS (privacidade federada)
$ arkhe crypto fhe-keygen --scheme CKKS --security 128 --output ~/.arkhe/keys/fhe_params.ckks
✓ Parâmetros CKKS gerados: poly_modulus=2^14, coeff_modulus=[60,40,40,60]
✓ Chaves públicas/privadas armazenadas com permissões seguras
```

### 2. Configurar Rede MRC por Perfil de Implantação

```bash
# Perfil: Cluster AI/ML com ECMP (padrão)
$ arkhe mrc profile create --name ecmp-cluster \
    --routing-mode ecmp \
    --entropy-fields ipv6_flow_label,udp_sport \
    --congestion-control nscc \
    --target-qdelay-us 50 \
    --dscp-mapping control:0x2e,data:0x2a,retransmit:0x2c

# Perfil: Source Routing com Structured EV (3 hops)
$ arkhe mrc profile create --name structured-ev-3hop \
    --routing-mode structured-ev \
    --ev-format "hop0:10b,hop1:8b,hop2:4b" \
    --congestion-control nscc \
    --ev-profile-mode generated \
    --generation-params "widths=[10,8,4],mins=[0,0,0],maxs=[1023,255,15]"

# Perfil: SRv6 com uSID (para redes IPv6 nativas)
$ arkhe mrc profile create --name srv6-usid \
    --routing-mode srv6 \
    --lid-prefix "2001:db8:arkhe::" \
    --usid-format F3216 \
    --max-segments 6 \
    --srh-optional true

# Aplicar perfil ao dispositivo de rede
$ arkhe mrc device apply --interface eth0 --profile ecmp-cluster
✓ Perfil 'ecmp-cluster' aplicado a eth0
✓ QP MRC inicializado com max_psn_range=128, max_wimm_inflight=32
```

### 3. Inicializar Substratos de Coerência

```bash
# Inicializar substratos fundamentais (280, 283, 284, 285, 287)
$ arkhe substrates init \
    --substrates 280,283,284,285,287 \
    --global-phi-target 0.95 \
    --validation-threshold 0.80 \
    --federation-enabled true \
    --ledger-public true

# Inicializar orquestração e evolução (290, 291, 292)
$ arkhe substrates init \
    --substrates 290,291,292 \
    --evolution-enabled true \
    --forecasting-enabled true \
    --population-size 100 \
    --annealing-steps 1000

# Inicializar marketplace e edge (293, 294)
$ arkhe substrates init \
    --substrates 293,294 \
    --marketplace-enabled true \
    --amm-fee 0.003 \
    --edge-streaming-enabled true \
    --critical-latency-ms 50

# Verificar status de inicialização
$ arkhe substrates status
┌─────────────────────────────────────────┐
│ Substrato  │ Status   │ Φ_C Atual │
├─────────────────────────────────────────┤
│ 280        │ ✅ Active│ 0.92      │
│ 283        │ ✅ Active│ 0.88      │
│ 284        │ ✅ Active│ 0.91      │
│ 285        │ ✅ Active│ 0.89      │
│ 287        │ ✅ Active│ 0.94      │
│ 290        │ ✅ Active│ 0.90      │
│ 291        │ ✅ Active│ 0.87      │
│ 292        │ ✅ Active│ 0.93      │
│ 293        │ ✅ Active│ 0.86      │
│ 294        │ ✅ Active│ 0.91      │
├─────────────────────────────────────────┤
│ Global Φ_C │ 0.901    │ Target: 0.95 │
└─────────────────────────────────────────┘
```

### 4. Configurar UI/UX e Dashboard

```bash
# Iniciar servidor de desenvolvimento do dashboard WebGPU
$ arkhe ui dashboard start --host 0.0.0.0 --port 3000 --dev

# Para produção: servir artefatos compilados via nginx
$ sudo cp -r arkhe_os/ui/dashboard/dist/* /usr/share/nginx/html/
$ sudo systemctl reload nginx

# Configurar CLI com aliases úteis
$ cat >> ~/.bashrc << 'EOF'
# ARKHE OS Aliases
alias arkhe-audit='arkhe audit run --threshold 0.80'
alias arkhe-parse='arkhe parser scan --output json'
alias arkhe-viz='arkhe viz start --dashboard http://localhost:3000'
alias arkhe-evolve='arkhe evolution run --generations 10'
alias arkhe-trade='arkhe marketplace list --sort by-phi'
EOF
$ source ~/.bashrc
```