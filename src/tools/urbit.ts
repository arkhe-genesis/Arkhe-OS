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

async function runUrbitAction(args: string[]): Promise<{stdout: string; stderr: string; code: number | null}> {
  const skillDir = path.resolve(process.cwd(), 'skills/urbit');

  return new Promise((resolve) => {
    // Assuming a simple interaction with the urbit repo via make or similar,
    // since the prompt implies integration as a skill/MCP server but there's no pre-defined scripts.
    // For now we'll just run "make" in the urbit repo as a demonstration of an action.
    const childProcess = spawn('make', args, {
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

export const urbitMake = defineTool({
  name: 'urbit_make',
  description: 'Run make commands in the Urbit repository.',
  annotations: {
    category: ToolCategory.URBIT,
    readOnlyHint: true,
  },
  schema: {
    target: zod.string().default('').describe('The make target to run (e.g., "build", "test", or leave empty for default).'),
  },
  handler: async (request, response) => {
    response.appendResponseLine('### Urbit Make Action');

    const args = request.params.target ? [request.params.target] : [];

    const {stdout, stderr, code} = await runUrbitAction(args);

    if (stdout) {
      response.appendResponseLine('\n' + stdout);
    }

    if (code !== 0) {
      response.appendResponseLine(`\n**Error**: Urbit make failed (Code ${code}).`);
      if (stderr) {
        response.appendResponseLine(`\`\`\`\n${stderr}\n\`\`\``);
      }
    } else if (stderr) {
      response.appendResponseLine('\n<details><summary>Diagnostics</summary>\n\n```\n' + stderr + '\n```\n</details>');
    }
  },
});
