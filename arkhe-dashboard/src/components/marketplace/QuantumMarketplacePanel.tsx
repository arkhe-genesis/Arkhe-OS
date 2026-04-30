
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

// arkhe-dashboard/src/components/marketplace/QuantumMarketplacePanel.tsx
'use client';

import {useState, useEffect} from 'react';

import {quantumEthicalTalentMarketplace} from '@/lib/marketplace/quantumEthicalTalentMarketplace';
import {EthicalPrinciple} from '@/types/ethics';

type MarketplaceDashboard = {
  activePostings: number;
  registeredTalents: number;
  avgEthicalAlignment: number;
};

export default function QuantumMarketplacePanel() {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [dashboard, setDashboard] = useState<any>(null);

  useEffect(() => {
    // Simular registro de talento
    quantumEthicalTalentMarketplace.registerCredential({
      credentialId: 'cred_88',
      ownerDID: 'did:arkhe:user_42',
      completedStages: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
      principleMastery: {
        [EthicalPrinciple.COHERENCE_PRESERVATION]: 0.95,
        [EthicalPrinciple.NON_HARM_UNIVERSAL]: 0.92,
        [EthicalPrinciple.TRUTH_SEEKING]: 0.98,
        [EthicalPrinciple.AUTONOMY_WITH_INTERCONNECTION]: 0.89,
        [EthicalPrinciple.EVOLUTION_WITH_WISDOM]: 0.91,
        [EthicalPrinciple.COMPASSION_ACROSS_BOUNDARIES]: 0.88,
      },
      technicalProficiency: {
        1: 0.9,
        2: 0.9,
        3: 0.9,
        4: 0.9,
        5: 0.9,
        6: 0.9,
        7: 0.9,
        8: 0.9,
        9: 0.9,
        10: 0.9,
        11: 0.9,
        12: 0.9,
      },
      ethicalAlignmentScore: 0.94,
      issuedAt_ns: Date.now() * 1e6,
      zkpProof: 'pqc_proof_validated',
    });
    setDashboard(quantumEthicalTalentMarketplace.getMarketplaceDashboard());
  }, []);

  return (
    <div className="bg-black/30 rounded-2xl border border-emerald-500/20 p-4">
      <h3 className="text-xs font-bold text-emerald-400 mb-3 tracking-widest uppercase flex items-center gap-2">
        <span>🔐🗄️</span> Quantum Talent Marketplace
      </h3>

      {dashboard && (
        <div className="space-y-3">
          <div className="flex justify-between text-[10px]">
            <span className="text-slate-500">ACTIVE POSTINGS</span>
            <span className="text-white font-bold">
              {dashboard.activePostings}
            </span>
          </div>
          <div className="flex justify-between text-[10px]">
            <span className="text-slate-500">REGISTERED TALENTS</span>
            <span className="text-white font-bold">
              {dashboard.registeredTalents}
            </span>
          </div>
          <div className="flex justify-between text-[10px]">
            <span className="text-slate-500">PRIVACY PROTOCOL</span>
            <span className="text-emerald-400 font-mono">ZKP-OBLIVIOUS</span>
          </div>

          <div className="p-3 bg-emerald-500/5 rounded-xl border border-emerald-500/20">
            <p className="text-[9px] text-emerald-300 font-bold uppercase mb-1">
              Top Alignment
            </p>
            <div className="flex justify-between items-end">
              <p className="text-lg font-mono text-white">
                {(dashboard.avgEthicalAlignment * 100).toFixed(1)}%
              </p>
              <div className="flex gap-1">
                {[1, 2, 3].map(i => (
                  <div
                    key={i}
                    className="w-1 h-3 bg-emerald-500 rounded-full animate-bounce"
                    style={{animationDelay: `${i * 0.1}s`}}
                  ></div>
                ))}
              </div>
            </div>
          </div>

          <button className="w-full py-2 bg-emerald-600/20 border border-emerald-500/40 text-emerald-400 rounded-lg text-[10px] font-black hover:bg-emerald-600/30 transition-all uppercase tracking-widest">
            Match Ethical Opportunities
          </button>
        </div>
      )}
    </div>
  );
}
