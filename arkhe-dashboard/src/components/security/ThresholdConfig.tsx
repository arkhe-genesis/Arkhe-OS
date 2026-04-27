'use client';

export default function ThresholdConfig({ onChange }: any) {
  return (
    <div className="bg-black/40 border border-white/5 rounded-3xl p-6">
      <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-4">⚙️ Configuração de Threshold</h3>
      <div className="space-y-4">
        <div>
          <label className="text-[10px] text-slate-500 block mb-1">Ω MÍNIMO (HUMANO)</label>
          <input
            type="range" min="0" max="100" defaultValue="60"
            className="w-full h-1 bg-white/10 rounded-lg appearance-none cursor-pointer accent-cyan-500"
            onChange={(e) => onChange?.({ minOmega: e.target.value })}
          />
        </div>
        <div>
          <label className="text-[10px] text-slate-500 block mb-1">SENSIBILIDADE DE ATAQUE</label>
          <div className="flex gap-2">
            {['LOW', 'MED', 'HIGH'].map(s => (
              <button key={s} className="flex-1 py-2 bg-white/5 border border-white/10 rounded-xl text-[10px] font-bold hover:bg-white/10 transition-all">
                {s}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
