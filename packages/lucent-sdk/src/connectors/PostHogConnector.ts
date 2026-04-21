
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

// packages/lucent-sdk/src/connectors/PostHogConnector.ts
import posthog from 'posthog-js';

import type { SessionEvent } from '../LucentCollector';

import { BaseConnector } from './BaseConnector';

export class PostHogConnector extends BaseConnector {
  start(): void {
    posthog.init(this.config.apiKey, {
      api_host: 'https://app.posthog.com',
      loaded: () => {
        // Override do capture original para interceptar
        const originalCapture = (posthog.capture as any).bind(posthog);
        posthog.capture = (eventName: string, properties?: any) => {
          // Envia para PostHog (comportamento normal)
          const result = originalCapture(eventName, properties);

          // Envia para Lucent-Ω (camada quântica)
          const lucentEvent = this.transform({ eventName, properties });
          this.lucent.track(lucentEvent);

          return result;
        };
      }
    });
  }

  stop(): void {
    posthog.opt_out_capturing();
  }

  protected transform(event: any): SessionEvent {
    return {
      type: this.mapEventType(event.eventName),
      timestamp: Date.now(),
      target: event.properties?.$current_url,
      metadata: {
        posthogEvent: event.eventName,
        distinctId: event.properties?.distinct_id,
        // Anonimizado se necessário
        ...event.properties
      }
    };
  }

  private mapEventType(eventName: string): SessionEvent['type'] {
    if (eventName.includes('rage')) {return 'rage_click';}
    if (eventName.includes('error')) {return 'error';}
    if (eventName.includes('navigation')) {return 'navigation';}
    return 'click';
  }
}
