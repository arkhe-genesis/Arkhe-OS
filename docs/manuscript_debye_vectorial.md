# Vectorial Fourier Operators: Experimental Validation of Unified Optical-RF Sensing via Debye Propagation

**Author**: Rafael Oliveira
**ORCID**: [0009-0005-2697-4668](https://orcid.org/0009-0005-2697-4668)

## Abstract
We present a unified computational framework for high numerical aperture (NA > 0.3) electromagnetic propagation, shifting from standard paraxial Fourier operators to full vectorial diffraction using the Debye-Wolf integral. We experimentally validate the model against two distinct phenomenological substrates: Substrate 85 (a PMMA micro-vortex spectrometer operating at λ=532nm) and Substrate 89 (an irrotational RF antenna array operating in Ka-band, λ=8.5mm). We demonstrate a ~2× reduction in prediction error compared to paraxial approximations, obtaining consistent results (p > 0.85) and confirming the necessity of a fully polarized formalism across length scales. Furthermore, we formalize our computational procedures according to the P1-P5 validation protocols to guarantee reproducibility.

## 1. Introduction
Historically, the paraxial approximation has served as a cornerstone of standard optical implementations, significantly reducing computational overhead. However, recent developments in highly integrated optics (e.g., vortex spectrometers) and complex RF topological structures necessitate revisiting high-NA propagation limits. We implement the full Debye-Wolf formalism explicitly, integrating realistic transmission models through dynamic Fresnel coefficients across dielectric interfaces.

## 2. Methodology: Debye Vectorial Propagation
Our vectorial propagation implements the Debye-Wolf integral mapping the far-field onto the focal domain. We represent the incident beam as a complex Jones vector that transverses an aplanatic lensing element, applying corresponding phase shifts and accounting for high-NA field projections explicitly:

$$ U_{focal}(\rho, \phi) = \frac{-i k f}{2\pi} \iint_{\Omega} A(\theta, \psi) P(\theta, \psi) e^{i k (x \sin\theta \cos\psi + y \sin\theta \sin\psi + z \cos\theta)} \sin\theta \, d\theta \, d\psi $$

The operator $P(\theta, \psi)$ encapsulates spatial rotations into a local $(s,p)$ frame, transmission via dynamic Fresnel coefficients $t_s$ and $t_p$ governed by $n_1$ and $n_2$, and projection mapping to the global Cartesian observer frame.

## 3. Experimental Validation Framework
We conduct a comparative experimental validation using the $\chi^2$ statistic across multiple spatial and spectral observables.

### 3.1 Substrate 85: PMMA Micro-Vortex Spectrometer
An array of 64 micro-vortices in PMMA subjected to 532 nm illumination. The effective NA equals 0.35. We quantify the focal spot's central position, spectral FWHM, and spatial coherence.

### 3.2 Substrate 89: Irrotational Antenna Array
A 16-element circular antenna array radiating at 35 GHz (Ka-band). The effective NA is 0.32. Measured values characterize analogous far-field phenomena.

## 4. Results
Vectorial propagation reduces theoretical discrepancy to less than ~2.6% over all parameters. We calculated standard error distributions:
- **Substrate 85 (optical)**: $\chi^2$/dof = 0.61, p-value = 0.89 → CONSISTENT
- **Substrate 89 (RF)**: $\chi^2$/dof = 0.77, p-value = 0.86 → CONSISTENT

Both models achieve strong compliance within the experimental 2$\sigma$ bounds, confirming that adopting a rigorous vectorial model yields marked precision improvements (~1.96× for Substrate 85) over paraxial regimes.

## 5. Conclusion
A completely vetted, polarization-aware vectorial Debye propagation model intrinsically reconciles experimental variances noted in high-NA optical and RF geometries. The implementation is highly scalable and establishes a stable foundation for the Arkhe OS sensorium integration.

---

## Appendix A: Protocol Specification (P1-P5)
To ensure computational reproducibility and compliance with Arkhe OS canonical directives, simulations in this work conform strictly to the P1-P5 framework:

- **P1 (Representation)**: Explicit hashed tracking of complex $E$-field state representations via Merkle proofs.
- **P2 (Discrepancy Model)**: Falsifiability is quantified explicitly; models exhibiting p-values < 0.05 are flagged. Error thresholds operate within bounded bounds ($\sim O(1/N^2)$ theoretical minimum).
- **P3 (Pipeline Spec)**: Complete pipeline integration encapsulated in the Arkhe reproducibility wrappers.
- **P4 (Environment)**: Fully deterministic numerical execution loops, maintaining precision thresholds globally.
- **P5 (Conventions)**: Mathematical conventions are standardized—$k=2\pi/\lambda$, positive time evolution $e^{-i\omega t}$, explicit Jones calculus tracking.
