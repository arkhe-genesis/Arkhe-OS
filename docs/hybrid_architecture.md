# ARKHE Hybrid Architecture — Documentação Técnica

## Visão Geral

A arquitetura híbrida FreeBSD+Linux combina:
- **FreeBSD host**: integridade, segurança, isolamento (Jails, Capsicum, ZFS)
- **Linux guests**: compatibilidade com ecossistema AI/ML (CUDA, PyTorch, etc.)

## Componentes

### Kernel Modules (C)
| Módulo | Função | Localização |
|--------|--------|-------------|
| `beaver_module.ko` | Verificação determinística de execuções | `/boot/kernel/` |
| `capsicum_helper.ko` | Política MAC para capability mode | `/boot/kernel/` |

### Userspace Binaries
| Binário | Linguagem | Função |
|---------|-----------|--------|
| `arkhe_zfs_monitor` | C | Monitor de integridade ZFS |
| `arkhe_jail_create` | C | Wrapper seguro para jail(2) |
| `arkhe_9p_server` | C | Servidor 9p para virtio-9p |
| `arkhe_temporal_anchor` | C | Cliente TemporalChain com PQC |
| `arkhe_bhyve_manager` | Rust | Gerenciador de VMs bhyve |
| `arkhe_jail_orchestrator` | Python | Orquestrador de ciclo de vida de jails |

### Scripts de Configuração
| Script | Função |
|--------|--------|
| `arkhe_zfs_setup.sh` | Cria estrutura de datasets ZFS |
| `hybrid_architecture_deploy.sh` | Deploy completo da arquitetura |

## Configuração de Jails

### Exemplo: `agent.conf`
```
name=agent_zero
path=/usr/local/jails/agent_zero
ip4_addr=10.0.0.10
hostname=arkhe-agent-zero
memory_limit_mb=2048
cpu_limit_pct=50
allow_raw_sockets=0
enable_capsicum=1
```

### Criar jail:
```sh
arkhe_jail_create /usr/local/etc/arkhe/jails/agent.conf
```

### Iniciar agente com Capsicum:
```sh
arkhe_jail_orchestrator start \
  --jail agent_zero \
  --agent /usr/local/bin/arkhe_agent \
  --args "--config /etc/arkhe/agent.yaml"
```

## Configuração de VMs Linux

### Exemplo: `linux_ai.json`
```json
{
  "vm_name": "linux_ai_01",
  "disk_path": "zroot/arkhe/vms/linux_ai_01",
  "memory_mb": 16384,
  "cpu_count": 8,
  "network_mac": "02:01:02:03:04:05",
  "network_bridge": "bridge0",
  "enable_9p": true,
  "ninep_share_path": "/mnt/arkhe_9p_export",
  "linux_kernel_path": "/usr/local/vms/kernels/vmlinuz-6.6-arkhe",
  "initrd_path": "/usr/local/vms/kernels/initrd.img-6.6-arkhe",
  "cmdline": "root=/dev/vda1 console=ttyS0 arkhe.mode=production"
}
```

### Criar e iniciar VM:
```sh
arkhe_bhyve_manager create --config linux_ai.json
arkhe_bhyve_manager start --vm linux_ai_01
```

## Compartilhamento de Dados via virtio-9p

### No guest Linux:
```bash
# Montar share 9p
mkdir -p /mnt/arkhe_shared
mount -t 9p -o trans=virtio,version=9p2000.L arkhe_shared /mnt/arkhe_shared
```

### No host FreeBSD:
- Arquivos em `/mnt/arkhe_9p_export` são acessíveis no guest via `/mnt/arkhe_shared`
- Permissões são mapeadas via UID/GID mapping configurado no bhyve

## Segurança

### Capsicum Capability Mode
- Agentes em jails com `enable_capsicum=1` entram em capability mode via `cap_enter()`
- Em capability mode: sem acesso a paths arbitrários, apenas FDs já abertos
- Validação via módulo kernel `capsicum_helper.ko`

### ZFS Security Properties
```
aclmode=restricted
aclinherit=restricted
readonly=on (para datasets de snapshot)
compression=lz4 (para performance + integridade)
```

### Firewall (pf)
- Regras em `/etc/pf.arkhe.conf`
- Tráfego entre jails/VMs isolado por padrão
- 9p server acessível apenas via localhost

## Monitoramento

### ZFS Integrity Monitor
```sh
# Logs em tempo real
tail -f /var/log/arkhe_zfs_integrity.log

# Verificar integridade manual
arkhe_zfs_monitor --verify --dataset zroot/arkhe/jails/agent_zero
```

### TemporalChain Anchoring
```sh
# Ancorar evento manualmente
arkhe_temporal_anchor \
  --institution orcid:0009-0005-2697-4668 \
  --event "jail_started" \
  --payload '{"jail":"agent_zero","timestamp":1234567890}'
```

## Troubleshooting

### Jail não inicia
```sh
# Verificar logs do jail
jls -n agent_zero
tail -f /usr/local/jails/agent_zero/var/log/messages

# Verificar recursos
rctl -u jail:agent_zero
```

### VM bhyve falha ao iniciar
```sh
# Verificar disco ZFS
zfs list zroot/arkhe/vms/linux_ai_01

# Verificar kernel modules
kldstat | grep vmm

# Logs do bhyve
tail -f /var/log/bhyve/linux_ai_01.log
```

### 9p mount falha no guest
```bash
# No guest Linux:
dmesg | grep virtio
ls -l /sys/bus/virtio/devices/

# Verificar server no host:
sockstat -4 -l | grep 5640
```

## Referências

- FreeBSD Handbook: https://docs.freebsd.org/en/books/handbook/
- Capsicum: https://www.freebsd.org/cgi/man.cgi?query=capsicum
- ZFS Administration: https://openzfs.github.io/openzfs-docs/
- bhyve: https://bhyve.org/
- 9p Protocol: https://manpages.debian.org/testing/plan9port/9p.5.en.html

---
**Canon**: ∞.Ω.∇+++.∞.docs.hybrid
**Última atualização**: 2026-05-17
**Arquiteto**: orcid:0009-0005-2697-4668
