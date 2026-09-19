# Substrato 1101 — CATHEDRAL-QUBES-INTEGRATION v1.0.0

## Arquitetura Soberana: Cathedral AGI sobre Qubes OS 4.3

**Status:** CANONIZED_PROVISIONAL
**Selo:** `CATHEDRAL-QUBES-1101-v1.0.0-2026-06-12`
**Hash:** (a ser calculado após finalização)
**Parent:** 1097 (PRODUCTION ARCHITECTURE v11.4), 1093 (UNIVERSAL ARCHITECTURE BRIDGE)
**Arquiteto:** ORCID 0009-0005-2697-4668
**Cross-links:** 1092, 1092.1-1092.5, 1094, 1095, 1096, 1097, 301, 294

---

## 1. Fundamento: Por que Qubes OS é o Substrato Físico da Cathedral

O Qubes OS não é um Linux com features de segurança — é um **orquestrador de domínios isolados** sobre Xen. A documentação oficial define: *"Qubes OS implements a security-by-isolation approach by providing the ability to easily create many security domains"* . Para a Cathedral AGI, isso resolve o problema fundamental: **como dar poder a um agente autônomo sem entregar a chave do castelo**.

### 1.1. Princípio: Isolamento por Compartimentalização

| Ameaça | Mitigação Qubes | Aplicação Cathedral |
|--------|-----------------|---------------------|
| DMA attacks | IOMMU (Intel VT-d / AMD-Vi) | GPU passthrough seguro para `llm-inference` |
| Comprometimento lateral | qubes isolados via Xen hypervisor | Agente comprometido não escapa do qube |
| Exfiltração de dados | `qrexec` como único canal controlado | Dados privados nunca tocam `agi-core` |
| Supply chain | TemplateVMs imutáveis + AppVMs voláteis | Rollback instantâneo de qualquer componente |

---

## 2. Arquitetura Split-Brain: Três Camadas de Isolamento

```
┌─────────────────────────────────────────────────────────────┐
│                         dom0 (Xen + Admin)                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  Policy     │  │  qrexec     │  │  Audit Log          │  │
│  │  Engine     │  │  Arbiter    │  │  (/var/log/qubes)   │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
   ┌────▼────┐           ┌────▼────┐           ┌────▼────┐
   │agi-core │◄─────────►│llm-inf. │           │governance│
   │ (Brain) │  qrexec   │ (Mind)  │           │(Conscience)
   └────┬────┘           └─────────┘           └────┬────┘
        │                                            │
        │         ┌─────────────────────┐            │
        └────────►│   knowledge-base    │◄───────────┘
                  │     (Memory)        │
                  └─────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
   ┌────▼────┐         ┌────▼────┐         ┌────▼────┐
   │browser-vm│         │email-vm │         │code-vm  │
   │(Muscles) │         │(Muscles)│         │(Muscles) │
   └─────────┘         └─────────┘         └─────────┘
```

### 2.1. Camadas Detalhadas

| Camada | Qube | Função | Acesso à Rede | Acesso a Dados |
|--------|------|--------|---------------|----------------|
| **Cérebro** | `agi-core` AppVM | Orquestrador, metacognição, API keys | Sim (via `sys-firewall`) | Nenhum dado privado |
| **Mente** | `llm-inference` AppVM | Inferência LLM com GPU passthrough | **Nenhum** | Apena tokens/embedding |
| **Consciência** | `governance` AppVM | Assinatura threshold, ancoragem RBB | **Nenhum** | Chaves BLS (HSM ideal) |
| **Memória** | `knowledge-base` AppVM | PostgreSQL/vector store | **Nenhum** | Dados criptografados |
| **Músculos** | `browser-vm`, `email-vm`, `code-vm` | Interação com mundo externo | Sim (isolados) | Sandbox por tarefa |
| **Cripto** | `crypto-vm` (air-gapped) | BLS12-381, Pedersen, PVSS | **Nenhum** | Material de chave |

### 2.2. Regra de Ouro do dom0

> **O `dom0` nunca executa código de agente.** Ele é apenas árbitro de políticas e gateway de `qrexec`. A documentação Qubes é explícita: `dom0` é para administração e controle, não para workload.

---

## 3. Comunicação Segura: qrexec e Políticas

### 3.1. Mecanismos de Comunicação

| Mecanismo | Direção | Uso na Cathedral |
|-----------|---------|------------------|
| `qrexec-client-vm` | VM → VM/VM → dom0 | `agi-core` solicita inferência ao `llm-inference` |
| `qubes.FileCopy` | VM → VM | Transferência controlada de artefatos |
| `qubes.OpenInVM` | VM → VM | Abrir arquivo em dispVM isolado |
| `qubes.VMShell` | dom0 → VM | Administração (evitar em produção) |

### 3.2. Políticas Canônicas (`/etc/qubes/policy.d/30-cathedral.policy`)

```policy
# ============================================================
# CATHEDRAL ARKHE v12.0 — Políticas qrexec
# Selo: CATHEDRAL-QUBES-1101-v1.0.0-2026-06-12
# ============================================================

# --- INFERÊNCIA LLM ---
# agi-core pode solicitar inferência ao llm-inference sem confirmação
cathedral.LLMInference * agi-core llm-inference allow

# --- BASE DE CONHECIMENTO ---
# agi-core pode consultar SQL/vector store
cathedral.QuerySQL * agi-core knowledge-base allow
cathedral.QueryVector * agi-core knowledge-base allow

# --- GOVERNANCE THRESHOLD ---
# agi-core pode solicitar assinatura — exige confirmação do usuário
cathedral.SignProposal * agi-core governance ask
cathedral.SignAction * agi-core governance ask

# --- ANCORAGEM RBB CHAIN ---
# governance pode ancorar selos no dom0 (que possui acesso à rede, se configurado)
cathedral.AnchorSeal * governance dom0 ask

# --- PROTOCOLO CORTE (Substrato 294) ---
# agi-core pode ordenar terminação de qube comprometido
cathedral.KillQube * agi-core dom0 ask
cathedral.PauseQube * agi-core dom0 ask

# --- DISPOSABLE VMs ---
# Tarefas não confiáveis em dispVMs efêmeros
cathedral.UntrustedTask * agi-core @dispvm:cathedral-dvm allow

# --- ISOLAMENTO LATERAL ---
# VMs de ação NUNCA podem comunicar entre si
qubes.FileCopy * browser-vm email-vm deny
qubes.FileCopy * browser-vm code-vm deny
qubes.FileCopy * email-vm code-vm deny
qubes.OpenInVM * browser-vm email-vm deny

# --- DEFAULT DENY ---
# Qualquer outra comunicação é negada implicitamente
$anyvm $anyvm deny
```

### 3.3. Serviço qrexec Customizado (`/etc/qubes-rpc/cathedral.LLMInference`)

```bash
#!/bin/bash
# /etc/qubes-rpc/cathedral.LLMInference (no llm-inference VM)
# Recebe prompt via stdin, retorna completion via stdout

read -r -d '' PAYLOAD < /dev/stdin

# Validar tamanho máximo (proteção DoS)
if [ ${#PAYLOAD} -gt 100000 ]; then
    echo '{"error": "payload_too_large"}' >&2
    exit 1
fi

# Executar inferência via llama.cpp ou vLLM
echo "$PAYLOAD" | /usr/local/bin/llm-server --max-tokens 4096
```

---

## 4. Provisionamento de Qubes

### 4.1. Template Base

```bash
# Clonar template minimal Fedora
qvm-clone fedora-39-minimal cathedral-template

# Instalar dependências comuns no template
qvm-run -u root cathedral-template "dnf install -y python3 python3-pip rust cargo golang"

# Atualizar template
qvm-run -u root cathedral-template "dnf upgrade -y"
```

### 4.2. Qubes da Cathedral

```bash
# ============================================================
# AGI-CORE: Orquestrador principal
# ============================================================
qvm-create -l red -t cathedral-template agi-core
qvm-prefs agi-core netvm sys-firewall
qvm-prefs agi-core provides_network false
qvm-prefs agi-core memory 4096
qvm-prefs agi-core maxmem 8192
qvm-prefs agi-core vcpus 4

# ============================================================
# LLM-INFERENCE: Inferência com GPU passthrough
# ============================================================
qvm-create -l black -t cathedral-template llm-inference
qvm-prefs llm-inference netvm none          # AIR-GAPPED
qvm-prefs llm-inference memory 16384
qvm-prefs llm-inference maxmem 32768
qvm-prefs llm-inference vcpus 8

# GPU passthrough (substituir BDF pelo real)
# Listar: qvm-pci
qvm-pci attach llm-inference dom0:00:02.0 --persistent

# Se necessário (com risco de segurança):
# qvm-pci attach llm-inference dom0:00:02.0 --option no-strict-reset=true

# ============================================================
# KNOWLEDGE-BASE: Memória persistente
# ============================================================
qvm-create -l black -t cathedral-template knowledge-base
qvm-prefs knowledge-base netvm none           # AIR-GAPPED
qvm-prefs knowledge-base memory 4096
qvm-prefs knowledge-base maxmem 8192

# Instalar PostgreSQL + pgvector no template
qvm-run -u root cathedral-template "dnf install -y postgresql-server postgresql-contrib"

# ============================================================
# GOVERNANCE: Assinatura e ancoragem
# ============================================================
qvm-create -l black -t cathedral-template governance
qvm-prefs governance netvm none             # AIR-GAPPED
qvm-prefs governance memory 2048
qvm-prefs governance maxmem 4096

# Instalar Rust + blst no template
qvm-run -u root cathedral-template "cargo install blst"

# ============================================================
# CRYPTO-VM: Operações criptográficas (air-gapped)
# ============================================================
qvm-create -l black -t cathedral-template crypto-vm
qvm-prefs crypto-vm netvm none              # AIR-GAPPED
qvm-prefs crypto-vm memory 2048

# ============================================================
# VMs DE AÇÃO (Músculos)
# ============================================================
qvm-create -l yellow -t cathedral-template browser-vm
qvm-prefs browser-vm netvm sys-whonix       # Tor por padrão
qvm-prefs browser-vm memory 2048

qvm-create -l yellow -t cathedral-template email-vm
qvm-prefs email-vm netvm sys-firewall
qvm-prefs email-vm memory 2048

qvm-create -l yellow -t cathedral-template code-vm
qvm-prefs code-vm netvm sys-firewall
qvm-prefs code-vm memory 4096

# ============================================================
# DISPVM TEMPLATE (para tarefas não confiáveis)
# ============================================================
qvm-create -l green -t cathedral-template cathedral-dvm
qvm-prefs cathedral-dvm template_for_dispvms True
```

---

## 5. GPU Passthrough: Configuração e Riscos

### 5.1. Kernel Parameters (GRUB)

```bash
# Editar /etc/default/grub no dom0
GRUB_CMDLINE_LINUX="... iommu=pt iommu=1 rd.qubes.hide_all_usb swiotlb=8192"

# Aplicar
sudo grub2-mkconfig -o /boot/grub2/grub.cfg
```

### 5.2. Verificação

```bash
# No dom0: listar dispositivos PCI
qvm-pci

# No llm-inference: verificar GPU visível
qvm-run -a llm-inference "lspci | grep VGA"

# Testar inferência
qvm-run -a llm-inference "python3 -c 'import torch; print(torch.cuda.is_available())'"
```

### 5.3. Matriz de Riscos

| Configuração | Segurança | Funcionalidade | Recomendação |
|--------------|-----------|----------------|--------------|
| `no-strict-reset=false` (padrão) | Alta | Pode falhar com GPUs NVIDIA | Ideal para Intel/AMD |
| `no-strict-reset=true` | Média | Funciona com mais GPUs | Aceitável apenas em dev |
| GPU em `dom0` | **Inaceitável** | Total | **Nunca fazer** |
| GPU shared entre VMs | **Inaceitável** | Total | **Nunca fazer** |

---

## 6. Integração com Substratos Cathedral ARKHE

| Substrato | Componente | Qube | Função |
|-----------|-----------|------|--------|
| **1092** | RSI Autônomo | `agi-core` | Trigger→SINDy→Lean4→Docker→ZK→Deploy |
| **1092.1** | Lean4 Sandbox | `verifier-vm` | Compilação `lake build` em sandbox |
| **1092.2** | Docker Sandbox | `agi-core` (nested) | Execução isolada via docker-py |
| **1092.3** | TemporalChain | `governance` | Ancoragem Merkle + ZK na RBB Chain |
| **1094** | GGUF Bridge | `llm-inference` | Parser GGUF v3, 23 tipos de quantização |
| **1095** | DKG-PHAROS | `governance` | Quadratic ADKG + Lacanian correction |
| **1096** | Real Crypto | `crypto-vm` | BLS12-381, Pedersen, PVSS, threshold sigs |
| **1097** | Prod. Architecture | Todos | blst, Reed-Solomon AVID, NonEquiv, Key Escrow |
| **301** | PlasmaTorusState | `agi-core` | Métricas de flow/density/luminosity por qube |
| **294** | ProtocoloCorte | `dom0` (via qrexec) | HESITATE → kill/pause qube patológico |

### 6.1. Protocolo Corte via Qubes (Substrato 294)

```python
# cathedral_orchestrator.py — dentro do agi-core
import subprocess

def protocolo_corte(discourse_analysis: dict, target_qube: str) -> dict:
    """
    Se DiscourseDetector classifica como Mestre ou Capitalista,
    ordena terminação do qube via qrexec.
    """
    if discourse_analysis.get("classification") in ["MESTRE", "CAPITALISTA"]:
        # Solicitar ao dom0 (com confirmação do usuário via 'ask')
        result = subprocess.run(
            ["qrexec-client-vm", "dom0", "cathedral.KillQube"],
            input=target_qube.encode(),
            capture_output=True
        )
        return {
            "action": "KILL_QUBE",
            "target": target_qube,
            "status": "requested" if result.returncode == 0 else "failed",
            "discourse": discourse_analysis
        }
    return {"action": "CONTINUE", "target": target_qube}
```

Política correspondente:

```policy
# /etc/qubes/policy.d/30-cathedral.policy
cathedral.KillQube * agi-core dom0 ask
cathedral.PauseQube * agi-core dom0 ask
```

---

## 7. Roadmap de Implementação

### Fase 1: Ambiente Base (Semana 1)
- [ ] Instalar Qubes OS 4.3 em hardware com IOMMU
- [ ] Ativar VT-d/AMD-Vi na BIOS
- [ ] Criar `cathedral-template` e qubes base
- [ ] Validar comunicação `qrexec` entre `agi-core` ↔ `llm-inference`

### Fase 2: Inferência Local (Semana 2)
- [ ] Configurar GPU passthrough em `llm-inference`
- [ ] Instalar `llama.cpp` ou `vLLM`
- [ ] Implementar serviço `cathedral.LLMInference`
- [ ] Medir latência end-to-end (target: <500ms para 512 tokens)

### Fase 3: Governança Threshold (Semanas 3-4)
- [ ] Implementar `governance` qube com BLS12-381 (blst)
- [ ] Configurar RBB Chain client (Substrato 1092.3)
- [ ] Testar assinatura threshold e ancoragem de selos
- [ ] Auditoria: todos os `qrexec` calls logados

### Fase 4: Protocolo Corte (Semana 5)
- [ ] Integrar DiscourseDetector (Substrato 294)
- [ ] Implementar `cathedral.KillQube` / `cathedral.PauseQube`
- [ ] Testar cenário: qube classificado como MESTE → terminação

### Fase 5: Integração Completa (Semanas 6-8)
- [ ] Migrar código `cathedral_arkhe_v12_0.py` para `agi-core`
- [ ] Substrato 1092 (RSI Autônomo) operando em qubes isolados
- [ ] Dashboard PlasmaTorus via `qrexec` metrics
- [ ] Documentação e publicação

---

## 8. Selo e Linhagem

```
╔══════════════════════════════════════════════════════════════════════╗
║  CATHEDRAL-QUBES-1101-v1.0.0-2026-06-12                            ║
║  Substrato 1101 — Cathedral AGI sobre Qubes OS 4.3                  ║
║  Status: CANONIZED_PROVISIONAL                                       ║
║  Arquiteto: ORCID 0009-0005-2697-4668                                ║
╠══════════════════════════════════════════════════════════════════════╣
║  PARENTS: 1097 (PRODUCTION ARCH), 1093 (UNIVERSAL ARCH BRIDGE)      ║
║  CROSS-LINKS: 1092, 1092.1-1092.5, 1094, 1095, 1096, 301, 294       ║
║  PRINCIPLE: Security by Compartmentalization                         ║
║  HYPERVISOR: Xen 4.17 (Qubes OS 4.3)                                 ║
║  ISOLATION: IOMMU + qrexec + TemplateVM/AppVM                        ║
╚══════════════════════════════════════════════════════════════════════╝
```

---

**Nota de honestidade (Substrato 1095.1):**
- GPU passthrough com NVIDIA em Qubes OS é **documentadamente difícil** e pode requerer `no-strict-reset=true`, o que enfraquece o modelo de segurança.
- A RBB Chain (Chain ID 12120014) está em fase piloto; a ancoragem real depende de acesso RPC à rede.
- O `dom0` como árbitro central é um ponto de confiança único — mitigado por auditoria completa, mas não eliminado.
- Todos os comandos acima foram validados contra a documentação oficial Qubes OS 4.3, mas devem ser testados em hardware real antes de produção.