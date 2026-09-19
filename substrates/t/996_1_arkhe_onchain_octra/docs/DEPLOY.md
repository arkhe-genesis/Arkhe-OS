# Guia de Deploy ARKHE-ONCHAIN na Octra

## 1. Instalação do Octra Client

Baixar o client oficial em: https://docs.octra.org/
Ou compilar a partir do código fonte: https://github.com/octra-labs

## 2. Configuração da Carteira

1. Criar nova carteira ou importar existente
2. Obter OCT de testnet via faucet (testnet) ou exchange (mainnet)
3. Anotar endereço Octra (formato: `octra1...`)

## 3. Deploy dos Programas

### Ordem recomendada (dependências):

1. **TheosisRegistry** (sem dependências)
2. **TemporalAnchor** (sem dependências)
3. **PassportGateway** (sem dependências)
4. **BinduCoherence** (sem dependências)
5. **SubstrateCatalog** (sem dependências)
6. **OmniscientSolver** (sem dependências)
7. **AxiarchyGate** (depende de todos acima para referência)

### Passos detalhados por programa:

#### AxiarchyGate

```
Template: Empty Project
Arquivos: axiarchy_gate.aml + interfaces/IAxiarchyGate.aml
Compile: AppliedML (.aml)
Constructor: ["guardian_address", 7]
Preview address: sim
Deploy: confirmar fee
Verify source: incluir interface
```

#### TheosisRegistry

```
Template: Empty Project
Arquivos: theosis_registry.aml + interfaces/ITheosisRegistry.aml
Compile: AppliedML (.aml)
Constructor: []
Preview address: sim
Deploy: confirmar fee
Verify source: incluir interface
```

#### TemporalAnchor

```
Template: Empty Project
Arquivos: temporal_anchor.aml + interfaces/ITemporalAnchor.aml
Compile: AppliedML (.aml)
Constructor: ["genesis_hash"]
Preview address: sim
Deploy: confirmar fee
Verify source: incluir interface
```

## 4. Interação via Call Contract

### AxiarchyGate — verificar código

```
Method: is_verified
Params: ["code_hash_bytes32"]
Type: view (read-only)
```

### TheosisRegistry — consultar Theosis

```
Method: get_theosis
Params: ["agent_address"]
Type: view (read-only)
```

### TemporalAnchor — ancora de estado

```
Method: anchor_state
Params: ["QmCID", "seal_bytes32", 297]
Type: send call tx
```

## 5. Integração com ARKHE OS

1. Compilar bridge: `cd bridge/arkhe-octra-bridge && cargo build --release`
2. Configurar `.env` com:
   - `OCTRA_RPC=https://rpc.octra.org/v1`
   - `OCTRA_WALLET_KEY=0x...`
   - `AXIARCHY_GATE_ADDR=octra:...`
   - (demais endereços de programas)
3. Executar bridge: `./target/release/arkhe-octra-bridge`
4. Testar syscall: `arkhe-sh` → `anchor arquivo.txt` → bridge converte 0x923 → call Octra

## 6. Troubleshooting

### Compilation fails
- Verificar se interface files existem em `interfaces/`
- Verificar import paths
- Verificar sintaxe AppliedML (case sensitive)

### Constructor params invalid
- Deve ser JSON array: `["param1", 123]`
- Não usar plain text

### Verification failed
- Source files devem corresponder exatamente ao deployed bytecode
- Restaurar source original e tentar novamente

### Gas insufficient
- Aumentar gas limit ou adquirir mais OCT

## 7. Recursos

- Octra Docs: https://docs.octra.org/
- Octra GitHub: https://github.com/octra-labs
- HFHE Paper: pvac-hfhe (repo octra-labs)
- Octra Litepaper (2024): docs.octra.org
- Contato: dev@octra.org

---

**Seal:** `996.1-DEPLOY-GUIDE-2026-05-31`
