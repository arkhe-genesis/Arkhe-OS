/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import {spawn} from 'node:child_process';

import {zod} from '../third_party/index.js';

import {ToolCategory} from './categories.js';
import {defineTool} from './ToolDefinition.js';

async function runMeshtasticCmd(args: string[]): Promise<string> {
  return new Promise((resolve, reject) => {
    const child = spawn('meshtastic', args);
    let stdout = '';
    let stderr = '';

    child.stdout.on('data', (data) => {
      stdout += data.toString();
    });

    child.stderr.on('data', (data) => {
      stderr += data.toString();
    });

    child.on('close', (code) => {
      if (code === 0) {
        resolve(stdout);
      } else {
        reject(new Error(`meshtastic exited with code ${code}: ${stderr}`));
      }
    });

    child.on('error', (err) => {
      reject(err);
    });
  });
}

export const meshtasticListDevices = defineTool(() => {
  return {
    name: 'meshtastic_list_devices',
    description: 'Meshtastic: Lists all connected Meshtastic devices.',
    annotations: {
      category: ToolCategory.MESHTASTIC,
      readOnlyHint: true,
      reasoningCost: 10,
    },
    schema: {},
    handler: async (_request, response) => {
      try {
        const output = await runMeshtasticCmd(['--list-ports']);
        response.appendResponseLine('### Meshtastic Devices');
        response.appendResponseLine(output);
      } catch (error) {
        response.appendResponseLine(`Error listing Meshtastic devices: ${(error as Error).message}`);
        response.appendResponseLine('\nNote: Ensure the `meshtastic` Python package is installed and in your PATH.');
      }
    },
  };
});

export const meshtasticInfo = defineTool(() => {
  return {
    name: 'meshtastic_info',
    description: 'Meshtastic: Returns information and configuration for a connected Meshtastic device.',
    annotations: {
      category: ToolCategory.MESHTASTIC,
      readOnlyHint: true,
      reasoningCost: 20,
    },
    schema: {
      port: zod.string().optional().describe('The serial port of the device (e.g., /dev/ttyUSB0). If not provided, it will try to auto-detect.'),
    },
    handler: async (request, response) => {
      const args = ['--info'];
      if (request.params.port) {
        args.push('--port', request.params.port);
      }
      try {
        const output = await runMeshtasticCmd(args);
        response.appendResponseLine('### Meshtastic Device Info');
        response.appendResponseLine(output);
      } catch (error) {
        response.appendResponseLine(`Error getting Meshtastic info: ${(error as Error).message}`);
      }
    },
  };
});

export const meshtasticSendText = defineTool(() => {
  return {
    name: 'meshtastic_send_text',
    description: 'Meshtastic: Sends a text message over the mesh network.',
    annotations: {
      category: ToolCategory.MESHTASTIC,
      readOnlyHint: false,
      reasoningCost: 30,
    },
    schema: {
      text: zod.string().describe('The text message to send.'),
      dest: zod.string().optional().describe('The destination node ID (e.g., ^abcdefgh). If not provided, it broadcasts to all nodes.'),
      port: zod.string().optional().describe('The serial port of the local device to use.'),
    },
    handler: async (request, response) => {
      const {text, dest, port} = request.params;
      const args = ['--sendtext', text];
      if (dest) {
        args.push('--dest', dest);
      }
      if (port) {
        args.push('--port', port);
      }

      try {
        const output = await runMeshtasticCmd(args);
        response.appendResponseLine('### Meshtastic Send Text');
        response.appendResponseLine(output);
        response.appendResponseLine(`\nMessage "${text}" sent ${dest ? `to ${dest}` : 'as broadcast'}.`);
      } catch (error) {
        response.appendResponseLine(`Error sending Meshtastic text: ${(error as Error).message}`);
      }
    },
  };
});
