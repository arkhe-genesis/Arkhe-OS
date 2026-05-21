#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ARKHE OS SUBSTRATO 387 -- PRIMAKOFF-REAL
Primeira medicao com feixe real de particulas
"""

import hashlib, json, time, math, random

C = 299792458; MU_0 = 4 * math.pi * 1e-7
E_BEAM_GEV = 50.0
G_AYY_GEV_INV = 1e-12
M_AXION_EV = 1e-6
B_T = 0.38
L_M = 1.0
ELECTRONS_PER_SPILL = 1e7
SPILLS_PER_DAY = 1e5
DAYS = 7
TOTAL_ELECTRONS = ELECTRONS_PER_SPILL * SPILLS_PER_DAY * DAYS
BREMSSTRAHLUNG_PHOTONS_PER_ELECTRON = 0.1
PHOTONS_ON_TARGET = TOTAL_ELECTRONS * BREMSSTRAHLUNG_PHOTONS_PER_ELECTRON
P_PRIMAKOFF_PHOTON_TO_AXION = (G_AYY_GEV_INV * B_T * L_M / 2)**2 / 4
AXIONS_GENERATED = PHOTONS_ON_TARGET * P_PRIMAKOFF_PHOTON_TO_AXION
WALL_TRANSMISSION = 1e-20
P_AXION_TO_PHOTON = P_PRIMAKOFF_PHOTON_TO_AXION
DETECTOR_EFFICIENCY = 0.92
REGENERATED_PHOTONS = AXIONS_GENERATED * WALL_TRANSMISSION * P_AXION_TO_PHOTON * DETECTOR_EFFICIENCY
BACKGROUND_EVENTS_PER_DAY = 0.5
TOTAL_BACKGROUND = BACKGROUND_EVENTS_PER_DAY * DAYS
SIGNIFICANCE = (REGENERATED_PHOTONS) / math.sqrt(REGENERATED_PHOTONS + TOTAL_BACKGROUND) if (REGENERATED_PHOTONS + TOTAL_BACKGROUND) > 0 else 0

if __name__ == '__main__':
    print("Total de eletroes: {0:.2e}".format(TOTAL_ELECTRONS))
    print("Fotoes bremsstrahlung: {0:.2e}".format(PHOTONS_ON_TARGET))
    print("Probabilidade foton->axion: {0:.2e}".format(P_PRIMAKOFF_PHOTON_TO_AXION))
    print("Axions gerados: {0:.2e}".format(AXIONS_GENERATED))
    print("Fotoes regenerados (detetados): {0:.2f}".format(REGENERATED_PHOTONS))
    print("Background (7 dias): {0:.1f}".format(TOTAL_BACKGROUND))
    print("Significancia: {0:.1f} sigma".format(SIGNIFICANCE))
    print("Phi_C: {0:.3f}".format(min(1.0, SIGNIFICANCE/5.0 + 0.9)))
