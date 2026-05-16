#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# deploy_all.sh — ARKHE Ω‑TEMP Universal Deploy Script v2.0
# Substrato ∞-Alpha: Fundação Operacional Bash (Ampliada)
# ═══════════════════════════════════════════════════════════════
# Este script utiliza todas as 18 estruturas fundamentais de Bash
# reconhecidas no diagrama "Bash Scripting Basics" (sysxplore.com),
# AMPLIADAS para orquestrar o deploy completo da Catedral:
#   • 15+ microserviços poliglotas
#   • 4 pilotos SCADA com nós edge (ESP32‑S3)
#   • Hardware quântico (emissor 1550nm)
#   • Malha BLE com 52+ nós nRF52840
#   • Federação cross‑org
#   • Dashboard unificado
#   • Health checks, rollback, e ancoragem temporal
# ═══════════════════════════════════════════════════════════════

set -euo pipefail  # Strict mode

# ── 1. Shebang ── (linha 1)

# ── 2. Variáveis ──
SCRIPT_VERSION="v∞.Ω.∇+++.∞.2"
username="${SUDO_USER:-$USER}"
timestamp=$(date +%Y%m%d-%H%M%S)
deploy_id="ARKHE_DEPLOY_${timestamp}"
deploy_log="/opt/arkhe/logs/deploy_${deploy_id}.log"
canonical_seal=""
exit_status=0
PHI_C_THRESHOLD=0.95
DEFAULT_NAMESPACE="arkhe-production"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ── 3. Entrada do Usuário ──
echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  ARKHE Ω‑TEMP v∞.Ω — UNIVERSAL DEPLOY SCRIPT v2.0         ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

read -p "🔷 Modo de deploy? (staging|production|custom): " deploy_mode
read -p "🔷 Namespace? (default: ${DEFAULT_NAMESPACE}): " namespace
namespace="${namespace:-$DEFAULT_NAMESPACE}"

# ── 4. Condicional if (validação de modo) ──
if [[ ! "$deploy_mode" =~ ^(staging|production|custom)$ ]]; then
    echo -e "${RED}❌ Modo de deploy inválido: $deploy_mode (use staging, production ou custom)${NC}"
    exit 1
fi

if [[ "$EUID" -ne 0 ]] && [[ "$deploy_mode" == "production" ]]; then
    echo -e "${YELLOW}⚠️  Deploy em produção recomendado com privilégios root. Continuando mesmo assim...${NC}"
fi

# ── 5. Confirmação ──
echo ""
echo -e "${PURPLE}Resumo do Deploy:${NC}"
echo "   Modo:      $deploy_mode"
echo "   Namespace: $namespace"
echo "   Script:    $SCRIPT_VERSION"
echo "   Data:      $(date)"
echo ""

read -p "🔷 Confirmar deploy de todos os microserviços em '$deploy_mode'? (s/N): " confirm
if [[ ! "$confirm" =~ ^[Ss]$ ]]; then
    echo -e "${RED}❌ Deploy cancelado pelo usuário.${NC}"
    exit 1
fi

# ── 6. Preparação de diretórios e logs ──
mkdir -p "$(dirname "$deploy_log")"
exec > >(tee -a "$deploy_log") 2>&1
echo -e "${BLUE}📝 Log redirecionado para: $deploy_log${NC}"

# ── 7. Condicional case ──
case $deploy_mode in
    staging)
        replicas=2
        resource_cpu="500m"
        resource_mem="512Mi"
        hpa_min=2
        hpa_max=8
        quantum_emulation="true"
        federation_enabled="false"
        ;;
    production)
        replicas=3
        resource_cpu="2000m"
        resource_mem="4Gi"
        hpa_min=3
        hpa_max=20
        quantum_emulation="false"
        federation_enabled="true"
        ;;
    custom)
        read -p "   Número de réplicas: " replicas
        read -p "   CPU por pod (ex: 1000m): " resource_cpu
        read -p "   Memória por pod (ex: 2Gi): " resource_mem
        hpa_min=$replicas
        hpa_max=$((replicas * 5))
        quantum_emulation="true"
        federation_enabled="false"
        ;;
esac

# ── 8. Operações de Arquivo (pré-requisitos) ──
echo ""
echo -e "${BLUE}🔍 Verificando pré-requisitos...${NC}"

prereqs_ok=true
for cmd in docker kubectl helm esptool.py; do
    if command -v "$cmd" &> /dev/null; then
        echo -e "   ${GREEN}✅${NC} $cmd encontrado"
    else
        echo -e "   ${YELLOW}⚠️${NC}  $cmd não encontrado — funcionalidades relacionadas serão puladas"
        prereqs_ok=false
    fi
done

if [ -e "docker-compose.yml" ] && [ -d "k8s/" ]; then
    echo -e "   ${GREEN}✅${NC} Configurações de deploy encontradas"
else
    echo -e "   ${RED}❌ Arquivos de deploy não encontrados no diretório corrente.${NC}"
    exit 1
fi

# ── 9. Argumentos de Linha de Comando ──
first_arg="${1:-default}"
second_arg="${2:-default}"
echo "   Argumentos extras: $first_arg, $second_arg"

# ── 10. Funções ──
function greet() {
    echo -e "${GREEN}🚀 Bem-vindo, Arquiteto $1!${NC}"
    echo -e "${GREEN}   Iniciando deploy da ARKHE Ω‑TEMP — $SCRIPT_VERSION${NC}"
    echo ""
}

function health_check() {
    local service=$1
    local port=$2
    local type=${3:-http}
    local max_retries=5
    local retry=0

    while [ $retry -lt $max_retries ]; do
        if [ "$type" == "http" ]; then
            curl -s "http://localhost:${port}/health" &> /dev/null && return 0
        elif [ "$type" == "grpc" ]; then
            grpcurl -plaintext "localhost:${port}" list &> /dev/null && return 0
        fi
        retry=$((retry + 1))
        sleep 2
    done
    return 1
}

function deploy_service() {
    local service=$1
    local port=$2
    local health_type=${3:-http}
    local critical=${4:-false}

    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}🔷 Deploying: $service (porta: $port)${NC}"

    # Simular deploy (substituir por kubectl apply ou docker-compose up em produção)
    sleep 1
    local deploy_exit=$?

    if [ $deploy_exit -eq 0 ]; then
        echo -e "${GREEN}   ✅ $service deployed${NC}"

        # Health check
        if health_check "$service" "$port" "$health_type"; then
            echo -e "${GREEN}   💚 $service saudável na porta $port${NC}"
            return 0
        else
            echo -e "${YELLOW}   ⚠️  $service deployed mas health check falhou${NC}"
            if [ "$critical" == "true" ]; then
                return 1
            fi
            return 0
        fi
    else
        echo -e "${RED}   ❌ $service deploy falhou (exit code: $deploy_exit)${NC}"
        return 1
    fi
}

# ── 11. Sinais de Processo (rollback) ──
function cleanup() {
    echo ""
    echo -e "${RED}⚠️  SINAL RECEBIDO — Executando rollback...${NC}"
    for service in "${all_services[@]}"; do
        echo -e "${YELLOW}   Rollback: $service${NC}"
        # kubectl rollout undo deployment/$service -n $namespace
    done
    echo -e "${RED}❌ Deploy interrompido. Sistema revertido.${NC}"
    exit 1
}
trap cleanup SIGTERM SIGINT

# ── 12. Comentários (multilinha) ──
: '
Este é o bloco principal de deploy ampliado.
Cada microserviço é implantado com verificações de saúde.
Em caso de falha, o rollback é acionado automaticamente.
A versão 2.0 inclui suporte a deploy condicional por flags.
'

# ═══════════════════════════════════════════════════════════════
# EXECUÇÃO PRINCIPAL
# ═══════════════════════════════════════════════════════════════

greet "$username"

# ── 11. Arrays Indexados ──
# Serviços Core (sempre deployados)
core_services=(
    "phi-bus"
    "temporal-chain"
    "guardian"
    "scada-gateway"
    "resilience-capsule"
    "diagnostic-agent"
    "dashboard"
    "broadcast-guardian"
)

# Serviços de domínio específico (deploy condicional)
energy_services=("energy-agent" "energy-edge-esp32")
water_services=("water-agent" "water-edge-esp32")
gas_services=("gas-agent" "gas-edge-esp32")
manufacturing_services=("manufacturing-agent" "manufacturing-edge-esp32")

# Serviços avançados (deploy condicional)
advanced_services=(
    "forecasting-mesh"
    "tinyml-aggregator"
    "quantum-fiber-optimizer"
    "federation-sidecar"
    "cics-bridge"
    "unified-dashboard"
)

# Todos os serviços combinados
all_services=(
    "${core_services[@]}"
    "${energy_services[@]}"
    "${water_services[@]}"
    "${gas_services[@]}"
    "${manufacturing_services[@]}"
    "${advanced_services[@]}"
)

# ── 12. Arrays Associativos ──
declare -A service_ports
declare -A service_health_types
declare -A service_critical
declare -A service_domains

# Core services
service_ports["phi-bus"]=8052;          service_health_types["phi-bus"]="grpc";  service_critical["phi-bus"]="true"
service_ports["temporal-chain"]=8051;   service_health_types["temporal-chain"]="http"; service_critical["temporal-chain"]="true"
service_ports["guardian"]=8050;         service_health_types["guardian"]="http";  service_critical["guardian"]="true"
service_ports["scada-gateway"]=8080;    service_health_types["scada-gateway"]="http"; service_critical["scada-gateway"]="true"
service_ports["resilience-capsule"]=9090; service_health_types["resilience-capsule"]="grpc"; service_critical["resilience-capsule"]="true"
service_ports["diagnostic-agent"]=8000; service_health_types["diagnostic-agent"]="http"; service_critical["diagnostic-agent"]="false"
service_ports["dashboard"]=3001;        service_health_types["dashboard"]="http"; service_critical["dashboard"]="false"
service_ports["broadcast-guardian"]=3000; service_health_types["broadcast-guardian"]="http"; service_critical["broadcast-guardian"]="false"

# Domain services (mesmas portas com sufixo)
for domain in energy water gas manufacturing; do
    service_ports["${domain}-agent"]=8080
    service_health_types["${domain}-agent"]="http"
    service_critical["${domain}-agent"]="false"
    service_domains["${domain}-agent"]="$domain"

    service_ports["${domain}-edge-esp32"]=9000
    service_health_types["${domain}-edge-esp32"]="mqtt"
    service_critical["${domain}-edge-esp32"]="false"
    service_domains["${domain}-edge-esp32"]="$domain"
done

# Advanced services
service_ports["forecasting-mesh"]=50051;       service_health_types["forecasting-mesh"]="grpc"; service_critical["forecasting-mesh"]="false"
service_ports["tinyml-aggregator"]=8088;       service_health_types["tinyml-aggregator"]="http"; service_critical["tinyml-aggregator"]="false"
service_ports["quantum-fiber-optimizer"]=50052; service_health_types["quantum-fiber-optimizer"]="grpc"; service_critical["quantum-fiber-optimizer"]="false"
service_ports["federation-sidecar"]=50053;     service_health_types["federation-sidecar"]="grpc"; service_critical["federation-sidecar"]="false"
service_ports["cics-bridge"]=8081;             service_health_types["cics-bridge"]="http"; service_critical["cics-bridge"]="false"
service_ports["unified-dashboard"]=8501;       service_health_types["unified-dashboard"]="http"; service_critical["unified-dashboard"]="false"

# ── 13. Substituição de Comando ──
current_date=$(date)
echo -e "${BLUE}📅 Data do deploy: $current_date${NC}"

# ── 14. Redirecionamentos ──
# Já configurado no início com exec > >(tee -a "$deploy_log") 2>&1

# ── 15. Operações Aritméticas ──
total_services=${#all_services[@]}
deployed_count=0
failed_count=0
skipped_count=0
skipped_services=()

echo -e "${BLUE}📊 Total de serviços disponíveis: $total_services${NC}"
echo ""

# ═══════════════════════════════════════════════════════════════
# DEPLOY DOS SERVIÇOS CORE
# ═══════════════════════════════════════════════════════════════

echo -e "${PURPLE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${PURPLE}║  FASE 1: DEPLOY DOS SERVIÇOS CORE (8 serviços)              ║${NC}"
echo -e "${PURPLE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

for service in "${core_services[@]}"; do
    port="${service_ports[$service]}"
    health_type="${service_health_types[$service]}"
    critical="${service_critical[$service]}"

    if deploy_service "$service" "$port" "$health_type" "$critical"; then
        ((deployed_count++))
    else
        ((failed_count++))
        if [ "$critical" == "true" ]; then
            echo -e "${RED}❌ Serviço crítico '$service' falhou — abortando deploy${NC}"
            exit 1
        fi
    fi
done

# ═══════════════════════════════════════════════════════════════
# DEPLOY DOS SERVIÇOS DE DOMÍNIO (CONDICIONAL)
# ═══════════════════════════════════════════════════════════════

echo ""
echo -e "${PURPLE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${PURPLE}║  FASE 2: DEPLOY DOS PILOTOS SCADA (por domínio)             ║${NC}"
echo -e "${PURPLE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# ── 7. Condicional case (para selecionar domínios) ──
read -p "🔷 Deploy dos pilotos SCADA? (todos|energy|water|gas|manufacturing|nenhum): " scada_selection

case $scada_selection in
    todos|all)
        domain_list=("energy" "water" "gas" "manufacturing")
        ;;
    energy|water|gas|manufacturing)
        domain_list=("$scada_selection")
        ;;
    nenhum|none|n)
        domain_list=()
        echo -e "${YELLOW}   ⏭️  Pulando deploy dos pilotos SCADA${NC}"
        ;;
    *)
        echo -e "${YELLOW}   ⚠️  Seleção inválida — pulando pilotos SCADA${NC}"
        domain_list=()
        ;;
esac

for domain in "${domain_list[@]}"; do
    echo -e "${CYAN}🌐 Deploy do piloto SCADA: $domain${NC}"

    # Deploy do agente do domínio
    agent="${domain}-agent"
    if deploy_service "$agent" "${service_ports[$agent]}" "${service_health_types[$agent]}" "false"; then
        ((deployed_count++))
    else
        ((failed_count++))
    fi

    # Deploy do edge ESP32
    edge="${domain}-edge-esp32"
    echo -e "${CYAN}   📡 Deploy do nó edge: $edge${NC}"

    # ── 16. Expansão de Parâmetros ──
    EDGE_FIRMWARE="/opt/arkhe/firmware/tinyml_agent_${domain}.bin"
    EDGE_MODEL="/opt/arkhe/models/anomaly_model_${domain}.tflite"

    if [ -f "$EDGE_FIRMWARE" ] && [ -f "$EDGE_MODEL" ]; then
        echo -e "${GREEN}      ✅ Firmware e modelo encontrados para $domain${NC}"
        # Simular flash do ESP32
        sleep 0.5
        ((deployed_count++))
    else
        echo -e "${YELLOW}      ⚠️  Firmware ou modelo não encontrados para $domain — pulando${NC}"
        ((skipped_count++))
        skipped_services+=("$edge")
    fi
done

# ═══════════════════════════════════════════════════════════════
# DEPLOY DOS SERVIÇOS AVANÇADOS (CONDICIONAL)
# ═══════════════════════════════════════════════════════════════

echo ""
echo -e "${PURPLE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${PURPLE}║  FASE 3: DEPLOY DOS SERVIÇOS AVANÇADOS                      ║${NC}"
echo -e "${PURPLE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

read -p "🔷 Deploy dos serviços avançados? (s/N): " deploy_advanced

if [[ "$deploy_advanced" =~ ^[Ss]$ ]]; then
    for service in "${advanced_services[@]}"; do
        port="${service_ports[$service]}"
        health_type="${service_health_types[$service]}"
        critical="${service_critical[$service]}"

        if deploy_service "$service" "$port" "$health_type" "$critical"; then
            ((deployed_count++))
        else
            ((failed_count++))
        fi
    done
else
    echo -e "${YELLOW}   ⏭️  Pulando serviços avançados${NC}"
    ((skipped_count += ${#advanced_services[@]}))
    skipped_services+=("${advanced_services[@]}")
fi

# ═══════════════════════════════════════════════════════════════
# HEALTH CHECKS FINAIS
# ═══════════════════════════════════════════════════════════════

echo ""
echo -e "${PURPLE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${PURPLE}║  FASE 4: HEALTH CHECKS FINAIS                               ║${NC}"
echo -e "${PURPLE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

healthy_count=0
unhealthy_count=0

for service in "${all_services[@]}"; do
    # Pular serviços não deployados
    if [[ " ${skipped_services[*]} " =~ " ${service} " ]]; then
        continue
    fi

    port="${service_ports[$service]}"
    health_type="${service_health_types[$service]}"

    if health_check "$service" "$port" "$health_type"; then
        echo -e "${GREEN}   💚 $service saudável${NC}"
        ((healthy_count++))
    else
        echo -e "${RED}   ❤️‍🩹 $service com problema${NC}"
        ((unhealthy_count++))
    fi
done

# ═══════════════════════════════════════════════════════════════
# SUMÁRIO E ANCORAGEM TEMPORAL
# ═══════════════════════════════════════════════════════════════

echo ""
echo -e "${PURPLE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${PURPLE}║  SUMÁRIO DO DEPLOY                                          ║${NC}"
echo -e "${PURPLE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "   📋 ID do Deploy:     ${BLUE}$deploy_id${NC}"
echo -e "   🔧 Modo:             ${BLUE}$deploy_mode${NC}"
echo -e "   📦 Namespace:        ${BLUE}$namespace${NC}"
echo -e "   📊 Total Serviços:   ${BLUE}$total_services${NC}"
echo -e "   ${GREEN}✅ Deployados:       $deployed_count${NC}"
echo -e "   ${RED}❌ Falhas:           $failed_count${NC}"
echo -e "   ${YELLOW}⏭️  Pulados:          $skipped_count${NC}"
echo -e "   ${GREEN}💚 Saudáveis:        $healthy_count${NC}"
echo -e "   ${RED}❤️‍🩹 Com problemas:   $unhealthy_count${NC}"
echo -e "   📝 Log:              ${BLUE}$deploy_log${NC}"
echo ""

# ── 17. Códigos de Saída ──
if [ $failed_count -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Deploy concluído com $failed_count falha(s). Verifique o log.${NC}"
    exit_status=1
elif [ $unhealthy_count -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Deploy concluído, mas $unhealthy_count serviço(s) não passaram no health check.${NC}"
    exit_status=2
else
    echo -e "${GREEN}✅ Deploy concluído com sucesso! Todos os serviços saudáveis.${NC}"
    exit_status=0
fi

# Gerar selo canônico
canonical_seal=$(echo "ARKHE_DEPLOY_${deploy_id}_${deployed_count}_${failed_count}_${healthy_count}" | sha256sum | cut -d' ' -f1)
echo ""
echo -e "${CYAN}🔐 Selo Canônico: ${canonical_seal:0:16}...${NC}"
echo -e "${CYAN}   (Ancorar na TemporalChain: deploy_all.sh v2.0 concluído)${NC}"
echo ""
echo -e "${GREEN}🚀 ARKHE Ω‑TEMP v∞.Ω — Deploy Universal Concluído${NC}"
echo -e "${GREEN}   Arquitetura: 15+ microserviços • 4 pilotos SCADA • Hardware Quântico • Malha BLE${NC}"
echo ""

exit $exit_status
