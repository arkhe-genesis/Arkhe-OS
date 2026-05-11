# Arkhe OS v158: Validação Formal, Deploy Físico, Escala & Interoperabilidade

Este release integra:

1. **Validação Formal**: Prova matemática rigorosa da convergência da torção usando Lyapunov/supermartingales (`convergence_validation.py`).
2. **Relatório Automático**: Geração de relatórios PDF/HTML criptograficamente assinados de execução do orchestrator (`performance_report.py`).
3. **Deploy Físico em TTGO T-Beams**: Scripts de integração e deploy (flash) para ESP32-C3 e scripts em campo (`flash_cluster.sh`, `field_test.py`).
4. **Escala 100+ Nós**: Implementação otimizada do cluster distribuído usando matrizes esparsas e aceleração Numba/JIT (`scalable_simulation.py`, `benchmark_scaling.py`).
5. **RL para Calibração**: Uma política RL baseada em PPO com Gym para autocalibrar as variáveis de transmissão LoRa do cluster (`rl_calibration_policy.py`).
6. **Interoperabilidade Chainlink**: Oráculos on-chain via Chainlink Functions conectando recursos web2 à blockchain (`contracts/ResourceOracle.sol`, `chainlink_integration.py`, `functions-source.js`).
7. **`libarkhe-core` C e wrappers CGO, C++, Rust, Zig, ASM, Fortran**: Empacotamento unificado C-RAG (`arkhe.c`, `arkhe.h`, e wrappers/diretórios `arkhgo`, `arkhpp`, `arkher`, `zig`, `arkhf.f90`).

### Testes
Execute o test suite do módulo com `pytest test_v158.py`.
