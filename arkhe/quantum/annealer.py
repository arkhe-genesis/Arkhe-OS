import asyncio

class QuantumAnnealer:
    def __init__(self, qbus_client):
        self.client = qbus_client

    async def solve(self, qubo: dict) -> dict:
        return await self.client.execute_annealing(qubo)
