# 📡 Guia de Deploy — ARKHE TV + GatesAir Maxiva

## 1. Pré‑requisitos

- Transmissor **GatesAir Maxiva** com firmware ≥ 4.2.1 (suporte ATSC 3.0)
- Acesso de rede ao Maxiva via porta **443** (REST) e **161** (SNMP)
- Credenciais de administrador do Maxiva
- Servidor ARKHE TV Gateway implantado (ver `deploy/docker-compose.yml`)
- Conectividade entre o Gateway ARKHE e o Maxiva (mesma VLAN ou rota IP)

## 2. Estabelecimento de Conectividade

```bash
# Teste de ping
ping -c 4 <ip-maxiva>

# Teste de porta REST
curl -k -u admin:password https://<ip-maxiva>/api/v3/status

# Teste SNMP
snmpwalk -v2c -c public <ip-maxiva> 1.3.6.1.4.1.3444
```

## 3. Execução do Script de Conectividade

```bash
python3 gatesair_maxiva_connectivity.py \
  --host 192.168.10.50 \
  --username admin \
  --password "broadcast2026" \
  --snmp-community public \
  --anchor-to-temporal
```

**Saída esperada:**
```
✅ REST API: reachable (Maxiva v4.2.3)
✅ SNMP: reachable
✅ ICMP: reachable
✅ SNMP Trap: configured → arkhe-gateway:8053
✅ Syslog: configured → arkhe-gateway:514
🌀 Φ_C Baseline: 0.9500
🔐 Temporal Seal: a3f2b8c9d1e4f5a6
```

## 4. Configuração de Canal ATSC 3.0

Via interface web do Maxiva ou API REST:

```bash
curl -k -X POST https://<ip-maxiva>/api/v3/channels \
  -u admin:password \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ARKHE_TEST_CHANNEL",
    "frequency_mhz": 557.0,
    "bandwidth_khz": 6000,
    "modulation": "ATSC3",
    "plps": [
      {"id": 1, "modulation": "QPSK", "code_rate": "4/15"},
      {"id": 2, "modulation": "256NUC", "code_rate": "10/15"}
    ],
    "ldm_enabled": true,
    "ldm_injection_db": -10.0
  }'
```

## 5. Validação da Integração

```bash
python3 gatesair_maxiva_validation.py \
  --host 192.168.10.50 \
  --username admin \
  --password "broadcast2026"
```

**Testes executados:**
1. ✅ Conectividade completa (REST + SNMP)
2. ✅ Métricas SNMP (CNR=28.5dB, MER=32.1dB, BER=1.2e-7)
3. ✅ Configuração LDM (injeção -10.0dB)
4. ✅ Injeção de metadados ARKHE

## 6. Troubleshooting

| Sintoma | Causa Provável | Solução |
|---------|---------------|---------|
| REST API unreachable | Firewall bloqueando porta 443 | Liberar regra no firewall |
| SNMP timeout | Comunidade SNMP incorreta | Verificar `snmp_community` |
| LDM não disponível | Firmware desatualizado | Atualizar Maxiva para ≥ 4.2.1 |
| Φ_C baseline baixo | Múltiplos serviços falhando | Verificar conectividade de rede |

## 7. Suporte

- **Documentação ARKHE**: https://arkhe.org/docs/tv/gatesair
- **GatesAir Support**: https://www.gatesair.com/support
- **Emergência**: security@arkhe.org
