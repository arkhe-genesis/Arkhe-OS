import time
import random

class EnergyOracle:
    """Consulta preço de energia em tempo real e ajusta o gas de parsing."""

    def __init__(self, oracle_address: str = "chainlink_energy_feed"):
        self.oracle_address = oracle_address
        self.base_price_mwh = 50.0  # referência
        self._cached_price = self.base_price_mwh
        self._last_update = 0

    async def get_current_price(self) -> float:
        # Em produção: chamar contrato Chainlink ou API de grid
        # Mock: valor aleatório entre 30 e 200
        if time.time() - self._last_update > 60:
            self._cached_price = random.uniform(30, 200)
            self._last_update = time.time()
        return self._cached_price

    async def adjust_gas(self, base_gas: float) -> float:
        price = await self.get_current_price()
        return base_gas * (price / self.base_price_mwh)
