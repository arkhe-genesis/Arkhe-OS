
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { GitMerge, Lock } from 'lucide-react';

import { Card } from './ui/Card';


interface YangBaxterVerifierProps {
  topology: {
    yangBaxterValid: boolean;
    berryPhase: number;
    handshakeSuccessRate: number;
  };
  security: {
    zkProofValid: boolean;
    nttLatency: number;
  };
}

export default function YangBaxterVerifier({ topology, security }: YangBaxterVerifierProps) {
  return (
    <Card
      title="Topological Consensus"
      icon={<GitMerge className="w-4 h-4" />}
      status={!topology.yangBaxterValid || !security.zkProofValid ? 'critical' : 'normal'}
    >
      <div className="flex flex-col gap-4">
        {/* Yang-Baxter Equation */}
        <div className={`p-3 rounded border ${topology.yangBaxterValid ? 'bg-[#151619] border-arkhe-border' : 'bg-arkhe-red/10 border-arkhe-red/30'}`}>
          <div className="flex justify-between items-center mb-2">
            <span className="text-[10px] font-mono text-arkhe-muted uppercase">Yang-Baxter Invariant</span>
            <span className={`text-[10px] font-mono font-bold ${topology.yangBaxterValid ? 'text-arkhe-green' : 'text-arkhe-red animate-pulse'}`}>
              {topology.yangBaxterValid ? 'VALIDATED' : 'VIOLATION'}
            </span>
          </div>
          <div className="text-center py-2 bg-black/20 rounded font-mono text-xs tracking-wider">
            <span className={topology.yangBaxterValid ? 'text-arkhe-text' : 'text-arkhe-red'}>
              R₁₂R₁₃R₂₃ = R₂₃R₁₃R₁₂
            </span>
          </div>
          <div className="flex justify-between mt-2 text-[10px] font-mono">
            <span className="text-arkhe-muted">Handshake Success</span>
            <span className={topology.handshakeSuccessRate > 90 ? 'text-arkhe-green' : 'text-arkhe-orange'}>
              {topology.handshakeSuccessRate.toFixed(1)}%
            </span>
          </div>
        </div>

        {/* ZK-Proof & Security */}
        <div className={`p-3 rounded border ${security.zkProofValid ? 'bg-[#151619] border-arkhe-border' : 'bg-arkhe-red/10 border-arkhe-red/30'}`}>
          <div className="flex justify-between items-center mb-2">
            <div className="flex items-center gap-1">
              <Lock className="w-3 h-3 text-arkhe-muted" />
              <span className="text-[10px] font-mono text-arkhe-muted uppercase">Ring-LWE ZK-Proof</span>
            </div>
            <span className={`text-[10px] font-mono font-bold ${security.zkProofValid ? 'text-arkhe-green' : 'text-arkhe-red animate-pulse'}`}>
              {security.zkProofValid ? 'VERIFIED' : 'FORGERY DETECTED'}
            </span>
          </div>
          <div className="flex justify-between items-center text-[10px] font-mono">
            <span className="text-arkhe-muted">NTT Latency</span>
            <span className="text-arkhe-cyan">{security.nttLatency.toFixed(2)} µs</span>
          </div>
        </div>
      </div>
    </Card>
  );
}
