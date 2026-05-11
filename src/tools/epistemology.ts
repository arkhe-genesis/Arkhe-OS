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

async function runEpistemology(
  mode: 'psa' | 'pefm' | 'diamond',
  input: any,
): Promise<string> {
  return new Promise((resolve, reject) => {
    // We'll create a bridge script to call the Python logic
    const scriptPath = path.resolve(process.cwd(), 'scripts', 'epistemic_bridge.py');
    const pythonProcess = spawn('python3', [
      scriptPath,
      '--mode',
      mode,
      '--input',
      JSON.stringify(input),
    ], {
      env: {
        ...process.env,
        PYTHONPATH: process.cwd(),
      }
    });
    let stdout = '';
    let stderr = '';

    pythonProcess.stdout.on('data', (data) => {
      stdout += data.toString();
    });

    pythonProcess.stderr.on('data', (data) => {
      stderr += data.toString();
    });

    pythonProcess.on('close', (code) => {
      if (code === 0) {
        resolve(stdout);
      } else {
        reject(new Error(`Epistemology bridge failed (code ${code}): ${stderr}`));
      }
    });
  });
}

export const psaEvaluate = defineTool({
  name: 'psa_evaluate',
  description: 'PSA v2.1: Deterministic Predicted Safety Analysis of a semantic graph.',
  annotations: {
    category: ToolCategory.EPISTEMOLOGY,
    readOnlyHint: true,
    reasoningCost: 40,
  },
  schema: {
    claims: zod.array(zod.object({
      id: zod.number(),
      text: zod.string(),
    })).describe('List of claims in the artifact.'),
    edges: zod.array(zod.object({
      src: zod.number(),
      dst: zod.number(),
      relation: zod.enum(['entails', 'contradicts', 'references']),
    })).describe('Relations between claims.'),
    domain: zod.string().default('general').describe('The knowledge domain.'),
  },
  handler: async (request, response) => {
    try {
      const result = await runEpistemology('psa', request.params);
      response.appendResponseLine('### PSA v2.1 Evaluation Result');
      response.appendResponseLine(result);
    } catch (err) {
      response.appendResponseLine(`**Error**: PSA evaluation failed: ${err}`);
    }
  },
});

export const pefmPredict = defineTool({
  name: 'pefm_predict',
  description: 'PEFM v1.0: Anticipate epistemic failure probability from enriched PSA features.',
  annotations: {
    category: ToolCategory.EPISTEMOLOGY,
    readOnlyHint: true,
    reasoningCost: 60,
  },
  schema: {
    artifact_id: zod.string().describe('ID of the artifact to evaluate.'),
    claims: zod.array(zod.object({
      id: zod.number(),
      text: zod.string(),
    })),
    edges: zod.array(zod.object({
      src: zod.number(),
      dst: zod.number(),
      relation: zod.enum(['entails', 'contradicts', 'references']),
    })),
    domain: zod.string().default('general'),
  },
  handler: async (request, response) => {
    try {
      const result = await runEpistemology('pefm', request.params);
      response.appendResponseLine('### PEFM v1.0 Prediction Report');
      response.appendResponseLine(result);
    } catch (err) {
      response.appendResponseLine(`**Error**: PEFM prediction failed: ${err}`);
    }
  },
});

export const diamondPipeline = defineTool({
  name: 'diamond_pipeline',
  description: 'Diamond Pipeline: Multi-stage hallucination reduction (Diverge -> Filter -> Converge).',
  annotations: {
    category: ToolCategory.EPISTEMOLOGY,
    readOnlyHint: false,
    reasoningCost: 150,
  },
  schema: {
    prompt: zod.string().describe('The intention/prompt to process.'),
    iterations: zod.number().default(3).describe('Number of candidates to generate.'),
  },
  handler: async (request, response) => {
    try {
      response.appendResponseLine('### Diamond Pipeline Initiated');
      response.appendResponseLine('1. **Divergence**: Generating candidate intentions...');
      const result = await runEpistemology('diamond', request.params);
      response.appendResponseLine(result);
    } catch (err) {
      response.appendResponseLine(`**Error**: Diamond pipeline failed: ${err}`);
    }
  },
});
