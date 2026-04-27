'use client';

export default function CoherenceMetrics({ metrics }: any) {
  const stats = [
    { label: 'Ω MÉDIO (REDE)', value: metrics?.avgOmega?.toFixed(4) || '0.9412', color: 'text-cyan-400' },
    { label: 'ENTROPIA (HUMANA)', value: '4.2 bits', color: 'text-purple-400' },
    { label: 'DIMENSÃO FRACTAL', value: '1.28', color: 'text-emerald-400' },
    { label: 'COERÊNCIA Ξ', value: '0.892', color: 'text-amber-400' },
  ];

  return (
    <div className="grid grid-cols-2 gap-4">
      {stats.map((s, i) => (
        <div key={i} className="bg-black/40 border border-white/5 rounded-2xl p-4">
          <p className="text-[10px] text-slate-500 font-bold mb-1 uppercase tracking-tighter">{s.label}</p>
          <p className={`text-xl font-mono font-black ${s.color}`}>{s.value}</p>
        </div>
      ))}
    </div>
  );
}
