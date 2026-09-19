# pacir-q

Framework PACIR-Ω para benchmarking de capacidade computacional quântica (QUOPS), com falsificadores executáveis, harnesses Kani e registo de defeitos de especificação.

## Estado da arte (2026)

| Sistema | QUOPS (Q) | QUOPS/s (Ω) |
|---|---:|---:|
| Google Willow | 216 | 2.0×10⁷ |
| IBM ibm_boston | 204 | 3.1×10⁵ |
| Quantinuum H2-1 | 1320 | 353 |
| Quantinuum Helios-1 | 1504 | 303 |
| Helios-1 + post-seleção | 1824 | 247 |
| Helios-1 + Steane ⟦7,1,3⟧ | 40 | 4.9 |

O limiar canónico é **α = 1/√e ≈ 0.6065**, não 1/e. O defeito textual
`1/e ≈ 61%` é registado no núcleo e corrigido em todos os cálculos.

## Uso

```bash
./scripts/verify-all.sh
cargo run -p pacir-q-cli -- report
cargo run -p pacir-q-cli -- falsify --id F3 --q0 1504 --q1 2000 --years 4
cargo kani -p pacir-q-kani
```

## Módulos

- `pacir-q-core`: limiar α, defeitos, falsificadores F1–F4 e estado QUOPS.
- `pacir-q-benchmarking`: INV-BENCH-01, convergência RB vs. XEB.
- `pacir-q-kani`: propriedades formais para os invariantes centrais.
- `pacir-q-cli`: comandos `alpha`, `report` e `falsify`.

## Licença

MIT OR Apache-2.0.
