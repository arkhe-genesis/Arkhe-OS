'use client';

import { useState, useEffect } from 'react';
import ThreatMap from '@/components/security/ThreatMap';
import CoherenceMetrics from '@/components/security/CoherenceMetrics';
import IncidentTable from '@/components/security/IncidentTable';
import ThresholdConfig from '@/components/security/ThresholdConfig';
import EulerPrismPanel from '@/components/security/EulerPrismPanel';
import dynamic from 'next/dynamic';

const ArkheCore3D = dynamic(() => import('@/components/ArkheCore3D'), { ssr: false });

export default function SecurityDashboardPage() {
  const [threats, setThreats] = useState<any[]>([]);
  const [incidents, setIncidents] = useState<any[]>([]);
  const [metrics, setMetrics] = useState<any>({ avgOmega: 0.9412 });
  const [eulerPrismActive, setEulerPrismActive] = useState(false);

  useEffect(() => {
    setThreats([
      { coordinates: [-43.1729, -22.9068], intensity: 75, severity: 'high', type: 'bot_flood', domain: 'arkhe.rio' },
      { coordinates: [-0.1278, 51.5074], intensity: 30, severity: 'low', type: 'scraping', domain: 'arkhe.uk' },
      { coordinates: [-122.4194, 37.7749], intensity: 95, severity: 'critical', type: 'injection', domain: 'arkhe.sf' }
    ]);

    setIncidents([
      { domain: 'node-alpha.network', attack_type: 'credential_stuffing', severity: 'medium', timestamp: Date.now() - 3600000 },
      { domain: 'core-bridge.eth', attack_type: 'bot_flood', severity: 'critical', timestamp: Date.now() - 1200000 },
      { domain: 'telemetry.arkhe', attack_type: 'scraping', severity: 'low', timestamp: Date.now() - 500000 },
    ]);
  }, []);

  return (
    <div className="min-h-screen bg-[#020305] text-white p-6">
      <header className="mb-8 flex justify-between items-center">
        <div>
           <h1 className="text-2xl font-black italic tracking-tighter uppercase">🛡️ Arkhe Security <span className="text-cyan-400">Sentinela</span></h1>
           <p className="text-[10px] font-mono text-slate-500 tracking-[0.2em]">SISTEMA NERVOSO DE DEFESA FEDERADA | ODÔMETRO: 002189</p>
        </div>
        <div className="flex gap-2">
            <span className="flex items-center gap-2 px-4 py-2 bg-emerald-500/10 border border-emerald-500/20 rounded-xl text-[10px] font-bold text-emerald-400">
                <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
                CONEXÃO FEDERADA ATIVA
            </span>
        </div>
      </header>

      <div className="grid grid-cols-12 gap-6">
        <div className="col-span-12 lg:col-span-8 space-y-6">
            <div className="bg-black/40 border border-white/5 rounded-[2rem] p-8 min-h-[400px] relative overflow-hidden group">
                <ArkheCore3D
                  omega={metrics.avgOmega}
                  kEth={0.92}
                  scaffoldMode={eulerPrismActive}
                  fibonacciVision={eulerPrismActive}
                />
            </div>
            <ThreatMap threats={threats} onThreatClick={(d: any) => console.log(d)} />
            <IncidentTable incidents={incidents} />
        </div>

        <div className="col-span-12 lg:col-span-4 space-y-6">
            <EulerPrismPanel active={eulerPrismActive} onToggle={() => setEulerPrismActive(!eulerPrismActive)} />
            <CoherenceMetrics metrics={metrics} />
            <ThresholdConfig onChange={(v: any) => console.log(v)} />

            <div className="bg-gradient-to-br from-indigo-900/40 to-purple-900/20 border border-white/10 rounded-3xl p-6">
                <h4 className="text-xs font-bold mb-4 uppercase tracking-widest text-indigo-300">🔒 Prova de Humanidade ZK</h4>
                <p className="text-[10px] text-slate-400 mb-4 leading-relaxed">
                    Nossa rede utiliza provas Groth16 para validar que o comportamento do usuário é humano
                    sem expor telemetria bruta.
                </p>
                <div className="p-4 bg-black/40 rounded-2xl border border-white/5 font-mono text-[9px] text-cyan-500/70">
                    {`{ "pi_a": ["0x23...", "0x45..."], "public": ["0x98..."] }`}
                </div>
            </div>
        </div>
      </div>
    </div>
  );
}
