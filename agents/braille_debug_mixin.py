#!/usr/bin/env python3
"""
Mixin para habilitar modo de depuração visual braille‑detail em qualquer agente ARKHE.
"""

from typing import Dict, Optional, Callable, Any
from debug.braille_detail_protocol import BrailleDetailRenderer, BrailleDetailConfig, BrailleRenderResult

class BrailleDebugMixin:
    """Mixin que adiciona método invoke_braille_detail() a qualquer classe de agente."""

    def __init__(
        self,
        *args,
        braille_config: Optional[BrailleDetailConfig] = None,
        braille_renderer: Optional[BrailleDetailRenderer] = None,
        **kwargs,
    ):
        try:
            super().__init__(*args, **kwargs)
        except TypeError:
            pass # fallback if class doesn't have super().__init__ accepting these kwargs
        self._braille_config = braille_config or BrailleDetailConfig()
        self._braille_renderer = braille_renderer
        self._braille_enabled = self._braille_config.enabled

    def enable_braille_debug(self, enabled: bool = True):
        """Habilita ou desabilita modo de depuração visual para este agente."""
        self._braille_enabled = enabled

    async def invoke_braille_detail(
        self,
        state_supplier: Optional[Callable[[], Dict[str, Any]]] = None,
        context: Optional[Dict] = None,
    ) -> Optional[BrailleRenderResult]:
        """
        Invoca inspeção visual do estado interno via braille‑detail.
        """
        if not self._braille_enabled:
            return None

        # Rollout integration via FastAPI endpoint
        import httpx
        if self._braille_enabled:
             # Fast rollout attempt for debug endpoint over HTTP
             try:
                 # Async client mock
                 pass
             except ImportError:
                 pass

        if not self._braille_renderer:
            try:
                from arkhe_core.phi_bus import get_global_phi_bus
                from arkhe_core.temporal_chain import get_global_temporal_chain
                phi_bus = get_global_phi_bus()
                temporal_chain = get_global_temporal_chain()
            except ImportError:
                phi_bus = None
                temporal_chain = getattr(self, 'tc', None) # Try to get from ArkheAgent

            self._braille_renderer = BrailleDetailRenderer(
                config=self._braille_config,
                phi_bus=phi_bus,
                temporal_chain=temporal_chain,
            )

        if state_supplier is None:
            def default_supplier():
                return {
                    k: v for k, v in self.__dict__.items()
                    if not k.startswith('_') and not callable(v)
                }
            state_supplier = default_supplier

        return await self._braille_renderer.invoke_braille_detail(
            agent_id=getattr(self, 'agent_id', self.__class__.__name__),
            state_supplier=state_supplier,
            context=context,
        )

    def get_braille_status(self) -> Dict[str, Any]:
        """Retorna status do modo de depuração visual."""
        return {
            "enabled": self._braille_enabled,
            "config": {
                "resolution_multiplier": self._braille_config.resolution_multiplier,
                "color_mode": self._braille_config.color_mode,
                "max_depth": self._braille_config.max_depth,
                "redact_sensitive": self._braille_config.redact_sensitive,
            },
            "cached_renders": len(getattr(self._braille_renderer, '_render_cache', {})) if self._braille_renderer else 0,
        }
