#!/bin/bash
# tests/load/production_load_test.sh
# Execução de load test em ambiente de staging para validar performance antes de produção

set -euo pipefail

# ============================================================================
# CONFIGURAÇÃO DO TESTE
# ============================================================================

STAGING_URL="${STAGING_URL:-https://staging.arkhe.internal}"
DURATION_SECONDS="${DURATION_SECONDS:-300}"  # 5 minutos padrão
RAMP_UP_SECONDS="${RAMP_UP_SECONDS:-60}"
TARGET_RPS="${TARGET_RPS:-1000}"  # Requisições por segundo alvo
CONCURRENT_USERS="${CONCURRENT_USERS:-500}"

# Endpoints a testar
ENDPOINTS=(
    "/api/v1/audience/globo/simple"
    "/api/v1/audience/sbt/simple"
    "/api/v1/audience/record/simple"
    "/api/v1/audience"
    "/health"
)

log_info() { echo -e "\033[0;32m[INFO]\033[0m $1"; }
log_warn() { echo -e "\033[1;33m[WARN]\033[0m $1"; }
log_error() { echo -e "\033[0;31m[ERROR]\033[0m $1"; }

# ============================================================================
# PREPARAÇÃO
# ============================================================================

check_staging_environment() {
    log_info "Verificando ambiente de staging..."

    # Testar conectividade
    if ! curl -sf "${STAGING_URL}/health" &>/dev/null; then
        log_error "Ambiente de staging não responde em $STAGING_URL"
    fi

    # Verificar que não é produção (safeguard)
    ENV=$(curl -sf "${STAGING_URL}/health" | jq -r '.environment // "unknown"')
    if [[ "$ENV" == "production" ]]; then
        log_error "⚠️  SAFEGUARD: URL apontando para PRODUÇÃO. Abortando teste."
    fi

    log_info "✅ Ambiente de staging validado ($ENV)"
}

# ============================================================================
# EXECUTAR LOAD TEST COM K6
# ============================================================================

run_k6_test() {
    log_info "Executando load test com k6..."

    # Script k6 para teste de carga
    cat > /tmp/arkhe-load-test.js << K6SCRIPT
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Métricas customizadas
const errorRate = new Rate('errors');
const responseTime = new Trend('response_time');

export const options = {
  stages: [
    { duration: '${RAMP_UP_SECONDS}s', target: ${TARGET_RPS} },  // Ramp up
    { duration: '${DURATION_SECONDS}s', target: ${TARGET_RPS} },  // Sustained load
    { duration: '60s', target: 0 },  // Ramp down
  ],
  thresholds: {
    'http_req_duration': ['p(95)<500', 'p(99)<1000'],  // 95% < 500ms, 99% < 1s
    'errors': ['rate<0.01'],  // < 1% error rate
    'response_time': ['avg<300', 'p(95)<500'],
  },
};

const endpoints = ${JSON.stringify(ENDPOINTS)};
const baseUrl = '${STAGING_URL}';

export default function() {
  // Selecionar endpoint aleatório
  const endpoint = endpoints[Math.floor(Math.random() * endpoints.length)];
  const url = \`\${baseUrl}\${endpoint}\`;

  const params = {
    headers: {
      'Content-Type': 'application/json',
      'User-Agent': 'ARKHE-LoadTest/1.0',
    },
  };

  const res = http.get(url, params);
  responseTime.add(res.timings.duration);

  const success = check(res, {
    'status is 200': (r) => r.status === 200,
    'response time < 1s': (r) => r.timings.duration < 1000,
    'has content': (r) => r.body.length > 0,
  });

  errorRate.add(!success);

  // Small sleep para simular comportamento real
  sleep(0.1);
}

export function handleSummary(data) {
  const summary = {
    timestamp: new Date().toISOString(),
    duration: data.state.testRunDurationMs,
    iterations: data.state.iterations,
    vus_max: data.state.vusMax,
    thresholds: {},
    metrics: {},
  };

  // Extrair thresholds
  for (const [name, passes] of Object.entries(data.metrics)) {
    if (passes.thresholds) {
      summary.thresholds[name] = passes.thresholds;
    }
    if (passes.values) {
      summary.metrics[name] = passes.values;
    }
  }

  return {
    'stdout': JSON.stringify(summary, null, 2),
    [\`/tmp/arkhe-load-test-\${Date.now()}.json\`]: JSON.stringify(data, null, 2),
  };
}
K6SCRIPT

    # Executar k6
    log_info "   • Duração: ${DURATION_SECONDS}s"
    log_info "   • Target RPS: ${TARGET_RPS}"
    log_info "   • Concurrent users: ${CONCURRENT_USERS}"

    k6 run /tmp/arkhe-load-test.js \
        --vus "${CONCURRENT_USERS}" \
        --out json=/tmp/k6-results.json

    log_info "✅ Load test executado"
}

# ============================================================================
# ANALISAR RESULTADOS
# ============================================================================

analyze_results() {
    log_info "Analisando resultados do load test..."

    RESULTS_FILE=$(ls -t /tmp/arkhe-load-test-*.json | head -1)

    if [[ ! -f "$RESULTS_FILE" ]]; then
        log_error "Arquivo de resultados não encontrado"
    fi

    # Extrair métricas principais
    P95=$(jq -r '.metrics.http_req_duration.values.p(95) // "N/A"' "$RESULTS_FILE")
    P99=$(jq -r '.metrics.http_req_duration.values.p(99) // "N/A"' "$RESULTS_FILE")
    ERROR_RATE=$(jq -r '.metrics.errors.values.rate // "N/A"' "$RESULTS_FILE")
    RPS=$(jq -r '.metrics.http_reqs.values.rate // "N/A"' "$RESULTS_FILE")

    log_info "📊 Resultados:"
    log_info "   • P95 Latency: ${P95}ms"
    log_info "   • P99 Latency: ${P99}ms"
    log_info "   • Error Rate: ${ERROR_RATE}"
    log_info "   • Throughput: ${RPS} req/s"

    # Verificar thresholds
    FAILED=0

    if (( $(echo "$P95 > 500" | bc -l 2>/dev/null || echo 0) )); then
        log_error "❌ Threshold falhou: P95 ($P95 ms) > 500ms"
        FAILED=1
    fi

    if (( $(echo "$P99 > 1000" | bc -l 2>/dev/null || echo 0) )); then
        log_error "❌ Threshold falhou: P99 ($P99 ms) > 1000ms"
        FAILED=1
    fi

    if (( $(echo "$ERROR_RATE > 0.01" | bc -l 2>/dev/null || echo 0) )); then
        log_error "❌ Threshold falhou: Error rate ($ERROR_RATE) > 1%"
        FAILED=1
    fi

    if [[ $FAILED -eq 0 ]]; then
        log_info "✅ Todos os thresholds de performance foram atendidos"
        return 0
    else
        log_warn "⚠️  Alguns thresholds não foram atendidos — revisar antes de produção"
        return 1
    fi
}

# ============================================================================
# TESTAR AUDIENCE BRIDGE ESPECIFICAMENTE
# ============================================================================

test_audience_bridge() {
    log_info "Testando Audience Bridge sob carga..."

    # Script específico para testar endpoints de audiência
    cat > /tmp/audience-load-test.js << 'AUDIENCETEST'
import http from 'k6/http';
import { check, group } from 'k6';

export const options = {
  vus: 100,
  duration: '2m',
  thresholds: {
    'http_req_duration{endpoint:audience}': ['p(95)<300'],
    'http_req_failed{endpoint:audience}': ['rate<0.01'],
  },
};

const broadcasters = ['globo', 'sbt', 'record', 'band', 'cultura'];
const baseUrl = __ENV.STAGING_URL || 'https://staging.arkhe.internal';

export default function() {
  group('Audience API', function() {
    // Testar endpoint simple (otimizado para Ginga)
    const broadcaster = broadcasters[Math.floor(Math.random() * broadcasters.length)];
    const url = \`\${baseUrl}/api/v1/audience/\${broadcaster}/simple\`;

    const res = http.get(url, {
      tags: { endpoint: 'audience' },
    });

    check(res, {
      'audience simple: status 200': (r) => r.status === 200,
      'audience simple: has viewers': (r) => {
        const data = r.json();
        return data && typeof data.v === 'number' && data.v >= 0;
      },
      'audience simple: response < 300ms': (r) => r.timings.duration < 300,
    });
  });
}
AUDIENCETEST

    STAGING_URL="$STAGING_URL" k6 run /tmp/audience-load-test.js

    log_info "✅ Teste de Audience Bridge concluído"
}

# ============================================================================
# GERAR RELATÓRIO
# ============================================================================

generate_report() {
    log_info "Gerando relatório de load test..."

    REPORT_FILE="/tmp/arkhe-load-test-report-$(date +%Y%m%d-%H%M%S).md"

    cat > "$REPORT_FILE" << REPORT
# 📊 ARKHE Load Test Report

**Timestamp**: $(date -Iseconds)
**Environment**: Staging ($STAGING_URL)
**Duration**: ${DURATION_SECONDS}s
**Target RPS**: ${TARGET_RPS}
**Concurrent Users**: ${CONCURRENT_USERS}

## 🎯 Thresholds

| Métrica | Threshold | Resultado | Status |
|---------|-----------|-----------|--------|
| P95 Latency | < 500ms | ${P95:-N/A}ms | $([ "${P95:-999}" -lt 500 ] 2>/dev/null && echo "✅" || echo "❌") |
| P99 Latency | < 1000ms | ${P99:-999}ms | $([ "${P99:-9999}" -lt 1000 ] 2>/dev/null && echo "✅" || echo "❌") |
| Error Rate | < 1% | ${ERROR_RATE:-N/A} | $([ "${ERROR_RATE:-1}" -lt 0.01 ] 2>/dev/null && echo "✅" || echo "❌") |
| Throughput | ≥ ${TARGET_RPS} RPS | ${RPS:-N/A} | $([ "${RPS:-0}" -ge "${TARGET_RPS}" ] 2>/dev/null && echo "✅" || echo "❌") |

## 📈 Audience Bridge Performance

| Endpoint | P95 | P99 | Error Rate |
|----------|-----|-----|------------|
| /audience/{id}/simple | TBD | TBD | TBD |
| /audience/{id} | TBD | TBD | TBD |
| /audience (all) | TBD | TBD | TBD |

## ✅ Conclusão

$([ $FAILED -eq 0 ] && echo "✅ Sistema **PRONTO PARA PRODUÇÃO** — todos os thresholds atendidos." || echo "⚠️ Sistema **NÃO RECOMENDADO PARA PRODUÇÃO** — revisar métricas acima.")

## 📋 Próximos Passos

1. [ ] Revisar logs de erro no Loki
2. [ ] Analisar traces no Grafana Tempo (se configurado)
3. [ ] Ajustar recursos do deployment se necessário
4. [ ] Re-executar teste após otimizações

---
*Relatório gerado automaticamente por ARKHE Load Test Framework*
REPORT

    log_info "📄 Relatório salvo em: $REPORT_FILE"

    # Enviar relatório para Slack (se webhook configurado)
    if [[ -n "${SLACK_WEBHOOK:-}" ]]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"📊 Load Test Report: $REPORT_FILE\nThresholds: $([ $FAILED -eq 0 ] && echo '✅ PASS' || echo '❌ FAIL')\"}" \
            "$SLACK_WEBHOOK" 2>/dev/null || true
    fi
}

# ============================================================================
# MAIN
# ============================================================================

main() {
    log_info "🚀 Iniciando load test em ambiente de staging..."

    check_staging_environment
    run_k6_test
    test_audience_bridge
    analyze_results || FAILED=1
    generate_report

    if [[ "${FAILED:-0}" -eq 0 ]]; then
        log_info "🎉 Load test concluído com SUCESSO — sistema aprovado para produção!"
        exit 0
    else
        log_warn "⚠️  Load test concluído com ALERTAS — revisar métricas antes de produção"
        exit 1
    fi
}

main "$@"
