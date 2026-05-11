
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { logger } from './logger';

/**
 * @module HospitalZoneControl
 * @description Manages "Bio-Silent Mode" for gateways near oncology centers.
 */

export interface HospitalZone {
  id: string;
  name: string;
  lat: number;
  lon: number;
  radius_m: number;
}

export const ONCOLOGY_ZONES: HospitalZone[] = [
  { id: 'INCA', name: 'Instituto Nacional de Câncer', lat: -22.9126, lon: -43.1852, radius_m: 500 },
  { id: 'HC1', name: 'Hospital do Câncer I', lat: -22.9110, lon: -43.1870, radius_m: 300 }
];

export interface GatewayMode {
  tx_power_dbm: number;
  frequency_hz: number;
  duty_cycle: number;
  bio_silent: boolean;
}

export class HospitalZoneManager {
  /**
   * Calculates the operational mode for a gateway based on its proximity to a hospital.
   */
  public static getGatewayMode(gw_lat: number, gw_lon: number, is_working_hours: boolean): GatewayMode {
    let near_hospital = false;

    for (const zone of ONCOLOGY_ZONES) {
      // Simple Euclidean distance for the PoC (1 deg ~ 111km)
      const dist = Math.sqrt(Math.pow(gw_lat - zone.lat, 2) + Math.pow(gw_lon - zone.lon, 2)) * 111000;
      if (dist < zone.radius_m) {
        near_hospital = true;
        break;
      }
    }

    if (near_hospital && is_working_hours) {
      logger.info("🜏 [BIO-SILENT] Attenuating gateway power near medical zone.");
      return {
        tx_power_dbm: 10,       // Reduced from 20
        frequency_hz: 868e6,   // LoRa only, avoid 2.4GHz
        duty_cycle: 0.5,       // Burst mode
        bio_silent: true
      };
    }

    return {
      tx_power_dbm: 20,
      frequency_hz: 2.4e9,
      duty_cycle: 1.0,
      bio_silent: false
    };
  }
}
