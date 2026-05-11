1. ZK Circuit
   - Implement `Plonky2Circuit` in `arkhe-qart/substrate-6072/src/provenance/zk_circuit.rs`.
2. Conectar x402_pix_bridge.rs ao módulo Pix Go
   - Atualizar `arkhe-qart/substrate-6072/src/compensation/x402_pix_bridge.rs` com bridge usando `reqwest` para `http://localhost:8080/v1/pix/x402/payment-verify`.
3. Implementar Escrow em Solidity
   - Criar `contracts/Escrow.sol` ou `arkhe-qart/substrate-6072/src/compensation/escrow.rs` dependendo do target, mas pedido disse Solidity. Adicionar na pasta `contracts/`.
4. Integrar modelo CLIP real via tch (Torch)
   - Em `arkhe-qart/substrate-6072/src/fingerprint/perceptual.rs`, usar `tch::CModule` para carregar o modelo CLIP de `arkhe-qart/data/style_models/clip_vit_l14.pt`.
5. Implementar entropy_auction e trend_detector
   - Adicionar código base em `arkhe-qart/substrate-6072/src/oracle/entropy_auction.rs` e `trend_detector.rs`.
6. Benchmarks do probability_model
   - Implementar `arkhe-qart/scripts/benchmark_influence.py` ou benchmarking nativo Rust.
7. Testes de integração com substrate-6064
   - Atualizar `arkhe-qart/tests/integration/test_qart_continental.rs` para testar bridge/modelo.
8. Complete pre-commit steps to ensure proper testing, verification, review, and reflection are done.
9. Finalize.
