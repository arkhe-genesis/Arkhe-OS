
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Brain, FlaskConical, Play } from 'lucide-react';
import React from 'react';

import type { LatentCoherenceResults } from '../../server/types';

import { Card } from './ui/Card';

interface LatentCoherencePanelProps {
  results?: LatentCoherenceResults;
  onRunExperiment: () => void;
}

const LatentCoherencePanel: React.FC<LatentCoherencePanelProps> = ({ results, onRunExperiment }) => {
  if (!results) {return null;}

  return (
    <Card
      title="LATENT COHERENCE"
      icon={<Brain className="w-4 h-4 text-purple-400" />}
      className="font-mono"
    >
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-2 text-[10px]">
          <div className="p-2 bg-red-500/5 border border-red-500/20 rounded">
            <p className="text-red-400 font-bold mb-1 uppercase">AVG λ₂ (CoT)</p>
            <p className="text-lg">{results.summary.avg_lambda_cot.toFixed(4)}</p>
          </div>
          <div className="p-2 bg-purple-500/5 border border-purple-500/20 rounded">
            <p className="text-purple-400 font-bold mb-1 uppercase">AVG λ₂ (CoCT)</p>
            <p className="text-lg">{results.summary.avg_lambda_coct.toFixed(4)}</p>
          </div>
        </div>

        <button
          onClick={onRunExperiment}
          className="w-full flex items-center justify-center gap-2 py-2 bg-purple-600/20 border border-purple-500/40 hover:bg-purple-600/30 transition-colors text-purple-300 text-[10px] font-bold text-white"
        >
          <Play className="w-3 h-3" />
          RUN REASONING EXPERIMENT
        </button>

        <div className="flex items-center gap-2 text-[9px] text-arkhe-muted">
          <FlaskConical className="w-3 h-3" />
          <span>Hypothesis: CoCT stabilizes phase attractor (state 'a')</span>
        </div>
      </div>
    </Card>
  );
};

export default LatentCoherencePanel;
