/**
 * @license
 * Copyright 2025 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import {spawn} from 'node:child_process';
import * as path from 'node:path';

import {zod} from '../third_party/index.js';
import {ToolCategory} from './categories.js';
import {definePageTool} from './ToolDefinition.js';

const CLI_PATH = path.resolve(process.cwd(), 'cathedral_cli.py');

/**
 * Invokes the Cathedral SecOps CLI.
 */
async function runSecOpsCli(args: string[]): Promise<string> {
  return new Promise((resolve, reject) => {
    const child = spawn('python3', [CLI_PATH, ...args]);
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
        reject(new Error(`CLI failed with code ${code}: ${stderr}`));
        return;
      }
      resolve(stdout);
    });

    child.on('error', (err) => {
      reject(err);
    });
  });
}

export const ebpfMonitorTraffic = definePageTool({
  name: 'ebpf_monitor_traffic',
  description: 'eBPF Sensor: Monitors network traffic and captures RED metrics.',
  annotations: {
    category: ToolCategory.ARKHE,
    readOnlyHint: true,
    reasoningCost: 30,
  },
  schema: {
    consent_id: zod.string().describe('Mandatory SecOps Consent ID.'),
    interface: zod.string().describe('Network interface to monitor (e.g., "eth0").'),
    duration: zod.number().default(60).describe('Monitoring duration in seconds.'),
  },
  handler: async (request, response) => {
    const {consent_id, interface: iface, duration} = request.params;
    try {
      const output = await runSecOpsCli([
        'ebpf',
        'monitor',
        '--consent-id',
        consent_id,
        '--interface',
        iface,
        '--duration',
        duration.toString(),
      ]);
      response.appendResponseLine(output);
    } catch (error: unknown) {
      response.appendResponseLine(`Error: ${error.message}`);
    }
  },
});

export const ebpfCheckReadiness = definePageTool({
  name: 'ebpf_check_readiness',
  description: 'eBPF Sensor: Performs Φ+ Hardening check to verify kernel compatibility.',
  annotations: {
    category: ToolCategory.ARKHE,
    readOnlyHint: true,
    reasoningCost: 20,
  },
  schema: {
    consent_id: zod.string().describe('Mandatory SecOps Consent ID.'),
  },
  handler: async (request, response) => {
    const {consent_id} = request.params;
    try {
      const output = await runSecOpsCli([
        'ebpf',
        'readiness',
        '--consent-id',
        consent_id,
      ]);
      response.appendResponseLine(output);
    } catch (error: unknown) {
      response.appendResponseLine(`Error: ${error.message}`);
    }
  },
});

export const ebpfRunBenchmark = definePageTool({
  name: 'ebpf_run_benchmark',
  description: 'eBPF Sensor: Executes Ω++ Grounding benchmark against distributed systems.',
  annotations: {
    category: ToolCategory.ARKHE,
    readOnlyHint: true,
    reasoningCost: 60,
  },
  schema: {
    consent_id: zod.string().describe('Mandatory SecOps Consent ID.'),
    benchmark_name: zod
      .enum(['distributed_consensus', 'microservices_network', 'tls_termination'])
      .default('distributed_consensus')
      .describe('Name of the benchmark to run.'),
  },
  handler: async (request, response) => {
    const {consent_id, benchmark_name} = request.params;
    try {
      const output = await runSecOpsCli([
        'ebpf',
        'benchmark',
        '--consent-id',
        consent_id,
        '--benchmark-name',
        benchmark_name,
      ]);
      response.appendResponseLine(output);
    } catch (error: unknown) {
      response.appendResponseLine(`Error: ${error.message}`);
    }
  },
});

export const ebpfLoadProgram = definePageTool({
  name: 'ebpf_load_program',
  description: 'eBPF Sensor: Simulates loading an eBPF ELF program into the kernel.',
  annotations: {
    category: ToolCategory.ARKHE,
    readOnlyHint: false,
    reasoningCost: 50,
  },
  schema: {
    consent_id: zod.string().describe('Mandatory SecOps Consent ID.'),
    elf_path: zod.string().describe('Path to the eBPF ELF object file.'),
  },
  handler: async (request, response) => {
    const {consent_id, elf_path} = request.params;
    try {
      const output = await runSecOpsCli([
        'ebpf',
        'load',
        '--consent-id',
        consent_id,
        '--elf-path',
        elf_path,
      ]);
      response.appendResponseLine(output);
    } catch (error: unknown) {
      response.appendResponseLine(`Error: ${error.message}`);
    }
  },
});

export const ebpfVerifyIntegrity = definePageTool({
  name: 'ebpf_verify_integrity',
  description: 'eBPF Sensor: Generates a ZK-proof for a batch of monitored kernel events.',
  annotations: {
    category: ToolCategory.ARKHE,
    readOnlyHint: true,
    reasoningCost: 100,
  },
  schema: {
    consent_id: zod.string().describe('Mandatory SecOps Consent ID.'),
    batch_id: zod.string().describe('Identifier for the event batch.'),
  },
  handler: async (request, response) => {
    const {consent_id, batch_id} = request.params;
    try {
      const output = await runSecOpsCli([
        'ebpf',
        'verify',
        '--consent-id',
        consent_id,
        '--batch-id',
        batch_id,
      ]);
      response.appendResponseLine(output);
    } catch (error: unknown) {
      response.appendResponseLine(`Error: ${error.message}`);
    }
  },
});
