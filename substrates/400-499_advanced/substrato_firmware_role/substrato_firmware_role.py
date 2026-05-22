import json
import tempfile
import os

class SubstratoFirmwareRole:
    def canonize(self):
        report = {
            "Title": "Arkhe Firmware Engineer Role",
            "Context": "You own critical pieces of the firmware stack that powers Arkhe consumer products - from board bring-up and peripheral drivers to the runtime environment that hosts on-device intelligence. This isn't firmware in a vacuum. You'll work directly with the hardware team on new silicon and sensor integrations, with the agent team on model execution and memory constraints, and with products on experiences that ship to real users. The problems are real, the constraints are tight, and the work matters immediately.",
            "Responsibilities": [
                "Develop and maintain embedded firmware in C/C++ targeting ARM-based SoCs and microcontrollers",
                "Own BSP development, peripheral driver integration (SPI, I2C, UART, I2S), and RTOS task scheduling",
                "Optimize power consumption and thermal performance for always-on, battery-powered operation",
                "Build and maintain OTA update infrastructure for reliable field updates",
                "Collaborate with the on-device AI team to support model inference within memory and latency budgets",
                "Develop factory test and calibration firmware for manufacturing",
                "Debug complex hardware-software interactions using logic analyzers, oscilloscopes, and JTAG"
            ],
            "Requirements": [
                "3+ years of professional firmware or embedded systems development",
                "Strong proficiency in C and/or C++ in resource-constrained environments",
                "Experience with ARM Cortex-M or Cortex-A processors and associated toolchains",
                "Hands-on experience with RTOS (FreeRTOS, Zephyr, or similar)",
                "Familiarity with wireless protocols (BLE, Wi-Fi, or Thread)"
            ]
        }

        fd, path = tempfile.mkstemp(suffix=".json", prefix="substrato_firmware_role_")
        with os.fdopen(fd, 'w') as f:
            json.dump(report, f, indent=4)

        print("Canonized Arkhe Firmware Engineer Role. Report saved to: " + path)
        return path

if __name__ == "__main__":
    substrate = SubstratoFirmwareRole()
    substrate.canonize()
