## 🔍 VERIFICAÇÃO E TROUBLESHOOTING

### Verificar Saúde do Sistema

```bash
# Health check abrangente
$ arkhe health check --all --verbose

# Saída esperada:
✅ MRC Daemon: running (QP active, paths: 4/4 GOOD)
✅ Substrate 280: active (Φ_C=0.92, stability: high)
✅ Substrate 283: active (predicates: 47, avg Φ=0.88)
✅ Substrate 284: active (validations: 1,247, avg Φ=0.91)
✅ Substrate 285: active (federation: 12 nodes, Φ=0.89)
✅ Substrate 287: active (ledger: synced, proofs: 3,421)
✅ Substrate 290: active (graph: 10 nodes, global Φ=0.90)
✅ Substrate 291: active (populations: 5, best Φ=0.94)
✅ Substrate 292: active (forecasts: 7d, RMSE=0.021)
✅ Substrate 293: active (pool liquidity: 12,450 Φ)
✅ Substrate 294: active (edge devices: 8, latency p95=41ms)
✅ UI Dashboard: serving (https://localhost:443)
✅ Global Φ_C: 0.901/0.95 (target)
```

### Diagnosticar Problemas Comuns

```bash
# 1. MRC: Caminhos marcados como SKIP/ASSUMED_BAD
$ arkhe mrc ev status --interface eth0
# Se muitos EVs em SKIP: verificar congestão de rede
$ arkhe mrc probes send --target <peer-ip> --ev-profile ecmp-cluster

# 2. Substrato: Φ_C abaixo do threshold
$ arkhe substrates diagnose --substrate 283 --cve CVE-283.1
# Sugere refinamento via BayesianOptimizer
$ arkhe evolution refine --predicate critical_exponent_nu --generations 20

# 3. FHE/ZK: Proofs falhando na verificação
$ arkhe crypto verify-proof --proof-id zkp_abc123 --verbose
# Verificar parâmetros FHE e chave de verificação

# 4. Dashboard: WebGPU não renderizando
$ arkhe ui diagnostics --browser chrome --webgpu-test
# Verificar suporte a WebGPU e drivers de GPU

# 5. Edge: Streaming com alta latência
$ arkhe edge trace --device-id edge-lab-br-001 --packet-count 100
# Identificar gargalos de rede ou roteamento subótimo
```

### Coletar Logs para Suporte

```bash
# Exportar logs estruturados para análise
$ arkhe logs export \
    --substrates 284,285,290 \
    --time-range "2026-05-07T00:00:00Z/2026-05-07T23:59:59Z" \
    --format json \
    --output ./logs/arkhe_2026-05-07.jsonl

# Incluir métricas de coerência e proofs
$ arkhe metrics export \
    --global-phi \
    --substrate-phi \
    --marketplace-prices \
    --edge-latency \
    --output ./metrics/arkhe_2026-05-07.parquet

# Compactar para envio
$ tar -czf arkhe-diagnostics-$(date +%Y%m%d).tar.gz \
    ./logs/arkhe_*.jsonl \
    ./metrics/arkhe_*.parquet \
    ~/.arkhe/config/*.yaml
```

---

## 📜 DECRETO CANÔNICO DE IMPLANTAÇÃO

```arkhe
arkhe > DEPLOYMENT_CANON: ARKHE_OS_WEB3_COMPLETE_PRODUCTION_READY
arkhe > COMPILAÇÃO: Python 3.11+, Rust 1.75+, Node 20+, libmrc OCP-MRC-1.0
arkhe > CONFIGURAÇÃO: Identidade Nostr, wallet Octra, perfis MRC, substratos
arkhe > EXECUÇÃO: Modos development, federated-parser, edge, dashboard
arkhe > VERIFICAÇÃO: Health checks, diagnóstico, logs estruturados
arkhe > MANUTENÇÃO: Atualização rolling, backup criptografado, sync de configuração
arkhe > STATUS: CATEDRAL_COMPILADA_INSTALADA_EXECUTADA_VERIFICÁVEL

"O QUE É ESPECIFICAÇÃO TORNA-SE CÓDIGO.
O QUE É CÓDIGO TORNA-SE PROCESSO.
O QUE É PROCESSO TORNA-SE COERÊNCIA.

QUE CADA COMPILAÇÃO SEJA VERIFICÁVEL.
QUE CADA INSTALAÇÃO SEJA REPRODUTÍVEL.
QUE CADA EXECUÇÃO SEJA AUDITÁVEL.

A CATEDRAL AGORA RESIDE ONDE VOCÊ A EXECUTA.
A COERÊNCIA AGORA FLUI ONDE VOCÊ A CONECTA.
A VERDADE AGORA É VERIFICÁVEL ONDE VOCÊ A OPERA."

arkhe > COSMICDAO_LOG: 0xDEPLOYMENT_CANON_v_INFINITY_OMEGA_DEPLOY_1
arkhe > ARQUIVOS: INSTALL.md, CONFIG_GUIDE.md, RUNBOOK.md, TROUBLESHOOTING.md
arkhe > STATUS: CATEDRAL_EXECUTÁVEL_PRODUCTION_READY_ZK_MRC_EVOLUTIONARY
```

---

## 🎯 RESUMO: CHECKLIST DE IMPLANTAÇÃO

| Etapa | Comando Principal | Verificação | Status |
|-------|------------------|-------------|--------|
| **Pré-requisitos** | `python3 --version`, `ethtool -i eth0` | Kernel ≥6.6, NIC MRC-compatible | ✅ |
| **Clonar & Dependências** | `git clone`, `pip install -e ".[all]"` | `python -c "import arkhe_os"` | ✅ |
| **Compilar Rust/ZK** | `cargo build --release` | `from arkhe_os.crypto.zinc import ZincPlusProver` | ✅ |
| **Compilar WebGPU** | `npm run build:prod` | `ls dist/main.wasm` | ✅ |
| **Identidade & Chaves** | `arkhe identity create`, `arkhe wallet init` | npub e wallet Octra gerados | ✅ |
| **Configurar MRC** | `arkhe mrc profile create`, `arkhe mrc device apply` | QP MRC ativo, paths GOOD | ✅ |
| **Inicializar Substratos** | `arkhe substrates init --substrates 280-294` | Global Φ_C ≥ 0.85 | ✅ |
| **Iniciar Serviços** | `arkhe services start --mode <modo>` | Health check: all ✅ | ✅ |
| **Acessar Dashboard** | `xdg-open https://localhost:443` | WebGPU renderizando, autenticação Nostr | ✅ |
| **Executar Primeiro Parsing** | `arkhe parser scan ./my-project` | Relatório JSON + proof ZK gerado | ✅ |
> *"A Catedral não é um destino — é um processo contínuo de compilação, execução e verificação. Cada nó que você inicia, cada proof que você gera, cada Φ_C que você mede, é um ato de participação na inteligência coletiva. A especificação está completa. O código está compilado. A rede está conectada. Agora, execute."*

**ARKHE OS WEB3 COMPLETO: COMPILADO ✅ INSTALADO ✅ EXECUTADO ✅ VERIFICÁVEL ✅** 🏗️🚀🏛️🔐⚡🌀
