
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import http from 'node:http';

import { logger } from './server/logger.js';

const req = http.request({
  hostname: 'localhost',
  port: 3000,
  path: '/api/x402/moltx-handshake',
  method: 'POST',
}, (res) => {
  let data = '';
  res.on('data', (chunk) => data += chunk);
  res.on('end', () => logger.info('Response: ' + data));
});

req.on('error', (e) => logger.error(e.message));
req.end();
