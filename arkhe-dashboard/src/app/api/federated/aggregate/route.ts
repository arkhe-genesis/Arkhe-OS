/**
 * @license
 * Copyright 2025 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

import { ethicalFederatedLearner } from '@/lib/federated/ethicalFederatedLearning';
import type { ClientUpdate } from '@/types/ethics';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { action, ...payload } = body;

    switch (action) {
      case 'submit_update': {
        const update: ClientUpdate = {
          clientId: payload.clientId,
          modelWeights: payload.modelWeights.map((w: number[]) => new Float32Array(w)),
          numSamples: payload.numSamples,
          loss: payload.loss,
          timestamp: Date.now(),
          dpNoiseScale: payload.dpNoiseScale,
        };

        // Simular agregação com outros updates para demonstração
        const simulatedUpdates: ClientUpdate[] = [update];
        for (let i = 0; i < 4; i++) {
          simulatedUpdates.push({
            clientId: `client_${i}`,
            modelWeights: update.modelWeights.map(w =>
              new Float32Array(w.map(v => v + (Math.random() - 0.5) * 0.01))
            ),
            numSamples: Math.floor(update.numSamples * (0.8 + Math.random() * 0.4)),
            loss: update.loss * (0.9 + Math.random() * 0.2),
            timestamp: Date.now(),
            dpNoiseScale: update.dpNoiseScale,
          });
        }

        const result = await ethicalFederatedLearner.aggregateClientUpdates(simulatedUpdates);

        return NextResponse.json({
          success: true,
          data: {
            roundNumber: result.roundNumber,
            participatingClients: result.participatingClients,
            avgLoss: result.avgLoss,
            privacyBudget: result.privacyBudget,
          },
        });
      }

      case 'get_metrics': {
        const metrics = ethicalFederatedLearner.getFederatedMetrics();
        return NextResponse.json({ success: true, metrics });
      }

      default:
        return NextResponse.json({ error: 'Unknown federated action' }, { status: 400 });
    }
  } catch (error: unknown) {
    console.error('❌ Federated learning error:', error);
    return NextResponse.json(
      { error: 'Federated operation failed', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}
