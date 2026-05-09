/**
 * @license
 * Copyright 2025 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */


/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import fs from 'node:fs';
import path from 'node:path';

import { logger } from './logger';
import type { TzinorMemoryState, OrbPayload } from './types';

const STATE_FILE = path.join(process.cwd(), 'tzinor-state.json');

export class EvolutionaryStateStore {
  state: TzinorMemoryState;

  constructor(agentId: string) {
    this.state = this.loadState() || this.getDefaultState(agentId);
  }

  getDefaultState(agentId: string): TzinorMemoryState {
    return {
      agentId,
      currentEpoch: Date.now() / 1000,
      fContext: [],
      gMemory: [
        { 
          originTime: 1742241655000, // Pi Day 2026
          consolidatedTime: Date.now(), 
          summaryHash: '0x35a60481274a38891eb296a4a29f05ccae47188104d9de6de496b5ab0d2745580ea324c6eb33d6dcd5a5baa0df3189b4200e1d3425ae5926ff5871a940a2cb231c', 
          resonanceWeight: 1.618033988749895 
        }
      ],
      warpFactor: 0.1,
      lambdaCoherence: 1.618033988749895,
    };
  }

  loadState(): TzinorMemoryState | null {
    try {
      if (fs.existsSync(STATE_FILE)) {
        const data = fs.readFileSync(STATE_FILE, 'utf-8');
        return JSON.parse(data);
      }
    } catch (err) {
      logger.error("Failed to load Tzinor state: " + err);
    }
    return null;
  }

  saveState() {
    try {
      fs.writeFileSync(STATE_FILE, JSON.stringify(this.state, null, 2));
    } catch (err) {
      logger.error("Failed to save Tzinor state: " + err);
    }
  }

  evolve(observation: OrbPayload) {
    const now = Date.now();
    this.state.currentEpoch = now / 1000;

    // 1. Calculate immediate relevance (simplified)
    const relevance = 1.0;

    // 2. Add to Immediate Context (fContext)
    this.state.fContext.unshift({
      time: observation.originTime,
      embedding: observation.embedding,
      salience: relevance,
    });

    // 3. Apply Decay (Warp)
    const dt = 1.0; // 1 second tick
    this.state.fContext = this.state.fContext.map(node => ({
      ...node,
      salience: node.salience * Math.exp(-this.state.warpFactor * dt)
    }));

    // Consolidate memory: move cooled context to gMemory
    const consolidationThreshold = 0.1;
    const toConsolidate = this.state.fContext.filter(n => n.salience < consolidationThreshold);
    this.state.fContext = this.state.fContext.filter(n => n.salience >= consolidationThreshold);

    toConsolidate.forEach(node => {
      this.state.gMemory.unshift({
        originTime: node.time,
        consolidatedTime: now,
        summaryHash: observation.id,
        resonanceWeight: node.salience * observation.coherence
      });
    });

    // Keep arrays bounded (VecDeque behavior)
    if (this.state.fContext.length > 20) {this.state.fContext = this.state.fContext.slice(0, 20);}
    if (this.state.gMemory.length > 100) {this.state.gMemory = this.state.gMemory.slice(0, 100);}

    // 4. Recalculate State Coherence
    this.state.lambdaCoherence = observation.coherence;
  }
}
