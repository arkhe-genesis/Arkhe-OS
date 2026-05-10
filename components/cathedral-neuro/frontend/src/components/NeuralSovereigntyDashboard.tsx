// frontend/src/components/NeuralSovereigntyDashboard.tsx
import React, { useState } from 'react';

export const NeuralSovereigntyDashboard: React.FC<{participantDid: string}> = ({ participantDid }) => {
  return (
    <div className="neural-sovereignty-dashboard">
      <h2>🧠🦾 Painel de Soberania Neural</h2>
      <p>ID do Participante: {participantDid}</p>
      <div className="status-grid">
        <div className="status-card">Status do Quantum Bus: 🟢</div>
        <div className="status-card">Consentimento Ativo: ✅</div>
      </div>
    </div>
  );
};
