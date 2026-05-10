# Orlov Miniaturized Antenna 2.4 GHz PCB Layout Specification

## 1. Overview
This document specifies the PCB layout and fabrication requirements for a miniaturized Orlov antenna designed for 2.4 GHz ISM band operation. It implements the irrotational scalar-longitudinal transducer concept for integration with the Fleuron interface and Pygfx scaffold.

## 2. RF Parameters
*   **Operating Frequency:** 2.4 GHz (ISM band)
*   **Target Bandwidth:** 2.35 GHz - 2.45 GHz
*   **Characteristic Impedance:** 50 Ω
*   **Coupling:** 180° ±0.1° antiphase excitation
*   **Mode:** TEM antiphase -> Irrotational Scalar (Zero-vector projection)

## 3. Physical Dimensions & Substrate
*   **PCB Material:** High-frequency laminate (e.g., Rogers RO4350B or equivalent)
*   **Dielectric Constant (Dk):** ~3.48 @ 10 GHz
*   **Substrate Thickness:** 0.762 mm (30 mil)
*   **Copper Weight:** 1 oz (35 μm thickness)
*   **Overall Module Size:** 10 × 10 × 5 mm (target for 3D waveguide integration)
*   **Waveguide Cavity:** Conductive shielded box surrounding the primary elements to enforce specific modes.

## 4. Components & Routing
1.  **Input Port (SMA):** 50 Ω edge-mount SMA connector for the Fleuron interface.
2.  **Power Divider / 180° Hybrid Coupler:**
    *   To achieve exact antiphase, use a 180° hybrid ring (rat-race coupler) or a precision SMD balun (e.g., Anaren Xinger or Johanson Technology).
    *   **Phase Tolerance:** < 0.1° required for true vector annihilation. Tuning stubs may be required.
3.  **Antenna Elements:**
    *   Two symmetrical planar waveguide structures or patch elements.
    *   Separation distance calculated to maximize coherent antiphase superposition within the target near-field volume.
4.  **Scalar Pick-up (Orlov Core):**
    *   A central shielded via or probe located at the geometric center (null point of the vector field).
    *   Designed to couple only to the longitudinal (irrotational) scalar mode.

## 5. Shielding & Grounding
*   **Continuous Ground Plane:** Bottom layer must be a solid, uninterrupted ground plane.
*   **Via Fencing:** Dense via stitching (spacing < λ/20 at 2.4 GHz, ~6mm, so 0.5mm via spacing recommended) along the perimeter of the RF traces and cavity to prevent transverse leakage.
*   **Metallic Shield:** A 35 μm Cu (or equivalent) electrodeposited/sputtered cap covering the 10x10mm area to reject external transverse EM noise.

## 6. Manufacturing & Tolerances
*   **Trace Width/Gap Tolerance:** ±25 μm (1 mil).
*   **Plating:** ENIG (Electroless Nickel Immersion Gold) finish to prevent oxidation and ensure stable RF performance.
*   **Drill Tolerance:** ±50 μm.

## 7. Validation Strategy (VNA)
1.  Measure Return Loss (S11) to ensure > 15 dB match at 2.4 GHz.
2.  Measure phase difference between the two split paths to confirm 180° ±0.1°.
3.  Characterize the "scalar extraction" port isolation (S31, S32) to ensure minimal coupling to transverse TEM modes.

---
*Status: Ready for CAD drafting (e.g., KiCad/Altium).*
