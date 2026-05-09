/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { TrendingUp, PieChart, Activity, ShieldCheck, ExternalLink, Coins, Info, BarChart2 } from 'lucide-react';
import React from 'react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

import type { SpectraState } from '../../server/types';

interface SpectraYieldPanelProps {
  spectra: SpectraState;
  onClose?: () => void;
}

export default function SpectraYieldPanel({ spectra, onClose }: SpectraYieldPanelProps) {
  // Mock history for the chart
  const historyData = [
    { time: '00:00', tvl: 14.2, apy: 4.1 },
    { time: '04:00', tvl: 14.5, apy: 4.3 },
    { time: '08:00', tvl: 14.8, apy: 4.2 },
    { time: '12:00', tvl: 15.1, apy: 4.5 },
    { time: '16:00', tvl: 15.4, apy: 4.4 },
    { time: '20:00', tvl: 15.67, apy: 4.5 }
  ];

  return (
    <div className="bg-black/40 border border-arkhe-border/50 rounded-xl p-6 flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-arkhe-cyan/20 rounded-lg flex items-center justify-center border border-arkhe-cyan/50">
            <TrendingUp className="w-6 h-6 text-arkhe-cyan" />
          </div>
          <div>
            <h2 className="font-mono text-lg font-bold tracking-tighter uppercase">
              Spectra <span className="text-arkhe-cyan">Yield Engine</span>
            </h2>
            <div className="text-[10px] font-mono text-arkhe-muted uppercase tracking-widest">
              DeFi Yield Tokenization & MetaVaults
            </div>
          </div>
        </div>
        <div className="flex items-center gap-6">
          <div className="text-right">
            <div className="text-[10px] font-mono text-arkhe-muted uppercase">Total TVL</div>
            <div className="text-xl font-mono font-bold text-arkhe-cyan">
              ${(spectra.totalTvl / 1e6).toFixed(2)}M
            </div>
          </div>
          {onClose && (
            <button onClick={onClose} className="text-arkhe-muted hover:text-white font-mono text-xs">
              [CLOSE]
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 flex-1 overflow-hidden">
        {/* Left Column: MetaVaults */}
        <div className="lg:col-span-2 space-y-8 flex flex-col overflow-hidden">
          {/* TVL & APY Trend */}
          <div className="bg-[#151B26]/50 rounded-xl border border-arkhe-border/50 p-4 h-[300px]">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-[10px] font-mono text-arkhe-muted uppercase flex items-center gap-2">
                <Activity className="w-3.5 h-3.5" />
                Performance Metrics (24h)
              </h3>
              <div className="flex gap-4">
                <div className="flex items-center gap-1.5">
                   <div className="w-2 h-2 rounded-full bg-arkhe-cyan" />
                   <span className="text-[9px] font-mono text-arkhe-muted uppercase">TVL ($M)</span>
                </div>
                <div className="flex items-center gap-1.5">
                   <div className="w-2 h-2 rounded-full bg-arkhe-purple" />
                   <span className="text-[9px] font-mono text-arkhe-muted uppercase">Avg APY (%)</span>
                </div>
              </div>
            </div>
            <div className="h-[220px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={historyData}>
                  <defs>
                    <linearGradient id="colorTvl" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#00FFAA" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#00FFAA" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <XAxis
                    dataKey="time"
                    stroke="#475569"
                    fontSize={9}
                    tickLine={false}
                    axisLine={false}
                  />
                  <YAxis
                    stroke="#475569"
                    fontSize={9}
                    tickLine={false}
                    axisLine={false}
                    tickFormatter={(value) => `${value}`}
                  />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0A0E17', border: '1px solid #262E3D', fontSize: '10px', fontFamily: 'monospace' }}
                    itemStyle={{ color: '#E2E8F0' }}
                  />
                  <Area type="monotone" dataKey="tvl" stroke="#00FFAA" fillOpacity={1} fill="url(#colorTvl)" strokeWidth={2} />
                  <Area type="monotone" dataKey="apy" stroke="#8B5CF6" fill="transparent" strokeWidth={2} strokeDasharray="5 5" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Active Vaults List */}
          <div className="flex-1 flex flex-col overflow-hidden">
            <h3 className="text-[10px] font-mono text-arkhe-muted uppercase mb-3 flex items-center gap-2">
              <PieChart className="w-3.5 h-3.5" />
              Active MetaVaults
            </h3>
            <div className="bg-[#0A0E17]/60 rounded-xl border border-arkhe-border/50 flex-1 overflow-y-auto custom-scrollbar">
              <table className="w-full text-left border-collapse">
                <thead className="sticky top-0 bg-[#0A0E17] z-10">
                  <tr className="border-b border-arkhe-border/50">
                    <th className="px-4 py-3 text-[9px] font-mono text-arkhe-muted uppercase">Vault</th>
                    <th className="px-4 py-3 text-[9px] font-mono text-arkhe-muted uppercase">Chain</th>
                    <th className="px-4 py-3 text-[9px] font-mono text-arkhe-muted uppercase text-right">TVL</th>
                    <th className="px-4 py-3 text-[9px] font-mono text-arkhe-muted uppercase text-right">APY</th>
                    <th className="px-4 py-3 text-[9px] font-mono text-arkhe-muted uppercase text-center">Epoch</th>
                    <th className="px-4 py-3 text-[9px] font-mono text-arkhe-muted uppercase text-center">Protocol</th>
                  </tr>
                </thead>
                <tbody>
                  {spectra.vaults.map((vault) => (
                    <tr key={vault.id} className="border-b border-arkhe-border/20 hover:bg-arkhe-cyan/5 transition-colors group">
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <div className="w-6 h-6 rounded bg-arkhe-cyan/10 flex items-center justify-center text-[10px] font-bold text-arkhe-cyan border border-arkhe-cyan/20">
                            {vault.asset[0]}
                          </div>
                          <div>
                            <div className="text-xs font-mono text-arkhe-text">{vault.name}</div>
                            <div className="text-[9px] font-mono text-arkhe-muted">{vault.asset}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <span className="text-[10px] font-mono text-arkhe-muted bg-white/5 px-1.5 py-0.5 rounded uppercase">
                          {vault.chain}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right text-xs font-mono text-arkhe-text">
                        ${(vault.tvl / 1e6).toFixed(2)}M
                      </td>
                      <td className="px-4 py-3 text-right text-xs font-mono text-arkhe-cyan font-bold">
                        {vault.apy.toFixed(2)}%
                      </td>
                      <td className="px-4 py-3 text-center text-xs font-mono text-arkhe-muted">
                        {vault.epoch}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <ShieldCheck className="w-3.5 h-3.5 text-arkhe-green mx-auto opacity-50 group-hover:opacity-100" />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Right Column: Oracles & Yield Tech */}
        <div className="space-y-6">
          {/* Oracle Status */}
          <div className="bg-[#151B26]/80 rounded-xl border border-arkhe-border/50 p-5 space-y-4 shadow-[0_10px_30px_rgba(0,0,0,0.3)]">
            <h3 className="text-[10px] font-mono text-arkhe-cyan uppercase tracking-widest flex items-center gap-2">
              <Activity className="w-3.5 h-3.5" />
              Spectra Oracle Matrix
            </h3>

            {spectra.oracles.map((oracle, i) => (
              <div key={i} className="bg-black/40 p-3 rounded-lg border border-arkhe-border/50 relative overflow-hidden group">
                <div className="absolute right-0 top-0 bottom-0 w-1 bg-arkhe-cyan/30 group-hover:bg-arkhe-cyan transition-colors" />
                <div className="flex justify-between items-start mb-2">
                  <div className="text-[10px] font-mono text-arkhe-text uppercase">{oracle.marketId}</div>
                  <div className={`text-[9px] font-mono px-1.5 py-0.5 rounded ${oracle.tokenType === 'PT' ? 'bg-blue-500/20 text-blue-400' : 'bg-arkhe-purple/20 text-arkhe-purple'}`}>
                    {oracle.tokenType}
                  </div>
                </div>
                <div className="flex justify-between items-end">
                  <div>
                    <div className="text-[9px] font-mono text-arkhe-muted uppercase">Latest Price</div>
                    <div className="text-sm font-mono text-arkhe-cyan font-bold">{oracle.price.toFixed(4)} <span className="text-[9px] font-normal">Asset</span></div>
                  </div>
                  <div className="text-right">
                    <div className="text-[9px] font-mono text-arkhe-muted uppercase">λ2 Coherence</div>
                    <div className="text-[10px] font-mono text-arkhe-green">{oracle.confidence.toFixed(4)}</div>
                  </div>
                </div>
              </div>
            ))}

            <button className="w-full py-2 border border-arkhe-border hover:border-arkhe-cyan hover:bg-arkhe-cyan/5 rounded font-mono text-[9px] text-arkhe-muted hover:text-arkhe-cyan transition-all flex items-center justify-center gap-2">
              <BarChart2 className="w-3 h-3" />
              REQUEST DETERMINISTIC PROOF
            </button>
          </div>

          {/* Protocol Architecture */}
          <div className="bg-arkhe-purple/5 border border-arkhe-purple/20 rounded-xl p-5 space-y-3">
             <h4 className="text-[10px] font-mono text-arkhe-purple uppercase flex items-center gap-2">
               <Info className="w-3.5 h-3.5" />
               Architecture Detail
             </h4>
             <div className="space-y-3">
                <div className="flex items-center gap-3">
                   <div className="w-8 h-8 rounded bg-arkhe-purple/10 flex items-center justify-center border border-arkhe-purple/20">
                      <Coins className="w-4 h-4 text-arkhe-purple" />
                   </div>
                   <div>
                      <div className="text-[10px] font-mono text-arkhe-text uppercase">ERC-5095 / 7540</div>
                      <div className="text-[9px] font-mono text-arkhe-muted">Standardized Yield Derivatives</div>
                   </div>
                </div>
                <div className="flex items-center gap-3">
                   <div className="w-8 h-8 rounded bg-arkhe-purple/10 flex items-center justify-center border border-arkhe-purple/20">
                      <ShieldCheck className="w-4 h-4 text-arkhe-purple" />
                   </div>
                   <div>
                      <div className="text-[10px] font-mono text-arkhe-text uppercase">Zodiac Integration</div>
                      <div className="text-[9px] font-mono text-arkhe-muted">On-chain Safety Constraints</div>
                   </div>
                </div>
             </div>
             <div className="pt-2">
                <a href="https://dev.spectra.finance" target="_blank" rel="noreferrer" className="text-[9px] font-mono text-arkhe-muted hover:text-arkhe-cyan flex items-center gap-1">
                   VIEW DEVELOPER DOCS <ExternalLink className="w-2.5 h-2.5" />
                </a>
             </div>
          </div>
        </div>
      </div>

      {/* Footer Status */}
      <div className="mt-8 pt-4 border-t border-arkhe-border/30 flex items-center justify-between">
         <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
               <div className="w-1.5 h-1.5 rounded-full bg-arkhe-green animate-pulse" />
               <span className="text-[9px] font-mono text-arkhe-muted uppercase">Amm-Pools: Connected</span>
            </div>
            <div className="flex items-center gap-2">
               <div className="w-1.5 h-1.5 rounded-full bg-arkhe-green animate-pulse" />
               <span className="text-[9px] font-mono text-arkhe-muted uppercase">Rate-Oracles: Synced</span>
            </div>
         </div>
         <div className="text-[9px] font-mono text-arkhe-muted">
            SYNC_EPOCH_BLOCK: 18,472,813
         </div>
      </div>
    </div>
  );
}
