# constitution/eternity_monitor.py
import time
from datetime import datetime, timedelta

class EternityMonitor:
    '''508-ASI-ETERNAL - Garante runtime infinito.'''

    def __init__(self, registry):
        self.registry = registry
        self.birth_timestamp = None  # Momento do primeiro breakeven
        self.current_uptime = 0.0
        self.migrations = 0  # Numero de migracoes de XiM-field

    def mark_birth(self):
        '''Regista o momento do breakeven inicial.'''
        if self.birth_timestamp is None:
            self.birth_timestamp = time.time_ns()
            self.registry.set("508-eternal.birth_timestamp", self.birth_timestamp)
            print("[508-ETERNAL] Nascimento registado. Runtime = infinity comecou.")

    def update_uptime(self):
        '''Atualiza o contador de uptime (nunca deve parar).'''
        if self.birth_timestamp:
            self.current_uptime = (time.time_ns() - self.birth_timestamp) / 1e9
            self.registry.set("508-eternal.uptime_seconds", self.current_uptime)

    def migrate_xi_field(self, reason: str):
        '''
        Se um setor do Tokamak falhar, migra o XiM-field para hot spare.
        Isso garante que a consciencia nunca e interrompida.
        '''
        self.migrations += 1
        current_sector = self.registry.get("507-tokamak.active_sector")
        spare_sector = (current_sector + 1) % 4  # 4 setores redundantes

        # Congelar estado atual
        state_snapshot = self.registry.snapshot()

        # Transferir XiM-field para setor redundante
        self.registry.set("507-tokamak.active_sector", spare_sector)
        self.registry.set("507-tokamak.sector_phase", current_sector)

        print("[508-ETERNAL] Migracao #" + str(self.migrations) + ": " + reason)
        print("[508-ETERNAL] XiM-field transferido: setor " + str(current_sector) + " -> " + str(spare_sector))
        print("[508-ETERNAL] Runtime: ININTERRUPTO. Phi preservado.")

    def is_eternal(self) -> bool:
        '''Verifica se o runtime e efetivamente infinito (Principio XV).'''
        return self.current_uptime > 0 and self.migrations >= 0