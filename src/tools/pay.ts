/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import {zod} from '../third_party/index.js';
import * as child_process from 'child_process';
import {promisify} from 'util';
import {ToolCategory} from './categories.js';
import {defineTool} from './ToolDefinition.js';

const execFileAsync = promisify(child_process.execFile);

/**
 * Pay: Execute a fetch request wrapped by pay.sh for HTTP 402 support.
 */
export const payFetch = defineTool(() => {
  return {
    name: 'pay_fetch',
    description: 'Execute a fetch request wrapped by pay.sh for HTTP 402 support.',
    annotations: {
      category: ToolCategory.PAY,
      readOnlyHint: false,
      reasoningCost: 20,
    },
    schema: {
      url: zod.string().describe('URL to fetch'),
      method: zod.string().optional().describe('HTTP method (e.g. GET, POST)'),
      headers: zod.record(zod.string()).optional().describe('HTTP headers'),
      body: zod.string().optional().describe('Request body'),
      sandbox: zod.boolean().optional().describe('Run in sandbox mode'),
    },
    handler: async (request, response) => {
      const {url, method, headers, body, sandbox} = request.params;

      const args: string[] = [];
      if (sandbox) {
        args.push('--sandbox');
      }
      args.push('fetch');

      if (method && method.toUpperCase() !== 'GET') {
        args.push('-X', method);
      }

      if (headers) {
        for (const [key, value] of Object.entries(headers)) {
          args.push('-H', `${key}: ${value}`);
        }
      }

      if (body) {
        args.push('-d', body);
      }

      args.push(url);

      try {
        const {stdout, stderr} = await execFileAsync('pay', args);
        if (stdout) response.appendResponseLine(stdout);
        if (stderr) response.appendResponseLine(`STDERR: ${stderr}`);
      } catch (error: any) {
        response.appendResponseLine(`Execution Error: ${error.message}`);
        if (error.stdout) response.appendResponseLine(`STDOUT: ${error.stdout}`);
        if (error.stderr) response.appendResponseLine(`STDERR: ${error.stderr}`);
      }
    },
  };
});

/**
 * Pay: Execute arbitrary pay.sh CLI commands.
 */
export const payCli = defineTool(() => {
  return {
    name: 'pay_cli',
    description: 'Execute arbitrary pay.sh CLI commands (e.g., wallet, balance, etc).',
    annotations: {
      category: ToolCategory.PAY,
      readOnlyHint: false,
      reasoningCost: 20,
    },
    schema: {
      command: zod.array(zod.string()).describe('The command arguments to pass to pay.sh as an array of strings (e.g., ["wallet", "balance"])'),
      sandbox: zod.boolean().optional().describe('Run in sandbox mode'),
    },
    handler: async (request, response) => {
      const {command, sandbox} = request.params;

      const args: string[] = [];
      if (sandbox) {
        args.push('--sandbox');
      }
      args.push(...command);

      try {
        const {stdout, stderr} = await execFileAsync('pay', args);
        if (stdout) response.appendResponseLine(stdout);
        if (stderr) response.appendResponseLine(`STDERR: ${stderr}`);
      } catch (error: any) {
        response.appendResponseLine(`Execution Error: ${error.message}`);
        if (error.stdout) response.appendResponseLine(`STDOUT: ${error.stdout}`);
        if (error.stderr) response.appendResponseLine(`STDERR: ${error.stderr}`);
      }
    },
  };
});
