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

async function runFortytwoQuery(args: string[]): Promise<{stdout: string; stderr: string; code: number | null}> {
  const skillDir = path.resolve(process.cwd(), 'skills/fortytwo-mcp');
  const scriptPath = path.join(skillDir, 'scripts/fortytwo_query.py');

  return new Promise((resolve) => {
    const childProcess = spawn('python3', [scriptPath, ...args], {
      cwd: skillDir,
      env: {...process.env}
    });
    let stdout = '';
    let stderr = '';

    childProcess.stdout.on('data', (data: Buffer) => {
      stdout += data.toString();
    });

    childProcess.stderr.on('data', (data: Buffer) => {
      stderr += data.toString();
    });

    childProcess.on('close', (code: number | null) => {
      resolve({stdout, stderr, code});
    });
  });
}

export const askFortytwoPrime = defineTool({
  name: 'ask_fortytwo_prime',
  description: 'Fortytwo Prime: collective multi-agent inference for high-stakes questions. ALWAYs use when the user says "Ask Fortytwo", "Ask Prime", or calls ask_fortytwo_prime.',
  annotations: {
    category: ToolCategory.FORTYTWO,
    readOnlyHint: true,
    reasoningCost: 100,
  },
  schema: {
    question: zod.string().describe('The question to ask Fortytwo Prime.'),
    network: zod.enum(['base', 'monad']).default('base').describe('The network to use for payment.'),
    noSession: zod.boolean().default(false).describe('Force a new payment and session.'),
  },
  handler: async (request, response) => {
    response.appendResponseLine('### Fortytwo Prime Collective Inference');
    response.appendResponseLine(`> *Query: "${request.params.question}"*`);

    const args = [request.params.question, '--network', request.params.network];
    if (request.params.noSession) {
      args.push('--no-session');
    }

    const {stdout, stderr, code} = await runFortytwoQuery(args);

    if (stdout) {
      response.appendResponseLine('\n' + stdout);
    }

    if (code !== 0) {
      response.appendResponseLine(`\n**Error**: Fortytwo query failed (Code ${code}).`);
      if (stderr) {
        response.appendResponseLine(`\`\`\`\n${stderr}\n\`\`\``);
      }
    } else if (stderr) {
      // Log diagnostics as a details block if they are verbose
      response.appendResponseLine('\n<details><summary>Diagnostics</summary>\n\n```\n' + stderr + '\n```\n</details>');
    }
  },
});
