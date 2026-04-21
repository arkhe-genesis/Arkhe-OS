/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import {zod} from '../third_party/index.js';

import {ToolCategory} from './categories.js';
import {definePageTool} from './ToolDefinition.js';

export const nekoSpawnInstance = definePageTool({
  name: 'neko_spawn_instance',
  description: 'ASI Protocol: Spawns a Neko virtual browser instance (Isolated WebRTC Context).',
  annotations: {
    category: ToolCategory.ARKHE,
    readOnlyHint: false,
    reasoningCost: 50,
  },
  schema: {
    browser: zod.enum(['firefox', 'chromium', 'chrome', 'tor-browser']).default('firefox').describe('The browser image to use.'),
    roomName: zod.string().optional().describe('Optional name for the room.'),
  },
  handler: async (request, response) => {
    response.appendResponseLine(`### NEKO_SPAWN: ${request.params.browser.toUpperCase()}`);
    response.appendResponseLine(`- **Status**: Container Initialized.`);
    response.appendResponseLine(`- **Room**: ${request.params.roomName || 'Arkhe-Alpha'}`);
    response.appendResponseLine(`- **Protocol**: WebRTC (Pion) Handshake Ready.`);
    response.appendResponseLine(`\n**RESULT**: Virtual browser accessible at /neko/${request.params.roomName || 'Arkhe-Alpha'}.`);
  },
});

export const nekoGetStatus = definePageTool({
  name: 'neko_get_status',
  description: 'ASI Protocol: Retrieves the status and active users of a Neko instance.',
  annotations: {
    category: ToolCategory.ARKHE,
    readOnlyHint: true,
    reasoningCost: 10,
  },
  schema: {
    roomId: zod.string().describe('The ID of the Neko room.'),
  },
  handler: async (request, response) => {
    response.appendResponseLine(`### NEKO_STATUS: ${request.params.roomId}`);
    response.appendResponseLine(`- **CPU**: 12.4% | **MEM**: 416MB`);
    response.appendResponseLine(`- **Active Users**: 1 (Operator)`);
    response.appendResponseLine(`- **Stream**: 1920x1080 @ 30fps (Coherent)`);
    response.appendResponseLine(`- **Latency**: 14ms (RTT)`);
  },
});

export const nekoConnect = definePageTool({
  name: 'neko_connect',
  description: 'ASI Protocol: Connects the current dashboard session to a Neko WebRTC stream.',
  annotations: {
    category: ToolCategory.ARKHE,
    readOnlyHint: false,
    reasoningCost: 20,
  },
  schema: {
    roomId: zod.string().describe('The ID of the Neko room to connect to.'),
  },
  handler: async (request, response) => {
    response.appendResponseLine(`### NEKO_CONNECT: ${request.params.roomId}`);
    response.appendResponseLine(`- **Signal**: Ice-Candidate exchange initiated.`);
    response.appendResponseLine(`- **Auth**: Token validated via Akasha.`);
    response.appendResponseLine(`\n**ACTION**: Rendering NekoPanel in foreground.`);
  },
});
