# arkhe_core/temporal_reference.py
"""
Módulo de Referência Temporal Terrestre Dinâmica (RTD).
Corrige timestamps e coordenadas para movimento orbital/rotacional da Terra.
"""

import numpy as np
from astropy.coordinates import EarthLocation, SkyCoord, ICRS
from astropy.time import Time
from astropy import units as u
from typing import Tuple, Optional

class TerrestrialReferenceFrame:
    """
    Fornece correções de posição/orientação terrestre para:
    - Timestamps (UTC → TAI → TT → TDB)
    - Coordenadas (ITRF → GCRS → ICRS)
    - Sincronização distribuída com correção Sagnac
    """

    def __init__(self, location: Optional[EarthLocation] = None):
        self.location = location or EarthLocation.of_site('greenwich')

    def correct_timestamp(self, timestamp_utc: float,
                         target_scale: str = 'tdb') -> float:
        """
        Converte timestamp UTC para escala temporal alvo com correções relativísticas.

        Escalas disponíveis:
        - 'utc': Tempo Universal Coordenado (com leap seconds)
        - 'tai': Tempo Atômico Internacional (contínuo)
        - 'tt': Tempo Terrestre (TAI + 32.184s)
        - 'tdb': Tempo Dinâmico Baricêntrico (para efemérides)
        """
        t_utc = Time(timestamp_utc, format='unix', scale='utc', location=self.location)
        t_corrected = getattr(t_utc, target_scale)
        return t_corrected.unix

    def correct_coordinates(self, ra_deg: float, dec_deg: float,
                           obs_time_utc: float,
                           target_frame: str = 'icrs') -> Tuple[float, float]:
        """
        Corrige coordenadas celestes para movimento terrestre.

        Args:
            ra_deg, dec_deg: Coordenadas observadas (J2000)
            obs_time_utc: Timestamp da observação
            target_frame: 'icrs', 'gcrs', 'itrs'

        Returns:
            (ra_corrected, dec_corrected) em graus
        """
        # Coordenadas observadas
        coord_obs = SkyCoord(ra=ra_deg*u.deg, dec=dec_deg*u.deg,
                            frame='icrs', obstime=Time(obs_time_utc, format='unix'))

        # Transformar para referencial alvo
        if target_frame == 'gcrs':
            coord_corrected = coord_obs.transform_to('gcrs')
        elif target_frame == 'itrs':
            # Note: itrs transform might need proper frame initialization with location
            from astropy.coordinates import ITRS
            itrs_frame = ITRS(obstime=Time(obs_time_utc, format='unix'), location=self.location)
            coord_corrected = coord_obs.transform_to(itrs_frame)
        else:  # icrs (já está)
            coord_corrected = coord_obs

        # Extract spherical coordinates regardless of frame
        if hasattr(coord_corrected, 'ra'):
            return coord_corrected.ra.deg, coord_corrected.dec.deg
        else:
            # For ITRS, it uses spherical (lat, lon)
            return coord_corrected.spherical.lon.deg, coord_corrected.spherical.lat.deg

    def sagnac_correction(self, signal_path: list[Tuple[float, float, float]],
                         signal_frequency_hz: float,
                         closed_loop: bool = False) -> float:
        """
        Calcula correção Sagnac para sincronização de sinais em rede distribuída.

        Args:
            signal_path: Lista de (lat, lon, alt) dos nós na rota do sinal.
            signal_frequency_hz: Frequência do sinal.
            closed_loop: Se True, assume que o sinal retorna ao ponto inicial.

        Returns:
            Correção de tempo em segundos.
        """
        earth_omega = 7.2921150e-5  # rad/s
        c = 299792458.0  # m/s

        area_proj = 0.0
        n = len(signal_path)

        if n < 2:
            return 0.0

        # Para caminho aberto, calculamos a área varrida em relação ao eixo da Terra
        # que é a soma das áreas dos triângulos (Polo, Nó i, Nó i+1)
        limit = n if closed_loop else n - 1

        for i in range(limit):
            lat1, lon1, _ = signal_path[i]
            lat2, lon2, _ = signal_path[(i+1) % n]

            # Coordenadas cartesianas no plano equatorial (normalizadas pelo raio)
            x1 = np.cos(np.radians(lat1)) * np.cos(np.radians(lon1))
            y1 = np.cos(np.radians(lat1)) * np.sin(np.radians(lon1))
            x2 = np.cos(np.radians(lat2)) * np.cos(np.radians(lon2))
            y2 = np.cos(np.radians(lat2)) * np.sin(np.radians(lon2))

            # Produto vetorial para área do triângulo (projeção Z)
            area_proj += (x1*y2 - x2*y1)

        # Raio equatorial médio (WGS84)
        Re = 6378137.0
        area_proj *= (Re**2) / 2.0

        # Correção Sagnac: dt = (2 * omega * Area) / c^2
        delta_t = (2 * earth_omega * area_proj) / (c**2)

        return delta_t
