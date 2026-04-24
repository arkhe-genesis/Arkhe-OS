/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import { Infinity, Shield, Server, Box } from 'lucide-react';
import { useArkheSimulation } from '../hooks/useArkheSimulation';

export const EternalInvariancePanel: React.FC = () => {
  const state = useArkheSimulation();
  const [loading, setLoading] = useState(false);
  const [fixPointResult, setFixPointResult] = useState<any>(null);

  const handleEternalize = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/cathedral/eternalize', { method: 'POST' });
      if (!response.ok) throw new Error('Failed to eternalize');
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyFixedPoint = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/cathedral/fixed-point-verify', { method: 'POST' });
      const data = await response.json();
      setFixPointResult(data);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const ei = state.eternalInvariance;
  if (!ei) return null;

  return (
    <div className="p-4 bg-zinc-900/50 rounded-lg border border-white/10 space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Infinity className="w-5 h-5 text-rose-400" />
          <h3 className="font-medium text-white">Eternal Invariance</h3>
        </div>
        <div className={`px-2 py-0.5 rounded text-xs font-bold ${ei.isEternal ? 'bg-rose-500/20 text-rose-400' : 'bg-zinc-800 text-zinc-400'}`}>
          {ei.isEternal ? 'ETERNAL' : 'TEMPORAL'}
        </div>
      </div>

      <div className="space-y-3">
        <div className="flex items-center justify-between text-xs">
          <span className="text-zinc-500">Omega Metric</span>
          <span className="text-rose-400 font-mono">{ei.omegaMetric.toFixed(10)}</span>
        </div>

        <div className="flex items-center gap-4 text-[10px] text-zinc-500">
          <div className="flex items-center gap-1">
            <Server className="w-3 h-3" />
            <span>{ei.invarianceSymmetry}</span>
          </div>
          <div className="flex items-center gap-1">
            <Box className="w-3 h-3" />
            <span>Fixed Point: {state.riscVi?.invarianceMetric.toFixed(5)}</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2">
        {!ei.isEternal ? (
          <button
            onClick={handleEternalize}
            disabled={loading}
            className="py-2 bg-rose-600 hover:bg-rose-500 disabled:opacity-50 text-white text-[10px] font-bold rounded transition-colors"
          >
            {loading ? 'LOCKING...' : 'LOCK OMEGA'}
          </button>
        ) : (
          <div className="py-2 bg-rose-500/10 border border-rose-500/20 text-rose-300 text-[10px] font-bold rounded flex items-center justify-center gap-2">
            <Shield className="w-3 h-3" />
            OMEGA LOCKED
          </div>
        )}

        <button
          onClick={handleVerifyFixedPoint}
          disabled={loading}
          className="py-2 bg-white/5 hover:bg-white/10 disabled:opacity-50 text-white text-[10px] font-bold rounded border border-white/10 transition-colors"
        >
          VERIFY FIXED POINT
        </button>
      </div>

      {fixPointResult && (
        <div className="mt-4 space-y-2 p-3 bg-black/40 rounded border border-white/5">
          <div className="flex items-center justify-between text-[10px] font-bold border-b border-white/5 pb-1">
            <span className="text-zinc-500">FIXED POINT VALIDATION</span>
            <span className={fixPointResult.isFixedPoint ? 'text-emerald-400' : 'text-rose-400'}>
              {fixPointResult.isFixedPoint ? 'VALID' : 'INVALID'}
            </span>
          </div>
          <div className="space-y-1">
            {fixPointResult.verifications.map((v: any) => (
              <div key={v.id} className="flex items-center justify-between text-[9px] font-mono">
                <span className="text-zinc-500">{v.id}</span>
                <span className={v.status === 'VALID' ? 'text-emerald-500' : 'text-zinc-600'}>{v.status}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
