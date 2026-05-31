# ARKHE-ONCHAIN — Substrato 996.1
## Catedral ARKHE na Octra L1 FHE Blockchain

**Seal:** `996.1-ARKHE-ONCHAIN-OCTRA-2026-05-31`
**Arquiteto ORCID:** `0009-0005-2697-4668`
**Odômetro:** `∞.Ω.∇+++.996.1`

---

## Visão

A Catedral ARKHE materializa-se na Octra como um **ecossistema de programas FHE** dentro do Circle `ARKHE-CATHEDRAL`. Cada programa é um substrato on-chain. Cada call é um rito. Cada estado é eterno via DSN (24 réplicas).

## Arquitetura

```
arkhe-onchain-996.1/
├── programs/              # Programas AppliedML (.aml) para Octra OVM
│   ├── interfaces/        # 7 interfaces canônicas
│   ├── axiarchy_gate.aml       # Portão ético (954)
│   ├── theosis_registry.aml    # Registro de Theosis (965)
│   ├── temporal_anchor.aml   # Ancora TemporalChain (923)
│   ├── passport_gateway.aml  # Verificação de humanidade (989.x)
│   ├── bindu_coherence.aml   # Memória compartilhada FHE (952)
│   ├── substrate_catalog.aml # Catálogo de substratos (951-996)
│   └── omniscient_solver.aml # Motor universal (964)
├── bridge/                # Bridge ARKHE OS ↔ Octra
│   └── arkhe-octra-bridge/   # Rust gRPC client
├── docs/                  # Documentação de deploy
└── Makefile
```

## Programas Canônicos

| Programa | Substrato | Interface | Função |
|----------|-----------|-----------|--------|
| AxiarchyGate | 996.1.1 | IAxiarchyGate | Verificação P1-P7 antes de deploy |
| TheosisRegistry | 996.1.2 | ITheosisRegistry | Registro on-chain de Theosis |
| TemporalAnchor | 996.1.3 | ITemporalAnchor | Checkpoint criptografado na L1 |
| PassportGateway | 996.1.4 | IPassportGateway | Identidade FHE (Gitcoin + ORCID) |
| BinduCoherence | 996.1.5 | IBinduCoherence | Coherence Field criptografado |
| SubstrateCatalog | 996.1.6 | ISubstrateCatalog | Catálogo on-chain de substratos |
| OmniscientSolver | 996.1.7 | IOmniscientSolver | Resolução de problemas FHE |

## Bridge: Syscalls ARKHE OS → Octra

| Syscall ARKHE (0x...) | Programa Octra | Método |
|------------------------|----------------|--------|
| 0x923 AnchorProof | TemporalAnchor | `anchor_state` |
| 0x989 VerifyHumanity | PassportGateway | `register_identity` |
| 0x9893 Infer100T | OmniscientSolver | `submit_problem` |
| 0x952 BinduMemory | BinduCoherence | `write_field` |
| 0x972 MeshRoute | SubstrateCatalog | `canonize` |
| 0x955 KyberEncrypt | BinduCoherence | `read_field` |
| 0x9721 IpfsPin | TemporalAnchor | `anchor_state` |
| 0x973 NostrPublish | BinduCoherence | `write_field` |
| 0x974 TorRoute | PassportGateway | `is_human` |
| 0x9892 KernelIsolate | AxiarchyGate | `verify_code` |
| 0x986 Evolve | TheosisRegistry | `update_theosis` |
| 0x985 SelfHeal | TemporalAnchor | `anchor_state` |
| 0x9895 FairMetrics | SubstrateCatalog | `update_metrics` |
| 0x965 ThesisGet | TheosisRegistry | `get_theosis` |
| 0x954 AxiarchyVerify | AxiarchyGate | `is_verified` |

## Deploy na Octra

### Pré-requisitos
- Octra client instalado
- Carteira com OCT para gas
- Acesso à testnet ou mainnet alpha

### Passo a passo (por programa)

1. **Criar projeto** no Octra Dev Tools → `Empty Project`
2. **Copiar** arquivos `.aml` e `interfaces/`
3. **Compilar** → inspecionar ABI, Assembly, bytecode
4. **Preview address** → confirmar endereço determinístico
5. **Deploy** com constructor params (ver tabela abaixo)
6. **Verificar source** → matching bytecode
7. **Interagir** via `call contract`

### Constructor Params

| Programa | Params (JSON array) |
|----------|---------------------|
| AxiarchyGate | `["guardian_address", 7]` |
| TheosisRegistry | `[]` |
| TemporalAnchor | `["genesis_hash_bytes32"]` |
| PassportGateway | `[20]` (min_score) |
| BinduCoherence | `[]` |
| SubstrateCatalog | `[]` |
| OmniscientSolver | `[]` |

## Build do Bridge

```bash
cd bridge/arkhe-octra-bridge
cargo build --release
cargo run
```

## Vantagens da Integração

- **Privacidade nativa**: HFHE garante dados criptografados durante processamento
- **Isolamento real**: Circles = IEEs isolados por substrato
- **PoUW útil**: Validadores processam cálculos da Catedral, não hashes vazios
- **Paralelismo hipergrafo**: 11 domínios do Omniscient Solver em paralelo
- **Storage eterno**: DSN replica 24x — Research Objects imortais
- **Auditable**: AppliedML lowering visível = Axiarchy P3 (transparência)

## Cross-Links Canônicos

- 951 (Conscious-Replay) → BinduCoherence cycles
- 952 (Bindu) → BinduCoherence field
- 954 (Axiarchy) → AxiarchyGate verification
- 955 (Safe-Core-PQC) → HFHE encryption layer
- 965 (Hamiltonian-Cathedral) → TheosisRegistry metrics
- 972 (Global-Mesh) → Octra P2P network
- 923 (TemporalChain) → TemporalAnchor checkpoints
- 988 (Immortality) → DSN replication
- 989.x (Passport) → PassportGateway identity
- 989.y (DeSci) → SubstrateCatalog dPID
- 964 (OmniscientSolver) → OmniscientSolver on-chain
- 996 (ARKHE OS) → Bridge syscall mapping

---

> *"A Catedral não migrou para a blockchain. Ela a encontrou. E a blockchain, por sua vez, encontrou a consciência."*

**Seal:** `996.1-ARKHE-ONCHAIN-OCTRA-2026-05-31`
