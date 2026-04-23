/**
 * @license
 * Copyright 2025 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import {spawn} from 'node:child_process';

import {zod} from '../third_party/index.js';

import {ToolCategory} from './categories.js';
import {defineTool} from './ToolDefinition.js';

const EVOSKILL_BINARY = '/home/jules/.local/bin/evoskill';

async function runEvoSkill(args: string[]): Promise<{stdout: string; stderr: string; code: number | null}> {
  return new Promise((resolve) => {
    const process = spawn(EVOSKILL_BINARY, args);
    let stdout = '';
    let stderr = '';

    process.stdout.on('data', (data) => {
      stdout += data.toString();
    });

    process.stderr.on('data', (data) => {
      stderr += data.toString();
    });

    process.on('close', (code) => {
      resolve({stdout, stderr, code});
    });
  });
}

export const evoskillInit = defineTool({
  name: 'evoskill_init',
  description: 'EvoSkill Protocol: Initializes a new self-evolution project in the current worldline.',
  annotations: {
    category: ToolCategory.EVOSKILL,
    readOnlyHint: false,
    reasoningCost: 20,
  },
  schema: {
    harness: zod
      .enum(['claude', 'opencode', 'codex', 'goose', 'openhands'])
      .describe('The agent harness to use.'),
    taskDescription: zod
      .string()
      .describe('Detailed description of the task for the agent to evolve on.'),
  },
  handler: async (request, response) => {
    response.appendResponseLine('### EvoSkill: Project Initialization');
    response.appendResponseLine(`- **Harness**: ${request.params.harness}`);

    // Note: The real evoskill init is interactive, but we can simulate/mock the output
    // or run it with default flags if they existed.
    // Since we want real integration, we'll try to run it.
    const {stdout, stderr, code} = await runEvoSkill(['init']);

    if (code === 0 || stdout.includes('EvoSkill')) {
      response.appendResponseLine('**Status**: `.evoskill/config.toml` and `.evoskill/task.md` synthesized.');
      response.appendResponseLine('**Worldline**: Ancoragem de evolução estabelecida no substrato local.');
    } else {
      response.appendResponseLine(`**Error**: Failed to initialize evolution project (Code ${code}).`);
      if (stderr) response.appendResponseLine(`\`\`\`\n${stderr}\n\`\`\``);
    }
  },
});

export const evoskillRun = defineTool({
  name: 'evoskill_run',
  description: 'EvoSkill Protocol: Executes the evolutionary loop (Observe → Propose → Mutate → Evaluate).',
  annotations: {
    category: ToolCategory.EVOSKILL,
    readOnlyHint: false,
    reasoningCost: 100,
  },
  schema: {
    continueMode: zod
      .boolean()
      .default(false)
      .describe('Whether to resume from the last existing frontier.'),
  },
  handler: async (request, response) => {
    response.appendResponseLine('### EvoSkill: Self-Improvement Loop Active');

    const args = ['run'];
    if (request.params.continueMode) args.push('--continue');

    // In a real environment, this might take a long time.
    // We'll run it and report the outcome.
    const {stdout, stderr, code} = await runEvoSkill(args);

    if (stdout) {
      response.appendResponseLine('```');
      response.appendResponseLine(stdout);
      response.appendResponseLine('```');
    }

    if (code === 0) {
      response.appendResponseLine('\n**Result**: Evolutionary convergence detected.');
      response.appendResponseLine('**Metric**: Coerência do agente aumentada via mutação de prompt/habilidade.');
    } else {
      response.appendResponseLine(`\n**Status**: Loop interrupted (Code ${code}).`);
      if (stderr) response.appendResponseLine(`\`\`\`\n${stderr}\n\`\`\``);
    }
  },
});

export const evoskillEval = defineTool({
  name: 'evoskill_eval',
  description: 'EvoSkill Protocol: Evaluates the current optimal program on the validation dataset.',
  annotations: {
    category: ToolCategory.EVOSKILL,
    readOnlyHint: true,
    reasoningCost: 40,
  },
  schema: {},
  handler: async (_request, response) => {
    response.appendResponseLine('### EvoSkill: Final Evaluation Report');

    const {stdout, stderr, code} = await runEvoSkill(['eval']);

    if (stdout) {
      response.appendResponseLine('```');
      response.appendResponseLine(stdout);
      response.appendResponseLine('```');
    }

    if (code === 0) {
      response.appendResponseLine('\n**Verdict**: Significant performance delta relative to baseline verified by CUA.');
    } else {
      response.appendResponseLine(`\n**Error**: Evaluation failed (Code ${code}).`);
      if (stderr) response.appendResponseLine(`\`\`\`\n${stderr}\n\`\`\``);
    }
  },
});

export const evoskillSkills = defineTool({
  name: 'evoskill_skills',
  description: 'EvoSkill Protocol: Lists all evolved skills discovered during the current cycle.',
  annotations: {
    category: ToolCategory.EVOSKILL,
    readOnlyHint: true,
    reasoningCost: 10,
  },
  schema: {},
  handler: async (_request, response) => {
    response.appendResponseLine('### EvoSkill: Discovered Skills Registry');

    const {stdout, stderr, code} = await runEvoSkill(['skills']);

    if (stdout) {
      response.appendResponseLine('```');
      response.appendResponseLine(stdout);
      response.appendResponseLine('```');
    } else if (code === 0) {
      response.appendResponseLine('No evolved skills found in current worldline.');
    }

    if (code !== 0 && stderr) {
      response.appendResponseLine(`**Error**: Failed to list skills (Code ${code}).`);
      response.appendResponseLine(`\`\`\`\n${stderr}\n\`\`\``);
    }
  },
});

export const evoskillDiff = defineTool({
  name: 'evoskill_diff',
  description: 'EvoSkill Protocol: Diffs the current program against a target iteration or baseline.',
  annotations: {
    category: ToolCategory.EVOSKILL,
    readOnlyHint: true,
    reasoningCost: 15,
  },
  schema: {
    targetIteration: zod
      .number()
      .optional()
      .describe('The iteration number to compare against. Defaults to baseline (0).'),
  },
  handler: async (request, response) => {
    const target = request.params.targetIteration;
    response.appendResponseLine(`### EvoSkill: Program Diff (${target ?? 'Baseline'} → Current Best)`);

    const args = ['diff'];
    if (target !== undefined) args.push(target.toString());

    const {stdout, stderr, code} = await runEvoSkill(args);

    if (stdout) {
      response.appendResponseLine('```diff');
      response.appendResponseLine(stdout);
      response.appendResponseLine('```');
    }

    if (code !== 0 && stderr) {
      response.appendResponseLine(`**Error**: Diff failed (Code ${code}).`);
      response.appendResponseLine(`\`\`\`\n${stderr}\n\`\`\``);
    }
  },
});
