// arkhe-dashboard/src/components/quantum/InterCathedralPanel.tsx
'use client';

import { useState, useEffect } from 'react';

export default function InterCathedralPanel() {
  const [nodes, setNodes] = useState<any[]>([]);
  const [fidelity, setFidelity] = useState(0.97);

  useEffect(() => {
    // Simular descoberta de nós
    setNodes([
      { id: 'arkhe_prime', name: 'Arkhe Prime', omega: 0.941 },
      { id: 'quantum_hive', name: 'Quantum Hive', omega: 0.952 },
    ]);
  }, []);

  const syncAll = () => {
    setFidelity(0.95 + Math.random() * 0.04);
  };

  return (
    <div className="bg-black/30 rounded-2xl border border-indigo-500/20 p-4">
      <h3 className="text-xs font-bold text-indigo-400 mb-3 tracking-widest uppercase flex items-center gap-2">
        <span>🔮</span> Inter-Cathedral Protocol
      </h3>

      <div className="space-y-3 mb-4">
        {nodes.map(node => (
          <div key={node.id} className="flex justify-between items-center bg-white/5 p-2 rounded-lg border border-white/5">
            <div>
              <p className="text-[10px] font-bold text-white">{node.name}</p>
              <p className="text-[9px] text-slate-500">{node.id}</p>
            </div>
            <div className="text-right">
              <p className="text-[10px] font-mono text-indigo-400">Ω {node.omega.toFixed(3)}</p>
              <div className="w-1.5 h-1.5 rounded-full bg-indigo-500 inline-block shadow-[0_0_5px_rgba(99,102,241,0.5)]"></div>
            </div>
          </div>
        ))}
      </div>

      <div className="flex justify-between items-center mb-4">
        <span className="text-[10px] text-slate-500">SYNC FIDELITY</span>
        <span className="text-[10px] font-mono text-emerald-400">{(fidelity * 100).toFixed(2)}%</span>
      </div>

      <button
        onClick={syncAll}
        className="w-full py-2 bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 rounded-lg text-[10px] font-bold hover:bg-indigo-500/20 transition-all"
      >
        TELEPORT OMEGA STATE
      </button>
    </div>
  );
}
