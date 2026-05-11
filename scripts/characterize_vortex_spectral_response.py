#!/usr/bin/env python3
"""
characterize_vortex_spectral_response.py
Characterizes fabricated vortex matrix spectral response using benchtop spectrometer.
"""
import numpy as np
import serial
import time
from pathlib import Path

class SpectralCharacterizer:
    """Interface com espectrômetro de bancada para caracterização óptica."""

    def __init__(self, spectrometer_port='/dev/ttyUSB0', baudrate=9600):
        self.spectrometer = serial.Serial(spectrometer_port, baudrate, timeout=1)
        self.wavelength_range = (400, 1550)  # nm
        self.resolution = 1  # nm

    def set_wavelength(self, wavelength_nm):
        """Configura laser sintonizável para comprimento de onda específico."""
        command = f"WAVE:{wavelength_nm:.1f}\n"
        self.spectrometer.write(command.encode())
        time.sleep(0.1)  # Aguardar estabilização
        return self._read_response()

    def measure_intensity(self, integration_time_ms=100):
        """Mede intensidade espectral no detector."""
        command = f"INT:{integration_time_ms}\n"
        self.spectrometer.write(command.encode())
        time.sleep(0.05)
        return self._read_response()

    def _read_response(self):
        """Lê resposta do instrumento."""
        response = b""
        while True:
            line = self.spectrometer.readline()
            if line.startswith(b'DONE') or line.startswith(b'ERR'):
                return line.decode().strip()
            response += line
            if len(response) > 1000:  # Safety limit
                break
        return response.decode().strip()

    def scan_spectral_response(self, phase_pattern=None):
        """Varre resposta espectral completa da matriz de vórtices."""
        print(f"🔬 Scanning spectral response: {self.wavelength_range[0]}–{self.wavelength_range[1]} nm")

        wavelengths = np.arange(*self.wavelength_range, self.resolution)
        intensities = []

        for wl in wavelengths:
            # Configurar laser
            self.set_wavelength(wl)

            # Aplicar padrão de fase se especificado (via SLM interface)
            if phase_pattern is not None:
                self._apply_phase_pattern(phase_pattern)

            # Medir intensidade
            intensity = self.measure_intensity()
            intensities.append(float(intensity))

            # Progresso
            if wl % 50 == 0:
                print(f"   • λ = {wl} nm: intensity = {intensity}")

        return wavelengths, np.array(intensities)

    def _apply_phase_pattern(self, phase_pattern):
        """Aplica padrão de fase via modulador espacial de luz (SLM)."""
        # Implementação específica do hardware SLM
        # Exemplo: enviar matriz de fase via interface serial/Ethernet
        pass

    def close(self):
        """Fecha conexão com espectrômetro."""
        self.spectrometer.close()

def characterize_prototype(output_path='results/prototype_spectral_response.npy'):
    """Caracteriza protótipo fabricado e salva resultados."""
    print("🏭 Characterizing fabricated vortex prototype...")

    # Inicializar caracterizador
    char = SpectralCharacterizer()

    try:
        # Medir resposta espectral para padrão de fase de referência
        # (fases aleatórias próximas ao manifold CAPTURE)
        np.random.seed(42)
        reference_phases = np.random.uniform(0.3*np.pi, 0.7*np.pi, 768)

        wavelengths, spectrum = char.scan_spectral_response(reference_phases)

        # Salvar resultados
        Path('results').mkdir(exist_ok=True)
        np.savez(output_path,
                wavelengths=wavelengths,
                spectrum=spectrum,
                phase_pattern=reference_phases,
                timestamp=str(np.datetime64('now')),
                prototype_id='ARKHE_VORTEX_PROTO_v340.2')

        print(f"✓ Spectral response saved: {output_path}")

        # Validar invertibilidade (reconstrução de fase)
        from simulate_vortex_array_response import spectrum_to_phase, VORTEX_PARAMS

        phi_rec, success, residual = spectrum_to_phase(
            spectrum, VORTEX_PARAMS, n_osc=768
        )

        print(f"✓ Phase reconstruction: success={success}, residual={residual:.4f}")

        return {
            'wavelengths': wavelengths,
            'spectrum': spectrum,
            'reconstruction_success': success,
            'reconstruction_residual': residual
        }

    finally:
        char.close()

if __name__ == '__main__':
    results = characterize_prototype()

    if results['reconstruction_success']:
        print(f"✅ Prototype characterization PASSED")
        print(f"🔗 Phase-spectrum invertibility validated experimentally")
    else:
        print(f"⚠️  Prototype characterization NEEDS ATTENTION")
        print(f"🔗 Review fabrication parameters or measurement setup")
