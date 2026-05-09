
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { AlertTriangle, CheckCircle, ShieldAlert } from 'lucide-react';
import React, { useEffect, useState } from 'react';

import { logger } from '../../server/logger';

interface ConsensusState {
  sigma: number;
}

export const ConsensusMeter: React.FC = () => {
  const [sigma, setSigma] = useState<number>(1.0);
  const [status, setStatus] = useState<'healthy' | 'warning' | 'critical'>('healthy');

  useEffect(() => {
    const fetchConsensus = async () => {
      try {
        const response = await fetch('/api/state/sigma');
        const data: ConsensusState = await response.json();
        setSigma(data.sigma);

        if (data.sigma > 0.9) {
          setStatus('healthy');
        } else if (data.sigma > 0.75) {
          setStatus('warning');
        } else {
          setStatus('critical');
        }
      } catch (error) {
        logger.error('Failed to fetch consensus state: ' + error);
        setStatus('critical');
        setSigma(0.5); // Fallback to critical on error
      }
    };

    const interval = setInterval(() => { void fetchConsensus(); }, 5000);
    void fetchConsensus(); // Initial fetch

    return () => clearInterval(interval);
  }, []);

  const getStatusColor = () => {
    switch (status) {
      case 'healthy': return 'text-green-500';
      case 'warning': return 'text-yellow-500';
      case 'critical': return 'text-red-500';
    }
  };

  const getStatusBg = () => {
    switch (status) {
      case 'healthy': return 'bg-green-500/20 border-green-500/50';
      case 'warning': return 'bg-yellow-500/20 border-yellow-500/50';
      case 'critical': return 'bg-red-500/20 border-red-500/50';
    }
  };

  return (
    <div className={`p-4 rounded-lg border flex flex-col items-center justify-center space-y-4 ${getStatusBg()}`}>
      <div className="flex items-center space-x-2">
        {status === 'healthy' && <CheckCircle className={`w-6 h-6 ${getStatusColor()}`} />}
        {status === 'warning' && <AlertTriangle className={`w-6 h-6 ${getStatusColor()}`} />}
        {status === 'critical' && <ShieldAlert className={`w-6 h-6 ${getStatusColor()}`} />}
        <h3 className={`text-lg font-bold uppercase tracking-wider ${getStatusColor()}`}>
          Consensus Health (Σ)
        </h3>
      </div>

      <div className="text-4xl font-mono font-bold text-white">
        {sigma.toFixed(4)}
      </div>

      <div className="w-full bg-black/50 h-2 rounded-full overflow-hidden">
        <div
          className={`h-full ${status === 'healthy' ? 'bg-green-500' : status === 'warning' ? 'bg-yellow-500' : 'bg-red-500'}`}
          style={{ width: `${Math.max(0, Math.min(100, sigma * 100))}%` }}
        />
      </div>

      <div className="text-xs text-white/60 font-mono text-center">
        {status === 'healthy' && 'Network Coherence Optimal. No reorgs detected.'}
        {status === 'warning' && 'Entropy Detected. Hashrate drop or minor forks.'}
        {status === 'critical' && 'CRITICAL: Severe Decoherence! Potential chain split.'}
      </div>
    </div>
  );
};
export default ConsensusMeter;
