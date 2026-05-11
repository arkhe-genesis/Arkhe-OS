
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

// packages/lucent-sdk/src/connectors/FullStoryConnector.ts
import type { SessionEvent } from '../LucentCollector';

import { BaseConnector } from './BaseConnector';

interface FSWindow extends Window {
  FS?: {
    event: (name: string, properties: Record<string, unknown>) => void;
    on: (name: string, callback: (event: unknown) => void) => void;
  };
}

export class FullStoryConnector extends BaseConnector {
  start(): void {
    const fsWindow = (window as unknown as FSWindow);
    if (fsWindow.FS) {
      fsWindow.FS.event('Lucent Connected', {
        hydroNodeId: this.lucent.hydroContext.nodeId
      });

      // Subscribe a eventos FullStory
      fsWindow.FS.on('recording', (event: unknown) => {
        this.lucent.track(this.transform(event));
      });
    }
  }

  stop(): void {
    // FullStory stop logic if any
  }

  protected transform(event: unknown): SessionEvent {
    const fsEvent = event as { timestamp: number; type: string; frustration?: number };
    return {
      type: 'performance',
      timestamp: fsEvent.timestamp,
      metadata: {
        fullStoryEvent: fsEvent.type,
        frustrationScore: fsEvent.frustration || 0
      }
    };
  }
}
