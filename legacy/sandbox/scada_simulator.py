#!/usr/bin/env python3
import asyncio
import random
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum, auto
import logging

logger = logging.getLogger(__name__)

class ModbusRegisterType(Enum):
    COIL = "coil"
    DISCRETE_INPUT = "discrete_input"
    INPUT_REGISTER = "input_register"
    HOLDING_REGISTER = "holding_register"

@dataclass
class ModbusDevice:
    device_id: str
    device_name: str
    unit_id: int
    registers: Dict[int, Dict]
    location: str
    last_poll: float = field(default_factory=time.time)

class SCADASimulator:
    def __init__(self):
        self.devices: Dict[str, ModbusDevice] = {}
        self.alarm_log: List[Dict] = []
        self._running = False
        self._initialize_test_devices()

    def _initialize_test_devices(self):
        self.devices["plc_temp_01"] = ModbusDevice(
            device_id="plc_temp_01",
            device_name="Temperature Control PLC",
            unit_id=1,
            registers={
                0: {"type": ModbusRegisterType.INPUT_REGISTER, "value": 22.5, "description": "Current Temperature (°C)"},
                1: {"type": ModbusRegisterType.HOLDING_REGISTER, "value": 25.0, "description": "Setpoint Temperature (°C)"},
                2: {"type": ModbusRegisterType.COIL, "value": False, "description": "Heater Relay"},
                3: {"type": ModbusRegisterType.DISCRETE_INPUT, "value": False, "description": "Overtemp Alarm"},
            },
            location="Lab Room A",
        )
        self.devices["sensor_pressure_01"] = ModbusDevice(
            device_id="sensor_pressure_01",
            device_name="Pressure Sensor",
            unit_id=2,
            registers={
                0: {"type": ModbusRegisterType.INPUT_REGISTER, "value": 101.3, "description": "Pressure (kPa)"},
                1: {"type": ModbusRegisterType.DISCRETE_INPUT, "value": False, "description": "Pressure High Alarm"},
            },
            location="Lab Room A",
        )
        logger.info(f"🏭 SCADA simulador inicializado com {len(self.devices)} dispositivos")

    async def start_simulation(self, update_interval: float = 1.0):
        self._running = True
        while self._running:
            for device in self.devices.values():
                await self._update_device_values(device)
                device.last_poll = time.time()
            await self._check_alarms()
            await asyncio.sleep(update_interval)

    async def _update_device_values(self, device: ModbusDevice):
        for addr, reg in device.registers.items():
            if reg["type"] == ModbusRegisterType.INPUT_REGISTER:
                if "Temperature" in reg["description"]:
                    reg["value"] = round(reg["value"] + random.uniform(-0.1, 0.1), 1)
                elif "Pressure" in reg["description"]:
                    reg["value"] = round(reg["value"] + random.uniform(-0.05, 0.05), 2)

    async def _check_alarms(self):
        for device in self.devices.values():
            temp_reg = device.registers.get(0)
            setpoint_reg = device.registers.get(1)
            alarm_coil = device.registers.get(3)
            if temp_reg and setpoint_reg and alarm_coil:
                if temp_reg["value"] > setpoint_reg["value"] + 5:
                    if not alarm_coil["value"]:
                        alarm_coil["value"] = True
                        await self._trigger_alarm(device, "OVERTEMP", temp_reg["value"])
                elif alarm_coil["value"] and temp_reg["value"] <= setpoint_reg["value"] + 2:
                    alarm_coil["value"] = False

    async def _trigger_alarm(self, device: ModbusDevice, alarm_type: str, value: float):
        alarm_entry = {
            "timestamp": time.time(), "device_id": device.device_id, "device_name": device.device_name,
            "alarm_type": alarm_type, "value": value, "location": device.location,
            "severity": "HIGH" if alarm_type == "OVERTEMP" else "MEDIUM", "acknowledged": False,
        }
        self.alarm_log.append(alarm_entry)
        logger.warning(f"🚨 Alarme: {alarm_type} em {device.device_name} = {value}")

    async def read_register(self, device_id: str, address: int, register_type: ModbusRegisterType) -> Optional[Dict]:
        device = self.devices.get(device_id)
        if not device: return None
        reg = device.registers.get(address)
        if not reg or reg["type"] != register_type: return None
        return {"device_id": device_id, "address": address, "value": reg["value"], "description": reg["description"], "timestamp": time.time()}

    async def write_register(self, device_id: str, address: int, value: int, authorization: str) -> bool:
        if authorization != "mock_scada_auth_token": return False
        device = self.devices.get(device_id)
        if not device: return False
        reg = device.registers.get(address)
        if not reg or reg["type"] != ModbusRegisterType.HOLDING_REGISTER: return False
        if "Temperature" in reg["description"]:
            if not (15.0 <= value <= 35.0): return False
        reg["value"] = float(value)
        logger.info(f"✏️ Registrador atualizado: {device_id}[{address}] = {value}")
        return True

    def get_alarm_log(self, since_timestamp: Optional[float] = None) -> List[Dict]:
        if since_timestamp: return [a for a in self.alarm_log if a["timestamp"] >= since_timestamp]
        return self.alarm_log.copy()

    async def shutdown(self):
        self._running = False
        logger.info("🏭 SCADA simulador encerrado")
