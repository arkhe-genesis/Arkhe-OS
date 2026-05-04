/**
 * @license
 * Copyright 2025 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import assert from 'node:assert';
import {describe, it} from 'node:test';

import {McpResponse} from '../../src/McpResponse.js';
import type {zod} from '../../src/third_party/index.js';
import {
  nashGetDeviceStatus,
  nashEnrollCognitiveProfile,
  nashAuthenticate,
  nashAttest,
  nashCoercionScan,
} from '../../src/tools/nash.js';
import type {
  Context,
  ContextPage,
  Request,
} from '../../src/tools/ToolDefinition.js';

describe('nash', () => {
  it('verifies Nash Identity Safe tools', async () => {
    const response = new McpResponse({} as never);
    const mockContext = {} as Context;
    const mockRequest = {params: {}} as unknown as Request<zod.ZodRawShape> & {
      page: ContextPage;
    };

    // nash_get_device_status
    await nashGetDeviceStatus.handler(mockRequest, response, mockContext);
    assert.ok(
      response.responseLines.some(line =>
        line.includes('Nash Identity Safe: Device Status'),
      ),
      'nash_get_device_status: Missing title',
    );
    assert.ok(
      response.responseLines.some(line =>
        line.includes('READY FOR AUTHORIZATION'),
      ),
      'nash_get_device_status: Missing ready status',
    );

    // nash_enroll_cognitive_profile
    response.resetResponseLineForTesting();
    await nashEnrollCognitiveProfile.handler(
      mockRequest,
      response,
      mockContext,
    );
    assert.ok(
      response.responseLines.some(line =>
        line.includes('New Revocable Cognitive Profile sealed to device'),
      ),
      'nash_enroll_cognitive_profile: Missing success message',
    );

    // nash_authenticate
    response.resetResponseLineForTesting();
    await nashAuthenticate.handler(
      {params: {pin: '1234'}} as Request<{pin: zod.ZodString}> & {
        page: ContextPage;
      },
      response,
      mockContext,
    );
    assert.ok(
      response.responseLines.some(line =>
        line.includes('AUTHORIZATION RELEASED'),
      ),
      'nash_authenticate: Missing authorization message',
    );
    assert.ok(
      response.responseLines.some(line => line.includes('verified locally')),
      'nash_authenticate: Missing verification message',
    );

    // nash_attest
    response.resetResponseLineForTesting();
    await nashAttest.handler(
      {params: {payload: 'test_tx_hash'}} as Request<{payload: zod.ZodString}> & {
        page: ContextPage;
      },
      response,
      mockContext,
    );
    assert.ok(
      response.responseLines.some(line =>
        line.includes('ml-dsa-sig:8f3c...9e21'),
      ),
      'nash_attest: Missing signature',
    );

    // nash_coercion_scan
    response.resetResponseLineForTesting();
    await nashCoercionScan.handler(mockRequest, response, mockContext);
    assert.ok(
      response.responseLines.some(
        line => line.includes('SAFETY STATE') && line.includes('VOLUNTARY'),
      ),
      'nash_coercion_scan: Missing safety state message',
    );
  });
});
