
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

export interface ArkhenConfig {
  baseUrl?: string;
  apiKey?: string;
}

export interface ParameterUpdate {
  couplingStrength?: number;
  lambdaThreshold?: number;
  autoMitigate?: boolean;
}

export class ArkhenClient {
  private baseUrl: string;
  private headers: HeadersInit;

  constructor(config: ArkhenConfig = {}) {
    this.baseUrl = (config.baseUrl || 'http://localhost:3000').replace(/\/$/, '');
    this.headers = {
      'Content-Type': 'application/json',
      'X-Arkhen-Client': 'js-sdk/1.0.0',
      ...(config.apiKey ? { 'Authorization': `Bearer ${config.apiKey}` } : {})
    };
  }

  /** Check system coherence and health */
  async getHealth(): Promise<unknown> {
    const res = await fetch(`${this.baseUrl}/api/health`, { headers: this.headers });
    if (!res.ok) {throw new Error(`Arkhe(n) API Error: ${res.statusText}`);}
    return res.json();
  }

  /** Update Kuramoto coupling and Tzinor gate thresholds */
  async updateParameters(params: ParameterUpdate): Promise<unknown> {
    const res = await fetch(`${this.baseUrl}/api/parameters`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify(params)
    });
    if (!res.ok) {throw new Error(`Arkhe(n) API Error: ${res.statusText}`);}
    return res.json();
  }

  /** Inject a simulated threat vector into the coherence field */
  async injectThreat(type: string): Promise<unknown> {
    const res = await fetch(`${this.baseUrl}/api/trigger-attack`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify({ type })
    });
    if (!res.ok) {throw new Error(`Arkhe(n) API Error: ${res.statusText}`);}
    return res.json();
  }

  /** Trigger the emission of a Python Orb into the ASTL */
  async emitPythonOrb(): Promise<unknown> {
    const res = await fetch(`${this.baseUrl}/api/emit-python`, {
      method: 'POST',
      headers: this.headers
    });
    if (!res.ok) {throw new Error(`Arkhe(n) API Error: ${res.statusText}`);}
    return res.json();
  }
}
