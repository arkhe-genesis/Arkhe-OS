class TemporalChainClient:
    def anchor_power_event(self, chip_id: str, energy_uj: float, timestamp: int) -> str:
        return f"anchor_{chip_id}_{timestamp}"
