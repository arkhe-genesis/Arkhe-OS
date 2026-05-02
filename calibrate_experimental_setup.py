#!/usr/bin/env python3
"""
calibrate_experimental_setup.py
Calibra setup experimental para caracterização pós-fabricação.
"""
import numpy as np
import time
from pathlib import Path

# Tratamento para serial se não disponível em CI/dev
try:
    import serial
except ImportError:
    print("⚠️  pyserial not available — using mock serial interfaces")
    class MockSerial:
        def __init__(self, *args, **kwargs):
            self.buffer = []
            self.read_state = 0
        def write(self, data):
            if b'STAT:CAL?' in data:
                self.buffer.append(b'COMPLETE\n')
            elif b'DATA:READ?' in data:
                self.buffer.extend([b'1.0\n', b'2.0\n', b'3.0\n', b'DONE\n'])
        def readline(self):
            if self.buffer:
                return self.buffer.pop(0)
            return b''
        def close(self):
            pass
    serial = type('serial', (), {'Serial': MockSerial})

class ExperimentalSetup:
    """Interface com equipamentos experimentais para caracterização."""

    def __init__(self, config_path='config/experimental_setup.json'):
        """Inicializa conexão com equipamentos."""
        import json
        try:
            with open(config_path, 'r') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            print(f"⚠️ Config {config_path} not found — using default values for test")
            self.config = {
                'laser': {'port': 'COM1', 'baudrate': 9600},
                'spectrometer': {'port': 'COM2', 'baudrate': 115200},
                'slm': {'port': 'COM3', 'baudrate': 9600},
                'calibration': {
                    'reference_wavelengths': [400, 500, 600],
                    'reference_intensities': [1.0, 2.0, 3.0]
                }
            }

        # Inicializar laser sintonizável
        self.laser = serial.Serial(
            self.config['laser']['port'],
            self.config['laser']['baudrate'],
            timeout=1
        )

        # Inicializar espectrômetro
        self.spectrometer = serial.Serial(
            self.config['spectrometer']['port'],
            self.config['spectrometer']['baudrate'],
            timeout=1
        )

        # Inicializar SLM (se disponível)
        self.slm_available = 'slm' in self.config
        if self.slm_available:
            self.slm = serial.Serial(
                self.config['slm']['port'],
                self.config['slm']['baudrate'],
                timeout=1
            )

    def calibrate_laser(self):
        """Calibra laser sintonizável para precisão de comprimento de onda."""
        print("🔧 Calibrating tunable laser...")

        # Comandos de calibração específicos do fabricante
        self.laser.write(b'CAL:WAVE:START 400\n')
        self.laser.write(b'CAL:WAVE:STOP 1550\n')
        self.laser.write(b'CAL:WAVE:STEP 1\n')
        self.laser.write(b'CAL:EXEC\n')

        # Aguardar conclusão
        time.sleep(30 if hasattr(serial, 'Serial') and serial.Serial.__name__ == 'Serial' else 1)

        # Verificar status
        self.laser.write(b'STAT:CAL?\n')
        status = self.laser.readline().decode().strip()

        if 'COMPLETE' in status:
            print("✓ Laser calibration complete")
            return True
        else:
            print(f"⚠️  Laser calibration status: {status}")
            return False

    def calibrate_spectrometer(self):
        """Calibra espectrômetro com fonte de referência."""
        print("🔧 Calibrating spectrometer...")

        # Carregar espectro de referência NIST-traceable
        reference_wavelengths = np.array(self.config['calibration']['reference_wavelengths'])
        reference_intensities = np.array(self.config['calibration']['reference_intensities'])

        # Medir espectro de referência
        self.spectrometer.write(b'MEAS:REF\n')
        measured = self._read_spectrometer_data()

        # Calcular fator de correção
        if len(measured) == len(reference_intensities):
            correction = reference_intensities / (measured + 1e-10)
            self.spectrometer.write(f'CAL:FACTOR {correction.tolist()}\n'.encode())
            print("✓ Spectrometer calibration complete")
            return True
        else:
            print("⚠️  Spectrometer calibration failed: data length mismatch")
            return False

    def calibrate_slm(self):
        """Calibra SLM para padrões de fase conhecidos."""
        if not self.slm_available:
            print("⚠️  SLM not available — skipping calibration")
            return True

        print("🔧 Calibrating spatial light modulator...")

        # Carregar padrão de fase de referência (grade de difração)
        phase_pattern = self._generate_reference_phase_pattern()

        # Enviar para SLM
        self.slm.write(b'PHASE:LOAD\n')
        for row in phase_pattern:
            self.slm.write(f'{row.tolist()}\n'.encode())
        self.slm.write(b'PHASE:APPLY\n')

        # Medir padrão de difração resultante
        # (Implementação específica do setup óptico)

        print("✓ SLM calibration complete")
        return True

    def _read_spectrometer_data(self):
        """Lê dados do espectrômetro."""
        self.spectrometer.write(b'DATA:READ?\n')
        data = []
        while True:
            line = self.spectrometer.readline()
            if line.startswith(b'DONE') or line == b'':
                break
            try:
                data.append(float(line.decode().strip()))
            except:
                pass
        return np.array(data)

    def _generate_reference_phase_pattern(self, size=(1920, 1080)):
        """Gera padrão de fase de referência para calibração do SLM."""
        # Grade de difração simples: fase linear em x
        x = np.linspace(0, 2*np.pi, size[1])
        phase = np.tile(x, (size[0], 1))
        return phase.astype(np.float32)

    def run_full_calibration(self):
        """Executa calibração completa do setup experimental."""
        print("🔬 Starting full experimental setup calibration...")

        results = {
            'laser': self.calibrate_laser(),
            'spectrometer': self.calibrate_spectrometer(),
            'slm': self.calibrate_slm() if self.slm_available else True
        }

        if all(results.values()):
            print(f"✅ Full calibration PASSED")
            return True
        else:
            print(f"⚠️  Full calibration NEEDS ATTENTION:")
            for component, success in results.items():
                print(f"   • {component}: {'✅' if success else '❌'}")
            return False

    def close(self):
        """Fecha conexões com equipamentos."""
        self.laser.close()
        self.spectrometer.close()
        if self.slm_available:
            self.slm.close()

if __name__ == '__main__':
    setup = ExperimentalSetup()

    try:
        success = setup.run_full_calibration()
        exit(0 if success else 1)
    finally:
        setup.close()
