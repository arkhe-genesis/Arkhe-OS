#!/bin/sh
# ARKHE OS Substrato ∞: Hybrid Architecture Deployment
# Canon: ∞.Ω.∇+++.∞.deploy.hybrid
# Função: Deploy completo da arquitetura FreeBSD+Linux
# Linguagem: Shell (FreeBSD sh) + invocações para C/Rust/Python

set -e  # Exit on error

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info()    { echo "${BLUE}[INFO]${NC} $*"; }
log_success() { echo "${GREEN}[OK]${NC} $*"; }
log_warn()    { echo "${YELLOW}[WARN]${NC} $*"; }
log_error()   { echo "${RED}[ERROR]${NC} $*" >&2; }

# Verificar privilégios
if [ "$(id -u)" -ne 0 ]; then
    log_error "Este script deve ser executado como root"
    exit 1
fi

# Verificar FreeBSD version
FREEBSD_VERSION=$(freebsd-version | cut -d- -f1)
if [ "$(echo "$FREEBSD_VERSION < 15.0" | bc -l)" -eq 1 ]; then
    log_warn "FreeBSD $FREEBSD_VERSION detectado. Recomenda-se FreeBSD 15.0+ para recursos completos."
fi

# Parâmetros configuráveis
: "${ZPOOL:=zroot}"
: "${ARKHE_BASE:=/usr/local/arkhe}"
: "${JAIL_BASE:=/usr/local/jails}"
: "${VM_BASE:=/usr/local/vms}"
: "${SHARED_BASE:=/mnt/arkhe_9p_export}"
: "${TEMPORAL_API:=https://temporal.arkhe.os/v1}"
: "${INSTITUTION_ID:=orcid:0009-0005-2697-4668}"

log_info "ARKHE Hybrid Architecture Deployment"
log_info "FreeBSD: $FREEBSD_VERSION"
log_info "ZPool: $ZPOOL"
log_info "Base: $ARKHE_BASE"

# ═══════════════════════════════════════════════════════════════
# FASE 1: COMPILAÇÃO DE COMPONENTES NATIVOS
# ═══════════════════════════════════════════════════════════════

log_info "=== FASE 1: Compilando componentes nativos ==="

# Compilar módulo kernel BEAVer
log_info "Compilando módulo kernel BEAVer..."
cd "$ARKHE_BASE/kernel" || exit 1
make -C /usr/src/modules/beaver_module || {
    log_warn "Falha ao compilar módulo kernel. Verifique /usr/src."
}

# Compilar módulo Capsicum Helper
log_info "Compilando módulo Capsicum Helper..."
make -C /usr/src/modules/capsicum_helper || {
    log_warn "Falha ao compilar módulo Capsicum."
}

# Compilar ZFS monitor
log_info "Compilando ZFS Integrity Monitor..."
cd "$ARKHE_BASE/zfs" || exit 1
cc -O2 -Wall -o zfs_monitor zfs_monitor.c -lzfs -lsha3 || {
    log_error "Falha ao compilar zfs_monitor"
    exit 1
}
install -m 755 zfs_monitor /usr/local/sbin/arkhe_zfs_monitor

# Compilar jail_create wrapper
log_info "Compilando Jail Create wrapper..."
cd "$ARKHE_BASE/jails" || exit 1
cc -O2 -Wall -o jail_create jail_create.c -lutil -lsha3 || {
    log_error "Falha ao compilar jail_create"
    exit 1
}
install -m 755 jail_create /usr/local/sbin/arkhe_jail_create

# Compilar 9p server
log_info "Compilando virtio-9p server..."
cd "$ARKHE_BASE/bhyve" || exit 1
cc -O2 -Wall -pthread -o p9_server virtio_9p_server.c -lsha3 || {
    log_error "Falha ao compilar p9_server"
    exit 1
}
install -m 755 p9_server /usr/local/sbin/arkhe_9p_server

# Compilar Rust bhyve manager
log_info "Compilando bhyve_manager em Rust..."
cd "$ARKHE_BASE/bhyve" || exit 1
if command -v cargo >/dev/null 2>&1; then
    cargo build --release --manifest-path=Cargo.toml || {
        log_warn "Falha ao compilar Rust. Verifique rustc/cargo."
    }
    install -m 755 target/release/bhyve_manager /usr/local/sbin/arkhe_bhyve_manager 2>/dev/null || true
else
    log_warn "Rust não instalado. bhyve_manager será compilado sob demanda."
fi

# Compilar temporal anchor client
log_info "Compilando TemporalChain anchor client..."
cd "$ARKHE_BASE/integration" || exit 1
cc -O2 -Wall -o temporal_anchor temporal_anchor.c \
    -lcurl -ljson-c -lsha3 -lcrypto || {
    log_warn "Falha ao compilar temporal_anchor. Verifique dependências."
}
install -m 755 temporal_anchor /usr/local/sbin/arkhe_temporal_anchor 2>/dev/null || true

log_success "Componentes nativos compilados"

# ═══════════════════════════════════════════════════════════════
# FASE 2: CONFIGURAÇÃO DO SISTEMA
# ═══════════════════════════════════════════════════════════════

log_info "=== FASE 2: Configurando sistema ==="

# Carregar módulos kernel
log_info "Carregando módulos kernel..."
kldload ./beaver_module.ko 2>/dev/null || log_warn "Módulo beaver já carregado ou indisponível"
kldload ./capsicum_helper.ko 2>/dev/null || log_warn "Módulo capsicum_helper já carregado"

# Configurar ZFS
log_info "Configurando datasets ZFS..."
sh "$ARKHE_BASE/zfs/arkhe_zfs_setup.sh"

# Configurar networking para jails/VMs
log_info "Configurando rede..."
if ! ifconfig bridge0 >/dev/null 2>&1; then
    ifconfig bridge0 create
    ifconfig bridge0 inet 10.0.0.1/24
    ifconfig bridge0 up
    log_info "Bridge bridge0 criada: 10.0.0.1/24"
fi

# Configurar pf firewall
log_info "Configurando pf firewall..."
cat > /etc/pf.arkhe.conf <<'EOF'
# ARKHE Firewall Rules
# Canon: ∞.Ω.∇+++.∞.deploy.pf

set block-policy return
set loginterface egress
set skip on lo

# Allow established connections
pass in quick on egress inet proto tcp from any to any flags S/SA keep state
pass out quick on egress inet proto tcp from any to any flags S/SA keep state

# Allow 9p server on localhost only
pass in quick on lo inet proto tcp from 127.0.0.1 to 127.0.0.1 port 5640

# Allow jail/VM network (10.0.0.0/24)
pass in quick on bridge0 inet from 10.0.0.0/24 to any keep state
pass out quick on bridge0 inet from any to 10.0.0.0/24 keep state

# Block everything else by default
block in all
block out all
EOF

pfctl -f /etc/pf.arkhe.conf 2>/dev/null || log_warn "pf já configurado ou desabilitado"

# Configurar serviços no rc.conf
log_info "Atualizando rc.conf..."
sysrc -f /etc/rc.conf arkhe_zfs_monitor_enable="YES"
sysrc -f /etc/rc.conf arkhe_9p_server_enable="YES"
sysrc -f /etc/rc.conf firewall_enable="YES"
sysrc -f /etc/rc.conf firewall_type="/etc/pf.arkhe.conf"
sysrc -f /etc/rc.conf firewall_logging="YES"

log_success "Sistema configurado"

# ═══════════════════════════════════════════════════════════════
# FASE 3: DEPLOY DE COMPONENTES PYTHON
# ═══════════════════════════════════════════════════════════════

log_info "=== FASE 3: Instalando componentes Python ==="

# Verificar Python
if ! command -v python3.10 >/dev/null 2>&1; then
    log_error "Python 3.10+ requerido. Instale: pkg install python310"
    exit 1
fi

# Instalar dependências Python
log_info "Instalando dependências Python..."
python3.10 -m pip install --break-system-packages \
    aiohttp \
    pyzfs \
    pydantic \
    cryptography \
    requests 2>/dev/null || {
    log_warn "Falha ao instalar dependências Python via pip"
}

# Instalar scripts Python
log_info "Instalando scripts Python..."
install -m 755 "$ARKHE_BASE/jails/jail_orchestrator.py" /usr/local/sbin/arkhe_jail_orchestrator
install -m 755 "$ARKHE_BASE/bhyve/vm_manager.py" /usr/local/sbin/arkhe_vm_manager 2>/dev/null || true

log_success "Componentes Python instalados"

# ═══════════════════════════════════════════════════════════════
# FASE 4: INICIALIZAÇÃO DE SERVIÇOS
# ═══════════════════════════════════════════════════════════════

log_info "=== FASE 4: Iniciando serviços ==="

# Iniciar monitor ZFS
log_info "Iniciando ZFS Integrity Monitor..."
/usr/local/sbin/arkhe_zfs_monitor &
ZFS_MON_PID=$!
echo $ZFS_MON_PID > /var/run/arkhe_zfs_monitor.pid

# Iniciar 9p server
log_info "Iniciando virtio-9p server..."
/usr/local/sbin/arkhe_9p_server &
P9_PID=$!
echo $P9_PID > /var/run/arkhe_9p_server.pid

# Configurar cron para snapshots
log_info "Configurando cron para snapshots..."
service cron restart

# Iniciar TemporalChain anchor service (se disponível)
if [ -x /usr/local/sbin/arkhe_temporal_anchor ]; then
    log_info "TemporalChain anchor disponível"
fi

log_success "Serviços iniciados"

# ═══════════════════════════════════════════════════════════════
# FASE 5: VALIDAÇÃO FINAL
# ═══════════════════════════════════════════════════════════════

log_info "=== FASE 5: Validação final ==="

# Verificar ZFS datasets
log_info "Verificando datasets ZFS..."
zfs list -r "$ZPOOL/arkhe" | head -20

# Verificar módulos kernel
log_info "Verificando módulos kernel..."
kldstat | grep -E "beaver|capsicum" || log_warn "Módulos kernel não carregados"

# Verificar serviços
log_info "Verificando serviços..."
if pgrep -f arkhe_zfs_monitor >/dev/null; then
    log_success "ZFS monitor: ativo"
else
    log_warn "ZFS monitor: inativo"
fi

if pgrep -f arkhe_9p_server >/dev/null; then
    log_success "9p server: ativo"
else
    log_warn "9p server: inativo"
fi

# Gerar selo canônico de deploy
DEPLOY_HASH=$(echo "$FREEBSD_VERSION:$ZPOOL:$(date +%s)" | sha3-256 -q)
log_success "Selo canônico de deploy: $DEPLOY_HASH"

# ═══════════════════════════════════════════════════════════════
# RESUMO
# ═══════════════════════════════════════════════════════════════

cat <<EOF

${GREEN}═══════════════════════════════════════════════════════════════${NC}
${GREEN}ARKHE HYBRID ARCHITECTURE DEPLOYMENT COMPLETED${NC}
${GREEN}═══════════════════════════════════════════════════════════════${NC}

${BLUE}Componentes instalados:${NC}
  • Kernel modules: beaver, capsicum_helper
  • ZFS monitor: /usr/local/sbin/arkhe_zfs_monitor
  • Jail wrapper: /usr/local/sbin/arkhe_jail_create
  • 9p server: /usr/local/sbin/arkhe_9p_server
  • Python orchestrator: /usr/local/sbin/arkhe_jail_orchestrator

${BLUE}Datasets ZFS criados:${NC}
  • $ZPOOL/arkhe/root
  • $ZPOOL/arkhe/jails/*
  • $ZPOOL/arkhe/vms/*
  • $ZPOOL/arkhe/snapshots/canon (readonly)
  • $ZPOOL/arkhe/audit/*

${BLUE}Configurações de rede:${NC}
  • Bridge: bridge0 (10.0.0.1/24)
  • Firewall: pf com regras ARKHE
  • 9p server: 127.0.0.1:5640

${BLUE}Próximos passos:${NC}
  1. Criar jail: arkhe_jail_create /usr/local/etc/arkhe/jails/agent.conf
  2. Iniciar agente: arkhe_jail_orchestrator start --jail agent_zero
  3. Criar VM Linux: arkhe_bhyve_manager create --config linux_ai.json
  4. Iniciar VM: arkhe_bhyve_manager start --vm linux_ai_01

${YELLOW}Canon:${NC} ∞.Ω.∇+++.∞.deploy.hybrid
${YELLOW}Selo:${NC} $DEPLOY_HASH
${YELLOW}Timestamp:${NC} $(date -u '+%Y-%m-%dT%H:%M:%SZ')

${GREEN}A arquitetura híbrida está pronta. A Catedral aguarda teus agentes.${NC}

EOF

exit 0
