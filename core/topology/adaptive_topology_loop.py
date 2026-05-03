# core/topology/adaptive_topology_loop.py
"""
ARKHE Adaptive Topology Loop — Closes A∘P for Skyrmion Excitation
Integrates Programmer → Excitation → Readout → Correction with convergence check.
"""
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import time
import logging

logger = logging.getLogger(__name__)

@dataclass
class LoopStats:
    iterations: int = 0
    Q_history: List[float] = field(default_factory=list)
    error_history: List[float] = field(default_factory=list)
    excitation_time_ms: List[float] = field(default_factory=list)
    readout_time_ms: List[float] = field(default_factory=list)
    correction_time_ms: List[float] = field(default_factory=list)

class AdaptiveTopologyController:
    """
    Closes the A∘P loop for plasmonic skyrmions.

    A (Analytical): SkyrmionProgrammer generates target texture.
    P (Perceptual): SNOMReader measures actual n(x,y) and computes Q.

    The controller adjusts core_radius and external field E_z
    to minimize |Q_target - Q_measured|.
    """

    def __init__(self,
                 programmer,
                 hardware: 'PlasmonicHardwareBridge',
                 reader: 'SNOMReader',
                 convergence_threshold: float = 0.05,
                 max_iterations: int = 10,
                 learning_rate: float = 0.1,
                 denoise_sigma: float = 1.0,
                 convergence_patience: int = 3,
                 max_oscillation_amplitude: float = 0.1):
        self.programmer = programmer
        self.hardware = hardware
        self.reader = reader
        self.epsilon = convergence_threshold
        self.max_iter = max_iterations
        self.lr = learning_rate
        self.denoise_sigma = denoise_sigma
        self.patience = convergence_patience
        self.max_oscillation = max_oscillation_amplitude
        self._error_history: List[float] = []
        self.stats = LoopStats()

    def close_loop(self, Q_target: int, texture_type: str, initial_core_radius: float,
                   external_field: float) -> Dict:
        from core.topology.denoising import compute_robust_charge
        """
        Executes the A∘P loop until convergence or max iterations.

        Returns:
            {
                'converged': bool,
                'final_Q_measured': float,
                'final_program': SkyrmionProgram,
                'loop_stats': LoopStats
            }
        """
        from core.topology.skyrmion_programmer import SkyrmionProgram, SkyrmionType

        program = SkyrmionProgram(
            target_charge=Q_target,
            skyrmion_type=SkyrmionType(texture_type),
            core_radius=initial_core_radius,
            boundary_condition="fixed",
            control_fields={"E_z": external_field}
        )

        logger.info(f"Starting A∘P loop: Q_target={Q_target}, texture={texture_type}, "
                     f"core_radius={initial_core_radius:.1f}nm, E_z={external_field:.1e} V/m")

        for iteration in range(self.max_iter):
            # --- A: Analytical excitation ---
            t0 = time.perf_counter()
            n_target = self.programmer.generate_texture(program)
            exc_time = self.hardware.excite_skyrmion(n_target, program.core_radius)
            self.stats.excitation_time_ms.append(exc_time)

            # --- P: Perceptual readout ---
            t1 = time.perf_counter()
            # In real experiment: acquire s-SNOM images
            # Here, we simulate the readout with noise added to target texture
            intensity_img = np.linalg.norm(n_target, axis=-1)**2
            phase_img = np.angle(n_target[..., 0] + 1j * n_target[..., 1])

            # Simulate measurement noise
            noise = np.random.randn(*intensity_img.shape) * self.reader.noise
            n_measured, snr_db = self.reader.read_field(intensity_img + noise, phase_img + noise * 0.5)

            # Apply spatial filtering for robust Q computation
            Q_measured = compute_robust_charge(
                n_measured,
                dx=1.0,
                denoise_sigma=self.denoise_sigma
            )
            read_time = (time.perf_counter() - t1) * 1000
            self.stats.readout_time_ms.append(read_time)

            # --- Error analysis ---
            error = abs(Q_target - Q_measured)
            self.stats.Q_history.append(Q_measured)
            self.stats.error_history.append(error)
            self._error_history.append(error)
            self.stats.iterations += 1

            logger.info(f"  Iter {iteration+1}/{self.max_iter}: Q_measured={Q_measured:.3f}, "
                         f"error={error:.4f}, SNR={snr_db:.1f} dB")

            # --- Convergence with patience & oscillation detection ---
            if error < self.epsilon:
                # Require patience consecutive iterations below threshold
                if len(self._error_history) >= self.patience:
                    recent = self._error_history[-self.patience:]
                    if all(e < self.epsilon for e in recent):
                        logger.info(f"✅ Converged at iteration {iteration+1}")
                        break

            # Detect oscillatory behavior (failure to converge)
            if len(self._error_history) >= 6:
                recent_errors = self._error_history[-6:]
                oscillation = max(recent_errors) - min(recent_errors)
                if oscillation > self.max_oscillation:
                    logger.warning(f"⚠️ Oscillation detected: amplitude={oscillation:.4f}")
                    # Reduce learning rate adaptively
                    self.lr *= 0.5
                    logger.info(f"   Reduced learning rate to {self.lr:.3f}")

            # --- Adaptive correction ---
            t2 = time.perf_counter()
            # Gradient descent: adjust core_radius and E_z to reduce error
            # ∂ε/∂r ≈ (Q_target - Q_measured) * (∂Q/∂r) approximation
            dQ_dr = 2.0 / program.core_radius  # Empirical scaling for skyrmion size
            dQ_dE = -0.5  # External field tends to reduce charge (pinching effect)

            program.core_radius += self.lr * error * np.sign(Q_target - Q_measured) * dQ_dr
            program.control_fields["E_z"] += self.lr * error * np.sign(Q_target - Q_measured) * dQ_dE

            # Clamp parameters to physical ranges
            program.core_radius = max(5.0, min(50.0, program.core_radius))
            program.control_fields["E_z"] = max(1e4, min(1e7, program.control_fields["E_z"]))

            corr_time = (time.perf_counter() - t2) * 1000
            self.stats.correction_time_ms.append(corr_time)

        converged = False
        if len(self._error_history) >= self.patience:
            recent = self._error_history[-self.patience:]
            if all(e < self.epsilon for e in recent):
                converged = True

        result = {
            'converged': converged,
            'iterations': self.stats.iterations,
            'final_Q_measured': Q_measured,
            'final_program': program,
            'final_error': error,
            'loop_stats': self.stats
        }

        # Final validation
        if not converged:
            logger.warning(f"⚠️ Loop did not converge: final error={error:.4f}")
            # Return best result anyway
            best_idx = np.argmin(self._error_history)
            result['best_iteration'] = int(best_idx + 1)
            result['best_error'] = float(self._error_history[best_idx])

        return result
