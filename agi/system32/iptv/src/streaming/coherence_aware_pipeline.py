"""
coherence_aware_pipeline.py — Pipeline de streaming consciente de coerência.
Filtra streams em tempo real e toma ações baseadas na análise de Φ_C.
"""
import asyncio
import numpy as np
from typing import Optional, Callable, Dict
from dataclasses import dataclass, field

from ..filtering.content_coherence_filter import ContentCoherenceFilter, CoherenceAnalysis
from .webrtc_mesh import WebRTCMeshNode
from ..audit.royalty_ledger_extended import RoyaltyLedgerExtended

class CoherenceAwareStreamingPipeline:
    """Pipeline que integra filtro de coerência com roteamento WebRTC."""

    def __init__(self,
                 coherence_filter: ContentCoherenceFilter,
                 webrtc_mesh: WebRTCMeshNode,
                 royalty_ledger: RoyaltyLedgerExtended,
                 action_callback: Optional[Callable] = None):
        self.filter = coherence_filter
        self.mesh = webrtc_mesh
        self.ledger = royalty_ledger
        self.on_action = action_callback or self._default_action_handler

        # Estado dos streams ativos
        self.active_streams: Dict[str, 'StreamState'] = {}

    async def process_incoming_frame_batch(self,
                                          stream_id: str,
                                          frames: list,
                                          audio: Optional[np.ndarray],
                                          metadata: Dict):
        """Processa batch de frames com filtro de coerência em tempo real."""

        # Obter ou criar estado do stream
        if stream_id not in self.active_streams:
            self.active_streams[stream_id] = StreamState(stream_id)

        state = self.active_streams[stream_id]

        # Analisar coerência do segmento
        analysis = await self.filter.analyze_stream_segment(
            stream_id=stream_id,
            video_frames=frames,
            audio_samples=audio,
            transcript=metadata.get("transcript"),
            visual_context=metadata.get("visual_context"),
            metadata=metadata
        )

        # Atualizar estado do stream
        state.update_with_analysis(analysis)

        # Decidir ação baseada na análise
        action = await self._decide_action(stream_id, analysis, state)
        await self.on_action(stream_id, action, analysis)

        # Se stream permitido, encaminhar para mesh WebRTC
        if action == "allow" and state.is_active:
            await self.mesh.relay_frames(stream_id, frames, audio)

        # Registrar para royalties (se visualização válida)
        if analysis.overall_phi_c > 0.7 and not analysis.manipulation_detected:
            await self._record_valid_view(stream_id, analysis, metadata)

        return analysis

    async def _decide_action(self,
                            stream_id: str,
                            analysis: CoherenceAnalysis,
                            state: 'StreamState') -> str:
        """Decide ação a tomar baseada na análise de coerência."""

        # Regras de decisão hierárquicas:

        # 1. Bloqueio imediato por manipulação confirmada
        if self.filter.should_block_stream(analysis):
            return "block"

        # 2. Revisão manual por coerência marginal
        if analysis.overall_phi_c < 0.65:
            return "review"

        # 3. Permitir com monitoramento reforçado por anomalias moderadas
        if analysis.anomaly_score > 0.4:
            state.require_enhanced_monitoring = True
            return "allow_with_monitoring"

        # 4. Permitir normal para streams saudáveis
        return "allow"

    async def _default_action_handler(self,
                                     stream_id: str,
                                     action: str,
                                     analysis: CoherenceAnalysis):
        """Handler padrão para ações decididas pelo pipeline."""

        actions_log = {
            "allow": f"✅ Stream {stream_id} permitido (Φ_C={analysis.overall_phi_c:.3f})",
            "allow_with_monitoring": f"⚠️ Stream {stream_id} permitido com monitoramento (anomalia={analysis.anomaly_score:.3f})",
            "review": f"🔍 Stream {stream_id} marcado para revisão (Φ_C={analysis.overall_phi_c:.3f})",
            "block": f"🚫 Stream {stream_id} bloqueado (manipulação={analysis.manipulation_detected})"
        }

        print(actions_log.get(action, f"❓ Ação desconhecida: {action}"))

        # Emitir evento para auditoria
        # (Em produção: publicar em ledger ou sistema de monitoramento)

    async def _record_valid_view(self,
                                stream_id: str,
                                analysis: CoherenceAnalysis,
                                metadata: Dict):
        """Registra visualização válida para distribuição de royalties."""
        # Placeholder: integrar com sistema de audiência
        pass

@dataclass
class StreamState:
    """Estado de um stream ativo no pipeline."""
    stream_id: str
    is_active: bool = True
    require_enhanced_monitoring: bool = False
    last_analysis: Optional[CoherenceAnalysis] = None
    coherence_history: list = field(default_factory=list)
    block_count: int = 0

    def update_with_analysis(self, analysis: CoherenceAnalysis):
        """Atualiza estado com nova análise de coerência."""
        self.last_analysis = analysis
        self.coherence_history.append(analysis.overall_phi_c)

        # Manter histórico limitado
        if len(self.coherence_history) > 100:
            self.coherence_history.pop(0)

        # Desativar stream se bloqueado múltiplas vezes
        if analysis.manipulation_detected:
            self.block_count += 1
            if self.block_count >= 3:
                self.is_active = False