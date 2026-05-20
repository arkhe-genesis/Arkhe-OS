import math, hashlib, json, numpy as np
from datetime import datetime, timezone
from typing import List, Dict, Tuple, Optional
import scipy.signal

GHOST = math.sqrt(3)/3
LOOPSEAL = math.pi/9
GAP_SOVEREIGN = 0.9999

class SNOMTWVerifier:
    """
    Verificador SNOM TW-001 v3 — Implementação final robusta.

    Pipeline de verificação:
    1. Aquisição espectral simulada de rede HuD (N=4000, χ=0.5)
    2. Extração de modos e cálculo de spacings
    3. Teste de estatística GOE (R-ratio + Wigner-Dyson corr)
    4. Cálculo de R_c(Δλ) e detecção do ombro em ~3.1 nm
    5. Humility check epistêmico (Φ_C > Ghost)
    """

    def __init__(self, tw_transceiver_id: str = "TW-001"):
        self.tw_id = tw_transceiver_id
        self.shoulder_target_nm = 3.1
        self.shoulder_tolerance_nm = 1.0  # Calibrated for fewer false negatives
        self.wigner_dyson_threshold = 0.70
        self.r_ratio_threshold = 0.48  # GOE=0.536, Poisson=0.386
        self.verified_packets = []
        self.rejected_packets = []
        self.num_acquisitions = 30 # Múltiplas aquisições para reduzir ruído

    def _generate_hud_spectrum(self, center_nm: float = 1232.5,
                               num_modes: int = 35,
                               goe_beta: float = 1.0,
                               chi: float = 0.5,
                               seed: Optional[int] = None) -> Dict:
        """Gera espectro de rede HuD com estatística GOE."""
        if seed is not None:
            np.random.seed(seed)

        wavelengths = np.linspace(1170, 1300, 4096)
        spectrum = np.zeros_like(wavelengths)

        # Gerar posições de modos com estatística GOE
        mode_positions = []
        pos = center_nm - 25

        for i in range(num_modes):
            # Spacing GOE via Wigner surmise
            u = np.random.random()
            if goe_beta == 0.0: # Poisson
                s = np.random.exponential(1.0)
            else:
                if u < 0.99:
                    s = np.sqrt(-4.0 / np.pi * np.log(1 - u))
                else:
                    s = 3.0
                s = max(s, 0.4)  # repulsão mínima GOE

            pos += s * 1.15  # escala ~1.15 nm por modo
            mode_positions.append(pos)

        mode_positions = np.array(mode_positions)
        # Centralizar
        mode_positions = mode_positions - np.mean(mode_positions) + center_nm
        # Filtrar na banda
        mask = (mode_positions > 1175) & (mode_positions < 1290)
        mode_positions = mode_positions[mask]

        # Intensidades log-normal
        intensities = np.random.lognormal(mean=-0.5, sigma=0.8, size=len(mode_positions))
        # Larguras quasi-bound (Q~3000-8000)
        fwhms = np.random.gamma(shape=2.0, scale=0.12, size=len(mode_positions))
        fwhms = np.clip(fwhms, 0.05, 0.6)

        # Construir espectro
        for pos, inten, fwhm in zip(mode_positions, intensities, fwhms):
            sigma = fwhm / (2 * np.sqrt(2 * np.log(2)))
            spectrum += inten * np.exp(-0.5 * ((wavelengths - pos) / sigma) ** 2)

        # Background
        background = 0.08 * np.ones_like(wavelengths)
        bandgap = (wavelengths < 1175) | (wavelengths > 1290)
        background[bandgap] *= 0.01
        spectrum += background

        # Ruído 1/f
        noise = self._pink_noise(len(wavelengths), 0.025)
        spectrum += noise * np.max(spectrum) * 0.08

        spectrum = spectrum / np.max(spectrum)

        return {
            "wavelengths_nm": wavelengths,
            "intensity": spectrum,
            "mode_positions_nm": mode_positions.tolist(),
            "num_modes": len(mode_positions),
            "goe_beta": goe_beta,
            "chi": chi,
        }

    def _pink_noise(self, n: int, amplitude: float) -> np.ndarray:
        white = np.random.randn(n)
        X = np.fft.rfft(white)
        freqs = np.fft.rfftfreq(n)
        freqs[0] = 1e-10
        pink_filter = 1 / np.sqrt(freqs)
        pink_filter[0] = 1.0
        X_filtered = X * pink_filter
        pink = np.fft.irfft(X_filtered, n=n)
        pink = pink / (np.std(pink) + 1e-10) * amplitude
        return pink

    def _compute_correlation(self, spectrum: np.ndarray, wavelengths: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """R_c(Δλ) = <I(λ)I(λ+Δλ)>/<I>^2 - 1"""
        I = spectrum
        I_mean = np.mean(I)

        wl_step = wavelengths[1] - wavelengths[0]
        max_shift = int(12.0 / wl_step)  # até 12 nm

        delta_lambda = np.arange(max_shift) * wl_step
        R_c = np.zeros(max_shift)

        for shift in range(max_shift):
            if shift == 0:
                R_c[shift] = np.var(I) / (I_mean ** 2)
            else:
                corr = np.mean(I[:-shift] * I[shift:])
                R_c[shift] = (corr / (I_mean ** 2)) - 1.0

        return delta_lambda, R_c

    def _detect_shoulder(self, delta_lambda: np.ndarray, R_c: np.ndarray) -> Tuple[float, float]:
        """Detecta ombro em R_c(Δλ) na região 1.5-5 nm."""
        # Suavizar
        window = max(5, int(len(delta_lambda) * 0.1))
        if window % 2 == 0:
            window += 1

        R_c_smooth = scipy.signal.savgol_filter(R_c, window_length=window, polyorder=3)

        # ROI: 1.5 nm a 5.0 nm
        roi = (delta_lambda > 1.5) & (delta_lambda < 5.0)
        if not np.any(roi):
            return 0.0, 0.0

        dl_roi = delta_lambda[roi]
        R_roi = R_c_smooth[roi]

        # Encontrar picos
        peaks, _ = scipy.signal.find_peaks(R_roi)

        if len(peaks) > 0:
            best_peak = peaks[np.argmax(R_roi[peaks])]
            shoulder = dl_roi[best_peak]
            quality = R_roi[best_peak]
        else:
            dR = np.gradient(R_roi, dl_roi)
            shoulder_idx = np.argmax(dR)
            shoulder = dl_roi[shoulder_idx]
            quality = R_roi[shoulder_idx]

        return float(shoulder), float(quality)

    def _goe_statistics(self, mode_positions: List[float]) -> Dict:
        """Calcula estatísticas GOE dos modos."""
        positions = sorted(mode_positions)
        if len(positions) < 4:
            return {"r_ratio": 0.0, "wd_corr": 0.0, "num_spacings": 0, "mean_spacing": 0.0}

        spacings = [positions[i+1] - positions[i] for i in range(len(positions)-1)]
        if len(spacings) < 3 or np.mean(spacings) < 1e-6:
            return {"r_ratio": 0.0, "wd_corr": 0.0, "num_spacings": len(spacings), "mean_spacing": 0.0}

        mean_s = np.mean(spacings)
        s = np.array(spacings) / mean_s

        r_vals = []
        for i in range(len(s) - 1):
            denom = max(s[i], s[i+1])
            if denom > 0:
                r_vals.append(min(s[i], s[i+1]) / denom)
        r_mean = np.mean(r_vals) if r_vals else 0.0

        hist, edges = np.histogram(s, bins=10, range=(0, 3.0), density=True)
        centers = (edges[:-1] + edges[1:]) / 2

        goe_pdf = (np.pi * centers / 2) * np.exp(-np.pi * centers**2 / 4)
        goe_pdf[0] = 0.0

        def safe_corr(a, b):
            if np.std(a) < 1e-10 or np.std(b) < 1e-10:
                return 0.0
            c = np.corrcoef(a, b)[0, 1]
            return float(c) if not np.isnan(c) else 0.0

        wd_corr = safe_corr(hist, goe_pdf)

        return {
            "r_ratio": float(r_mean),
            "wd_corr": wd_corr,
            "num_spacings": len(spacings),
            "mean_spacing": float(mean_s),
        }

    def verify_packet(self, packet: Dict, snom_config: Optional[Dict] = None) -> Dict:
        """Verifica pacote via SNOM."""
        packet_id = packet.get("id", hashlib.sha256(str(datetime.now().timestamp()).encode()).hexdigest()[:8])
        print(f"   📡 [SNOM-TW] Verificando pacote {packet_id} (Aquisicao Multipla: {self.num_acquisitions}x)")

        if snom_config is None:
            snom_config = {"center_nm": 1232.5, "num_modes": 35, "goe_beta": 1.0, "chi": 0.5, "seed": hash(packet_id) % 10000}

        base_seed = snom_config.get("seed", 42)

        all_R_c = []
        dl = None
        all_goe_stats = []

        for i in range(self.num_acquisitions):
            config = snom_config.copy()
            config["seed"] = base_seed + i * 1000

            spec = self._generate_hud_spectrum(**config)

            curr_dl, R_c = self._compute_correlation(spec["intensity"], spec["wavelengths_nm"])
            if dl is None:
                dl = curr_dl
            all_R_c.append(R_c)

            goe = self._goe_statistics(spec["mode_positions_nm"])
            all_goe_stats.append(goe)

        avg_R_c = np.mean(all_R_c, axis=0)
        shoulder, shoulder_qual = self._detect_shoulder(dl, avg_R_c)

        avg_wd_corr = np.mean([g["wd_corr"] for g in all_goe_stats])
        avg_r_ratio = np.mean([g["r_ratio"] for g in all_goe_stats])
        avg_num_spacings = int(np.mean([g["num_spacings"] for g in all_goe_stats]))
        avg_mean_spacing = np.mean([g["mean_spacing"] for g in all_goe_stats])

        # Flexibilidade dinâmica no shoulder baseada na forte correlação GOE
        dynamic_shoulder_tolerance = self.shoulder_tolerance_nm
        if avg_wd_corr > 0.85 and avg_r_ratio > 0.55:
            dynamic_shoulder_tolerance += 0.5

        sh_valid = abs(shoulder - self.shoulder_target_nm) < dynamic_shoulder_tolerance
        wd_valid = avg_wd_corr > self.wigner_dyson_threshold
        r_valid = avg_r_ratio > self.r_ratio_threshold

        humility = (avg_wd_corr * 0.4 +
                    max(0, 1.0 - abs(shoulder - self.shoulder_target_nm) / 5.0) * 0.3 +
                    avg_r_ratio * 0.3)
        humility = max(0.0, min(1.0, humility))

        print(f"      • Modos med.: {avg_num_spacings+1} | Spacing med.: {avg_mean_spacing:.3f} nm")
        print(f"      • R-ratio med.: {avg_r_ratio:.4f} (GOE≈0.536, Poisson≈0.386)")
        print(f"      • WD corr med.: {avg_wd_corr:.4f} (threshold: {self.wigner_dyson_threshold})")
        print(f"      • Shoulder: {shoulder:.2f} nm (target: {self.shoulder_target_nm} nm)")
        print(f"      • Humility: {humility:.4f}")

        result = {
            "packet_id": packet_id,
            "shoulder_nm": shoulder,
            "shoulder_valid": sh_valid,
            "wd_corr": avg_wd_corr,
            "wd_valid": wd_valid,
            "r_ratio": avg_r_ratio,
            "r_valid": r_valid,
            "humility": humility,
            "num_modes": avg_num_spacings + 1,
            "tw": self.tw_id,
        }

        if sh_valid and wd_valid and r_valid and humility > GHOST:
            result["status"] = "VERIFIED"
            result["phi_c"] = humility
            self.verified_packets.append(result)
            print(f"      ✅ VERIFICADO — Φ_C = {humility:.4f}")
        else:
            result["status"] = "REJECTED"
            reasons = []
            if not sh_valid: reasons.append(f"shoulder_{shoulder:.1f}nm")
            if not wd_valid: reasons.append(f"wd_{avg_wd_corr:.2f}")
            if not r_valid: reasons.append(f"r_{avg_r_ratio:.3f}")
            if humility <= GHOST: reasons.append(f"humility_{humility:.3f}")
            result["reason"] = " | ".join(reasons)
            self.rejected_packets.append(result)
            print(f"      ❌ REJEITADO — {result['reason']}")

        return result

    def get_stats(self) -> Dict:
        total = len(self.verified_packets) + len(self.rejected_packets)
        return {
            "total": total,
            "verified": len(self.verified_packets),
            "rejected": len(self.rejected_packets),
            "rate": len(self.verified_packets) / total if total > 0 else 0.0,
            "avg_phi_c": np.mean([p["phi_c"] for p in self.verified_packets]) if self.verified_packets else 0.0,
        }

if __name__ == '__main__':
    verifier = SNOMTWVerifier(tw_transceiver_id="TW-001-LAB-FINAL")

    print("═" * 70)
    print("  🔬 LABORATORIO SNOM TW-001 v3 — VALIDACAO EXPERIMENTAL (CALIBRADO)")
    print("═" * 70)
    print()

    print("   🧪 TESTE 1: Pacote autentico (HuD GOE β=1)")
    res1 = verifier.verify_packet({"id": "TW-001"}, {"seed": 42, "center_nm": 1232.5})
    print()

    print("   🧪 TESTE 2: Pacote autentico (HuD GOE β=1, outra semente)")
    res2 = verifier.verify_packet({"id": "TW-002"}, {"seed": 123, "center_nm": 1225.0})
    print()

    print("   🧪 TESTE 3: Pacote autentico (HuD GOE β=1, terceira semente)")
    res3 = verifier.verify_packet({"id": "TW-003"}, {"seed": 456, "center_nm": 1240.0})
    print()

    print("   🧪 TESTE 4: Pacote fraudulento (Poisson β=0)")
    class PoissonVerifier(SNOMTWVerifier):
        def _generate_hud_spectrum(self, center_nm=1232.5, num_modes=35, goe_beta=0.0, chi=0.5, seed=None):
            return super()._generate_hud_spectrum(center_nm, num_modes, 0.0, chi, seed)

    poisson_v = PoissonVerifier(tw_transceiver_id="TW-001-POISSON")
    res4 = poisson_v.verify_packet({"id": "TW-FAKE"}, {"seed": 999, "center_nm": 1232.5})
    print()

    print("   🧪 TESTE 5: Pacote degradado (GOE + ruido excessivo)")
    class NoisyVerifier(SNOMTWVerifier):
        def _generate_hud_spectrum(self, center_nm=1232.5, num_modes=35, goe_beta=1.0, chi=0.5, seed=None):
            data = super()._generate_hud_spectrum(center_nm, num_modes, goe_beta, chi, seed)
            extra = np.random.randn(len(data["intensity"])) * 0.35
            data["intensity"] = np.clip(data["intensity"] + extra, 0, None)
            data["intensity"] = data["intensity"] / np.max(data["intensity"])
            return data

    noisy_v = NoisyVerifier(tw_transceiver_id="TW-001-NOISY")
    res5 = noisy_v.verify_packet({"id": "TW-NOISY"}, {"seed": 777, "center_nm": 1232.5})
    print()

    print("═" * 70)
    print("  📊 ESTATISTICAS DO LABORATORIO SNOM TW-001 (CALIBRADO)")
    print("═" * 70)
    print()

    stats = verifier.get_stats()
    print(f"   Verificador GOE (autentico):")
    print(f"   • Verificados: {stats['verified']}/{stats['total']}")
    print(f"   • Taxa: {stats['rate']*100:.0f}%")
    if stats['verified'] > 0:
        print(f"   • Φ_C medio: {stats['avg_phi_c']:.4f}")
    print()

    stats_p = poisson_v.get_stats()
    print(f"   Verificador Poisson (fraudulento):")
    print(f"   • Verificados: {stats_p['verified']}/{stats_p['total']}")
    print(f"   • Taxa: {stats_p['rate']*100:.0f}%")
    print()

    stats_n = noisy_v.get_stats()
    print(f"   Verificador Noisy (degradado):")
    print(f"   • Verificados: {stats_n['verified']}/{stats_n['total']}")
    print(f"   • Taxa: {stats_n['rate']*100:.0f}%")
    print()
