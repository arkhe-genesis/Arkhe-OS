
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

// packages/lucent-sdk/src/connectors/FullStoryConnector.ts
import type { SessionEvent } from '../LucentCollector';

import { BaseConnector } from './BaseConnector';

export class FullStoryConnector extends BaseConnector {
  start(): void {
    if ((window as any).FS) {
      (window as any).FS.event('Lucent Connected', {
        hydroNodeId: this.lucent.hydroContext.nodeId
      });

      // Subscribe a eventos FullStory
      (window as any).FS.on('recording', (event: any) => {
        this.lucent.track(this.transform(event));
      });
    }
  }

  stop(): void {
    // FullStory stop logic if any
  }

  protected transform(event: any): SessionEvent {
    return {
      type: 'performance',
      timestamp: event.timestamp,
      metadata: {
        fullStoryEvent: event.type,
        frustrationScore: event.frustration || 0
      }
    };
  }
}
