
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */


import { Clock } from 'lucide-react';

import type { OrbLog } from '../../server/types';

import { Card } from './ui/Card';

interface TemporalLogProps {
  logs: OrbLog[];
}

export default function TemporalLog({ logs }: TemporalLogProps) {
  const formatTime = (ms: number) => {
    const d = new Date(ms);
    return `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}:${d.getSeconds().toString().padStart(2, '0')}.${d.getMilliseconds().toString().padStart(3, '0')}`;
  };

  return (
    <Card
      title="Temporal Orb Log (HTTP/4 PNT)"
      icon={<Clock className="w-4 h-4" />}
      className="h-full"
    >
      <div className="overflow-auto h-full pr-2">
        <table className="w-full text-left border-collapse">
          <thead className="sticky top-0 bg-arkhe-card z-10">
            <tr>
              <th className="py-2 px-2 text-[10px] font-mono text-arkhe-muted uppercase border-b border-arkhe-border">Orb ID</th>
              <th className="py-2 px-2 text-[10px] font-mono text-arkhe-muted uppercase border-b border-arkhe-border">Origin Time</th>
              <th className="py-2 px-2 text-[10px] font-mono text-arkhe-muted uppercase border-b border-arkhe-border">Target Time</th>
              <th className="py-2 px-2 text-[10px] font-mono text-arkhe-muted uppercase border-b border-arkhe-border">λ₂</th>
              <th className="py-2 px-2 text-[10px] font-mono text-arkhe-muted uppercase border-b border-arkhe-border">Status</th>
            </tr>
          </thead>
          <tbody className="font-mono text-xs">
            {logs.map((log, i) => {
              const isRejected = log.status === 'Rejected';
              const isMitigated = log.status === 'Mitigated';

              return (
                <tr key={`${log.id}-${i}`} className="border-b border-arkhe-border/50 hover:bg-[#151619] transition-colors">
                  <td className="py-2 px-2 text-arkhe-muted truncate max-w-[80px]" title={log.id}>
                    {log.id.substring(0, 8)}
                  </td>
                  <td className={`py-2 px-2 ${isRejected ? 'text-arkhe-red' : 'text-arkhe-text'}`}>
                    {formatTime(log.originTime || 0)}
                  </td>
                  <td className="py-2 px-2 text-arkhe-text">
                    {formatTime(log.targetTime || 0)}
                  </td>
                  <td className={`py-2 px-2 ${log.coherence < 0.618 ? 'text-arkhe-red' : 'text-arkhe-cyan'}`}>
                    {log.coherence.toFixed(3)}
                  </td>
                  <td className="py-2 px-2">
                    <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                      isRejected ? 'bg-arkhe-red/20 text-arkhe-red' :
                      isMitigated ? 'bg-arkhe-orange/20 text-arkhe-orange' :
                      'bg-arkhe-green/20 text-arkhe-green'
                    }`}>
                      {log.status.toUpperCase()}
                    </span>
                    {log.threatType && (
                      <span className="ml-2 text-[9px] text-arkhe-muted uppercase">
                        {log.threatType}
                      </span>
                    )}
                  </td>
                </tr>
              );
            })}
            {logs.length === 0 && (
              <tr>
                <td colSpan={5} className="py-4 text-center text-arkhe-muted text-xs font-mono">
                  Awaiting Orb telemetry...
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
