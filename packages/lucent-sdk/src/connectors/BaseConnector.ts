
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

// packages/lucent-sdk/src/connectors/BaseConnector.ts
import type { LucentCollector, SessionEvent } from '../LucentCollector';

export interface ConnectorConfig {
  apiKey: string;
  projectId: string;
  options?: {
    filterEvents?: string[];
    sampleRate?: number;
  };
}

export abstract class BaseConnector {
  constructor(
    protected config: ConnectorConfig,
    protected lucent: LucentCollector
  ) {}

  abstract start(): void;
  abstract stop(): void;

  // Transforma evento do provedor em formato Lucent
  protected abstract transform(event: unknown): SessionEvent;
}
