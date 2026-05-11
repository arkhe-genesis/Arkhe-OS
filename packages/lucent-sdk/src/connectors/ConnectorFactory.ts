
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

// packages/lucent-sdk/src/connectors/ConnectorFactory.ts
import type { LucentCollector } from '../LucentCollector';

import type { BaseConnector, ConnectorConfig } from './BaseConnector';
import { FullStoryConnector } from './FullStoryConnector';
import { PostHogConnector } from './PostHogConnector';

// Factory para instanciar conectores
export class ConnectorFactory {
  static create(
    type: 'posthog' | 'fullstory' | 'amplitude',
    config: ConnectorConfig,
    lucent: LucentCollector
  ): BaseConnector {
    switch(type) {
      case 'posthog': return new PostHogConnector(config, lucent);
      case 'fullstory': return new FullStoryConnector(config, lucent);
      default: throw new Error(`Connector ${type} not implemented`);
    }
  }
}
