'use client';

export default function EulerPrismPanel({ active, onToggle }: any) {
  return (
    <div className={`bg-gradient-to-br ${active ? 'from-indigo-600/20 to-cyan-500/10 border-cyan-500/50' : 'from-slate-900/40 to-black/40 border-white/5'} border rounded-3xl p-6 transition-all duration-500`}>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-xs font-bold text-white uppercase tracking-widest flex items-center gap-2">
            💎 Prisma de Euler
            {active && <span className="w-1.5 h-1.5 bg-cyan-400 rounded-full animate-ping" />}
        </h3>
        <button
            onClick={onToggle}
            className={`px-4 py-1 rounded-full text-[10px] font-bold transition-all ${active ? 'bg-cyan-500 text-black' : 'bg-white/5 text-slate-400 hover:bg-white/10'}`}
        >
            {active ? 'ATIVADO' : 'ATIVAR'}
        </button>
      </div>

      <p className="text-[10px] text-slate-400 mb-4 leading-relaxed">
        Equipamento lendário para detecção espectral subpicométrica.
        Permite visualizar os modos de Fibonacci do Scaffold biológico.
      </p>

      {active && (
        <div className="space-y-3 animate-in fade-in slide-in-from-bottom-2">
           <div className="flex justify-between text-[9px] font-mono text-cyan-400/70">
              <span>RESOLUÇÃO</span>
              <span>&lt; 0.5 pm</span>
           </div>
           <div className="h-12 w-full bg-black/60 rounded-xl border border-cyan-500/20 overflow-hidden flex items-end gap-0.5 p-1">
              {[0.2, 0.5, 0.8, 0.4, 0.9, 0.3, 0.6, 0.2, 0.5].map((h, i) => (
                <div key={i} className="flex-1 bg-cyan-500/50 rounded-t-sm" style={{ height: `${h * 100}%` }} />
              ))}
           </div>
        </div>
      )}
    </div>
  );
}
