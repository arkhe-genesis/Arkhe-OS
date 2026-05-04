/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { FileText, Download, Fingerprint, Calendar } from 'lucide-react';
import React from 'react';

import type { SimulationState } from '../../server/types';
import type { SimulationState, GovernanceDirective } from '../../server/types';

import { Card } from './ui/Card';

interface GovernanceManifestoPanelProps {
  state: SimulationState;
}

const GovernanceManifestoPanel: React.FC<GovernanceManifestoPanelProps> = ({ state }) => {
  const manifesto = state.governanceManifesto;

  if (!manifesto) {return null;}

  const handleExport = () => {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(manifesto, null, 2));
    const downloadAnchorNode = document.createElement('a');
    downloadAnchorNode.setAttribute("href", dataStr);
    downloadAnchorNode.setAttribute("download", "manifesto_governanca_2027.json");
    document.body.appendChild(downloadAnchorNode);
    downloadAnchorNode.click();
    downloadAnchorNode.remove();
  };

  return (
    <Card
      title="Manifesto de Governança 2027"
      icon={<FileText className="text-arkhe-cyan w-4 h-4" />}
      action={
        <button
          onClick={handleExport}
          className="p-1 hover:bg-arkhe-cyan/20 rounded transition-colors text-arkhe-cyan"
          title="Exportar JSON para Arkhe-Chain"
        >
          <Download className="w-4 h-4" />
        </button>
      }
      className="bg-[#0A0E17]/90 border-arkhe-cyan/30"
    >
      <div className="space-y-4 max-h-[350px] overflow-y-auto pr-2 scrollbar-hide">
        <div className="flex justify-between items-center text-[8px] font-mono text-white/40 border-b border-white/5 pb-2">
          <div className="flex items-center gap-1">
            <Calendar className="w-3 h-3" />
            {new Date(manifesto.timestamp).toLocaleDateString()}
          </div>
          <div className="flex items-center gap-1">
            <Fingerprint className="w-3 h-3" />
            {manifesto.version}
          </div>
        </div>

        <div className="space-y-3">
          {manifesto.directives?.map((d: any) => (
          {manifesto.directives.map((d: GovernanceDirective) => (
            <div key={d.id} className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="text-arkhe-cyan font-bold text-[10px]">{d.id}.</span>
                <h4 className="text-[10px] font-bold text-white/90 uppercase tracking-tight">{d.title}</h4>
              </div>
              <p className="text-[9px] text-white/60 leading-relaxed italic ml-4">
                {d.description}
              </p>
            </div>
          ))}
        </div>

        {manifesto.cellular_impact && (
          <div className="pt-3 border-t border-white/5 space-y-2">
            <p className="text-[8px] text-white/30 uppercase font-mono">Impacto Biológico Projetado</p>
            <div className="grid grid-cols-2 gap-2 text-[9px]">
              <div className="flex justify-between text-white/50">
                <span>Ganho Telomérico:</span>
                <span className="text-[#00FFAA]">+{manifesto.cellular_impact.telomere_gain}%</span>
              </div>
              <div className="flex justify-between text-white/50">
                <span>Redução Estresse:</span>
                <span className="text-[#00FFAA]">{manifesto.cellular_impact.oxidative_stress}%</span>
              </div>
            </div>
          </div>
        )}

        <div className="pt-2">
          <p className="text-[7px] text-white/20 font-mono break-all leading-tight">
            SIGNATURE: {manifesto.signature}
          </p>
        </div>
      </div>
    </Card>
  );
};

export default GovernanceManifestoPanel;
