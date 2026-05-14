from typing import Dict
from arkhe_os.layers.energy.microsparc import MicroSPARC

class MockResourceMgr:
    def open_file(self, path: str, perms: str):
        return None

class MockQip:
    def record_influence(self, origin: str, device_id: str, event_type: str):
        pass

class FdPerms:
    READ_WRITE = "rw"

class ArkpCLI:
    def __init__(self):
        self.resource_mgr = MockResourceMgr()
        self.qip = MockQip()

    def harvest_energy(self, device_id: str) -> Dict:
        """Ativa e monitora um MicroSPARC conectado via Fd."""
        fd = self.resource_mgr.open_file(f"/dev/microsparc/{device_id}", FdPerms.READ_WRITE)
        chip = MicroSPARC(chip_id=device_id)
        for _ in range(10):
            data = chip.step(0.1)
        self.qip.record_influence("microsparc-power", device_id, "energy_event")
        return chip.step(0.1)

    def energy_balance(self) -> float:
        """Retorna energia total gerada por todos os MicroSPARCs gerenciados."""
        return 100e-6  # simulação placeholder
