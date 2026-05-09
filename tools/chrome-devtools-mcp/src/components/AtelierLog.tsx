
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Terminal, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
import React, { useState } from 'react';

import { Card } from './ui/Card';


interface LogEntry {
  agent: string;
  message: string;
  status: 'PENDING' | 'SUCCESS' | 'ERROR';
  timestamp: string;
}

export default function AtelierLog() {
  const [logs] = useState<LogEntry[]>([
    {
      agent: 'REACHABILITY_AGENT',
      message: 'Analyzing DREAMS.md for RIO_2027_STABILITY...',
      status: 'SUCCESS',
      timestamp: new Date().toLocaleTimeString()
    },
    {
      agent: 'REACHABILITY_AGENT',
      message: 'Synthesizing Lean 4 tactic: simp [dream_feasibility]',
      status: 'SUCCESS',
      timestamp: new Date().toLocaleTimeString()
    },
    {
      agent: 'MANIFESTATION_AGENT',
      message: 'Proof 0x7b2f verified. Initiating Veo-3.1 Synthesis...',
      status: 'PENDING',
      timestamp: new Date().toLocaleTimeString()
    }
  ]);

  return (
    <Card className="mt-4 bg-[#0a0a0a] border-arkhe-cyan/20 p-4 font-mono">
      <div className="flex items-center gap-2 mb-4 text-arkhe-cyan border-b border-arkhe-cyan/20 pb-2">
        <Terminal className="w-4 h-4" />
        <span className="text-xs uppercase tracking-tighter">Atelier Collaborative Log</span>
      </div>
      <div className="space-y-3 max-h-60 overflow-y-auto">
        {logs.map((log, idx) => (
          <div key={idx} className="flex gap-3 text-[10px] leading-relaxed">
            <span className="text-arkhe-muted">[{log.timestamp}]</span>
            <span className="text-arkhe-cyan font-bold">{log.agent}</span>
            <span className="flex-1 text-arkhe-text">{log.message}</span>
            {log.status === 'SUCCESS' && <CheckCircle2 className="w-3 h-3 text-green-500" />}
            {log.status === 'PENDING' && <Loader2 className="w-3 h-3 text-arkhe-cyan animate-spin" />}
            {log.status === 'ERROR' && <AlertCircle className="w-3 h-3 text-arkhe-red" />}
          </div>
        ))}
      </div>
    </Card>
  );
}
