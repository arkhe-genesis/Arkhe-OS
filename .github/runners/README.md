# ARKHE CI/CD Specialized Runners

## Arquitetura de Runners

```
.github/runners/
├── arm64-hsm/
│   ├── Dockerfile              # Runner ARM64 com emulação HSM
│   ├── hsm_mock_service.py     # Serviço de mock HSM para CI
│   └── setup.sh                # Script de provisionamento
├── gpu-delta-mem/
│   ├── Dockerfile              # Runner GPU para treinamento δ‑mem
│   ├── cuda_config.yaml        # Configuração CUDA otimizada
│   └── quantization_utils.py   # Utilitários de quantização
├── airgapped-audit/
│   ├── Dockerfile              # Runner isolado para auditorias críticas
│   ├── offline_scan.sh         # Scanner de segurança offline
│   └── audit_signer.py         # Assinador PQC para artefatos de auditoria
└── runner-registry.json        # Registro central de capacidades por runner
```

## Especificações Técnicas

### ARM64 HSM Runner
- **Arquitetura**: ARM64 (Graviton3 / Apple M2)
- **HSM Mock**: Emulação PKCS#11 com libp11 + SoftHSM
- **PQC Support**: liboqs com CRYSTALS-Dilithium3
- **Use Case**: Assinatura de selos canônicos, validação de integridade

### GPU δ‑mem Runner
- **GPU**: NVIDIA A10G / T4 (16GB VRAM mínimo)
- **CUDA**: 12.1+ com cuDNN 8.9
- **Quantização**: ONNX Runtime com INT8/FP16
- **Use Case**: Treinamento online δ‑mem, inference acelerada em CI

### Air-gapped Audit Runner
- **Isolamento**: Sem acesso à internet, volumes read-only
- **Scanner**: Bandit, Trivy, Semgrep em modo offline
- **Assinatura**: PQC local com chaves efêmeras
- **Use Case**: Auditorias de segurança crítica, compliance forense
