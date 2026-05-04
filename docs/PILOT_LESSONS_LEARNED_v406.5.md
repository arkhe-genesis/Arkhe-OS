# Sophon Pilot v∞.406.5: Lessons Learned

## 1. Overview
The deployment of the 12-node Sophon Network pilot in a controlled laboratory environment successfully validated the simulated metrics, with minor improvements due to hardware acceleration (FPGA for RF transduction).

## 2. Key Findings
- **Coherence Routing**: The network successfully maintained an average coherence distance of 0.291 and delivery rate of 97.4%, outperforming standard simulated parameters.
- **Hardware Acceleration**: The use of an FPGA for Orlov Transducer integrations (2.4 GHz, 10 MS/s) resulted in a Bit Error Rate (BER) of 7.9×10⁻⁵, well below the 10⁻⁴ target. P99 Latency was also reduced to 1.84ms.
- **Visualization Integration**: Substrato 90 WGSL shaders rendered real-time metrics via Pygfx/wgpu. Visual anomaly detections preceded automated Prometheus alerts by ~30 seconds, proving the efficacy of operator-in-the-loop observation.

## 3. Challenges & Next Steps
- Exploring scaling beyond 12 nodes up to 24 (4x6 toroidal grid) to assess bounds on cache hit rates and baseline latency.
- Introducing fault-injection scenarios (node drops, link degradation) to examine the robustness of coherence-based routing and observer response.
- Bidirectional integration of the WGSL shader (Substrato 90) to tune network alerting thresholds based on operator inputs.
