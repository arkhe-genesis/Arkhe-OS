/**
 * @license
 * Copyright 2025 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import {spawn} from 'node:child_process';

import {zod} from '../third_party/index.js';

import {ToolCategory} from './categories.js';
import {defineTool} from './ToolDefinition.js';

async function runGitNexus(args: string[]): Promise<{stdout: string; stderr: string; code: number | null}> {
  return new Promise((resolve) => {
    // In production, we'd use the local installation or a specific version.
    // npx -y ensures it runs without prompt.
    const child = spawn('npx', ['-y', 'gitnexus@latest', ...args]);
    let stdout = '';
    let stderr = '';

    child.stdout.on('data', (data) => {
      stdout += data.toString();
    });

    child.stderr.on('data', (data) => {
      stderr += data.toString();
    });

    child.on('close', (code) => {
      resolve({stdout, stderr, code});
    });
  });
}

export const gitnexusListRepos = defineTool({
  name: 'gitnexus_list_repos',
  description: 'GitNexus: Discover all indexed repositories and their status.',
  annotations: {
    category: ToolCategory.GITNEXUS,
    readOnlyHint: true,
    reasoningCost: 10,
  },
  schema: {},
  handler: async (_request, response) => {
    const {stdout, stderr, code} = await runGitNexus(['list']);
    if (stdout) {response.appendResponseLine(stdout);}
    if (code !== 0 && stderr) {response.appendResponseLine(`Error: ${stderr}`);}
  },
});

export const gitnexusAnalyze = defineTool({
  name: 'gitnexus_analyze',
  description: 'GitNexus: Index a repository (full analysis) to build a knowledge graph.',
  annotations: {
    category: ToolCategory.GITNEXUS,
    readOnlyHint: false,
    reasoningCost: 100,
  },
  schema: {
    path: zod.string().optional().describe('Path to the repository to index (default: current directory).'),
    force: zod.boolean().default(false).describe('Force full re-index.'),
  },
  handler: async (request, response) => {
    response.appendResponseLine('### GitNexus: Analyzing Repository');
    const args = ['analyze'];
    if (request.params.path) {args.push(request.params.path);}
    if (request.params.force) {args.push('--force');}

    const {stdout, stderr, code} = await runGitNexus(args);

    if (stdout) {
      response.appendResponseLine('```');
      response.appendResponseLine(stdout);
      response.appendResponseLine('```');
    }

    if (code === 0) {
      response.appendResponseLine('\n**Success**: Repository indexed and registered.');
    } else {
      response.appendResponseLine(`\n**Error**: Analysis failed (Code ${code}).`);
      if (stderr) {response.appendResponseLine(`\`\`\`\n${stderr}\n\`\`\``);}
    }
  },
});

export const gitnexusQuery = defineTool({
  name: 'gitnexus_query',
  description: 'GitNexus: Search the knowledge graph for execution flows related to a concept.',
  annotations: {
    category: ToolCategory.GITNEXUS,
    readOnlyHint: true,
    reasoningCost: 30,
  },
  schema: {
    query: zod.string().describe('Search query for the knowledge graph.'),
    repo: zod.string().optional().describe('Target repository name.'),
    limit: zod.number().default(5).describe('Max processes to return.'),
  },
  handler: async (request, response) => {
    const args = ['query', request.params.query];
    if (request.params.repo) {
      args.push('--repo', request.params.repo);
    }
    args.push('--limit', request.params.limit.toString());

    const {stdout, stderr, code} = await runGitNexus(args);

    if (stdout) {
      response.appendResponseLine(stdout);
    }

    if (code !== 0 && stderr) {
      response.appendResponseLine(`\n**Error**: Query failed (Code ${code}).`);
      response.appendResponseLine(`\`\`\`\n${stderr}\n\`\`\``);
    }
  },
});

export const gitnexusContext = defineTool({
  name: 'gitnexus_context',
  description: 'GitNexus: 360-degree view of a code symbol: callers, callees, processes.',
  annotations: {
    category: ToolCategory.GITNEXUS,
    readOnlyHint: true,
    reasoningCost: 20,
  },
  schema: {
    name: zod.string().describe('The name of the symbol to inspect.'),
    repo: zod.string().optional().describe('Target repository name.'),
  },
  handler: async (request, response) => {
    const args = ['context', request.params.name];
    if (request.params.repo) {
      args.push('--repo', request.params.repo);
    }

    const {stdout, stderr, code} = await runGitNexus(args);

    if (stdout) {
      response.appendResponseLine(stdout);
    }

    if (code !== 0 && stderr) {
      response.appendResponseLine(`\n**Error**: Context retrieval failed (Code ${code}).`);
      response.appendResponseLine(`\`\`\`\n${stderr}\n\`\`\``);
    }
  },
});

export const gitnexusImpact = defineTool({
  name: 'gitnexus_impact',
  description: 'GitNexus: Blast radius analysis: what breaks if you change a symbol.',
  annotations: {
    category: ToolCategory.GITNEXUS,
    readOnlyHint: true,
    reasoningCost: 40,
  },
  schema: {
    target: zod.string().describe('The symbol to analyze for impact.'),
    repo: zod.string().optional().describe('Target repository name.'),
  },
  handler: async (request, response) => {
    const args = ['impact', request.params.target];
    if (request.params.repo) {
      args.push('--repo', request.params.repo);
    }

    const {stdout, stderr, code} = await runGitNexus(args);

    if (stdout) {
      response.appendResponseLine(stdout);
    }

    if (code !== 0 && stderr) {
      response.appendResponseLine(`\n**Error**: Impact analysis failed (Code ${code}).`);
      response.appendResponseLine(`\`\`\`\n${stderr}\n\`\`\``);
    }
  },
});

export const gitnexusDetectChanges = defineTool({
  name: 'gitnexus_detect_changes',
  description: 'GitNexus: Map git diff hunks to indexed symbols and affected execution flows.',
  annotations: {
    category: ToolCategory.GITNEXUS,
    readOnlyHint: true,
    reasoningCost: 30,
  },
  schema: {
    repo: zod.string().optional().describe('Target repository name.'),
  },
  handler: async (request, response) => {
    const args = ['detect_changes'];
    if (request.params.repo) {
      args.push('--repo', request.params.repo);
    }

    const {stdout, stderr, code} = await runGitNexus(args);
    if (stdout) {response.appendResponseLine(stdout);}
    if (code !== 0 && stderr) {response.appendResponseLine(`Error: ${stderr}`);}
  },
});

export const gitnexusRename = defineTool({
  name: 'gitnexus_rename',
  description: 'GitNexus: Multi-file coordinated rename with graph + text search.',
  annotations: {
    category: ToolCategory.GITNEXUS,
    readOnlyHint: false,
    reasoningCost: 80,
  },
  schema: {
    symbol_name: zod.string().describe('Original symbol name.'),
    new_name: zod.string().describe('New name for the symbol.'),
    dry_run: zod.boolean().default(true).describe('Preview changes without applying.'),
    repo: zod.string().optional().describe('Target repository name.'),
  },
  handler: async (request, response) => {
    const args = ['rename', request.params.symbol_name, request.params.new_name];
    if (request.params.dry_run) {args.push('--dry-run');}
    if (request.params.repo) {args.push('--repo', request.params.repo);}

    const {stdout, stderr, code} = await runGitNexus(args);
    if (stdout) {response.appendResponseLine(stdout);}
    if (code !== 0 && stderr) {response.appendResponseLine(`Error: ${stderr}`);}
  },
});

export const gitnexusCypher = defineTool({
  name: 'gitnexus_cypher',
  description: 'GitNexus: Execute raw Cypher query against the knowledge graph.',
  annotations: {
    category: ToolCategory.GITNEXUS,
    readOnlyHint: true,
    reasoningCost: 50,
  },
  schema: {
    query: zod.string().describe('The Cypher query string.'),
    repo: zod.string().optional().describe('Target repository name.'),
  },
  handler: async (request, response) => {
    const args = ['cypher', request.params.query];
    if (request.params.repo) {args.push('--repo', request.params.repo);}

    const {stdout, stderr, code} = await runGitNexus(args);
    if (stdout) {response.appendResponseLine(stdout);}
    if (code !== 0 && stderr) {response.appendResponseLine(`Error: ${stderr}`);}
  },
});
