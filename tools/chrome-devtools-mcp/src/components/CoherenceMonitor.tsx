
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Activity } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';

import { Card } from './ui/Card';


interface CoherenceMonitorProps {
  data: Array<{ time: string; lambda: number; threshold: number }>;
  currentLambda: number;
}

export default function CoherenceMonitor({ data, currentLambda }: CoherenceMonitorProps) {
  const isCritical = currentLambda < 0.618;
  const isWarning = currentLambda < 0.85 && currentLambda >= 0.618;

  return (
    <Card
      title="Coherence Monitor (λ₂)"
      icon={<Activity className="w-4 h-4" />}
      status={isCritical ? 'critical' : isWarning ? 'warning' : 'normal'}
      className="h-[300px]"
    >
      <div className="flex justify-between items-end mb-4">
        <div>
          <div className="text-arkhe-muted text-xs uppercase tracking-wider mb-1">Current λ₂</div>
          <div className={`text-4xl font-mono font-bold ${isCritical ? 'text-arkhe-red glitch' : isWarning ? 'text-arkhe-orange' : 'text-arkhe-green'}`}>
            {currentLambda.toFixed(4)}
          </div>
        </div>
        <div className="text-right">
          <div className="text-arkhe-muted text-xs uppercase tracking-wider mb-1">Threshold</div>
          <div className="text-lg font-mono text-arkhe-muted">0.6180</div>
        </div>
      </div>

      <div className="flex-1 w-full h-full min-h-0">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1f2024" vertical={false} />
            <XAxis
              dataKey="time"
              stroke="#8E9299"
              fontSize={10}
              tickLine={false}
              axisLine={false}
              minTickGap={30}
            />
            <YAxis
              domain={[0, 1]}
              stroke="#8E9299"
              fontSize={10}
              tickLine={false}
              axisLine={false}
              tickFormatter={(val: number) => val.toFixed(1)}
            />
            <Tooltip
              contentStyle={{ backgroundColor: '#111214', borderColor: '#1f2024', color: '#E0E0E0', fontSize: '12px', fontFamily: 'monospace' }}
              itemStyle={{ color: '#00E5FF' }}
            />
            <ReferenceLine y={0.618} stroke="#FF3366" strokeDasharray="3 3" opacity={0.5} />
            <Line
              type="monotone"
              dataKey="lambda"
              stroke={isCritical ? '#FF3366' : isWarning ? '#FF9900' : '#00E5FF'}
              strokeWidth={2}
              dot={false}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}
