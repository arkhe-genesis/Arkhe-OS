'use client';

export default function IncidentTable({ incidents = [] }: any) {
  return (
    <div className="bg-black/40 border border-white/5 rounded-3xl p-6 overflow-hidden">
      <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-4">🔍 Incidentes Recentes</h3>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs font-mono">
          <thead>
            <tr className="text-slate-500 border-b border-white/5">
              <th className="pb-2">DOMÍNIO</th>
              <th className="pb-2">TIPO</th>
              <th className="pb-2">SEVERIDADE</th>
              <th className="pb-2 text-right">TIMESTAMP</th>
            </tr>
          </thead>
          <tbody className="text-slate-300">
            {incidents.map((inc: any, i: number) => (
              <tr key={i} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                <td className="py-2">{inc.domain}</td>
                <td className="py-2">{inc.attack_type}</td>
                <td className="py-2">
                   <span className={`px-2 py-0.5 rounded-full text-[8px] font-bold uppercase ${
                     inc.severity === 'critical' ? 'bg-red-500/20 text-red-500' :
                     inc.severity === 'high' ? 'bg-orange-500/20 text-orange-500' :
                     'bg-cyan-500/20 text-cyan-500'
                   }`}>
                     {inc.severity}
                   </span>
                </td>
                <td className="py-2 text-right text-slate-500">{new Date(inc.timestamp).toLocaleTimeString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
