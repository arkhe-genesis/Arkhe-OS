'use client';
/**
 * arkhe-dashboard/src/app/dashboard/network/page.tsx
 * Multi-tenant PoC network management page.
 */
import React, { useCallback, useEffect, useState } from 'react';
import { listNetworks, createNetwork, registerVertex } from '@/lib/api-client';
import type { NetworkSummary, VertexInfo } from '@/types/api';

export default function NetworkPage() {
  const [networks, setNetworks] = useState<NetworkSummary[]>([]);
  const [selectedNetwork, setSelectedNetwork] = useState<NetworkSummary | null>(null);
  const [tenantId, setTenantId] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load from localStorage
  useEffect(() => {
    const stored = localStorage.getItem('arkhe_tenant_id');
    if (stored) setTenantId(stored);
  }, []);

  const loadNetworks = useCallback(async () => {
    if (!tenantId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await listNetworks(tenantId);
      setNetworks(data);
      if (data.length > 0 && !selectedNetwork) {
        setSelectedNetwork(data[0]);
      }
    } catch (err) {
      setError('Failed to load networks. Is the backend running?');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [tenantId, selectedNetwork]);

  useEffect(() => {
    void loadNetworks();
  }, [loadNetworks]);

  const handleCreateNetwork = useCallback(async () => {
    if (!tenantId) return;
    setLoading(true);
    try {
      const network = await createNetwork(tenantId, {
        name: `Coherence Network ${networks.length + 1}`,
        target_epsilon: [0.07, 0.07, 0.07],
        sigma: [0.015, 0.015, 0.015],
        consensus_threshold: 0.55,
        odysseus_multiplier: 0.3,
      });
      setNetworks(prev => [...prev, network]);
      setSelectedNetwork(network);
    } catch (err) {
      setError('Failed to create network');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [tenantId, networks.length]);

  const handleRegisterVertex = useCallback(async () => {
    if (!selectedNetwork) return;
    setLoading(true);
    try {
      await registerVertex({
        network_id: selectedNetwork.id,
        did: `did:arkhe:${Math.random().toString(36).slice(2, 10)}`,
        public_key: 'MOCK_PUBLIC_KEY_' + Math.random().toString(36).slice(2, 8),
        epsilon_history: Array.from({ length: 10 }, () =>
          [0.07, 0.07, 0.07].map(v => v + (Math.random() - 0.5) * 0.01)
        ),
      });
    } catch (err) {
      setError('Failed to register vertex');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [selectedNetwork]);

  return (
    <div className="min-h-screen bg-[#020305] text-white p-6">
      <header className="flex justify-between items-center mb-8 border-b border-white/5 pb-6">
        <div>
          <h1 className="text-2xl font-black tracking-tighter uppercase italic">
            PoC Network <span className="text-cyan-400">Management</span>
          </h1>
          <p className="text-[10px] font-mono text-slate-500 tracking-[0.2em]">
            Proof-of-Coherence Multi-Tenant Console
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => void loadNetworks()}
            className="px-6 py-2 bg-white/5 border border-white/10 text-slate-300 rounded-xl text-xs font-bold hover:bg-white/10 transition-all"
          >
            ↻ REFRESH
          </button>
          <button
            onClick={() => void handleCreateNetwork()}
            disabled={loading || !tenantId}
            className="px-6 py-2 bg-cyan-500/20 border border-cyan-500/40 text-cyan-300 rounded-xl text-xs font-bold hover:bg-cyan-500/30 transition-all disabled:opacity-50"
          >
            + NOVA REDE
          </button>
        </div>
      </header>

      {error && (
        <div className="mb-4 p-4 bg-red-900/20 border border-red-500/30 rounded-xl text-red-400 text-sm">
          {error}
        </div>
      )}

      <div className="grid grid-cols-12 gap-6">
        {/* Networks List */}
        <div className="col-span-12 md:col-span-4 space-y-4">
          <h2 className="text-sm font-bold text-slate-400 uppercase tracking-widest">
            Coherence Networks
          </h2>
          {loading && networks.length === 0 ? (
            <div className="p-8 text-center text-slate-500">Loading...</div>
          ) : networks.length === 0 ? (
            <div className="p-8 text-center text-slate-500 border border-dashed border-white/10 rounded-xl">
              No networks yet. Create one to get started.
            </div>
          ) : (
            networks.map(net => (
              <button
                key={net.id}
                onClick={() => setSelectedNetwork(net)}
                className={`w-full text-left p-4 rounded-xl border transition-all ${
                  selectedNetwork?.id === net.id
                    ? 'bg-cyan-500/10 border-cyan-500/30'
                    : 'bg-black/40 border-white/5 hover:border-white/20'
                }`}
              >
                <p className="font-bold text-white">{net.name}</p>
                <p className="text-[10px] text-slate-500 font-mono mt-1">
                  ε: [{net.target_epsilon.map(v => v.toFixed(3)).join(', ')}]
                </p>
                <p className="text-[10px] text-slate-500 font-mono">
                  σ: [{net.sigma.map(v => v.toFixed(3)).join(', ')}]
                </p>
              </button>
            ))
          )}
        </div>

        {/* Network Details */}
        <div className="col-span-12 md:col-span-8 space-y-6">
          {selectedNetwork ? (
            <>
              <div className="bg-black/40 border border-white/5 rounded-[2rem] p-8">
                <div className="flex justify-between items-start mb-6">
                  <div>
                    <h2 className="text-xl font-black">{selectedNetwork.name}</h2>
                    <p className="text-[10px] font-mono text-slate-500 mt-1">
                      ID: {selectedNetwork.id}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-[10px] text-slate-500">Consensus Threshold</p>
                    <p className="text-lg font-bold text-cyan-400">
                      {(selectedNetwork.consensus_threshold * 100).toFixed(0)}%
                    </p>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-4 mb-6">
                  <div className="bg-black/60 p-4 rounded-xl border border-white/5">
                    <p className="text-[10px] text-slate-500 mb-1">Target ε (phase)</p>
                    <p className="font-mono text-emerald-400">
                      {selectedNetwork.target_epsilon[0].toFixed(3)}
                    </p>
                  </div>
                  <div className="bg-black/60 p-4 rounded-xl border border-white/5">
                    <p className="text-[10px] text-slate-500 mb-1">σ (phase)</p>
                    <p className="font-mono text-purple-400">
                      {selectedNetwork.sigma[0].toFixed(3)}
                    </p>
                  </div>
                  <div className="bg-black/60 p-4 rounded-xl border border-white/5">
                    <p className="text-[10px] text-slate-500 mb-1">Odysseus Mult</p>
                    <p className="font-mono text-amber-400">
                      {selectedNetwork.odysseus_multiplier.toFixed(2)}
                    </p>
                  </div>
                </div>

                {/* Register Vertex */}
                <div className="border-t border-white/5 pt-6">
                  <h3 className="text-sm font-bold text-slate-400 uppercase mb-4">
                    Register Vertex
                  </h3>
                  <button
                    onClick={() => void handleRegisterVertex()}
                    disabled={loading}
                    className="px-6 py-3 bg-purple-500/20 border border-purple-500/40 text-purple-300 rounded-xl text-xs font-bold hover:bg-purple-500/30 transition-all disabled:opacity-50"
                  >
                    ⊕ REGISTER VERTEX NODE
                  </button>
                </div>
              </div>

              {/* PoC Parameters Card */}
              <div className="bg-gradient-to-br from-cyan-900/20 to-purple-900/20 border border-white/10 rounded-[2rem] p-8">
                <h3 className="text-sm font-bold text-slate-300 uppercase mb-4">
                  Multi-Dimensional ε Parameters
                </h3>
                <div className="grid grid-cols-3 gap-6">
                  {['phase', 'latency', 'power'].map((dim, i) => (
                    <div key={dim} className="text-center">
                      <p className="text-[10px] text-slate-500 uppercase tracking-widest mb-2">
                        {dim}
                      </p>
                      <div className="h-24 bg-black/60 rounded-xl border border-white/5 flex items-center justify-center">
                        <div
                          className="w-12 h-12 rounded-full border-2"
                          style={{
                            borderColor: ['#22d3ee', '#a78bfa', '#fbbf24'][i],
                            boxShadow: `0 0 20px ${['#22d3ee', '#a78bfa', '#fbbf24'][i]}40`,
                          }}
                        />
                      </div>
                      <p className="text-[10px] font-mono text-slate-400 mt-2">
                        ε: {selectedNetwork.target_epsilon[i].toFixed(3)}
                      </p>
                      <p className="text-[10px] font-mono text-slate-500">
                        σ: {selectedNetwork.sigma[i].toFixed(3)}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </>
          ) : (
            <div className="col-span-8 flex items-center justify-center h-96 bg-black/40 border border-white/5 rounded-[2rem]">
              <p className="text-slate-500">Select or create a network</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
