import React from 'react';
import ProtectionDashboard from './ProtectionDashboard';

const ProtectionShowcase: React.FC = () => {
  const now = Math.floor(Date.now() / 1000);

  return (
    <div className="p-10 space-y-10 bg-neutral-900 min-h-screen text-white">
      <h1 className="text-3xl font-bold mb-8">Neverland Protection Dashboard Showcase</h1>

      <div className="space-y-4">
        <h2 className="text-xl font-semibold text-emerald-400">1. Equity Secure (HF > 1.0)</h2>
        <ProtectionDashboard healthFactor={1.25} riskTimestamp={0} />
      </div>

      <div className="space-y-4">
        <h2 className="text-xl font-semibold text-amber-400">2. Safety Net Active (HF < 1.0, < 24h)</h2>
        <ProtectionDashboard healthFactor={0.85} riskTimestamp={now - (14 * 3600 + 22 * 60)} />
      </div>

      <div className="space-y-4">
        <h2 className="text-xl font-semibold text-red-400">3. Protection Expired (HF < 1.0, > 24h)</h2>
        <ProtectionDashboard healthFactor={0.75} riskTimestamp={now - (26 * 3600)} />
      </div>
    </div>
  );
};

export default ProtectionShowcase;
