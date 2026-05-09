# Quantum Anyon Analyzer

This directory contains the real-time C++ modules for analyzing anyon fusion outcomes on the BIP-1 (Bio-Implante de Pulso) hardware.

## Files
- `anyon_analyzer.hpp`: Header with statistical models (Poisson, Mixture) and Likelihood Ratio Test logic.
- `anyon_analyzer.cpp`: Global instance and C-interface for kernel integration.
- `corvo_main.cpp`: Example of integration with the system task loop and APD interrupts.
- `test_anyon_analyzer.cpp`: Unit test suite for verifying mathematical models.

## Usage
The analyzer expects raw photon counts from an APD (Avalanche Photodiode). It computes the log-likelihood ratio between the Fibonacci model ($c = \pi/5$, $p_{vac} \approx 0.382$) and the Ising/Classical model ($p_{vac} = 0.5$).

A decision is reached when the log-likelihood ratio exceeds the `LOG_LIKELIHOOD_THRESHOLD` (default 6.0) after a minimum number of trials.

## Mathematical Basis
The photon count $k$ follows a Poisson mixture:
$P(k) = p_{vac} \cdot \text{Poisson}(k; \mu_0) + (1 - p_{vac}) \cdot \text{Poisson}(k; \mu_1)$

Where:
- $\mu_0$: Mean dark counts (vacuum state).
- $\mu_1$: Mean signal photons (excited state).

## Hardware Interface (Verilog-A)
The module includes a physical model of the APD (`apd_pixel.vams`) and its interface to the system ADC (`apd_to_adc_interface.v`).

### Model Parameters
- **Efficiency (η):** 65% at 674nm.
- **Dark Count Rate (DCR):** 50 cps.
- **Timing Jitter:** 50 ps.
- **Dead Time:** 100 ns.

These models allow for full-chip co-simulation of the anyon analyzer with the analog front-end and the biological substrate.
