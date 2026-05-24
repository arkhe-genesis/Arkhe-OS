#!/usr/bin/env python3
"""
ARKHE 390-OPT — acquisition_daemon.py
Daemon user-space para leitura via relayfs, parse de eventos e dispatch para análise.
"""

import os
import mmap
import struct
import signal
import sys
import time
import logging
import yaml
from pathlib import Path

# Adiciona o diretório raiz do opt ao sys.path para importações
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analysis.pulse_classifier import PulseClassifier
from analysis.calibration import EnergyCalibrator

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)-8s | %(message)s')
logger = logging.getLogger(__name__)

RELAY_PATH = "/sys/kernel/debug/alx/event_buffer"
EVENT_FMT = "I H H B 1x"  # timestamp:4, amplitude:2, integral:2, flags:1, padding:1
EVENT_SIZE = struct.calcsize(EVENT_FMT)

class AcquisitionDaemon:
    def __init__(self, config_path="config.yaml"):
        # Resolve to current dir if relative
        config_path = os.path.join(os.path.dirname(__file__), config_path)
        with open(config_path) as f:
            self.config = yaml.safe_load(f)
        self.running = False
        self.classifier = PulseClassifier(
            threshold_sigma=self.config["detection"]["threshold_sigma"],
            coincidence_window_ns=self.config["detection"]["coincidence_window_ns"]
        )
        self.calibrator = EnergyCalibrator.load(self.config["calibration"]["table_path"])
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        logger.info("Received shutdown signal. Exiting gracefully...")
        self.running = False

    def _parse_event(self, data):
        ts, amp, integral, flags = struct.unpack(EVENT_FMT, data)
        return {
            "timestamp_ns": ts,
            "amplitude_raw": amp,
            "integral_raw": integral,
            "flags": flags,
            "energy_kev": self.calibrator.calibrate(amp) if self.calibrator else amp * 0.1
        }

    def run(self):
        self.running = True
        logger.info(f"Starting Arkhe 390-OPT Acquisition Daemon")

        try:
            with open(RELAY_PATH, "rb") as f:
                mm = mmap.mmap(f.fileno(), 0, prot=mmap.PROT_READ)
                offset = 0

                while self.running:
                    try:
                        available = len(mm) - offset
                        if available >= EVENT_SIZE:
                            event_data = mm[offset:offset+EVENT_SIZE]
                            offset += EVENT_SIZE

                            event = self._parse_event(event_data)
                            classified = self.classifier.process(event)

                            if classified["detected"]:
                                logger.info(
                                    f"Event | t={event['timestamp_ns']}ns | E={event['energy_kev']:.1f}keV | "
                                    f"Type={classified['particle_type']} | Amp={event['amplitude_raw']}"
                                )
                                # Aqui: enviar para dashboard, banco, ou trigger externo
                        else:
                            time.sleep(0.001)  # Yield CPU
                    except Exception as e:
                        logger.error(f"Read error: {e}")
                        break
        except FileNotFoundError:
            logger.error(f"RelayFS path {RELAY_PATH} not found. Is the kernel module loaded?")
            self.running = False

        logger.info("Acquisition Daemon stopped.")

if __name__ == "__main__":
    daemon = AcquisitionDaemon()
    daemon.run()
