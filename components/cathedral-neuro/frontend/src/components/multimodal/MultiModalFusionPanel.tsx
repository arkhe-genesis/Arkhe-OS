// frontend/src/components/multimodal/MultiModalFusionPanel.tsx
import React, { useState } from 'react';
import { EcoGSignalViewer } from './EcoGSignalViewer';

export const MultiModalFusionPanel: React.FC<{participantDid: string}> = ({ participantDid }) => {
  return (
    <div className="multimodal-fusion-panel">
      <h3>🧩 Fusão Multi-Modal: EEG + ECoG</h3>
      <EcoGSignalViewer participantDid={participantDid} />
      <div className="fusion-status">Confiança da Fusão: 94.2%</div>
    </div>
  );
};
