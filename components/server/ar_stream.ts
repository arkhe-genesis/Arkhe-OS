
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { WebSocket } from 'ws';

import { logger } from './logger';
import { state } from './state';

/**
 * @module ARStreamServer
 * @description Streams 3D node data to field technician AR devices (Unity/ARCore).
 */

export function setupARStream(wss: any) {
  wss.on('connection', (ws: WebSocket) => {
    logger.info("🜏 [AR] Field technician connected for Phase Cloud visualization.");

    // Send data every 500ms
    const interval = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        // Map Tzinor state to AR-ready JSON
        const arPayload = {
          type: "node_update",
          timestamp: Date.now(),
          nodes: state.shards.map(shard => ({
            id: shard.id,
            // Simulated coordinates centered on Rio Central Station
            lat: -22.9099 + (Math.random() - 0.5) * 0.005,
            lon: -43.1775 + (Math.random() - 0.5) * 0.005,
            alt: 5.0 + Math.random() * 2.0,
            R: state.currentLambda * (0.9 + Math.random() * 0.2),
            type: shard.id.toString().startsWith('GW') ? 'gateway' : 'sensor',
            battery: 0.3 + Math.random() * 0.7,
            failureCause: shard.status === 'corrupted' ?
              (Math.random() > 0.5 ? 'obstruction' : 'battery') : null
          })),
          threatLevel: state.threatLevel
        };

        ws.send(JSON.stringify(arPayload));
      }
    }, 500);

    ws.on('close', () => {
      clearInterval(interval);
      logger.info("🜏 [AR] Field technician disconnected.");
    });
  });
}
