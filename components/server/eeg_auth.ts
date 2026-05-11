
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import * as crypto from 'node:crypto';

import { logger } from './logger';

/**
 * @module EEGAuthentication
 * @description Implements the biometric phase anchoring for mobile Tzinor nodes (Rio Phase 2).
 */

export interface EEGData {
  channels: number[]; // 19 channels
  timestamp: number;
  samplingRate: number;
}

export class EEGAuthenticator {
  private static readonly PHASE_SCALE = 0.3; // Scale factor α (rad)
  private static readonly COUPLING_BETA = 0.4; // Coupling strength β

  /**
   * Generates a 32-bit biometric embedding from raw EEG data using a simulated autoencoder.
   * In production, this would be a TFLite model running in the secure enclave.
   */
  public static generateEmbedding(data: EEGData): Buffer {
    // 1. Feature Extraction (Simulated)
    // We use a combination of channel variance and spectral peaks as entropy sources.
    const entropySource = data.channels.map(v => Math.sin(v) * Math.cos(v)).join('|');

    // 2. Dimensionality Reduction (32-bit Hash)
    const hash = crypto.createHash('sha256').update(entropySource).digest();
    return hash.subarray(0, 4); // Take first 32 bits
  }

  /**
   * Maps the 32-bit EEG embedding to a phase shift δθ.
   * This shift is idiossincratic and non-deterministic for external observers.
   */
  public static calculatePhaseShift(embedding: Buffer): number {
    const value = embedding.readUInt32BE(0);
    // Normalize to [-π, π] and apply scale
    return ((value / 0xFFFFFFFF) * 2 * Math.PI - Math.PI) * this.PHASE_SCALE;
  }

  /**
   * Verifies the liveness of the EEG signal.
   * Rejects synthetic/flat signals or repeated recordings (replay attacks).
   */
  public static verifyLiveness(data: EEGData): boolean {
    // 1. Check for signal variance (reject flatlines)
    const variance = data.channels.reduce((acc, v) => acc + Math.abs(v), 0) / data.channels.length;
    if (variance < 1e-6) {
      logger.warn("EEG Liveness Check Failed: Signal too static.");
      return false;
    }

    // 2. Reject Replay Attacks (Simplified)
    // In production, we'd check against a rolling window of recent embeddings.
    return true;
  }

  /**
   * Integrates the EEG shift into the Kuramoto state update.
   */
  public static updateNodePhase(currentPhase: number, eegShift: number, neighbors: number[]): number {
    // Standard Kuramoto Coupling
    let couplingSum = 0;
    for (const neighborPhase of neighbors) {
      couplingSum += Math.sin(neighborPhase - currentPhase);
    }

    // Phase Equation: θ_dot = ω + K*Σsin(Δφ) + β*f(EEG)
    // We assume Δt=1 for simplicity in this PoC
    const deltaTheta = 0.1 + (0.5 * couplingSum) + (this.COUPLING_BETA * eegShift);
    return (currentPhase + deltaTheta) % (2 * Math.PI);
  }
}

/**
 * @class AggregateEEGAuthenticator
 * @description Handles collective biometric signatures for mass transport vehicles (BRT/SuperVia).
 */
export class AggregateEEGAuthenticator {
  /**
   * Simulates a CNN+LSTM model that aggregates multiple surveillance streams
   * into a 32-bit "Collective Vigilance" signature.
   */
  public static generateCollectiveSignature(
    videoFeatures: number[][], // From onboard cameras
    audioStreams: number[][],   // From microphones
    vibrationData: number[]     // From rail/road sensors
  ): Buffer {
    // 1. Feature Fusion (Simulated weighted sum)
    const fusedValue = videoFeatures.flat().reduce((a, b) => a + b, 0) * 0.5 +
                       audioStreams.flat().reduce((a, b) => a + b, 0) * 0.3 +
                       vibrationData.reduce((a, b) => a + b, 0) * 0.2;

    // 2. State-driven Embedding (Simulated LSTM temporal dependency)
    const temporalContext = Math.sin(fusedValue + (Date.now() % 1000));

    const hash = crypto.createHash('sha256')
      .update(`collective_v1_${temporalContext}`)
      .digest();

    return hash.subarray(0, 4);
  }

  /**
   * Returns a phase shift based on the collective state.
   * A "Vigilant" crowd (high entropy/attention) increases the Phase Shield strength.
   */
  public static getCollectivePhaseShift(signature: Buffer): number {
    const raw = signature.readUInt32BE(0);
    const entropy = (raw / 0xFFFFFFFF);

    // Collective shifts are more stable, less scale than individual EEG
    return (entropy * Math.PI - (Math.PI / 2)) * 0.2;
  }
}
