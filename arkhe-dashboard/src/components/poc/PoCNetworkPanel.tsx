'use client';
/**
 * arkhe-dashboard/src/components/poc/PoCNetworkPanel.tsx
 * Proof-of-Coherence network status panel for the dashboard sidebar.
 */
import React, { useCallback, useState } from 'react';
import { createNetwork, registerVertex, castVote, evaluateMerge } from '@/lib/api-client';
import type { NetworkSummary } from '@/types/api';

interface Props {
  networks: NetworkSummary[];
  tenantId: string;
}

export default function PoCNetworkPanel({ networks, tenantId }: Props) {
  const [loading, setLoading] = useState(false);
  const [consensusResult, setConsensusResult] = useState<{
    accept: boolean;
    score: number;
  } | null>(null);
  const [selectedNet, setSelectedNet] = useState<NetworkSummary | null>(null);

  const handleCreateNetwork = useCallback(async () => {
    if (!tenantId) return;
    setLoading(true);
    try {
      await createNetwork(tenantId, {
        name: `Arkhe Network ${networks.length + 1}`,
        target_epsilon: [0.07, 0.07, 0.07],
        sigma: [0.015, 0.015, 0.015],
        consensus_threshold: 0.55,
        odysseus_multiplier: 0.3,
      });
    } finally {
      setLoading(false);
    }
  }, [tenantId, networks.length]);

  const handleSimulateConsensus = useCallback(async () => {
    if (!tenantId || networks.length === 0) return;
    setLoading(true);
    try {
      const net = networks[0];
      const forkId = 'fork_' + Math.random().toString(36).slice(2, 8);

      // Register vertices
      for (let i = 0; i < 5; i++) {
        await registerVertex({
          network_id: net.id,
          did: `did:arkhe:vertex_${i}`,
          public_key: 'MOCK_KEY_' + i,
          epsilon_history: Array.from({ length: 10 }, () =>
            [0.07, 0.07, 0.07].map(v => v + (Math.random() - 0.5) * 0.01)
          ),
        });
      }

      // Cast votes
      for (let i = 0; i < 5; i++) {
        await castVote(tenantId, {
          fork_id: forkId,
          voter_did: `did:arkhe:vertex_${i}`,
          vote_direction: i % 2 === 0 || i === 4,  // most vote "for"
          timestamp: Date.now(),
          signature: 'MOCK_SIG_' + i,
        });
      }

      // Evaluate
      const result = await evaluateMerge(tenantId, {
        fork_id: forkId,
        odysseus_insight_ratio: 1.1,
      });
      setConsensusResult({ accept: result.accept, score: result.consensus_score });
      setSelectedNet(net);
    } catch (err) {
      console.error('Consensus simulation failed:', err);
    } finally {
      setLoading(false);
    }
  }, [tenantId, networks]);

  return (
    <div className="bg-black/40 border border-white/5 rounded-2xl p-5 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">
          Proof-of-Coherence
        </h3>
        <div className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
      </div>

      {/* Network count */}
      <div className="flex items-end gap-2">
        <p className="text-2xl font-black text-cyan-400">{networks.length}</p>
        <p className="text-[10px] text-slate-500 pb-1">Networks</p>
      </div>

      {/* Selected network details */}
      {selectedNet ? (
        <div className="space-y-2">
          <p className="text-xs font-bold text-white">{selectedNet.name}</p>
          <div className="grid grid-cols-2 gap-2">
            <div className="bg-black/60 p-2 rounded-lg">
              <p className="text-[9px] text-slate-500">ε target</p>
              <p className="text-[10px] font-mono text-emerald-400">
                {selectedNet.target_epsilon[0].toFixed(3)}
              </p>
            </div>
            <div className="bg-black/60 p-2 rounded-lg">
              <p className="text-[9px] text-slate-500">Threshold</p>
              <p className="text-[10px] font-mono text-purple-400">
                {(selectedNet.consensus_threshold * 100).toFixed(0)}%
              </p>
            </div>
          </div>
        </div>
      ) : null}

      {/* Consensus simulation result */}
      {consensusResult && (
        <div
          className={`p-3 rounded-xl border text-center ${
            consensusResult.accept
              ? 'bg-emerald-900/20 border-emerald-500/30'
              : 'bg-red-900/20 border-red-500/30'
          }`}
        >
          <p className="text-[10px] text-slate-500 mb-1">Consensus</p>
          <p
            className={`text-lg font-black ${
              consensusResult.accept ? 'text-emerald-400' : 'text-red-400'
            }`}
          >
            {consensusResult.accept ? '✓ ACCEPT' : '✗ REJECT'}
          </p>
          <p className="text-[10px] font-mono text-slate-400">
            Score: {consensusResult.score.toFixed(4)}
          </p>
        </div>
      )}

      {/* Actions */}
      <div className="flex flex-col gap-2">
        <button
          onClick={() => void handleSimulateConsensus()}
          disabled={loading}
          className="px-3 py-2 bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 rounded-lg text-[10px] font-bold hover:bg-cyan-500/20 transition-all disabled:opacity-50"
        >
          {loading ? '⟳ Processing...' : '⟐ Simulate Consensus'}
        </button>
        <button
          onClick={() => void handleCreateNetwork()}
          disabled={loading}
          className="px-3 py-2 bg-purple-500/10 border border-purple-500/30 text-purple-400 rounded-lg text-[10px] font-bold hover:bg-purple-500/20 transition-all disabled:opacity-50"
        >
          + New Network
        </button>
      </div>

      {/* ε visualization */}
      <div className="flex justify-around">
        {[0.07, 0.07, 0.07].map((val, i) => (
          <div key={i} className="text-center">
            <div
              className="w-6 h-6 rounded-full border"
              style={{
                borderColor: ['#22d3ee', '#a78bfa', '#fbbf24'][i],
                boxShadow: `0 0 8px ${['#22d3ee', '#a78bfa', '#fbbf24'][i]}40`,
              }}
            />
          </div>
        ))}
      </div>
    </div>
  );
}
