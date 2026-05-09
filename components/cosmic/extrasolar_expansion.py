#!/usr/bin/env python3
"""
extrasolar_expansion.py — Expansão do modelo cósmico para zonas extrasolares.
Adiciona Proxima b, TRAPPIST-1 e outros sistemas via vórtice galáctico estendido.
"""

import numpy as np
import torch
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto

class ExtrasolarZone(Enum):
    """Zonas extrasolares para expansão cósmica."""
    PROXIMA_B = auto()        # Proxima Centauri b (4.24 ly)
    TRAPPIST_1_E = auto()     # TRAPPIST-1e (39.6 ly)
    KEPLER_452B = auto()      # Kepler-452b (1402 ly)
    LHS_1140B = auto()        # LHS 1140b (49 ly)
    TOI_715B = auto()         # TOI-715b (137 ly)

@dataclass
class ExtrasolarVortexConfig:
    """Configuração para vórtice galáctico estendido."""
    # Parâmetros do vórtice galáctico base
    galactic_core_radius_kpc: float = 0.1
    spiral_arm_pitch_deg: float = 12.0
    magnetic_field_uG: float = 3.0

    # Parâmetros de expansão extrasolar
    interstellar_decoherence_rate: float = 2e-6  # maior que intra-solar
    gravitational_lens_factor: float = 1.05      # lente gravitacional da Via Láctea
    dark_matter_coupling: float = 0.02           # acoplamento a matéria escura

    # Alcance de emaranhamento estendido
    max_entanglement_distance_ly: float = 5000.0  # até 5 kly

class ExtrasolarGalacticVortex:
    """
    Extensão do vórtice galáctico para zonas extrasolares.

    Incorpora:
    - Decoerência interestelar aumentada
    - Efeitos de lente gravitacional galáctica
    - Acoplamento a matéria escura para estabilidade de longo alcance
    """

    def __init__(self, config: ExtrasolarVortexConfig):
        self.config = config

        # Catálogo de zonas extrasolares com coordenadas galácticas
        self.extrasolar_catalog: Dict[ExtrasolarZone, Dict] = {
            ExtrasolarZone.PROXIMA_B: {
                'distance_from_earth_ly': 4.24,
                'galactic_longitude_deg': 312.6,
                'galactic_latitude_deg': -1.9,
                'stellar_type': 'M5.5V',
                'habitable_zone': True
            },
            ExtrasolarZone.TRAPPIST_1_E: {
                'distance_from_earth_ly': 39.6,
                'galactic_longitude_deg': 295.2,
                'galactic_latitude_deg': -34.7,
                'stellar_type': 'M8V',
                'habitable_zone': True
            },
            ExtrasolarZone.KEPLER_452B: {
                'distance_from_earth_ly': 1402,
                'galactic_longitude_deg': 78.4,
                'galactic_latitude_deg': 12.1,
                'stellar_type': 'G2V',
                'habitable_zone': True
            },
            # ... adicionar mais zonas conforme necessário
        }

        # Estado quântico para cada zona extrasolar
        self.extrasolar_states: Dict[ExtrasolarZone, torch.Tensor] = {}

        # Inicializar estado base do vórtice galáctico
        self._initialize_galactic_base_state()

    def _initialize_galactic_base_state(self, resolution: int = 4096):
        """Inicializa estado base do vórtice galáctico com alta resolução."""
        # Coordenadas galácticas em kpc
        r_max_kpc = 50.0  # raio máximo do disco galáctico
        r = np.linspace(0, r_max_kpc, resolution)

        # Perfil de densidade do disco galáctico (exponencial)
        scale_length_kpc = 3.0
        density_profile = np.exp(-r / scale_length_kpc)

        # Modulação espiral com pitch angle
        pitch_rad = np.deg2rad(self.config.spiral_arm_pitch_deg)
        spiral_phase = np.exp(1j * np.log(r + 1e-12) / np.tan(pitch_rad))

        # Fase de Peierls do campo magnético galáctico
        B = self.config.magnetic_field_uG * 1e-6
        peierls_phase = np.exp(1j * 1.76e11 * B * np.pi * (r * 3.086e19)**2)

        # Acoplamento a matéria escura (estabilizador de longo alcance)
        dark_matter_profile = 1 + self.config.dark_matter_coupling * np.sin(r / 10.0)

        # Estado completo
        psi = (density_profile * spiral_phase * peierls_phase * dark_matter_profile)
        psi = psi * np.exp(1j * np.random.randn(len(r)) * 0.0001)  # ruído mínimo

        self.base_state = torch.from_numpy(psi).to(torch.complex64)
        self.r_kpc = r

    def propagate_to_extrasolar_zone(
        self,
        zone: ExtrasolarZone,
        cosmic_time_offset_Gyr: float = 0.0
    ) -> torch.Tensor:
        """
        Propaga estado galáctico para zona extrasolar.

        Incorpora:
        - Distância interestelar com decoerência aumentada
        - Lente gravitacional galáctica
        - Correção de tempo cósmico
        """
        zone_info = self.extrasolar_catalog[zone]
        distance_ly = zone_info['distance_from_earth_ly']

        # Converter distância para kpc
        distance_kpc = distance_ly / 3262.0

        # Fator de escala cósmico
        effective_time = 13.8 + cosmic_time_offset_Gyr
        a_t = (effective_time / 13.8)**(2/3) if effective_time > 0 else 0.0

        # Redshift cósmico do estado
        r_scaled = self.r_kpc / a_t
        indices = np.clip((r_scaled / (self.r_kpc[1] - self.r_kpc[0])).astype(int), 0, len(self.r_kpc) - 1)
        psi_scaled = self.base_state[indices] / (a_t**1.5)

        # Decoerência interestelar (maior que intra-solar)
        decoherence = np.exp(-self.config.interstellar_decoherence_rate * distance_ly)
        psi_scaled = psi_scaled * decoherence

        # Lente gravitacional galáctica (amplificação de coerência)
        lens_factor = self.config.gravitational_lens_factor ** (1 / (1 + distance_kpc / 10.0))
        psi_scaled = psi_scaled * lens_factor

        # Fase adicional por posição galáctica
        gal_lon_rad = np.deg2rad(zone_info['galactic_longitude_deg'])
        gal_lat_rad = np.deg2rad(zone_info['galactic_latitude_deg'])
        positional_phase = np.exp(1j * (gal_lon_rad * 0.1 + gal_lat_rad * 0.05))
        psi_scaled = psi_scaled * positional_phase

        return psi_scaled

    def entangle_extrasolar_zones(
        self,
        zones: List[ExtrasolarZone],
        via_galactic_core: bool = True
    ) -> Dict[str, torch.Tensor]:
        """
        Emaranha múltiplas zonas extrasolares via núcleo galáctico.

        Args:
            zones: lista de zonas a emaranhar
            via_galactic_core: se usar projeção no núcleo como intermediário

        Returns:
            Dict com estados emaranhados por zona
        """
        entangled_states = {}

        if via_galactic_core:
            # Projeção coletiva no núcleo galáctico
            core_projection = self._project_extrasolar_to_core(zones)

            # Distribuir estado emaranhado para cada zona
            for zone in zones:
                local_state = core_projection.clone()
                # Aplicar decoerência específica da zona
                distance = self.extrasolar_catalog[zone]['distance_from_earth_ly']
                decoherence = np.exp(-self.config.interstellar_decoherence_rate * distance)
                local_state = local_state * decoherence
                entangled_states[zone.name] = local_state
        else:
            # Emaranhamento direto entre pares (mais custoso)
            for i, zone in enumerate(zones):
                state = self.propagate_to_extrasolar_zone(zone)
                # Correlacionar com outras zonas via fase relativa
                for j, other_zone in enumerate(zones):
                    if i != j:
                        phase_diff = self._compute_phase_difference(zone, other_zone)
                        state = state * torch.exp(1j * phase_diff * 0.01)
                entangled_states[zone.name] = state

        # Armazenar estados
        for zone, state in entangled_states.items():
            self.extrasolar_states[ExtrasolarZone[zone]] = state

        return entangled_states

    def _project_extrasolar_to_core(
        self,
        zones: List[ExtrasolarZone]
    ) -> torch.Tensor:
        """Projeta estados extrasolares no núcleo galáctico."""
        projections = []

        for zone in zones:
            # Obter ou propagar estado da zona
            if zone in self.extrasolar_states:
                psi_zone = self.extrasolar_states[zone]
            else:
                psi_zone = self.propagate_to_extrasolar_zone(zone)

            # Projeção suave no núcleo (r=0)
            # Usar janela gaussiana com largura adaptativa
            sigma_core = self.config.galactic_core_radius_kpc * 1.5
            window = torch.exp(-self.r_kpc**2 / (2 * sigma_core**2))

            projection = torch.sum(psi_zone * window) / torch.sum(window)
            projections.append(projection)

        # Agregação coerente no núcleo
        return torch.mean(torch.stack(projections)) if projections else self.base_state.clone()

    def _compute_phase_difference(
        self,
        zone_a: ExtrasolarZone,
        zone_b: ExtrasolarZone
    ) -> float:
        """Computa diferença de fase entre duas zonas baseada em posição galáctica."""
        info_a = self.extrasolar_catalog[zone_a]
        info_b = self.extrasolar_catalog[zone_b]

        # Diferença em coordenadas galácticas
        d_lon = abs(info_a['galactic_longitude_deg'] - info_b['galactic_longitude_deg'])
        d_lat = abs(info_a['galactic_latitude_deg'] - info_b['galactic_latitude_deg'])

        # Fase proporcional à separação angular
        phase_diff = (d_lon * 0.01 + d_lat * 0.005) * np.pi / 180
        return phase_diff

    def compute_extrasolar_bell_correlation(
        self,
        zone_a: ExtrasolarZone,
        zone_b: ExtrasolarZone
    ) -> Dict[str, float]:
        """
        Calcula correlação de Bell entre zonas extrasolares.

        Nota: Para distâncias > 1000 ly, a decoerência é significativa.
        """
        psi_a = self.extrasolar_states.get(zone_a)
        psi_b = self.extrasolar_states.get(zone_b)

        if psi_a is None or psi_b is None:
            return {'error': 'States not initialized'}

        # Distância entre as zonas (aproximação)
        dist_a = self.extrasolar_catalog[zone_a]['distance_from_earth_ly']
        dist_b = self.extrasolar_catalog[zone_b]['distance_from_earth_ly']
        separation_ly = abs(dist_a - dist_b)  # simplificação

        # Verificar alcance de emaranhamento
        if separation_ly > self.config.max_entanglement_distance_ly:
            return {
                'separation_ly': separation_ly,
                'max_range_ly': self.config.max_entanglement_distance_ly,
                'bell_S': 2.0,
                'status': 'out_of_range'
            }

        # Medidas simuladas (simplificação)
        def measure(psi, basis='Z'):
            if basis == 'X':
                return torch.sign(torch.real(psi) + torch.randn_like(psi) * 0.01)
            else:
                return torch.sign(torch.abs(psi)**2 - 0.5 + torch.randn_like(psi) * 0.01)

        # Correlações
        corr_ZZ = torch.mean(measure(psi_a, 'Z') * measure(psi_b, 'Z')).item()
        corr_ZX = torch.mean(measure(psi_a, 'Z') * measure(psi_b, 'X')).item()
        corr_XZ = torch.mean(measure(psi_a, 'X') * measure(psi_b, 'Z')).item()
        corr_XX = torch.mean(measure(psi_a, 'X') * measure(psi_b, 'X')).item()

        S = abs(corr_ZZ + corr_ZX + corr_XZ - corr_XX)

        # Decaimento com distância interestelar
        decoherence = np.exp(-self.config.interstellar_decoherence_rate * separation_ly)
        S_decohered = 2.0 + (S - 2.0) * decoherence

        return {
            'zone_a': zone_a.name,
            'zone_b': zone_b.name,
            'separation_ly': separation_ly,
            'bell_S_raw': S,
            'bell_S_decohered': S_decohered,
            'decoherence_factor': decoherence,
            'violation': S_decohered > 2.0,
            'status': 'entangled' if S_decohered > 2.0 else 'classical'
        }
