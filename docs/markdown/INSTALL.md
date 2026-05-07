# 🏗️🚀 ARKHE OS — GUIA DE COMPILAÇÃO E INSTALAÇÃO

## 📋 PRÉ-REQUISITOS DO SISTEMA

### Hardware Mínimo por Nó

```yaml
# Nó de Desenvolvimento/Teste
cpu: "8+ cores (AVX-512 recomendado para FHE)"
ram: "32GB+ (64GB para parsing federado)"
storage: "1TB NVMe (cache de proofs ZK + LFIR)"
network: "2x 100GbE NICs com suporte a OCP-MRC-1.0"
gpu: "Opcional: NVIDIA A100/H100 para annealing quântico simulado"

# Nó de Produção (Cluster AI/ML)
cpu: "64+ cores"
ram: "256GB+"
storage: "4TB+ NVMe RAID"
network: "4x 200/400GbE com MRC + RoCE v2"
gpu: "8x aceleradores (H100/MI300X) para inferência Φ"
```

### Software Base

```bash
# Sistema Operacional
$ lsb_release -a
# Requerido: Linux kernel ≥ 6.6 (suporte a SRv6, XDP, eBPF)

# Runtime e Compiladores
$ python3 --version          # ≥ 3.11
$ rustc --version           # ≥ 1.75 (para componentes FHE/ZK)
$ cargo --version           # ≥ 1.75
$ node --version            # ≥ 20.x (para dashboard WebGPU)
$ npm --version             # ≥ 10.x

# Dependências de Rede MRC
$ ethtool -i eth0 | grep driver  # Driver NIC compatível com OCP-MRC-1.0
$ ip -d link show eth0           # Verificar suporte a SRv6/Structured EV
```

### Configuração de Rede MRC (OCP-MRC-1.0)

```bash
# 1. Instalar utilitários MRC (libmrc)
$ git clone https://github.com/opencomputeproject/OCP-Multipath-Reliable-Connection
$ cd OCP-Multipath-Reliable-Connection/libmrc
$ mkdir build && cd build
$ cmake -DCMAKE_BUILD_TYPE=Release ..
$ make -j$(nproc)
$ sudo make install

# 2. Configurar DSCP para classes de tráfego MRC
$ sudo tc qdisc add dev eth0 root prio bands 3 \
    priomap 2 2 2 2 2 2 2 2 1 2 2 2 2 2 2 2

# Mapeamento DSCP → Traffic Class:
# DSCP_CONTROL (0x2e) → Band 0 (alta prioridade)
# DSCP_TRIMMABLE (0x2a) → Band 1 (dados)
# DSCP_TRIMMED (0x2c) → Band 0 (controle)

# 3. Habilitar ECN para congestion control NSCC
$ sudo sysctl -w net.ipv4.tcp_ecn=2
$ sudo sysctl -w net.ipv4.tcp_ecn_fallback=1

# 4. Configurar SRv6 (se usando source routing)
$ sudo ip -6 route add <prefix>::/48 dev eth0 encap seg6 mode encap segs <sid1>,<sid2>,<sid3>
```

---

## 🔧 COMPILAÇÃO DO ARKHE OS WEB3 COMPLETO

### 1. Clonar Repositório e Instalar Dependências Python

```bash
# Clonar repositório oficial
$ git clone https://github.com/arkhe-os/arkhe-os-web3-complete.git
$ cd arkhe-os-web3-complete

# Criar ambiente virtual Python
$ python3 -m venv .venv
$ source .venv/bin/activate

# Instalar dependências base
$ pip install --upgrade pip setuptools wheel

# Instalar dependências por camada (escolha conforme necessidade)
$ pip install -e ".[core]"                    # Substratos 280-290
$ pip install -e ".[evolution]"              # Substratos 291-292 (bayesian + annealing)
$ pip install -e ".[marketplace]"            # Substrato 293 (AMM + pricing)
$ pip install -e ".[edge]"                   # Substrato 294 (streaming adaptativo)
$ pip install -e ".[ui]"                     # Substrato 292 UI/UX (WebGPU + CLI)
$ pip install -e ".[mrc]"                    # Integração OCP-MRC-1.0

# OU: instalar tudo (requer ~8GB RAM para compilação)
$ pip install -e ".[all]"
```

### 2. Compilar Componentes Rust (FHE/ZK Provers)

```bash
# Navegar para diretório de componentes nativos
$ cd arkhe_os/crypto/zinc_plus

# Compilar prover Zinc+ com otimizações para sua arquitetura
$ cargo build --release --features=avx512,openmp

# Compilar bindings Python
$ maturin develop --release

# Verificar instalação
$ python -c "from arkhe_os.crypto.zinc import ZincPlusProver; print('✅ Zinc+ OK')"
```

### 3. Compilar Dashboard WebGPU (TypeScript/WebAssembly)

```bash
# Navegar para frontend
$ cd arkhe_os/ui/dashboard

# Instalar dependências Node.js
$ npm ci

# Compilar para produção (WebGPU + WASM)
$ npm run build:prod

# Verificar artefatos gerados
$ ls -lh dist/
# Expected: index.html, main.wasm, coherence_renderer.wgsl, etc.
```

### 4. Verificar Compilação Completa

```bash
# Executar suite de testes unitários
$ pytest tests/unit/ -v --tb=short

# Executar testes de integração MRC (requer NIC compatível)
$ pytest tests/integration/mrc/ -v -m "requires_mrc"

# Verificar imports de todos os substratos
$ python -c "
from arkhe_os.substrates import (
    substrate_280, substrate_283, substrate_284,
    substrate_285, substrate_287, substrate_290,
    substrate_291, substrate_292, substrate_293,
    substrate_294, substrate_292_ui
)
print('✅ Todos os substratos importados com sucesso')
"
```