// arkhe-dashboard/src/components/quantum/QuantumTelepathyPanel.tsx
'use client';
import { useState } from 'react';

export function QuantumTelepathyPanel() {
  const [intentions, setIntentions] = useState(7);

  return (
    <div className="bg-black/30 rounded-2xl border border-purple-500/20 p-4">
      <h2 className="text-lg font-semibold mb-4 flex items-center gap-2 text-purple-400">
        <span>🧠⚛️</span> Telepatia Quântica
      </h2>
      <div className="space-y-3">
        <div className="flex justify-between text-xs">
          <span className="text-slate-400">Canal Entangled</span>
          <span className="text-green-400">ATIVO</span>
        </div>
        <div className="flex justify-between text-xs">
          <span className="text-slate-400">Fidelidade</span>
          <span className="text-purple-300">0.9921</span>
        </div>
        <div className="flex justify-between text-xs">
          <span className="text-slate-400">Intenções Transmitidas</span>
          <span className="text-white font-mono">{intentions}</span>
        </div>
        <button
          onClick={() => setIntentions(i => i + 1)}
          className="w-full py-2 bg-purple-600 hover:bg-purple-700 rounded-lg text-xs font-bold transition-all shadow-[0_0_15px_rgba(168,85,247,0.4)]"
        >
          Transmitir Intenção Direta
        </button>
      </div>
    </div>
  );
}
