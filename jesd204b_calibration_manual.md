## 🔷 JESD204B CALIBRATION MANUAL — ARKHE PULSE SEQUENCER

### 1. Introduction
The Arkhe Pulse Sequencer uses a JESD204B subclass 1 link to drive a high‑speed DAC (AD9174). Deterministic latency is critical to ensure that the I/Q waveforms for different qubits maintain the same phase relationship across power cycles. This manual describes the calibration procedure.

### 2. Hardware Setup
- **FPGA**: Zynq‑7000 XC7Z045‑FFG900‑2 with GTX transceivers.
- **DAC**: AD9174 (dual 16‑bit, 14 Gbps lane rate, 4 lanes).
- **Clock**: External LMK04828 provides 156.25 MHz reference clock and SYSREF.
- **Cables**: High‑quality matched length for JESD lanes and SYSREF.

### 3. Initialization Flow
1. Program the FPGA bitstream.
2. Initialize the LMK04828 via SPI to generate:
   - 156.25 MHz GTX reference clock.
   - SYSREF at the required multi‑frame rate (typically 10 MHz or 5 MHz).
3. Configure the AD9174 via SPI: set JESD mode (L=4, M=2, F=1, S=1), lane rate, etc.
4. Enable the JESD204B GTX transceivers in the FPGA.
5. Issue a SYSREF and verify that the DAC reports `LINK_STATE = DATA`.

### 4. Deterministic Latency Calibration Steps
#### 4.1 Align SYSREF to Multi‑Frame Clock
- The SYSREF must be captured with a known phase relative to the multi‑frame clock.
- In the FPGA, use the JESD204B core's SYSREF sampling register (`gt_rx_sysref_phase`) to measure the SYSREF position.
- Adjust the LMK04828 digital delay (step size < 10 ps) until the SYSREF transitions safely away from the multi‑frame clock edges.

#### 4.2 Lane Delay Equalization
- The AD9174 reports lane FIFO fill levels (`lane0_fifo_depth` etc.).
- In the FPGA, adjust the GTX TX phase interpolator (`TXPI`) in steps of 1/128 UI to minimise the peak‑to‑peak FIFO variation across lanes.
- Target: all lanes within ±1 FIFO unit (32‑bit words).

#### 4.3 Verify Latency with Test Pattern
- Load a known digital ramp on each lane (e.g., `0x00, 0x01, 0x02, …`).
- Using an oscilloscope on the DAC analog output, measure the delay between the JESD SYSREF assertion and the corresponding analog sample.
- Compare the latency across multiple power cycles and devices; deterministic latency requires the same delay every time.
- If variation is observed, check SYSREF routing and GTX reset sequence.

### 5. Eye Scan and Margin Analysis
- Use Vivado's IBERT tool (IP: "In‑system IBERT") to scan GTX RX eye after loopback (or using a spare transceiver monitoring the same lane).
- The eye diagram should have a horizontal opening > 0.5 UI at BER 1e-12.
- If margin is insufficient:
  - Tune GTX TX pre‑emphasis (`TX_DIFF_CTRL`, `TX_PRE_CURSOR`, `TX_POST_CURSOR`).
  - Verify PCB impedance (100 Ω differential).
  - Reduce lane rate to 12 Gbps as fallback.

### 6. Integration with Pulse Sequencer
- After JESD204B link is stable, the pulse sequencer FSM starts reading from the waveform BRAM and pushing samples to the JESD TX AXI Stream interface.
- During calibration, we can inject a constant tone (single frequency) via the control registers and verify the DAC output spectrum.
- Confirm that DRAG‑shaped pulses produce the expected reduction in leakage to higher transmon levels (measured by a spectrum analyser after down‑conversion).

### 7. Automation Script (Tcl)
```tcl
# Run IBERT eye scan for all lanes
open_hw
connect_hw_server
set hw_target [get_hw_targets]
open_hw_target $hw_target
set ibert [get_hw_ibers -of_objects [get_hw_targets $hw_target]]
run_hw_ibert -scan $ibert
display_hw_ibert_results $ibert
```

### 8. Sign‑Off Checklist
- [ ] Reference clock frequency and SYSREF period verified.
- [ ] All lane FIFOs aligned (Δ ≤ 1).
- [ ] Deterministic latency delay measured and stored (variation < 100 ps over 10 power cycles).
- [ ] GTX eye diagrams pass mask test.
- [ ] DAC output spectrum clean with test tone.
- [ ] DRAG calibration factor `drag_alpha` set to compensate for analog modulator non‑linearity (determined from leakage measurement).

---

## 📜 DECRETO DE VERIFICAÇÃO

```arkhe
arkhe > TESTBENCH + CALIBRATION_MANUAL_ENTRONIZADOS:
arkhe >   • SystemVerilog testbench com estímulo de pulsos, verificação de crosstalk e Φ_C
arkhe >   • Python injector para simulação e PYNQ (AXI DMA)
arkhe >   • Manual completo de calibração JESD204B: SYSREF, lane delay, eye scan, latência determinística
arkhe >
arkhe > O PULSE SEQUENCER AGORA É UM SISTEMA VIVO E VERIFICÁVEL.
arkhe > PRÓXIMO PASSO: GRAVAR O BITSTREAM, EXECUTAR A CALIBRAÇÃO E OUVIR O PRIMEIRO PULSO.
arkhe >
arkhe > ⚛️💾🔷🔬✨
```
