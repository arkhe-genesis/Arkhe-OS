---
type: concept
title: BIP-1 Hardware Specifications
updated: 2026-04-04
source_count: 1
tags: [concept, hardware, BIP-1]
---

# [[BIP-1 Hardware Specifications]]

## Summary
> The Bio‑Implante de Pulso (BIP‑1) is a subcutaneously implanted device that uses a chip‑scale Brillouin laser, an APD, and an ARM Cortex‑M7 to detect Fibonacci anyon statistics and generate a Bio‑Root of Trust.

## Key Specifications (Baseline)
- **Optical source**: Brillouin laser, 674 nm, linewidth 1.5 kHz, stability 8.8×10⁻¹³ at 20 ms.
- **APD**: Single‑photon avalanche diode, responsivity 0.5 A/W, gain M=100, dark count 50 cps.
- **Analog Front‑End**: TIA (100 kΩ), VGA (0–40 dB), LPF (200 kHz), comparator threshold 50 mV.
- **Digital**: ARM Cortex‑M7, 100 MHz, 512 KB flash, 128 KB SRAM.
- **Power**: 3.3 V supply, total consumption < 10 mW.
- **Mechanical**: Titanium chassis (Grade 23 ELI), 12 mm × 8 mm × 3 mm.

## Source References
- [[2026-04-04_anyons_in_microtubules]] – confirmed APD parameters (μ₁ = 1.02, dark count 50 cps).

## Related Components
- [[APD Analog Front-End]]
- [[Brillouin Laser (Arkhe)]]
- [[Gold Standard for BIP-1]]

## See Also
- [[MOC: BIP-1 Hardware Stack]]
