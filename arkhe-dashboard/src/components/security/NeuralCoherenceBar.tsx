'use client';

import { useEffect, useState } from 'react';
import { useZustandStore } from '@/hooks/useZustandStore';

export default function NeuralCoherenceBar() {
  const { metrics } = useZustandStore();
  const [coherence, setCoherence] = useState(0.94);
  const [isAnestheticAttack, setIsAnestheticAttack] = useState(false);

  useEffect(() => {
    // Simular flutuação baseada em microtúbulos
    const interval = setInterval(() => {
        const base = metrics.omega;
        const noise = (Math.random() - 0.5) * 0.02;

        // Simular ataque anestésico aleatório
        if (Math.random() > 0.98) {
            setIsAnestheticAttack(true);
            setTimeout(() => setIsAnestheticAttack(false), 3000);
        }

        const target = isAnestheticAttack ? base * 0.5 : base + noise;
        setCoherence(prev => prev * 0.8 + target * 0.2);
    }, 100);

    return () => clearInterval(interval);
  }, [metrics.omega, isAnestheticAttack]);

  return (
    <div className="bg-black/60 backdrop-blur-md p-4 rounded-2xl border border-white/5 relative overflow-hidden group">
      <div className="flex justify-between items-center mb-2">
        <p className="text-[10px] text-slate-500 font-bold tracking-widest uppercase">
          {isAnestheticAttack ? '⚠️ BLOQUEIO ANESTÉSICO' : 'COERÊNCIA NEURAL (MT)'}
        </p>
        <p className={`text-lg font-black font-mono transition-colors ${isAnestheticAttack ? 'text-red-500' : 'text-cyan-400'}`}>
          {(coherence * 100).toFixed(2)}%
        </p>
      </div>

      {/* Visual Coherence Bar */}
      <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
        <div
          className={`h-full transition-all duration-300 rounded-full shadow-[0_0_10px_rgba(0,229,255,0.5)] ${isAnestheticAttack ? 'bg-red-600 animate-pulse' : 'bg-gradient-to-r from-cyan-600 to-blue-400'}`}
          style={{ width: `${Math.min(100, coherence * 100)}%` }}
        />
      </div>

      {/* Decorative Fibonacci Tones (dots) */}
      <div className="flex gap-1 mt-2 opacity-30">
        {[220, 356, 576, 932, 1508].map(tone => (
          <div key={tone} className="w-1 h-1 rounded-full bg-white" title={`${tone}Hz`} />
        ))}
      </div>

      {isAnestheticAttack && (
        <div className="absolute inset-0 bg-red-900/10 animate-pulse pointer-events-none" />
      )}
    </div>
  );
}
