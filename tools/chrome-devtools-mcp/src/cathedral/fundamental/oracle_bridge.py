# src/cathedral/fundamental/oracle_bridge.py
"""
Oracle Bridge: Conecta simuladores físicos aos Oráculos de Coerência no Gno.land.
"""

import json

class OracleBridge:
    def __init__(self, mcp_gno_tool):
        self.gno = mcp_gno_tool
        self.pkg_path = "gno.land/r/cathedral/coherence_oracle"

    async def push_metric(self, omega: float, status: str):
        """Usa a ferramenta gno_call do MCP para persistir dados on-chain."""
        args = [str(omega), status]
        # Chamada via MCP (simulado na estrutura da classe)
        return await self.gno.call_contract(self.pkg_path, "RecordCoherence", args)

    async def record_baseline(self, participant_hash: str, baseline: float):
        """Ancorar baseline individual no Gno.land."""
        args = [participant_hash, str(baseline)]
        return await self.gno.call_contract(self.pkg_path, "RecordIndividualBaseline", args)
