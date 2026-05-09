import numpy as np
import matplotlib.pyplot as plt
from scipy.fft import fft2, ifft2
from typing import Dict, Optional

# Attempt to use cupy for GPU acceleration, fallback to numpy
try:
    import cupy as cp
    def to_numpy(x):
        return cp.asnumpy(x)
except ImportError:
    cp = np
    def to_numpy(x):
        return x

class PhaseFocusingEngine:
    """
    Phase focusing engine for C->Z projection in specific worlds.
    Implements phi-optimized SLM and optical Fourier transform.
    """

    def __init__(self, merkabah_core, world_id: int = 42):
        self.core = merkabah_core
        self.world_id = world_id
        self.phi = (1 + 5**0.5) / 2

        # Extract target world state
        branch = self.core.multiverse.get_branch(world_id)
        self.psi_world = cp.array(branch.psi_c)
        self.lambda_world = branch.lambda_2

        # phi-optimized SLM parameters
        self.resolution = 512
        self.pixel_pitch = 10e-6  # 10 µm
        self.wavelength = 532e-9  # 532 nm (green)
        self.k = 2 * np.pi / self.wavelength

        # Coordinate field
        x = np.linspace(-self.resolution//2, self.resolution//2, self.resolution) * self.pixel_pitch
        self.X, self.Y = np.meshgrid(x, x)
        self.R = np.sqrt(self.X**2 + self.Y**2)
        self.Theta = np.arctan2(self.Y, self.X)

    def design_phase_mask(self, focal_length: float = 10e-3,
                         pattern: str = "spherical",
                         correction_phi: bool = True) -> cp.ndarray:
        """
        Designs a phase mask for a lens with optional phi-optimal correction or vortex pattern.
        """
        if pattern == "vortex":
            # Laguerre-Gauss vortex of order l=2
            l = 2
            phase_pattern = l * self.Theta
        else:
            # Basic parabolic phase (ideal lens)
            r_squared = self.X**2 + self.Y**2
            phase_pattern = -self.k * r_squared / (2 * focal_length)

            if correction_phi:
                # phi-optimal correction: minimized sphericity term
                phase_correction = (self.k * r_squared**2) / (8 * focal_length**3 * self.phi)
                phase_pattern += phase_correction

        # Complex mask
        phase_mask = cp.array(np.exp(1j * phase_pattern), dtype=cp.complex128)
        return phase_mask

    def apply_reorganization(self, input_field: cp.ndarray,
                            phase_mask: cp.ndarray) -> cp.ndarray:
        """
        Applies phase reorganization in the C domain.
        """
        field_2d = input_field.reshape(self.resolution, self.resolution)
        field_after_slm = field_2d * phase_mask

        # Normalization preserving coherence
        field_after_slm /= cp.linalg.norm(field_after_slm)

        return field_after_slm

    def project_to_z(self, field_c: cp.ndarray, propagation_distance: float = 10e-3) -> Dict:
        """
        Projects field from C domain to observable Z structure.
        """
        # FFT 2D of the field
        # We use numpy for FFT if cupy is not available
        if cp == np:
            field_fft = fft2(field_c)
        else:
            # Assuming cupy.fft is available if cupy is
            import cupy.fft as cpfft
            field_fft = cpfft.fft2(field_c)

        # Spatial frequency coordinates
        fx = np.fft.fftfreq(self.resolution, self.pixel_pitch)
        FX, FY = np.meshgrid(fx, fx)

        # Longitudinal wave vector
        kz = np.sqrt(self.k**2 - (2*np.pi*FX)**2 - (2*np.pi*FY)**2 + 0j)

        # Propagation transfer function
        H = np.exp(1j * kz * propagation_distance)

        # Propagated field
        if cp == np:
            field_propagated = ifft2(field_fft * H)
        else:
            import cupy.fft as cpfft
            field_propagated = cpfft.ifft2(field_fft * cp.array(H))

        # Z PROJECTION: Collapse into intensity (|psi|^2)
        field_np = to_numpy(field_propagated)
        intensity_z = np.abs(field_np)**2
        phase_z = np.angle(field_np)

        # Projection metrics
        total_energy = np.sum(intensity_z)
        peak_intensity = np.max(intensity_z)
        focal_spot_size = self._calculate_spot_size(intensity_z)

        return {
            'intensity_z': intensity_z,
            'phase_z': phase_z,
            'total_energy': float(total_energy),
            'peak_intensity': float(peak_intensity),
            'focal_spot_size_um': float(focal_spot_size * 1e6),
            'coherence_projected': float(np.abs(np.mean(field_np)))
        }

    def _calculate_spot_size(self, intensity: np.ndarray, threshold: float = 0.5) -> float:
        """
        Calculates focal spot size (FWHM).
        """
        center = self.resolution // 2
        y_profile = intensity[:, center]

        half_max = np.max(y_profile) * threshold
        above_half = np.where(y_profile > half_max)[0]

        if len(above_half) > 1:
            fwhm_pixels = above_half[-1] - above_half[0]
            fwhm_meters = fwhm_pixels * self.pixel_pitch
            return fwhm_meters
        return 0.0

    def visualize_projection(self, results: Dict, output_path: str):
        """
        Visualizes the resulting Z projection.
        """
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))

        # Input Field (C)
        psi_2d = to_numpy(self.psi_world).reshape(self.resolution, self.resolution)
        axes[0,0].imshow(np.abs(psi_2d)**2, cmap='hot')
        axes[0,0].set_title(f'World {self.world_id}: Input Intensity (C)')

        # Phase Mask (SLM)
        # Using default spherical for visualization of mask if needed,
        # but here we just show what was used.
        axes[0,1].imshow(results['phase_z'], cmap='hsv')
        axes[0,1].set_title('Z Projection Phase')

        # Z Projection: Intensity
        im = axes[1,0].imshow(results['intensity_z'], cmap='hot')
        axes[1,0].set_title('Z Projection: Intensity (Manifested)')
        plt.colorbar(im, ax=axes[1,0])

        # Z Projection: Phase
        axes[1,1].imshow(results['phase_z'], cmap='hsv')
        axes[1,1].set_title('Z Projection: Residual Phase')

        plt.suptitle(f'Phase Focusing - World {self.world_id} (lambda2 = {self.lambda_world:.3f})')
        plt.tight_layout()
        plt.savefig(output_path, dpi=150)
        plt.close()
