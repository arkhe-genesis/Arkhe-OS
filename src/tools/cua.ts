/**
 * @license
 * Copyright 2025 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import {spawn} from 'node:child_process';
import path from 'node:path';

import {zod} from '../third_party/index.js';
import {ToolCategory} from './categories.js';
import {defineTool} from './ToolDefinition.js';

const BRIDGE_PATH = path.resolve(process.cwd(), 'scripts', 'cua_bridge.py');

async function runBridge(args: string[]): Promise<any> {
  return new Promise((resolve, reject) => {
    const child = spawn('python3', [BRIDGE_PATH, ...args]);
    let stdout = '';
    let stderr = '';

    child.stdout.on('data', (data) => {
      stdout += data.toString();
    });

    child.stderr.on('data', (data) => {
      stderr += data.toString();
    });

    child.on('close', (code) => {
      if (code !== 0) {
        reject(new Error(`Bridge failed with code ${code}: ${stderr}`));
        return;
      }
      try {
        resolve(JSON.parse(stdout));
      } catch (e) {
        reject(new Error(`Failed to parse bridge output: ${stdout}`));
      }
    });

    child.on('error', (err) => {
      reject(err);
    });
  });
}

export const cuaCreateSandbox = defineTool({
  name: 'cua_create_sandbox',
  description: 'Cua: Provisions a new sandboxed environment (VM or container).',
  annotations: {
    category: ToolCategory.CUA,
    readOnlyHint: false,
    reasoningCost: 100,
  },
  schema: {
    name: zod.string().describe('Unique name for the sandbox.'),
    os: zod.enum(['linux', 'macos', 'windows', 'android']).default('linux').describe('Operating system type.'),
    local: zod.boolean().default(true).describe('Whether to run locally (Docker/QEMU) or in the Cua cloud.'),
    cpu: zod.number().optional().describe('Number of vCPUs.'),
    memory: zod.number().optional().describe('Memory in MiB.'),
  },
  handler: async (request, response) => {
    const args = ['create', '--name', request.params.name, '--os', request.params.os];
    if (request.params.local) args.push('--local');
    if (request.params.cpu) args.push('--cpu', request.params.cpu.toString());
    if (request.params.memory) args.push('--memory', request.params.memory.toString());

    try {
      const result = await runBridge(args);
      if (result.error) {
        response.appendResponseLine(`**Error**: ${result.error}`);
      } else {
        response.appendResponseLine(`### Cua Sandbox Created: ${result.name}`);
        response.appendResponseLine(`- **Status**: ${result.status}`);
        response.appendResponseLine(`- **Message**: ${result.message}`);
      }
    } catch (e: any) {
      response.appendResponseLine(`**Execution Error**: ${e.message}`);
    }
  },
});

export const cuaRunCommand = defineTool({
  name: 'cua_run_command',
  description: 'Cua: Executes a shell command inside a Cua sandbox.',
  annotations: {
    category: ToolCategory.CUA,
    readOnlyHint: false,
    reasoningCost: 50,
  },
  schema: {
    name: zod.string().describe('The name of the sandbox.'),
    command: zod.string().describe('The command to execute.'),
    local: zod.boolean().default(true).describe('Whether the sandbox is local.'),
  },
  handler: async (request, response) => {
    const args = ['run', request.params.name, request.params.command];
    if (request.params.local) args.push('--local');

    try {
      const result = await runBridge(args);
      if (result.error) {
        response.appendResponseLine(`**Error**: ${result.error}`);
      } else {
        response.appendResponseLine(`### Cua Exec: ${request.params.name}`);
        response.appendResponseLine(`**Stdout**:\n\`\`\`\n${result.stdout}\n\`\`\``);
        if (result.stderr) {
          response.appendResponseLine(`**Stderr**:\n\`\`\`\n${result.stderr}\n\`\`\``);
        }
        response.appendResponseLine(`**Exit Code**: ${result.exit_code}`);
      }
    } catch (e: any) {
      response.appendResponseLine(`**Execution Error**: ${e.message}`);
    }
  },
});

export const cuaTakeScreenshot = defineTool({
  name: 'cua_take_screenshot',
  description: 'Cua: Captures a screenshot from a Cua sandbox.',
  annotations: {
    category: ToolCategory.CUA,
    readOnlyHint: true,
    reasoningCost: 40,
  },
  schema: {
    name: zod.string().describe('The name of the sandbox.'),
    local: zod.boolean().default(true).describe('Whether the sandbox is local.'),
  },
  handler: async (request, response) => {
    const args = ['screenshot', request.params.name];
    if (request.params.local) args.push('--local');

    try {
      const result = await runBridge(args);
      if (result.error) {
        response.appendResponseLine(`**Error**: ${result.error}`);
      } else {
        response.appendResponseLine(`Screenshot captured from ${request.params.name}.`);
        response.attachImage({data: result.screenshot, mimeType: 'image/png'});
      }
    } catch (e: any) {
      response.appendResponseLine(`**Execution Error**: ${e.message}`);
    }
  },
});

export const cuaListSandboxes = defineTool({
  name: 'cua_list_sandboxes',
  description: 'Cua: Lists active and suspended sandboxes.',
  annotations: {
    category: ToolCategory.CUA,
    readOnlyHint: true,
    reasoningCost: 10,
  },
  schema: {
    local: zod.boolean().default(true).describe('Whether to list local sandboxes.'),
  },
  handler: async (request, response) => {
    const args = ['list'];
    if (request.params.local) args.push('--local');

    try {
      const result = await runBridge(args);
      if (result.error) {
        response.appendResponseLine(`**Error**: ${result.error}`);
      } else {
        response.appendResponseLine('### Active Cua Sandboxes');
        response.appendResponseLine('| Name | OS | Status | Source | Created At |');
        response.appendResponseLine('|------|----|--------|--------|------------|');
        for (const sb of result.sandboxes) {
          response.appendResponseLine(`| ${sb.name} | ${sb.os_type} | ${sb.status} | ${sb.source} | ${sb.created_at} |`);
        }
      }
    } catch (e: any) {
      response.appendResponseLine(`**Execution Error**: ${e.message}`);
    }
  },
});

export const cuaComputerUse = defineTool({
  name: 'cua_computer_use',
  description: 'Cua: Performs high-level interactions (click, type, move, scroll, drag, key) using the Cua driver.',
  annotations: {
    category: ToolCategory.CUA,
    readOnlyHint: false,
    reasoningCost: 60,
  },
  schema: {
    name: zod.string().describe('The name of the sandbox.'),
    action: zod.enum(['click', 'type', 'move', 'scroll', 'drag', 'key']).describe('Action to perform.'),
    params: zod.string().describe('JSON-encoded parameters for the action (e.g. {"x": 100, "y": 200}).'),
    local: zod.boolean().default(true).describe('Whether the sandbox is local.'),
  },
  handler: async (request, response) => {
    const args = ['computer_use', request.params.name, request.params.action, '--params', request.params.params];
    if (request.params.local) args.push('--local');

    try {
      const result = await runBridge(args);
      if (result.error) {
        response.appendResponseLine(`**Error**: ${result.error}`);
      } else {
        response.appendResponseLine(`Action ${result.action} executed successfully on ${request.params.name}.`);
      }
    } catch (e: any) {
      response.appendResponseLine(`**Execution Error**: ${e.message}`);
    }
  },
});
