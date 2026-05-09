
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */


import { ShieldAlert } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';

import type { MetricsHistory } from '../../server/types';

import { Card } from './ui/Card';

interface ThreatDetectionProps {
  metrics: {
    musd: number;
    musda: number;
    wmaBc: number;
    threshold: number;
  };
  metricsHistory: MetricsHistory[];
  threatLevel: 'normal' | 'warning' | 'critical';
}

export default function ThreatDetection({ metrics, metricsHistory, threatLevel }: ThreatDetectionProps) {
  return (
    <Card
      title="Threat Detection (MuSD/MuSDA)"
      icon={<ShieldAlert className="w-4 h-4" />}
      status={threatLevel}
    >
      <div className="flex-1 flex flex-col">
        <div className="h-40 w-full mb-4">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={metricsHistory}>
              <XAxis dataKey="time" hide />
              <YAxis domain={[0, 1.5]} hide />
              <Tooltip
                contentStyle={{ backgroundColor: '#111214', borderColor: '#1f2024', fontFamily: 'monospace', fontSize: '10px' }}
                itemStyle={{ color: '#fff' }}
              />
              <ReferenceLine y={metrics.threshold} stroke="#8E9299" strokeDasharray="3 3" />
              <Line type="monotone" dataKey="musd" stroke="#FF3366" strokeWidth={2} dot={false} isAnimationActive={false} />
              <Line type="monotone" dataKey="musda" stroke="#FF9900" strokeWidth={2} dot={false} isAnimationActive={false} />
              <Line type="monotone" dataKey="wmaBc" stroke="#00FFCC" strokeWidth={2} dot={false} isAnimationActive={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="grid grid-cols-3 gap-2 text-center mb-4">
          <div className="bg-[#151619] border border-arkhe-border rounded p-2">
            <div className="text-[10px] text-arkhe-muted uppercase mb-1">MuSD</div>
            <div className={`text-xs font-mono font-bold ${metrics.musd > metrics.threshold ? 'text-arkhe-red' : 'text-arkhe-text'}`}>
              {metrics.musd.toFixed(3)}
            </div>
          </div>
          <div className="bg-[#151619] border border-arkhe-border rounded p-2">
            <div className="text-[10px] text-arkhe-muted uppercase mb-1">MuSDA</div>
            <div className={`text-xs font-mono font-bold ${metrics.musda > metrics.threshold ? 'text-arkhe-orange' : 'text-arkhe-text'}`}>
              {metrics.musda.toFixed(3)}
            </div>
          </div>
          <div className="bg-[#151619] border border-arkhe-border rounded p-2">
            <div className="text-[10px] text-arkhe-muted uppercase mb-1">WMA-BC</div>
            <div className={`text-xs font-mono font-bold ${metrics.wmaBc > metrics.threshold ? 'text-arkhe-cyan' : 'text-arkhe-text'}`}>
              {metrics.wmaBc.toFixed(3)}
            </div>
          </div>
        </div>

        <div className="mt-auto pt-4 border-t border-arkhe-border flex justify-between items-center">
          <div className="text-xs font-mono text-arkhe-muted uppercase">Detection Status</div>
          <div className={`text-xs font-mono font-bold px-2 py-1 rounded ${
            threatLevel === 'critical' ? 'bg-arkhe-red/20 text-arkhe-red animate-pulse' :
            threatLevel === 'warning' ? 'bg-arkhe-orange/20 text-arkhe-orange' :
            'bg-arkhe-green/20 text-arkhe-green'
          }`}>
            {threatLevel === 'critical' ? 'ATTACK DETECTED' :
             threatLevel === 'warning' ? 'ANOMALY DETECTED' :
             'CLEAR'}
          </div>
        </div>
      </div>
    </Card>
  );
}
