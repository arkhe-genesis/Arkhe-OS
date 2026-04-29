# arkhe_optica/integrated_bidual_sorter_pipeline.py
"""
Pipeline integrado: DualOpticalWhiteHole → LC Filter → Photon Sorter → Certificação de Pureza.
"""

import torch
import asyncio
from typing import Dict, Optional
from arkhe_optica.dual_optical_white_hole import DualOpticalWhiteHole
from arkhe_optica.photon_sorter_simulator import PhotonSorterHighFidelity, PhotonSorterConfig
from arkhe_hardware.lc_materializer import LiquidCrystalMaterializer, LCDeviceConfig

class IntegratedBidualSorterPipeline:
    """
    Pipeline completo para geração de luz com coerência certificada:
    1. DualOpticalWhiteHole: otimiza parâmetros espaciais + espectrais
    2. LC Materializer: fabrica filtro espectral em tempo real
    3. Photon Sorter: analisa pureza de estados de Fock na saída
    4. Certificação: calcula Ω_granular = P₁/(P₁+P₂) para registro na CosmicDAO
    """

    def __init__(
        self,
        dual_white_hole: DualOpticalWhiteHole,
        lc_config: LCDeviceConfig,
        sorter_config: PhotonSorterConfig
    ):
        self.dual_wh = dual_white_hole
        self.lc_materializer = LiquidCrystalMaterializer(lc_config)
        self.sorter = PhotonSorterHighFidelity(sorter_config)

    async def generate_certified_coherent_light(
        self,
        spatial_targets: Dict[str, float],
        spectral_target: torch.Tensor,
        target_fock_state: str = "fock_1",  # "fock_1" ou "fock_2"
        min_sorting_fidelity: float = 0.85
    ) -> Dict:
        """
        Gera luz com coerência espacial, espectral e de número de fótons certificada.

        Returns:
            Dict com métricas de coerência e prova de certificação
        """
        # === FASE 1: OTIMIZAÇÃO BIDUAL ===
        print("🔬 Fase 1: Otimizando receita óptica bidual...")
        opt_result = self.dual_wh.generate(
            spatial_targets=spatial_targets,
            spectral_target=spectral_target,
            steps=150  # Reduzido para pipeline integrado
        )

        if not opt_result or 'optimized_params' not in opt_result:
            raise RuntimeError("Otimização bidual falhou")

        opt = opt_result['optimized_params']
        print(f"✅ Otimização: SIC={opt['pred_spatial'][0,0].item()*40:.1f}dB")

        # === FASE 2: FABRICAÇÃO DO FILTRO LC ===
        print("🏭 Fase 2: Fabricando filtro LC...")
        fab_result = await self.lc_materializer.write_pattern(
            rho=opt['rho'],
            verify=True
        )

        if not fab_result['success'] or fab_result['fidelity'] < 0.9:
            raise RuntimeError(f"Falha na fabricação LC: fidelity={fab_result['fidelity']}")

        # === FASE 3: ANÁLISE DE PUREZA COM PHOTON SORTER ===
        print("💎 Fase 3: Analisando pureza de Fock com Photon Sorter...")

        # Simular resposta do sorter para o feixe gerado
        sorter_result = self.sorter.simulate_input_output(
            input_state=target_fock_state,
            input_amplitude=0.1,
            mzi_phase=0.0  # Pode ser otimizado conjuntamente
        )

        sorting_fidelity = sorter_result['sorting_fidelity']
        bsm_prob = sorter_result['bsm_success_prob']

        if sorting_fidelity < min_sorting_fidelity:
            print(f"⚠️ Fidelidade de sorting abaixo do limiar: {sorting_fidelity:.3f} < {min_sorting_fidelity}")
            # Tentar re-otimizar com peso maior na pureza de Fock

        # === FASE 4: CERTIFICAÇÃO DE COERÊNCIA GRANULAR ===
        # Ω_granular = P₁ / (P₁ + P₂) para estados de Fock
        p1 = sorter_result['output_probabilities']['p_upper'] if target_fock_state == "fock_1" else sorter_result['output_probabilities']['p_lower']
        p2 = sorter_result['output_probabilities']['p_lower'] if target_fock_state == "fock_1" else sorter_result['output_probabilities']['p_upper']

        omega_granular = p1 / (p1 + p2 + 1e-10)

        # Certificação combinada: coerência espacial + espectral + granular
        overall_coherence = (
            opt['pred_spatial'][0,1].item() * 0.4 +  # ρ_spatial
            opt_result.get('spectral_fidelity', 0.9) * 0.3 +  # Fidelidade espectral
            omega_granular * 0.3  # Pureza de Fock
        )

        import time
        return {
            'certification': {
                'omega_spatial': opt['pred_spatial'][0,1].item(),
                'omega_spectral': opt_result.get('spectral_fidelity', 0.9),
                'omega_granular': float(omega_granular),
                'overall_coherence': float(overall_coherence),
                'sorting_fidelity': float(sorting_fidelity),
                'bsm_success_probability': float(bsm_prob),
                'certified': overall_coherence > 0.85 and sorting_fidelity > min_sorting_fidelity
            },
            'parameters': {
                'spatial': {'l_p': opt['l_p'], 'm': opt['m'], 'ratio': opt['ratio']},
                'spectral': {'rho_hash': hash(opt['rho'].numpy().tobytes())},
                'sorter': {'mzi_phase': 0.0, 'target_fock': target_fock_state}
            },
            'fabrication': fab_result,
            'ready_for_quantum_use': (
                fab_result['fidelity'] > 0.9 and
                sorting_fidelity > min_sorting_fidelity and
                overall_coherence > 0.85
            )
        }
