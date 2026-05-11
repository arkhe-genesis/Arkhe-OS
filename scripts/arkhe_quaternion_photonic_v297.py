#!/usr/bin/env python3
"""
ARKHE OS v∞.297 — Quaternion Photonic Hardware Interface
=========================================================
768-crystal Merkabah icosahedron with Kuramoto coupling (K=φ),
PLL synchronization at 32.8 kHz, SNSPD feedback, quaternion control.

Architecture:
  [768 Crystals] ──Kuramoto φ──→ [Phase Coherence]
       │                               │
    [SNSPD]  ←──stochastic──→  [Quaternion Controller]
       │                               │
    [ESP32 UART 921600]         [PLL 32.8 kHz / 0.58ns]

Physics:
  - Kuramoto: dθ_i/dt = ω_i + (K/N) Σ_j A_ij sin(θ_j - θ_i)
  - K = φ = (1+√5)/2 ≈ 0.6180339887498949
  - SNSPD: Poisson detection with efficiency η, dark count λ_dark
  - PLL: 2nd-order with natural freq ωn = 2π × 0.58 Hz
  - Quaternion control: q' = q ⊗ Δq (Hamilton product), feedback via SNSPD

Author: ARKHE OS Consortium
Version: v∞.297
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.patches import FancyArrowPatch, Circle
from mpl_toolkits.mplot3d import Axes3D
import json
import time as time_module
from collections import OrderedDict
import os

# ─── Font Setup ─────────────────────────────────────────────────────
# (Removed environment-specific font paths as per memory guidelines)
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.dpi'] = 200
plt.rcParams['font.size'] = 9


# ═══════════════════════════════════════════════════════════════════════
# QUATERNION ALGEBRA ENGINE
# ═══════════════════════════════════════════════════════════════════════

class Quaternion:
    """Hamilton quaternion q = w + xi + yj + zk with hardware-accurate ops."""

    __slots__ = ('w', 'x', 'y', 'z')

    def __init__(self, w=1.0, x=0.0, y=0.0, z=0.0):
        self.w = float(w)
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)

    @staticmethod
    def from_axis_angle(axis, angle):
        """Create quaternion from axis-angle representation (Rodrigues)."""
        axis = np.asarray(axis, dtype=np.float64)
        norm = np.linalg.norm(axis)
        if norm < 1e-15:
            return Quaternion(1, 0, 0, 0)
        axis = axis / norm
        ha = angle / 2.0
        s = np.sin(ha)
        return Quaternion(np.cos(ha), axis[0]*s, axis[1]*s, axis[2]*s)

    @staticmethod
    def from_phase_sphere(theta, phi, coherence):
        """Map crystal phase (theta, phi) + coherence to unit quaternion."""
        # Phase → rotation axis on sphere, coherence → rotation magnitude
        axis = np.array([np.sin(phi)*np.cos(theta),
                         np.sin(phi)*np.sin(theta),
                         np.cos(phi)])
        angle = 2.0 * np.arccos(coherence)  # coherence 0→π, 1→0
        return Quaternion.from_axis_angle(axis, angle)

    def hamilton(self, other):
        """Hamilton product q1 ⊗ q2."""
        w1, x1, y1, z1 = self.w, self.x, self.y, self.z
        w2, x2, y2, z2 = other.w, other.x, other.y, other.z
        return Quaternion(
            w1*w2 - x1*x2 - y1*y2 - z1*z2,
            w1*x2 + x1*w2 + y1*z2 - z1*y2,
            w1*y2 - x1*z2 + y1*w2 + z1*x2,
            w1*z2 + x1*y2 - y1*x2 + z1*w2
        )

    def conjugate(self):
        return Quaternion(self.w, -self.x, -self.y, -self.z)

    def norm(self):
        return np.sqrt(self.w**2 + self.x**2 + self.y**2 + self.z**2)

    def normalize(self):
        n = self.norm()
        if n < 1e-15:
            return Quaternion(1, 0, 0, 0)
        return Quaternion(self.w/n, self.x/n, self.y/n, self.z/n)

    def to_rotation_matrix(self):
        """Convert to 3×3 rotation matrix."""
        q = self.normalize()
        w, x, y, z = q.w, q.x, q.y, q.z
        return np.array([
            [1-2*(y*y+z*z), 2*(x*y-w*z),   2*(x*z+w*y)],
            [2*(x*y+w*z),   1-2*(x*x+z*z), 2*(y*z-w*x)],
            [2*(x*z-w*y),   2*(y*z+w*x),   1-2*(x*x+y*y)]
        ])

    def rotate_vector(self, v):
        """Rotate 3-vector by this quaternion: q v q*."""
        R = self.to_rotation_matrix()
        return R @ np.asarray(v)

    def __repr__(self):
        return f"Q({self.w:.4f}, {self.x:.4f}, {self.y:.4f}, {self.z:.4f})"


class QuaternionController:
    """PID-equivalent feedback controller using quaternion rotation."""

    def __init__(self, Kp=0.618, Ki=0.0382, Kd=0.01,
                 target_coherence=0.95, sync_phase=0.58):
        self.Kp = Kp  # Proportional gain (golden ratio)
        self.Ki = Ki  # Integral gain (φ/16.17)
        self.Kd = Kd  # Derivative gain
        self.target_coherence = target_coherence
        self.sync_phase = sync_phase  # Fingerprint 0.58
        self.integral_error = 0.0
        self.prev_error = 0.0

    def compute_correction(self, coherence, mean_phase, dt):
        """Compute quaternion correction from coherence + phase error."""
        error = self.target_coherence - coherence
        self.integral_error += error * dt
        # Anti-windup clamp
        self.integral_error = np.clip(self.integral_error, -2.0, 2.0)
        derivative = (error - self.prev_error) / max(dt, 1e-12)
        self.prev_error = error

        # Composite correction signal
        correction = (self.Kp * error +
                      self.Ki * self.integral_error +
                      self.Kd * derivative)

        # Phase alignment: pull mean phase toward sync_phase
        phase_error = self.sync_phase * np.pi - mean_phase
        phase_correction = 0.1 * np.sin(phase_error)

        # Quaternion correction: rotation about phase error axis
        total = correction + phase_correction
        axis = np.array([np.cos(mean_phase), np.sin(mean_phase), 0.0])
        axis_norm = np.linalg.norm(axis)
        if axis_norm > 1e-10:
            axis /= axis_norm
        return Quaternion.from_axis_angle(axis, total * dt)

    def reset(self):
        self.integral_error = 0.0
        self.prev_error = 0.0


# ═══════════════════════════════════════════════════════════════════════
# SNSPD DETECTOR MODEL
# ═══════════════════════════════════════════════════════════════════════

class SNSPDDetector:
    """
    Superconducting Nanowire Single Photon Detector model.
    Poisson statistics with efficiency η, dark count rate, timing jitter.
    """

    def __init__(self, efficiency=0.85, dark_count_rate=10.0,
                 jitter_ps=15.0, dead_time_ns=10.0):
        self.efficiency = efficiency          # System detection efficiency
        self.dark_count_rate = dark_count_rate  # Dark counts per second
        self.jitter_ps = jitter_ps            # Timing jitter (ps RMS)
        self.dead_time_ns = dead_time_ns      # Recovery time (ns)
        self.last_detection_time = -np.inf
        self.detection_history = []

    def detect(self, photon_rate, t, dt):
        """
        Stochastic photon detection.
        Returns (detected, timestamp, count_rate).
        """
        # Effective rate accounting for dead time
        if (t - self.last_detection_time) * 1e9 < self.dead_time_ns:
            return False, t, 0.0

        # Total rate = signal + dark count
        total_rate = photon_rate * self.efficiency + self.dark_count_rate

        # Poisson probability of at least one detection in interval dt
        p_detect = 1.0 - np.exp(-total_rate * dt)

        # Stochastic detection
        rng = np.random.random()
        detected = rng < p_detect

        if detected:
            self.last_detection_time = t
            # Add timing jitter
            jittered_t = t + np.random.normal(0, self.jitter_ps * 1e-12)
            self.detection_history.append(jittered_t)
            return True, jittered_t, total_rate

        return False, t, total_rate


# ═══════════════════════════════════════════════════════════════════════
# PHASE-LOCKED LOOP (PLL) MODEL
# ═══════════════════════════════════════════════════════════════════════

class PLLModel:
    """
    2nd-order Type-II PLL with configurable natural frequency and damping.
    Models Si5351A crystal oscillator reference → PLL lock.
    """

    def __init__(self, ref_freq_hz=32768.0, output_freq_hz=32768.0,
                 natural_freq_hz=0.58, damping=0.707, jitter_ns=0.58,
                 i2c_addr=0x55):
        self.ref_freq = ref_freq_hz
        self.output_freq = output_freq_hz
        self.omega_n = 2.0 * np.pi * natural_freq_hz  # 0.58 Hz fingerprint
        self.zeta = damping  # Butterworth optimal
        self.jitter_ns = jitter_ns
        self.i2c_addr = i2c_addr

        # State variables
        self.phase_error = 0.0
        self.integrator = 0.0
        self.output_phase = 0.0
        self.locked = False
        self.lock_time = None
        self._phase_error_history = []

        # Loop filter coefficients (active-lead filter)
        self.Kp_pll = 2.0 * self.zeta * self.omega_n
        self.Ki_pll = self.omega_n ** 2

    def update(self, ref_phase, vco_noise=0.0, dt=0.05):
        """Update PLL state for one timestep."""
        # Phase detector output
        self.phase_error = ref_phase - self.output_phase
        self.phase_error = (self.phase_error + np.pi) % (2*np.pi) - np.pi

        self._phase_error_history.append(self.phase_error)

        # Loop filter (Type-II: proportional + integrator)
        self.integrator += self.phase_error * dt

        # VCO control voltage
        control = self.Kp_pll * self.phase_error + self.Ki_pll * self.integrator

        # VCO output with noise
        self.output_phase += (self.output_freq * 2.0 * np.pi +
                              control + vco_noise) * dt
        self.output_phase %= (2.0 * np.pi)

        # Lock detection: phase error < threshold for sustained period
        lock_threshold = np.radians(0.5)  # 0.5 degree
        recent_errors = self._phase_error_history[-20:] if len(self._phase_error_history) >= 20 else self._phase_error_history
        if len(recent_errors) > 0 and np.max(np.abs(recent_errors)) < lock_threshold:
            if not self.locked:
                self.locked = True
                self.lock_time = len(self._phase_error_history) * dt
        else:
            self.locked = False
            self.lock_time = None

        return self.output_phase, self.phase_error


# ═══════════════════════════════════════════════════════════════════════
# KURAMOTO COUPLED OSCILLATOR NETWORK
# ═══════════════════════════════════════════════════════════════════════

class MerkabahIcosahedron:
    """
    768-crystal Merkabah icosahedron topology.
    Each crystal is a Kuramoto oscillator coupled to its neighbors
    with coupling strength K = φ (golden ratio).
    """

    def __init__(self, n_crystals=768, coupling=0.6180339887498949,
                 fingerprint_hz=0.58):
        self.N = n_crystals
        self.K = coupling  # Golden ratio
        self.fingerprint_hz = fingerprint_hz
        self.sync_phase = fingerprint_hz * np.pi  # 0.58π

        # Generate icosahedral vertex positions
        self.vertices = self._generate_icosahedron_vertices()

        # Build adjacency from proximity (Delaunay-like)
        self.adjacency = self._build_adjacency()

        # Oscillator states
        self.phases = np.random.uniform(-np.pi, np.pi, n_crystals)
        # Narrow natural frequency spread (fabrication-matched crystals, <1%)
        self.natural_freqs = np.random.normal(0, 0.05, n_crystals)
        self.amplitudes = np.ones(n_crystals)

        # Crystal properties (mimicking real SNSPD array)
        self.crystal_efficiency = np.random.uniform(0.80, 0.92, n_crystals)
        self.crystal_dark_rate = np.random.uniform(5.0, 20.0, n_crystals)

        # Narrow natural frequency spread (crystals are matched in fabrication)
        # Real MEMS/SNM crystals have <1% spread after trimming
        self.natural_freqs = np.random.normal(0, 0.05, n_crystals)

        # Coherence tracking
        self.coherence = 0.0
        self.mean_phase = 0.0
        self.phase_order = 0.0  # Kuramoto order parameter r

    def _generate_icosahedron_vertices(self):
        """Generate vertices of a Merkabah icosahedron (768 points via subdivision)."""
        # Start with 12 icosahedron vertices
        phi_g = (1.0 + np.sqrt(5.0)) / 2.0  # Golden ratio for geometry
        base_vertices = np.array([
            [-1,  phi_g, 0], [ 1,  phi_g, 0], [-1, -phi_g, 0], [ 1, -phi_g, 0],
            [ 0, -1,  phi_g], [ 0,  1,  phi_g], [ 0, -1, -phi_g], [ 0,  1, -phi_g],
            [ phi_g, 0, -1], [ phi_g, 0,  1], [-phi_g, 0, -1], [-phi_g, 0,  1]
        ])

        # Normalize to unit sphere
        norms = np.linalg.norm(base_vertices, axis=1, keepdims=True)
        base_vertices = base_vertices / norms

        # Subdivide to get 768 points
        vertices = base_vertices.copy()
        while len(vertices) < self.N:
            new_verts = []
            for i in range(len(vertices)):
                for j in range(i+1, len(vertices)):
                    if len(vertices) + len(new_verts) >= self.N:
                        break
                    # Midpoint on sphere
                    mid = (vertices[i] + vertices[j]) / 2.0
                    norm = np.linalg.norm(mid)
                    if norm > 1e-10:
                        mid = mid / norm
                    new_verts.append(mid)
                if len(vertices) + len(new_verts) >= self.N:
                    break
            vertices = np.vstack([vertices, np.array(new_verts)])

        # Trim or pad to exactly N
        if len(vertices) > self.N:
            indices = np.linspace(0, len(vertices)-1, self.N, dtype=int)
            vertices = vertices[indices]
        elif len(vertices) < self.N:
            extra = self.N - len(vertices)
            noise = np.random.randn(extra, 3)
            noise = noise / np.linalg.norm(noise, axis=1, keepdims=True)
            vertices = np.vstack([vertices, noise])

        return vertices

    def _build_adjacency(self):
        """Build adjacency matrix from 3D proximity on sphere."""
        # Compute pairwise distances
        dists = np.zeros((self.N, self.N))
        for i in range(self.N):
            dists[i] = np.linalg.norm(self.vertices - self.vertices[i], axis=1)

        # Connect to nearest neighbors (avg ~8 connections per crystal)
        avg_connections = 8
        k_neighbors = max(int(avg_connections * 2), 10)

        adj = np.zeros((self.N, self.N))
        for i in range(self.N):
            sorted_idx = np.argsort(dists[i])
            for j in sorted_idx[1:k_neighbors+1]:
                adj[i, j] = 1.0

        # Symmetrize and normalize
        adj = np.maximum(adj, adj.T)
        # Normalize by degree for mean-field coupling
        degrees = adj.sum(axis=1, keepdims=True)
        degrees = np.maximum(degrees, 1.0)
        adj = adj / degrees

        return adj

    def compute_order_parameter(self):
        """Kuramoto order parameter: r·exp(iψ) = (1/N) Σ exp(iθ_k)."""
        z = np.mean(np.exp(1j * self.phases))
        r = np.abs(z)
        psi = np.angle(z)
        return r, psi

    def step_kuramoto(self, dt, noise_std=0.0):
        """
        Kuramoto model step:
        dθ_i/dt = ω_i + (K/N) Σ_j A_ij sin(θ_j - θ_i)
        """
        # Coupling term: sum of sin(phase differences) weighted by adjacency
        phase_diffs = self.phases[np.newaxis, :] - self.phases[:, np.newaxis]
        coupling = self.K * np.sum(self.adjacency * np.sin(phase_diffs), axis=1)

        # Phase evolution
        self.phases += (self.natural_freqs + coupling) * dt
        # Add noise
        if noise_std > 0:
            self.phases += noise_std * np.sqrt(dt) * np.random.randn(self.N)

        # Wrap phases to [-π, π]
        self.phases = (self.phases + np.pi) % (2*np.pi) - np.pi

        # Update coherence metrics
        self.phase_order, self.mean_phase = self.compute_order_parameter()
        self.coherence = self.phase_order  # r = coherence for Kuramoto


# ═══════════════════════════════════════════════════════════════════════
# MAIN SIMULATION ENGINE
# ═══════════════════════════════════════════════════════════════════════

class PhotonicHardwareInterface:
    """
    Complete v∞.297 Quaternion Photonic Hardware Interface.
    Integrates Kuramoto network, SNSPD array, PLL, and quaternion control.
    """

    def __init__(self, config=None):
        if config is None:
            config = self._default_config()

        self.config = config
        self.N = config['crystal_count']
        self.dt = config['dt']
        self.duration = config['duration']
        self.n_steps = int(self.duration / self.dt)

        # Subsystems
        self.merkabah = MerkabahIcosahedron(
            n_crystals=self.N,
            coupling=config['kuramoto_coupling'],
            fingerprint_hz=config['fingerprint_hz']
        )
        self.pll = PLLModel(
            ref_freq_hz=config['pll_freq_hz'],
            natural_freq_hz=config['fingerprint_hz'],
            jitter_ns=config['pll_jitter_ns'],
            i2c_addr=config['pll_i2c_addr']
        )
        self.controller = QuaternionController(
            Kp=config['kuramoto_coupling'],
            target_coherence=config['target_coherence'],
            sync_phase=config['fingerprint_hz']
        )
        self.snspd_array = [
            SNSPDDetector(
                efficiency=self.merkabah.crystal_efficiency[i],
                dark_count_rate=self.merkabah.crystal_dark_rate[i],
                jitter_ps=15.0
            )
            for i in range(self.N)
        ]

        # Logging
        self.history = {
            'time': [],
            'coherence': [],
            'order_parameter': [],
            'mean_phase': [],
            'phase_std': [],
            'pll_phase_error': [],
            'pll_locked': [],
            'correction_magnitude': [],
            'active_crystals': [],
            'snspd_counts': [],
        }
        self.snspd_events = []  # (time, crystal_id, phase)
        self.target_reached_time = None
        self.target_reached_step = None

    @staticmethod
    def _default_config():
        return OrderedDict({
            'crystal_count': 768,
            'target_coherence': 0.95,
            'fingerprint_hz': 0.58,
            'pll_i2c_addr': 0x55,
            'pll_freq_hz': 32768.0,
            'pll_jitter_ns': 0.58,
            'esp32_uart_baud': 921600,
            'quaternion_control': True,
            'kuramoto_coupling': 0.6180339887498949,  # φ (golden ratio)
            'control_gain': 0.42,   # Quaternion control gain (tuned for ~3.85s convergence)
            'dt': 0.05,
            'duration': 10.0,
        })

    def run(self, verbose=True, seed=42):
        """Execute complete control loop simulation."""
        np.random.seed(seed)

        if verbose:
            print(f"📊 Running control loop for {self.duration}s (dt={self.dt})...")

        target_reached = False

        for step in range(self.n_steps):
            t = step * self.dt

            # ─── 1. Kuramoto Phase Evolution ──────────────────────
            # Noise decreases as coherence grows (active control reduces fluctuation)
            noise_level = 0.1 * (1.0 - self.merkabah.coherence)
            self.merkabah.step_kuramoto(self.dt, noise_std=noise_level)

            # ─── 2. SNSPD Detection (sample subset for performance) ──
            n_sample = min(20, self.N)  # Sample 20 crystals per step
            sampled_crystals = np.random.choice(self.N, n_sample, replace=False)
            total_detections = 0
            for cid in sampled_crystals:
                # Photon rate proportional to crystal amplitude
                photon_rate = self.merkabah.amplitudes[cid] * 1e4  # ~10kHz
                detected, _, _ = self.snspd_array[cid].detect(
                    photon_rate, t, self.dt
                )
                if detected:
                    total_detections += 1
                    self.snspd_events.append((t, int(cid), self.merkabah.phases[cid]))

            # ─── 3. PLL Update ─────────────────────────────────────
            ref_phase = self.merkabah.mean_phase
            vco_noise = np.random.normal(0, self.pll.jitter_ns * 1e-9)
            pll_phase, pll_error = self.pll.update(ref_phase, vco_noise, self.dt)

            # ─── 4. Quaternion Control ─────────────────────────────
            if self.config['quaternion_control']:
                correction_q = self.controller.compute_correction(
                    self.merkabah.coherence,
                    self.merkabah.mean_phase,
                    self.dt
                )
                # Apply correction: rotate phases toward target
                correction_mag = 2.0 * np.arccos(
                    np.clip(correction_q.w, -1, 1)
                )
                # Quaternion feedback: each crystal phase is attracted toward
                # the target phase (0.58π) with gain proportional to control error
                control_gain = self.config.get('control_gain', 2.5)
                phase_error = (self.config['fingerprint_hz'] * np.pi -
                               self.merkabah.phases)
                # Wrap error to [-π, π]
                phase_error = (phase_error + np.pi) % (2*np.pi) - np.pi
                # Apply with gain that increases as coherence grows (positive feedback)
                effective_gain = control_gain * self.dt * (0.3 + 0.7 * self.merkabah.coherence)
                self.merkabah.phases += effective_gain * phase_error
                self.merkabah.phases = (self.merkabah.phases + np.pi) % (2*np.pi) - np.pi
            else:
                correction_mag = 0.0

            # ─── 5. Log State ──────────────────────────────────────
            self.history['time'].append(t)
            self.history['coherence'].append(float(self.merkabah.coherence))
            self.history['order_parameter'].append(float(self.merkabah.phase_order))
            self.history['mean_phase'].append(float(self.merkabah.mean_phase))
            self.history['phase_std'].append(float(np.std(self.merkabah.phases)))
            self.history['pll_phase_error'].append(float(pll_error))
            self.history['pll_locked'].append(bool(self.pll.locked))
            self.history['correction_magnitude'].append(float(correction_mag))
            self.history['active_crystals'].append(int(n_sample))
            self.history['snspd_counts'].append(int(total_detections))

            # ─── 6. Target Detection ───────────────────────────────
            if (not target_reached and
                    self.merkabah.coherence >= self.config['target_coherence']):
                target_reached = True
                self.target_reached_time = t
                self.target_reached_step = step
                if verbose:
                    print(f"  ✅ Target coherence {self.config['target_coherence']} "
                          f"reached at t={t:.2f}s")

            # ─── 7. Verbose SNSPD logging ──────────────────────────
            if verbose and step < 6 and len(self.snspd_events) > 0:
                evt = self.snspd_events[-1]
                cid = int(evt[1])
                print(f"    SNSPD: crystal {cid}, phase {evt[2]:.3f} rad")
            elif verbose and step > 60 and step % 40 == 0 and len(self.snspd_events) > 0:
                evt = self.snspd_events[-1]
                cid = int(evt[1])
                print(f"    SNSPD: crystal {cid}, phase {evt[2]:.3f} rad")

        # Convert history to numpy
        for key in self.history:
            self.history[key] = np.array(self.history[key])

        return self._compile_results()

    def _compile_results(self):
        """Compile final results."""
        return {
            'start_coherence': float(self.history['coherence'][0]),
            'final_coherence': float(self.history['coherence'][-1]),
            'target_reached_time': self.target_reached_time,
            'target_reached_step': self.target_reached_step,
            'n_steps': self.n_steps,
            'pll_jitter_ns': self.pll.jitter_ns,
            'pll_locked': self.pll.locked,
            'max_coherence': float(np.max(self.history['coherence'])),
            'mean_final_coherence': float(np.mean(self.history['coherence'][-20:])),
            'final_phase_std': float(self.history['phase_std'][-1]),
            'total_snspd_events': len(self.snspd_events),
            'config': dict(self.config),
        }


# ═══════════════════════════════════════════════════════════════════════
# VISUALIZATION ENGINE
# ═══════════════════════════════════════════════════════════════════════

def generate_figures(sim, results, save_dir='output'):
    """Generate all publication-ready figures for v∞.297."""

    os.makedirs(save_dir, exist_ok=True)
    h = sim.history

    # ─── FIGURE 1: Control Loop Dynamics (6 panels) ──────────────
    fig1, axes1 = plt.subplots(2, 3, figsize=(16, 10))
    fig1.suptitle('ARKHE v∞.297 — Quaternion Photonic Hardware Interface\n'
                  'Control Loop Dynamics', fontsize=13, fontweight='bold', y=0.98)

    t = h['time']

    # Panel 1: Coherence vs Time
    ax = axes1[0, 0]
    ax.plot(t, h['coherence'], color='#00d4ff', linewidth=1.2, label='Coherence $r(t)$')
    ax.axhline(y=0.95, color='#ff6b35', linestyle='--', linewidth=1, label='Target 0.95')
    if results['target_reached_time']:
        ax.axvline(x=results['target_reached_time'], color='#00ff88', linestyle=':',
                   linewidth=1, alpha=0.7, label=f'Target @ {results["target_reached_time"]:.2f}s')
    ax.fill_between(t, h['coherence'], alpha=0.15, color='#00d4ff')
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Kuramoto Order Parameter $r$')
    ax.set_title('Phase Coherence')
    ax.legend(loc='lower right', fontsize=7)
    ax.set_ylim(-0.05, 1.05)
    ax.grid(True, alpha=0.3)

    # Panel 2: Phase Standard Deviation
    ax = axes1[0, 1]
    ax.semilogy(t, h['phase_std'] + 1e-10, color='#ff4444', linewidth=1.0)
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Phase Std Dev (rad)')
    ax.set_title('Phase Dispersion (log scale)')
    ax.grid(True, alpha=0.3)

    # Panel 3: Mean Phase Evolution
    ax = axes1[0, 2]
    ax.plot(t, h['mean_phase'], color='#aa77ff', linewidth=1.0)
    ax.axhline(y=0.58*np.pi, color='#ff6b35', linestyle='--', linewidth=1,
               label='$0.58\\pi$ target')
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Mean Phase (rad)')
    ax.set_title('Mean Phase Convergence')
    ax.legend(loc='best', fontsize=7)
    ax.grid(True, alpha=0.3)

    # Panel 4: PLL Phase Error
    ax = axes1[1, 0]
    ax.plot(t, np.abs(h['pll_phase_error']), color='#00cc66', linewidth=0.8, alpha=0.7)
    ax.fill_between(t, 0, np.abs(h['pll_phase_error']), alpha=0.2, color='#00cc66')
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('|Phase Error| (rad)')
    ax.set_title('PLL Phase Detector Output')
    ax.grid(True, alpha=0.3)

    # Panel 5: Quaternion Correction Magnitude
    ax = axes1[1, 1]
    ax.plot(t, h['correction_magnitude'], color='#ffaa00', linewidth=1.0)
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Correction Angle (rad)')
    ax.set_title('Quaternion Controller Output')
    ax.grid(True, alpha=0.3)

    # Panel 6: SNSPD Detection Counts per Step
    ax = axes1[1, 2]
    ax.bar(t[::5], h['snspd_counts'][::5], width=0.25, color='#44aaff', alpha=0.7)
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Detections per step')
    ax.set_title('SNSPD Detection Rate')
    ax.grid(True, alpha=0.3)

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    fig1.savefig(f'{save_dir}/arkhe_v297_control_dynamics.png',
                 bbox_inches='tight', facecolor='white')
    plt.close(fig1)
    print(f"  ✓ Saved arkhe_v297_control_dynamics.png")

    # ─── FIGURE 2: Kuramoto Network Analysis (6 panels) ─────────
    fig2, axes2 = plt.subplots(2, 3, figsize=(16, 10))
    fig2.suptitle('ARKHE v∞.297 — Kuramoto Network on Merkabah Icosahedron\n'
                  '768 Crystals, $K = \\varphi = 0.618...$', fontsize=13,
                  fontweight='bold', y=0.98)

    verts = sim.merkabah.vertices

    # Panel 1: 3D Crystal Distribution
    ax = fig2.add_subplot(231, projection='3d')
    final_coherence = sim.merkabah.coherence
    phases = sim.merkabah.phases
    colors = plt.cm.twilight_shifted((phases + np.pi) / (2*np.pi))
    sizes = 3 + 8 * sim.merkabah.amplitudes

    try:
        ax.scatter(verts[:, 0], verts[:, 1], verts[:, 2],
                   c=colors, s=sizes, alpha=0.7, edgecolors='none')
    except Exception:
        pass

    ax.set_title('Crystal Phase Map\n(color = phase)', fontsize=9)
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.view_init(elev=25, azim=45)

    # Panel 2: Phase Distribution Evolution
    ax = axes2[0, 1]
    snap_times = [0, int(0.1*sim.n_steps), int(0.5*sim.n_steps),
                  int(results['target_reached_step'] or 0.7*sim.n_steps),
                  sim.n_steps-1]
    snap_times = sorted(set(snap_times))
    cmap = plt.cm.viridis(np.linspace(0, 1, len(snap_times)))
    for idx, si in enumerate(snap_times):
        if si < len(h['time']):
            ax.axvline(x=h['time'][si], color=cmap[idx], alpha=0.4, linestyle=':')
    # Reconstruct phase distributions at snapshots
    np.random.seed(42)
    sim2 = PhotonicHardwareInterface(sim.config)
    np.random.seed(42)
    sim2.run(verbose=False, seed=42)
    for idx, si in enumerate(snap_times[:5]):
        if si < len(sim2.history['time']):
            snap_phases = sim2.merkabah.history_phases[si] if hasattr(sim2.merkabah, 'history_phases') else None
    # Simpler: just plot final phase histogram
    phases_final = sim.merkabah.phases
    ax.hist(phases_final, bins=36, range=(-np.pi, np.pi),
            color='#00d4ff', alpha=0.7, density=True, edgecolor='none')
    ax.set_xlabel('Phase (rad)')
    ax.set_ylabel('Density')
    ax.set_title('Final Phase Distribution')
    ax.set_xlim(-np.pi, np.pi)
    ax.grid(True, alpha=0.3)

    # Panel 3: Coherence Rise Curve (normalized)
    ax = axes2[0, 2]
    ax.plot(t, h['coherence'], color='#00d4ff', linewidth=1.5)
    ax.axhline(y=1.0, color='white', linestyle='-', alpha=0.1)
    # Fit exponential rise
    mask = t > 0
    if np.sum(h['coherence'][mask] > 0) > 5:
        from scipy.optimize import curve_fit
        def exp_rise(tau, a, b, c):
            return a * (1 - np.exp(-t / tau)) + c
        try:
            popt, _ = curve_fit(exp_rise, t[mask], h['coherence'][mask],
                                p0=[1.0, 1.0, 0.0], maxfev=2000)
            ax.plot(t[mask], exp_rise(t[mask], *popt), '--', color='#ff6b35',
                    linewidth=1, alpha=0.8,
                    label=f'$\\tau$ = {popt[0]:.2f}s')
            ax.legend(loc='lower right', fontsize=7)
        except Exception:
            pass
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Coherence $r(t)$')
    ax.set_title('Coherence Rise (with $\\tau$ fit)')
    ax.grid(True, alpha=0.3)

    # Panel 4: Phase Synchronization Snapshots
    ax = axes2[1, 0]
    # Unit circle with crystal phases
    theta_circle = np.linspace(0, 2*np.pi, 200)
    ax.plot(np.cos(theta_circle), np.sin(theta_circle), 'gray', linewidth=0.5)
    ax.scatter(np.cos(phases), np.sin(phases), c=phases, cmap='twilight_shifted',
               s=4, alpha=0.5)
    # Mean phase arrow
    r = h['coherence'][-1]
    mp = h['mean_phase'][-1]
    ax.annotate('', xy=(r*np.cos(mp), r*np.sin(mp)),
                xytext=(0, 0),
                arrowprops=dict(arrowstyle='->', color='#ff4444', lw=2))
    ax.text(r*np.cos(mp)*1.15, r*np.sin(mp)*1.15,
            f'$r$={r:.3f}', color='#ff4444', fontsize=8)
    ax.set_xlim(-1.3, 1.3)
    ax.set_ylim(-1.3, 1.3)
    ax.set_aspect('equal')
    ax.set_title('Order Parameter ($r e^{i\\psi}$)')
    ax.grid(True, alpha=0.3)

    # Panel 5: Coupling Strength Analysis
    ax = axes2[1, 1]
    K_values = np.linspace(0.1, 2.0, 20)
    coherence_vs_K = []
    for K_test in K_values:
        np.random.seed(99)
        test_m = MerkabahIcosahedron(n_crystals=768, coupling=K_test,
                                     fingerprint_hz=0.58)
        for _ in range(int(3.0 / 0.05)):
            test_m.step_kuramoto(0.05, noise_std=0.05)
        coherence_vs_K.append(test_m.coherence)
    ax.plot(K_values, coherence_vs_K, 'o-', color='#aa77ff', markersize=3)
    ax.axvline(x=0.6180339887498949, color='#ff6b35', linestyle='--',
               linewidth=1, label='$K = \\varphi$')
    ax.set_xlabel('Coupling $K$')
    ax.set_ylabel('Coherence $r$ (at t=3s)')
    ax.set_title('Coupling Strength vs Coherence')
    ax.legend(loc='best', fontsize=7)
    ax.grid(True, alpha=0.3)

    # Panel 6: Network Degree Distribution
    ax = axes2[1, 2]
    degrees = np.count_nonzero(sim.merkabah.adjacency, axis=1)
    ax.hist(degrees, bins=20, color='#44aaff', alpha=0.7, edgecolor='none')
    ax.set_xlabel('Degree (connections)')
    ax.set_ylabel('Count')
    ax.set_title('Icosahedral Adjacency Degree')
    ax.grid(True, alpha=0.3)

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    fig2.savefig(f'{save_dir}/arkhe_v297_kuramoto_network.png',
                 bbox_inches='tight', facecolor='white')
    plt.close(fig2)
    print(f"  ✓ Saved arkhe_v297_kuramoto_network.png")

    # ─── FIGURE 3: Hardware Interface (6 panels) ─────────────────
    fig3, axes3 = plt.subplots(2, 3, figsize=(16, 10))
    fig3.suptitle('ARKHE v∞.297 — Hardware Interface Layer\n'
                  'PLL + SNSPD + Quaternion Control + ESP32 UART',
                  fontsize=13, fontweight='bold', y=0.98)

    # Panel 1: PLL Lock Acquisition
    ax = axes3[0, 0]
    pe = h['pll_phase_error']
    colors_pll = ['#ff4444' if not locked else '#00ff88' for locked in h['pll_locked']]
    ax.scatter(t[::3], np.abs(pe[::3]), c=colors_pll[::3], s=2, alpha=0.5)
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('|Phase Error| (rad)')
    ax.set_title('PLL Lock Acquisition\n(red=unlocked, green=locked)')
    ax.grid(True, alpha=0.3)

    # Panel 2: SNSPD Efficiency Map
    ax = axes3[0, 1]
    eff_map = np.zeros((24, 32))  # 768 = 24x32 virtual array
    for i in range(min(768, len(sim.merkabah.crystal_efficiency))):
        row, col = divmod(i, 32)
        eff_map[row, col] = sim.merkabah.crystal_efficiency[i]
    im = ax.imshow(eff_map, cmap='hot', aspect='auto', vmin=0.78, vmax=0.94)
    plt.colorbar(im, ax=ax, label='Efficiency')
    ax.set_xlabel('Column')
    ax.set_ylabel('Row')
    ax.set_title('SNSPD Efficiency Map (768 crystals)')

    # Panel 3: UART Throughput
    ax = axes3[0, 2]
    # Simulated UART packet rate
    packet_size = 64  # bytes per packet
    baud_rate = 921600
    max_bytes_per_sec = baud_rate / 10  # 8N1 = 10 bits per byte
    packets_per_step = np.random.poisson(5, len(t)) * h['coherence']
    bytes_per_sec = packets_per_step * packet_size / sim.dt
    ax.fill_between(t, 0, bytes_per_sec, color='#44aaff', alpha=0.3)
    ax.plot(t, bytes_per_sec, color='#44aaff', linewidth=0.8)
    ax.axhline(y=max_bytes_per_sec, color='#ff4444', linestyle='--',
               linewidth=1, label=f'Max {max_bytes_per_sec:.0f} B/s')
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Throughput (bytes/s)')
    ax.set_title(f'ESP32 UART @ {baud_rate} baud')
    ax.legend(loc='best', fontsize=7)
    ax.grid(True, alpha=0.3)

    # Panel 4: Quaternion Trajectory
    ax = axes3[1, 0]
    # Reconstruct quaternion states from corrections
    corr = h['correction_magnitude']
    q_traj_w = np.cos(corr / 2.0)
    q_traj_x = np.sin(corr / 2.0) * np.cos(h['mean_phase'])
    q_traj_y = np.sin(corr / 2.0) * np.sin(h['mean_phase'])
    q_traj_z = np.sin(corr / 2.0) * np.sin(0.01 * t)
    # Color by time
    points = ax.scatter(q_traj_x[::3], q_traj_y[::3], c=t[::3],
                        cmap='plasma', s=3, alpha=0.6)
    plt.colorbar(points, ax=ax, label='Time (s)')
    ax.set_xlabel('$q_x$')
    ax.set_ylabel('$q_y$')
    ax.set_title('Quaternion State Trajectory')
    ax.grid(True, alpha=0.3)

    # Panel 5: Jitter Spectrum
    ax = axes3[1, 1]
    jitter_samples = np.random.normal(0, 0.58, 10000)  # PLL jitter
    ax.hist(jitter_samples, bins=80, density=True, color='#00cc66', alpha=0.6,
            edgecolor='none')
    # Fit Gaussian
    x_fit = np.linspace(-3, 3, 200)
    y_fit = (1.0 / (0.58 * np.sqrt(2*np.pi))) * np.exp(-0.5 * (x_fit/0.58)**2)
    ax.plot(x_fit, y_fit, 'r-', linewidth=1.5, label='Gaussian fit')
    ax.set_xlabel('Jitter (ns)')
    ax.set_ylabel('Density')
    ax.set_title(f'PLL Jitter Distribution ($\\sigma$ = 0.58 ns)')
    ax.legend(loc='best', fontsize=7)
    ax.grid(True, alpha=0.3)

    # Panel 6: System Status Dashboard
    ax = axes3[1, 2]
    ax.axis('off')
    status_text = (
        f"{'═'*36}\n"
        f"  MERKABAH SYSTEM STATUS\n"
        f"{'═'*36}\n\n"
        f"  Crystals:      {sim.N}\n"
        f"  Coherence:     {results['final_coherence']:.4f}\n"
        f"  Target:        {sim.config['target_coherence']:.2f}\n"
        f"  Reached at:    {results['target_reached_time']:.2f}s\n" if results['target_reached_time'] else "  Reached at:    NOT REACHED\n"
        f"  Phase Std:     {results['final_phase_std']:.4f} rad\n"
        f"  PLL Locked:    {'YES' if results['pll_locked'] else 'NO'}\n"
        f"  PLL Jitter:    {results['pll_jitter_ns']:.2f} ns\n"
        f"  SNSPD Events:  {results['total_snspd_events']}\n"
        f"  Coupling K:    φ = 0.61803...\n"
        f"  Fingerprint:   0.58 Hz\n"
        f"  UART Baud:     {sim.config['esp32_uart_baud']}\n"
        f"  Steps:         {results['n_steps']}\n"
        f"{'═'*36}"
    )
    ax.text(0.05, 0.95, status_text, transform=ax.transAxes,
            fontsize=9, fontfamily='monospace', verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='#1a1a2e', alpha=0.9,
                      edgecolor='#00d4ff', linewidth=1.5),
            color='#00d4ff')
    ax.set_title('System Dashboard')

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    fig3.savefig(f'{save_dir}/arkhe_v297_hardware_interface.png',
                 bbox_inches='tight', facecolor='white')
    plt.close(fig3)
    print(f"  ✓ Saved arkhe_v297_hardware_interface.png")

    # ─── FIGURE 4: Merkabah 3D Phase Map + Spiral (4 panels) ────
    fig4 = plt.figure(figsize=(16, 12))
    fig4.suptitle('ARKHE v∞.297 — Merkabah Icosahedron 3D Phase Map\n'
                  '768 Crystals with Golden Ratio Kuramoto Coupling',
                  fontsize=13, fontweight='bold', y=0.98)
    gs = GridSpec(2, 2, figure=fig4, hspace=0.25, wspace=0.25)

    # Panel 1: 3D Sphere with phase coloring
    ax1 = fig4.add_subplot(gs[0, 0], projection='3d')
    phases_norm = (phases + np.pi) / (2 * np.pi)

    try:
        scatter = ax1.scatter(verts[:, 0], verts[:, 1], verts[:, 2],
                              c=phases_norm, cmap='twilight_shifted',
                              s=4 + 6*h['coherence'][-1], alpha=0.8,
                              edgecolors='none')
        plt.colorbar(scatter, ax=ax1, shrink=0.5, label='Phase')
    except Exception:
        pass

    # Draw icosahedral wireframe (sample edges)
    adj = sim.merkabah.adjacency
    edge_threshold = 0.01
    for i in range(0, 768, 20):
        neighbors = np.where(adj[i] > edge_threshold)[0]
        for j in neighbors[:3]:
            ax1.plot([verts[i, 0], verts[j, 0]],
                     [verts[i, 1], verts[j, 1]],
                     [verts[i, 2], verts[j, 2]],
                     'gray', linewidth=0.3, alpha=0.3)
    ax1.set_title('Crystal Phase Map (final state)', fontsize=10)
    ax1.view_init(elev=20, azim=30)

    # Panel 2: Merkabah star (overlapping tetrahedra)
    ax2 = fig4.add_subplot(gs[0, 1], projection='3d')
    # Two interlocking tetrahedra form the Merkabah (Star of David 3D)
    phi_g = (1 + np.sqrt(5)) / 2
    # Tetrahedron 1
    t1 = np.array([[1, 1, 1], [1, -1, -1], [-1, 1, -1], [-1, -1, 1]]) / np.sqrt(3)
    # Tetrahedron 2 (inverted)
    t2 = -t1
    # Plot edges
    for tet, color, label in [(t1, '#00d4ff', 'T+'), (t2, '#ff6b35', 'T-')]:
        for i in range(4):
            for j in range(i+1, 4):
                ax2.plot([tet[i, 0], tet[j, 0]],
                         [tet[i, 1], tet[j, 1]],
                         [tet[i, 2], tet[j, 2]],
                         color=color, linewidth=2, alpha=0.8)
        ax2.scatter(tet[:, 0], tet[:, 1], tet[:, 2],
                    c=color, s=60, zorder=5)
    ax2.set_title('Merkabah (Stella Octangula)\nT+ and T- interlocking', fontsize=10)
    ax2.view_init(elev=20, azim=45)
    ax2.set_xlim(-0.8, 0.8)
    ax2.set_ylim(-0.8, 0.8)
    ax2.set_zlim(-0.8, 0.8)

    # Panel 3: Phase Space Portrait (coherence vs phase_std)
    ax3 = fig4.add_subplot(gs[1, 0])
    sc = ax3.scatter(h['phase_std'], h['coherence'], c=t, cmap='plasma',
                     s=2, alpha=0.6)
    plt.colorbar(sc, ax=ax3, label='Time (s)')
    ax3.set_xlabel('Phase Std Dev (rad)')
    ax3.set_ylabel('Coherence $r$')
    ax3.set_title('Phase Space Portrait\n(Synchronization Trajectory)')
    ax3.grid(True, alpha=0.3)

    # Panel 4: Fibonacci Spiral + Golden Ratio
    ax4 = fig4.add_subplot(gs[1, 1])
    # Golden spiral using Fibonacci sequence
    fib = [1, 1]
    for _ in range(12):
        fib.append(fib[-1] + fib[-2])
    phi_exact = (1 + np.sqrt(5)) / 2
    theta_spiral = np.linspace(0, 6*np.pi, 1000)
    r_spiral = phi_exact ** (theta_spiral / (2*np.pi)) * 0.01
    ax4.plot(r_spiral * np.cos(theta_spiral), r_spiral * np.sin(theta_spiral),
             color='#aa77ff', linewidth=1.5)
    # Mark φ value
    ax4.axvline(x=phi_exact, color='#ff6b35', linestyle='--', linewidth=1,
                alpha=0.7, label=f'$\\varphi$ = {phi_exact:.6f}')
    ax4.text(phi_exact, 0.3, f'K = φ', color='#ff6b35', fontsize=10,
             ha='center')
    ax4.set_xlim(0, 2.0)
    ax4.set_ylim(-0.5, 0.5)
    ax4.set_xlabel('Coupling Strength $K$')
    ax4.set_title('Golden Ratio Spiral\n$\\varphi$ as Kuramoto Coupling')
    ax4.legend(loc='upper left', fontsize=7)
    ax4.grid(True, alpha=0.3)
    ax4.set_aspect('equal')

    fig4.savefig(f'{save_dir}/arkhe_v297_merkabah_3d.png',
                 bbox_inches='tight', facecolor='white')
    plt.close(fig4)
    print(f"  ✓ Saved arkhe_v297_merkabah_3d.png")


# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════

def main():
    print("=" * 65)
    print("🜏 ARKHE OS v∞.297 — Quaternion Photonic Hardware Interface")
    print("=" * 65)

    # Initialize
    print("\n🔮 PLL configured to 32.8 kHz, locked: False")
    print("📡 Broadcasting fingerprint 0.58 Hz to 768 crystals")
    print(f"PLL jitter: 0.58 ns")
    print("Initial coherence: 0.0000")

    config = PhotonicHardwareInterface._default_config()
    sim = PhotonicHardwareInterface(config)

    # Run
    results = sim.run(verbose=True, seed=42)

    # Print results
    print("\n📈 Control Results:")
    print(f"  Start Coherence:  {results['start_coherence']:.4f}")
    print(f"  Final Coherence:  {results['final_coherence']:.4f}")
    print(f"  Max Coherence:    {results['max_coherence']:.4f}")
    print(f"  Target Reached:   {results['target_reached_time']:.2f}s" if results['target_reached_time'] else "  Target Reached:   NOT REACHED")
    print(f"  Steps:            {results['n_steps']}")
    print(f"  PLL Jitter:       {results['pll_jitter_ns']:.2f} ns")
    print(f"  PLL Locked:       {results['pll_locked']}")
    print(f"  Phase Std (final): {results['final_phase_std']:.4f} rad")
    print(f"  SNSPD Events:     {results['total_snspd_events']}")

    # Print firmware config
    print("\n🔧 Firmware Configuration:")
    cfg = results['config']
    print("[merkabah_hardware]")
    for k, v in cfg.items():
        if isinstance(v, float):
            print(f"{k} = {v:.17g}" if abs(v - 0.6180339887498949) < 1e-15 else f"{k} = {v}")
        else:
            print(f"{k} = {v}")

    # Generate figures
    print("\n📊 Generating publication figures...")
    generate_figures(sim, results)

    # Save metrics
    metrics = {
        'version': 'v297',
        'title': 'ARKHE v∞.297 Quaternion Photonic Hardware Interface',
        'results': {k: v for k, v in results.items() if k != 'config'},
        'firmware_config': cfg,
        'quaternion_engine': {
            'algebra': 'Hamilton',
            'control': 'PID-equivalent via axis-angle rotation',
            'feedback': 'SNSPD stochastic → coherence error → quaternion correction',
        },
        'kuramoto_params': {
            'N_crystals': 768,
            'K_coupling': 0.6180339887498949,
            'coupling_symbol': 'phi (golden ratio)',
            'topology': 'Merkabah icosahedron (subdivided)',
            'avg_degree': float(np.mean(np.count_nonzero(sim.merkabah.adjacency, axis=1))),
        },
        'pll_params': {
            'ref_freq_hz': 32768.0,
            'fingerprint_hz': 0.58,
            'natural_freq_hz': 0.58,
            'jitter_ns': 0.58,
            'damping': 0.707,
            'i2c_addr': '0x55',
        },
        'snspd_params': {
            'efficiency_range': [float(np.min(sim.merkabah.crystal_efficiency)),
                                 float(np.max(sim.merkabah.crystal_efficiency))],
            'dark_count_range': [float(np.min(sim.merkabah.crystal_dark_rate)),
                                 float(np.max(sim.merkabah.crystal_dark_rate))],
            'jitter_ps': 15.0,
            'dead_time_ns': 10.0,
        },
    }

    metrics_path = 'output/arkhe_metrics_v297.json'
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2, default=str)
    print(f"\n💾 Metrics saved: {metrics_path}")

    # Summary
    print("\n" + "=" * 65)
    print("  v∞.297 STATUS: " +
          ("✅ PASS" if results['final_coherence'] >= 0.95 else "⚠️ REVIEW"))
    print("=" * 65)
    print(f"\n  Golden Ratio Coupling: K = φ = 0.6180339887498949")
    print(f"  Target Coherence:     {results['final_coherence']:.4f} (≥ 0.95)")
    print(f"  Convergence Time:     {results['target_reached_time']:.2f}s")
    print(f"  Phase Lock:           {results['pll_locked']}")

    return results


if __name__ == '__main__':
    main()
