// arkhe-dashboard/src/components/security/SafeCorePanel.tsx
'use client';

import { useState, useEffect } from 'react';
import { safeCoreEngine } from '@/lib/security/safeCore';

export default function SafeCorePanel() {
  const [dashboard, setDashboard] = useState<any>(null);

  useEffect(() => {
    // Simular registro de agentes e scaffolds
    safeCoreEngine.registerAgentContext('agent_alpha', 'scaffold_ethics', { role: 'evaluator' });
    safeCoreEngine.registerAgentContext('agent_beta', 'scaffold_ethics', { role: 'validator' });

    setDashboard(safeCoreEngine.getSafeCoreDashboard());
  }, []);

  const triggerConsensus = async () => {
    await safeCoreEngine.computeGeometricConsensus(
      ['agent_alpha', 'agent_beta'],
      { action: 'verify_law_3' },
      'scaffold_ethics'
    );
    setDashboard(safeCoreEngine.getSafeCoreDashboard());
  };

  return (
    <div className="bg-black/30 rounded-2xl border border-blue-500/20 p-4">
      <h3 className="text-xs font-bold text-blue-400 mb-3 tracking-widest uppercase flex items-center gap-2">
        <span>🛡️</span> Safe Core: Geometric Security
      </h3>

      {dashboard && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-white/5 p-2 rounded-lg border border-white/5 text-center">
              <p className="text-[9px] text-slate-500 uppercase">Scaffolds</p>
              <p className="text-sm font-bold text-white">{dashboard.totalScaffolds}</p>
            </div>
            <div className="bg-white/5 p-2 rounded-lg border border-white/5 text-center">
              <p className="text-[9px] text-slate-500 uppercase">Agents</p>
              <p className="text-sm font-bold text-white">{dashboard.registeredAgents}</p>
            </div>
          </div>

          <div className="flex justify-between items-center bg-blue-500/10 p-3 rounded-xl border border-blue-500/30">
            <div>
              <p className="text-[9px] text-blue-300 font-bold uppercase tracking-tighter">Avg Convergence</p>
              <p className="text-lg font-mono text-white">{(dashboard.avgConvergenceScore * 100).toFixed(2)}%</p>
            </div>
            <div className="w-10 h-10 rounded-full border-2 border-blue-500 flex items-center justify-center">
              <div className="w-6 h-6 rounded-full bg-blue-500 animate-pulse"></div>
            </div>
          </div>

          <button
            onClick={triggerConsensus}
            className="w-full py-2 bg-blue-600/20 border border-blue-500/40 text-blue-400 rounded-lg text-[10px] font-black hover:bg-blue-600/30 transition-all uppercase tracking-widest"
          >
            Run Isomorphic Consensus
          </button>

          <p className="text-[8px] text-slate-500 italic text-center">
            Security emerging from geometric alignment, not communication.
          </p>
        </div>
      )}
    </div>
  );
}
