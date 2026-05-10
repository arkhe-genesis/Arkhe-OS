// frontend/src/components/multimodal/EcoGSignalViewer.tsx
import React, { useState } from 'react';

export const EcoGSignalViewer: React.FC<{participantDid: string}> = ({ participantDid }) => {
  return (
    <div className="ecog-signal-viewer">
      <h3>📡 Sinal ECoG em Tempo Real</h3>
      <p>Participante: {participantDid}</p>
      <div className="ecog-grid-mock">Grid 64 canais: 🟢 Ativo</div>
    </div>
  );
};
