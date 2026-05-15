import asyncio
from typing import Dict, Any, List
from arkhe.agents.base import ArkheAgent
from arkhe.consensus.phi_bus import PhiBusClient

class ContextAgent(ArkheAgent):
    """Estrutura o contexto multimodal em uma timeline causal."""
    async def process(self, history: dict) -> dict:
        # Utiliza o Guardian para validar a integridade do texto
        safe_history = await self.guardian.exorcise_context(history)
        # Estrutura no formato H_{1:tau}
        return self._structure_timeline(safe_history)

    def _structure_timeline(self, history: dict) -> dict:
        return {"timeline": history.get("data", [])}

class MacroAgent(ArkheAgent):
    """Gera projeção de tendência de longo prazo."""
    async def reason(self, structured_history: dict) -> dict:
        # Utiliza LLM local (Ollama) para gerar a trajetória macro
        return await self.llm.predict_macro(structured_history)

class MicroAgent(ArkheAgent):
    """Gera projeção granular passo a passo."""
    async def reason(self, structured_history: dict) -> dict:
        return await self.llm.predict_micro(structured_history)

class SynthesizerAgent(ArkheAgent):
    """Mescla perspectivas macro e micro usando pesos dinâmicos do Phi‑Bus."""
    async def synthesize(self, macro: dict, micro: dict, guidelines: list) -> dict:
        # Obtém o Φ_C atual dos agentes macro e micro
        phi_macro = await self.phi_bus.get_agent_coherence(macro['agent_id'])
        phi_micro = await self.phi_bus.get_agent_coherence(micro['agent_id'])

        # Ponderação dinâmica baseada na coerência
        total_phi = phi_macro + phi_micro
        weight_macro = phi_macro / total_phi if total_phi > 0 else 0.5
        weight_micro = 1 - weight_macro

        # Combina as previsões
        final_forecast = []
        macro_vals = macro.get('values', [])
        micro_vals = micro.get('values', [])

        for i in range(min(len(macro_vals), len(micro_vals))):
            val = (macro_vals[i] * weight_macro +
                   micro_vals[i] * weight_micro)
            final_forecast.append(val)

        # Ancoragem quântica do resultado
        seal = await self.temporal.anchor_event(
            "forecast_synthesized",
            {"macro_weight": weight_macro, "horizon": len(final_forecast)}
        )
        return {"values": final_forecast, "temporal_seal": seal}
