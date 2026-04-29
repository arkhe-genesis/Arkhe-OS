
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { HydroUXCorrelator } from './packages/lucent-sdk/src/correlation/HydroUXCorrelator';
import { LucentCollector } from './packages/lucent-sdk/src/LucentCollector';

async function testLucent() {
  console.log("Starting Lucent Test...");

  // Mock browser globals
  (global as any).WebSocket = class {
    private onopen_val: any;
    send() {}
    close() {}
    set onopen(val: any) {
        this.onopen_val = val;
    }
    get onopen() { return this.onopen_val; }
  };
  (global as any).window = { location: { href: 'http://localhost' }, innerWidth: 1024, innerHeight: 768 };

  const collector = new LucentCollector("localhost:3000", "session-123", "node-01", {
    correlateHydro: true,
    flushInterval: 0 // Disable interval for test
  });

  console.log("Collector initialized.");

  collector.track({
    type: 'click',
    timestamp: Date.now(),
    target: 'button-1'
  });

  collector.track({
    type: 'rage_click',
    timestamp: Date.now(),
    target: 'frustrating-element'
  });

  console.log("Events tracked.");

  const correlator = new HydroUXCorrelator();
  const hydroState = {
    nodeId: "node-01",
    waterLevel: 10, // low level
    coherence: 0.9,
    history: [{ timestamp: Date.now(), waterLevel: 10, coherence: 0.9 }]
  };

  const uxEvents: any[] = [
    { type: 'rage_click', timestamp: Date.now() },
    { type: 'error', timestamp: Date.now() }
  ];

  const result = await correlator.correlate(uxEvents, hydroState);
  console.log("Correlation Result:", result);

  if (result.correlationCoefficient > 0.5) {
    console.log("SUCCESS: High correlation detected as expected.");
  } else {
    console.log("FAILURE: Correlation lower than expected.");
    process.exit(1);
  }

  collector.end();
}

testLucent().catch(err => {
  console.error("Test failed", err);
  process.exit(1);
});
