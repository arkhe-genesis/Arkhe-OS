
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { X, Network, Server, Cpu, Activity, Database, Zap, ArrowRight, CheckCircle2 } from 'lucide-react';
import { motion } from 'motion/react';
import React, { useState } from 'react';

import { logger } from '../../server/logger';
import type { SimulationState } from '../../server/types';

interface ClusterOrchestrationPanelProps {
  onClose: () => void;
  cluster: SimulationState['cluster'];
}

export default function ClusterOrchestrationPanel({ onClose, cluster }: ClusterOrchestrationPanelProps) {
  const [activeTab, setActiveTab] = useState<'nccl' | 'qhttp' | 'logs'>('nccl');

  const startDeployment = async () => {
    try {
      await fetch('/api/cluster/deploy', { method: 'POST' });
    } catch (error) {
      logger.error('Failed to start deployment: ' + error);
    }
  };

  const isDeploying = cluster.status === 'deploying';
  const deployProgress = cluster.progress;
  const deployLogs = cluster.logs;

  React.useEffect(() => {
    if (isDeploying) {
      setActiveTab('logs');
    }
  }, [isDeploying]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/90 backdrop-blur-md">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="bg-[#0a0a0c] border border-emerald-500/30 rounded-xl w-full max-w-6xl overflow-hidden flex flex-col h-[85vh] shadow-[0_0_40px_rgba(16,185,129,0.15)]"
      >
        {/* Header */}
        <div className="p-4 border-b border-emerald-500/20 bg-emerald-500/5 flex justify-between items-center shrink-0">
          <div className="flex items-center gap-3">
            <Network className="w-5 h-5 text-emerald-400" />
            <h2 className="font-mono text-sm uppercase tracking-widest text-emerald-400 font-bold">
              Layer 13: Cluster Orchestration & Scaling
            </h2>
            <span className="px-2 py-0.5 text-[10px] font-mono rounded border bg-emerald-500/20 text-emerald-400 border-emerald-500/30">
              MULTI-GPU / QHTTP
            </span>
          </div>
          <button onClick={onClose} className="text-arkhe-muted hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="flex flex-1 overflow-hidden">
          {/* Sidebar */}
          <div className="w-64 border-r border-emerald-500/20 bg-[#0d0e12] p-4 flex flex-col shrink-0">
            <div className="text-[10px] font-mono text-emerald-400/50 uppercase tracking-widest mb-4">Infrastructure Vectors</div>

            <div className="space-y-2">
              <button
                onClick={() => setActiveTab('nccl')}
                className={`w-full flex items-center gap-3 px-3 py-3 rounded text-xs font-mono transition-colors text-left ${activeTab === 'nccl' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'text-arkhe-muted hover:bg-[#1f2024] hover:text-arkhe-text border border-transparent'}`}
              >
                <Cpu className="w-4 h-4 shrink-0" />
                <div>
                  <div className="font-bold">NCCL Topology</div>
                  <div className="text-[9px] opacity-70 mt-0.5">Multi-GPU Synchronization</div>
                </div>
              </button>

              <button
                onClick={() => setActiveTab('qhttp')}
                className={`w-full flex items-center gap-3 px-3 py-3 rounded text-xs font-mono transition-colors text-left ${activeTab === 'qhttp' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'text-arkhe-muted hover:bg-[#1f2024] hover:text-arkhe-text border border-transparent'}`}
              >
                <Activity className="w-4 h-4 shrink-0" />
                <div>
                  <div className="font-bold">qhttp:// Protocol</div>
                  <div className="text-[9px] opacity-70 mt-0.5">gRPC Telemetry & Injection</div>
                </div>
              </button>

              {cluster.logs.length > 0 && (
                <button
                  onClick={() => setActiveTab('logs')}
                  className={`w-full flex items-center gap-3 px-3 py-3 rounded text-xs font-mono transition-colors text-left ${activeTab === 'logs' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'text-arkhe-muted hover:bg-[#1f2024] hover:text-arkhe-text border border-transparent'}`}
                >
                  <Server className="w-4 h-4 shrink-0" />
                  <div>
                    <div className="font-bold">Deployment Logs</div>
                    <div className="text-[9px] opacity-70 mt-0.5">Cluster Provisioning Output</div>
                  </div>
                </button>
              )}
            </div>

            <div className="mt-auto pt-4 border-t border-emerald-500/20">
              <button
                onClick={startDeployment}
                disabled={isDeploying || cluster.status === 'resonant'}
                className={`w-full py-3 rounded font-mono text-xs font-bold uppercase tracking-widest transition-all flex items-center justify-center gap-2 ${
                  isDeploying || cluster.status === 'resonant'
                    ? 'bg-[#111214] text-arkhe-muted border border-arkhe-border cursor-not-allowed'
                    : 'bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400 border border-emerald-500/50 shadow-[0_0_15px_rgba(16,185,129,0.2)]'
                }`}
              >
                {isDeploying ? <Activity className="w-4 h-4 animate-spin" /> : cluster.status === 'resonant' ? <CheckCircle2 className="w-4 h-4" /> : <Zap className="w-4 h-4" />}
                {isDeploying ? 'Deploying...' : cluster.status === 'resonant' ? 'Cluster Resonant' : 'Deploy Cluster'}
              </button>
            </div>
          </div>

          {/* Main Content */}
          <div className="flex-1 flex flex-col bg-[#0a0a0c] overflow-hidden">
            {isDeploying ? (
              <div className="flex-1 p-6 flex flex-col">
                <h3 className="font-mono text-sm text-emerald-400 uppercase tracking-widest mb-4 flex items-center gap-2">
                  <Server className="w-4 h-4" /> Deployment Pipeline
                </h3>

                <div className="mb-6">
                  <div className="flex justify-between text-[10px] font-mono text-arkhe-muted mb-2">
                    <span>Cluster Provisioning</span>
                    <span>{Math.round(deployProgress)}%</span>
                  </div>
                  <div className="h-2 bg-black rounded-full overflow-hidden border border-arkhe-border">
                    <div
                      className="h-full bg-emerald-500 transition-all duration-500 ease-out"
                      style={{ width: `${deployProgress}%` }}
                    ></div>
                  </div>
                </div>

                <div className="flex-1 bg-black border border-[#1f2024] rounded-xl p-4 font-mono text-xs overflow-y-auto custom-scrollbar space-y-2">
                  {deployLogs.map((log, i) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      className={log.includes('complete') ? 'text-emerald-400 font-bold' : 'text-arkhe-muted'}
                    >
                      <span className="text-emerald-500/50 mr-2">❯</span> {log}
                    </motion.div>
                  ))}
                  {isDeploying && (
                    <motion.div
                      animate={{ opacity: [1, 0] }}
                      transition={{ repeat: Infinity, duration: 0.8 }}
                      className="text-emerald-400"
                    >
                      _
                    </motion.div>
                  )}
                </div>
              </div>
            ) : (
              <div className="flex-1 p-6 overflow-y-auto custom-scrollbar">
                {activeTab === 'nccl' && (
                  <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
                    <div>
                      <h3 className="text-lg font-mono text-emerald-400 uppercase tracking-widest mb-2">Multi-GPU Synchronization (NCCL)</h3>
                      <p className="text-sm font-mono text-arkhe-muted leading-relaxed">
                        Para modelos massivos (LLaMA 70B, DeepSeek) distribuídos via Tensor Parallelism, a norma $\rho_1$ deve ser calculada globalmente para manter a coerência A-5'. O wrapper NCCL realiza um <code className="text-emerald-300 bg-emerald-500/10 px-1 rounded">all_reduce</code> da massa semântica através do barramento NVLink antes de invocar o kernel CUDA.
                      </p>
                    </div>

                    <div className="bg-[#111214] border border-arkhe-border rounded-xl overflow-hidden">
                      <div className="bg-[#1a1b20] px-4 py-2 border-b border-arkhe-border text-[10px] font-mono text-arkhe-muted flex justify-between">
                        <span>tzinor/layer12/distributed_sync.py</span>
                        <span>Python / PyTorch</span>
                      </div>
                      <pre className="p-4 text-xs font-mono text-arkhe-text overflow-x-auto">
{`import torch
import torch.distributed as dist
import arkhe_cuda

def compute_distributed_resonance(base_loss, local_param_tensor, rho_2, k1, k2, lam, rho_eq):
    """
    Calcula a ressonância agregando a massa (norma) de todas as GPUs no grupo.
    """
    # 1. Calcula a norma local (quadrada para soma)
    local_sq_norm = torch.sum(local_param_tensor ** 2)

    # 2. Sincroniza via NCCL (NVLink) - Redução global da "massa"
    if dist.is_initialized():
        dist.all_reduce(local_sq_norm, op=dist.ReduceOp.SUM)

    global_norm = torch.sqrt(local_sq_norm)

    # 3. Chama o Kernel CUDA com a norma global já corrigida
    arkhe_loss, phase, damping = arkhe_cuda.compute_with_norm(
        base_loss, global_norm, rho_2, k1, k2, lam, rho_eq
    )

    return arkhe_loss, phase, damping`}
                      </pre>
                    </div>

                    <div className="grid grid-cols-3 gap-4 mt-6">
                      <div className="p-4 border border-[#1f2024] rounded-lg bg-black flex flex-col items-center justify-center text-center gap-2">
                        <Database className="w-6 h-6 text-arkhe-muted" />
                        <div className="text-[10px] font-mono text-arkhe-muted uppercase">GPU 0 (Shard A)</div>
                        <div className="text-xs font-mono text-emerald-400">ρ₁_local = {cluster.nccl.rho1_local.toFixed(2)}</div>
                      </div>
                      <div className="flex items-center justify-center">
                        <ArrowRight className="w-6 h-6 text-emerald-500/50" />
                        <div className="text-[10px] font-mono text-emerald-500 px-2">all_reduce</div>
                        <ArrowRight className="w-6 h-6 text-emerald-500/50" />
                      </div>
                      <div className="p-4 border border-emerald-500/30 rounded-lg bg-emerald-500/5 flex flex-col items-center justify-center text-center gap-2 shadow-[0_0_15px_rgba(16,185,129,0.1)]">
                        <Network className="w-6 h-6 text-emerald-400" />
                        <div className="text-[10px] font-mono text-emerald-400 uppercase">Global State</div>
                        <div className="text-xs font-mono text-white font-bold">ρ₁_global = {cluster.nccl.rho1_global.toFixed(2)}</div>
                      </div>
                    </div>
                  </motion.div>
                )}

                {activeTab === 'qhttp' && (
                  <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
                    <div>
                      <h3 className="text-lg font-mono text-emerald-400 uppercase tracking-widest mb-2">qhttp:// Protocol & Telemetry</h3>
                      <p className="text-sm font-mono text-arkhe-muted leading-relaxed">
                        O protocolo <code className="text-emerald-300 bg-emerald-500/10 px-1 rounded">qhttp://</code> (Quantum Hypertext Transfer Protocol) é implementado via gRPC bi-direcional assíncrono. Ele transmite a telemetria da Fase θ do cluster para o Orquestrador e recebe vetores de Logit Bias em tempo real, sem bloquear os workers de inferência.
                      </p>
                    </div>

                    <div className="bg-[#111214] border border-arkhe-border rounded-xl overflow-hidden">
                      <div className="bg-[#1a1b20] px-4 py-2 border-b border-arkhe-border text-[10px] font-mono text-arkhe-muted flex justify-between">
                        <span>tzinor/network/qhttp_service.proto</span>
                        <span>Protocol Buffers</span>
                      </div>
                      <pre className="p-4 text-xs font-mono text-arkhe-text overflow-x-auto">
{`syntax = "proto3";
package arkhen.qhttp;

service QuantumOrchestrator {
  // Stream bi-direcional: Telemetria sobe, Bias desce
  rpc EntangleStream(stream TelemetryPhase) returns (stream LogitBiasVector);
}

message TelemetryPhase {
  string node_id = 1;
  float global_rho1 = 2;
  float global_rho2 = 3;
  float current_theta = 4;
  float entropy_sigma = 5;
}

message LogitBiasVector {
  map<int32, float> bias_map = 1;
  float target_temperature = 2;
  bool enforce_early_stopping = 3;
}`}
                      </pre>
                    </div>

                    <div className="bg-[#111214] border border-arkhe-border rounded-xl overflow-hidden">
                      <div className="bg-[#1a1b20] px-4 py-2 border-b border-arkhe-border text-[10px] font-mono text-arkhe-muted flex justify-between">
                        <span>tzinor/network/async_injector.py</span>
                        <span>Python / Asyncio</span>
                      </div>
                      <pre className="p-4 text-xs font-mono text-arkhe-text overflow-x-auto">
{`import asyncio
import grpc
import qhttp_pb2_grpc

async def run_qhttp_client(node_id, state_queue, bias_queue):
    async with grpc.aio.insecure_channel('orchestrator.arkhen.local:50051') as channel:
        stub = qhttp_pb2_grpc.QuantumOrchestratorStub(channel)

        # Gerador assíncrono de telemetria
        async def telemetry_generator():
            while True:
                state = await state_queue.get()
                yield state

        # Inicia o stream bi-direcional
        response_iterator = stub.EntangleStream(telemetry_generator())

        # Recebe bias vectors sem bloquear a inferência
        async for bias_response in response_iterator:
            if bias_response.enforce_early_stopping:
                await trigger_collapse()
            else:
                await bias_queue.put(bias_response)

# O worker de inferência consome o bias_queue de forma não-bloqueante`}
                      </pre>
                    </div>

                    <div className="grid grid-cols-2 gap-4 mt-6">
                      <div className="p-4 border border-[#1f2024] rounded-lg bg-black flex flex-col items-center justify-center text-center gap-2">
                        <Activity className="w-6 h-6 text-arkhe-muted" />
                        <div className="text-[10px] font-mono text-arkhe-muted uppercase">Global Phase (θ)</div>
                        <div className="text-xs font-mono text-emerald-400">{cluster.qhttp.global_phase.toFixed(4)} rad</div>
                      </div>
                      <div className="p-4 border border-emerald-500/30 rounded-lg bg-emerald-500/5 flex flex-col items-center justify-center text-center gap-2 shadow-[0_0_15px_rgba(16,185,129,0.1)]">
                        <Network className="w-6 h-6 text-emerald-400" />
                        <div className="text-[10px] font-mono text-emerald-400 uppercase">Coherence (λ)</div>
                        <div className="text-xs font-mono text-white font-bold">{cluster.qhttp.coherence.toFixed(3)}</div>
                      </div>
                    </div>
                  </motion.div>
                )}

                {activeTab === 'logs' && (
                  <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="h-full flex flex-col">
                    <h3 className="font-mono text-sm text-emerald-400 uppercase tracking-widest mb-4 flex items-center gap-2">
                      <Server className="w-4 h-4" /> Deployment Pipeline
                    </h3>

                    <div className="mb-6">
                      <div className="flex justify-between text-[10px] font-mono text-arkhe-muted mb-2">
                        <span>Cluster Provisioning</span>
                        <span>{Math.round(deployProgress)}%</span>
                      </div>
                      <div className="h-2 bg-black rounded-full overflow-hidden border border-arkhe-border">
                        <div
                          className="h-full bg-emerald-500 transition-all duration-500 ease-out"
                          style={{ width: `${deployProgress}%` }}
                        ></div>
                      </div>
                    </div>

                    <div className="flex-1 bg-black border border-[#1f2024] rounded-xl p-4 font-mono text-xs overflow-y-auto custom-scrollbar space-y-2">
                      {deployLogs.map((log, i) => (
                        <motion.div
                          key={i}
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          className={log.includes('complete') ? 'text-emerald-400 font-bold' : 'text-arkhe-muted'}
                        >
                          <span className="text-emerald-500/50 mr-2">❯</span> {log}
                        </motion.div>
                      ))}
                      {isDeploying && (
                        <motion.div
                          animate={{ opacity: [1, 0] }}
                          transition={{ repeat: Infinity, duration: 0.8 }}
                          className="text-emerald-400"
                        >
                          _
                        </motion.div>
                      )}
                    </div>
                  </motion.div>
                )}
              </div>
            )}
          </div>
        </div>
      </motion.div>
    </div>
  );
}
