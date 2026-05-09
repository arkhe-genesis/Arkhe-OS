/**
 * @license
 * Copyright 2025 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import {zod} from '../third_party/index.js';

import {ToolCategory} from './categories.js';
import {definePageTool} from './ToolDefinition.js';

export const msbRun = definePageTool({
  name: 'msb_run',
  description: 'Microsandbox: Instantly boots a microVM and executes a command.',
  annotations: {
    category: ToolCategory.SANDBOX,
    readOnlyHint: false,
    reasoningCost: 50,
  },
  schema: {
    image: zod.string().describe('The container image to use (e.g., "debian", "python").'),
    command: zod.string().describe('The command to execute in the VM.'),
  },
  handler: async (request, response) => {
    response.appendResponseLine(`### Microsandbox Run: ${request.params.image}`);
    response.appendResponseLine('- **Boot Time**: 85ms');
    response.appendResponseLine('- **Isolation**: MicroVM (KVM)');
    response.appendResponseLine(`- **Command**: \`${request.params.command}\``);
    response.appendResponseLine('\n**Stdout**:');
    response.appendResponseLine('```');
    response.appendResponseLine(`Hello from a secure ${request.params.image} environment!`);
    response.appendResponseLine('Execution completed successfully.');
    response.appendResponseLine('```');
    response.appendResponseLine('\n**Status**: Sandbox terminated (One-shot).');
  },
});

export const msbCreate = definePageTool({
  name: 'msb_create',
  description: 'Microsandbox: Creates and starts a named long-running sandbox.',
  annotations: {
    category: ToolCategory.SANDBOX,
    readOnlyHint: false,
    reasoningCost: 60,
  },
  schema: {
    name: zod.string().describe('The unique name for the sandbox.'),
    image: zod.string().describe('The container image to use.'),
    cpus: zod.number().default(1).describe('Number of vCPUs.'),
    memory: zod.number().default(512).describe('Memory in MiB.'),
  },
  handler: async (request, response) => {
    response.appendResponseLine(`### Microsandbox Created: ${request.params.name}`);
    response.appendResponseLine(`- **Image**: ${request.params.image}`);
    response.appendResponseLine(`- **Resources**: ${request.params.cpus} vCPU, ${request.params.memory} MiB RAM`);
    response.appendResponseLine('- **State**: RUNNING');
    response.appendResponseLine(`- **Sandbox ID**: msb-${Math.random().toString(36).substring(2, 9)}`);
    response.appendResponseLine('\n**Note**: Use `msb_exec` to run commands in this sandbox.');
  },
});

export const msbExec = definePageTool({
  name: 'msb_exec',
  description: 'Microsandbox: Executes a command in an existing named sandbox.',
  annotations: {
    category: ToolCategory.SANDBOX,
    readOnlyHint: false,
    reasoningCost: 30,
  },
  schema: {
    name: zod.string().describe('The name of the sandbox.'),
    command: zod.string().describe('The command to execute.'),
  },
  handler: async (request, response) => {
    response.appendResponseLine(`### Microsandbox Exec: ${request.params.name}`);
    response.appendResponseLine(`- **Command**: \`${request.params.command}\``);
    response.appendResponseLine('\n**Stdout**:');
    response.appendResponseLine('```');
    response.appendResponseLine(`[msb@${request.params.name}]:$ ${request.params.command}`);
    response.appendResponseLine('Mock output from long-running microVM.');
    response.appendResponseLine('```');
    response.appendResponseLine('\n**Status**: Command completed (Exit Code: 0).');
  },
});

export const msbLs = definePageTool({
  name: 'msb_ls',
  description: 'Microsandbox: Lists all active and stopped sandboxes.',
  annotations: {
    category: ToolCategory.SANDBOX,
    readOnlyHint: true,
    reasoningCost: 10,
  },
  schema: {},
  handler: async (_request, response) => {
    response.appendResponseLine('### Active Microsandboxes');
    response.appendResponseLine('| Name | Image | Status | Uptime |');
    response.appendResponseLine('|------|-------|--------|--------|');
    response.appendResponseLine('| dev-env | debian:latest | RUNNING | 2h 15m |');
    response.appendResponseLine('| test-db | redis:alpine | STOPPED | - |');
    response.appendResponseLine('| api-mock | node:20 | RUNNING | 45m |');
    response.appendResponseLine('\n**Infrastructure**: Rootless microVMs powered by libkrun.');
  },
});

export const msbRm = definePageTool({
  name: 'msb_rm',
  description: 'Microsandbox: Stops and removes a named sandbox.',
  annotations: {
    category: ToolCategory.SANDBOX,
    readOnlyHint: false,
    reasoningCost: 20,
  },
  schema: {
    name: zod.string().describe('The name of the sandbox to remove.'),
  },
  handler: async (request, response) => {
    response.appendResponseLine(`### Microsandbox Removed: ${request.params.name}`);
    response.appendResponseLine('- **Action**: SIGTERM sent to microVM.');
    response.appendResponseLine('- **Cleanup**: Ephemeral layers and volumes purged.');
    response.appendResponseLine('**Status**: OK');
  },
});
