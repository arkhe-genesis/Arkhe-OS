'use client';
/**
 * @license
 * Copyright 2025 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import dynamic from 'next/dynamic';
import React, {useEffect, useState, useCallback} from 'react';

import CosmicMemoryViewer from '@/components/CosmicMemoryViewer';
import EthicalPredictionChart from '@/components/EthicalPredictionChart';
import HomomorphicTrainingPanel from '@/components/homomorphic/HomomorphicTrainingPanel';
import QuantumMarketplacePanel from '@/components/marketplace/QuantumMarketplacePanel';
import CoherentMeditationPanel from '@/components/meditation/CoherentMeditationPanel';
import P2PNetworkStatus from '@/components/network/P2PNetworkStatus';
import InterCathedralPanel from '@/components/quantum/InterCathedralPanel';
import QuantumTelepathyPanel from '@/components/quantum/QuantumTelepathyPanel';
import SynchronicityBlockchainPanel from '@/components/quantum/SynchronicityBlockchainPanel';
import RetrocausalWisdomPanel from '@/components/retrocausality/RetrocausalWisdomPanel';
import NeuralCoherenceBar from '@/components/security/NeuralCoherenceBar';
import SafeCorePanel from '@/components/security/SafeCorePanel';
import EthicalSimulatorPanel from '@/components/simulator/EthicalSimulatorPanel';
import PoCNetworkPanel from '@/components/poc/PoCNetworkPanel';
import TelemetryStream from '@/components/TelemetryStream';
import ZKPVerificationPanel from '@/components/ZKPVerificationPanel';
import {ethicalFederatedLearner} from '@/lib/ai/ethicalFederatedLearner';
import {useZustandStore} from '@/lib/store';
import {createTenant, listNetworks} from '@/lib/api-client';
import type {EthicalMetrics} from '@/types/ethics';
import type {NetworkSummary} from '@/types/api';

const ArkheCore3D = dynamic(() => import('@/components/ArkheCore3D'), {
  ssr: false,
});
const QuantumARViewer = dynamic(
  () => import('@/components/ar/QuantumARViewer'),
  {ssr: false},
);

export default function DashboardPage() {
  const {metrics, setMetrics, predictions, setPredictions} = useZustandStore();
  const [isTraining, setIsTraining] = useState(false);
  const [federatedMetrics, setFederatedMetrics] = useState<
    Record<string, number>
  >({});
  const [activeTab, setActiveTab] = useState<'3d' | 'ar' | 'scaffold'>('3d');
  const [networks, setNetworks] = useState<NetworkSummary[]>([]);
  const [tenantId, setTenantId] = useState<string>('');

  // Multi-tenant PoC network init
  useEffect(() => {
    const stored = localStorage.getItem('arkhe_tenant_id');
    if (!stored) {
      const newId = 'tenant_' + Math.random().toString(36).slice(2, 10);
      localStorage.setItem('arkhe_tenant_id', newId);
      setTenantId(newId);
    } else {
      setTenantId(stored);
    }
  }, []);

  // Load coherence networks
  useEffect(() => {
    if (!tenantId) return;
    void listNetworks(tenantId)
      .then(setNetworks)
      .catch(() => setNetworks([]));
  }, [tenantId]);

  // Conexão WebSocket Simulada
  useEffect(() => {
    const interval = setInterval(() => {
      const nextMetrics: EthicalMetrics = {
        ...metrics,
        omega: 0.9418 + (Math.random() - 0.5) * 0.005,
        kEth: 0.9312 + (Math.random() - 0.5) * 0.002,
        crystalTick: metrics.crystalTick + 1,
        timestamp: Date.now(),
      };
      setMetrics(nextMetrics);
    }, 2000);

    return () => clearInterval(interval);
  }, [metrics, setMetrics]);

  // Predição federada
  const requestPrediction = useCallback(async () => {
    try {
      const prediction = await ethicalFederatedLearner.predict(metrics);
      setPredictions(prediction);
    } catch (error) {
      console.error('Prediction failed:', error);
    }
  }, [metrics, setPredictions]);

  // Treinamento federado local
  const handleFederatedTraining = useCallback(async () => {
    setIsTraining(true);
    try {
      const localData = {
        features: Array.from({length: 50}, () =>
          Array.from({length: 10}, () =>
            Array.from({length: 6}, () => 0.9 + Math.random() * 0.1),
          ),
        ),
        labels: Array.from({length: 50}, () => 0.92 + Math.random() * 0.08),
      };

      const update = await ethicalFederatedLearner.trainLocalModel(
        'client_arkhe_dashboard',
        localData,
        3,
      );

      const response = await fetch('/api/federated/aggregate', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          action: 'submit_update',
          ...update,
          modelWeights: update.modelWeights.map(w => Array.from(w)),
        }),
      });

      const result = await response.json();
      if (result.success) {
        setFederatedMetrics(result.data);
      }
    } catch (error) {
      console.error('Federated training failed:', error);
    } finally {
      setIsTraining(false);
    }
  }, []);

  return (
    <div className="min-h-screen bg-[#020305] text-white p-6 selection:bg-cyan-500/30">
      <header className="flex justify-between items-center mb-8 border-b border-white/5 pb-6">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-cyan-500 rounded-2xl flex items-center justify-center shadow-[0_0_20px_rgba(0,229,255,0.3)]">
            <span className="text-2xl font-bold text-black">Ω</span>
          </div>
          <div>
            <h1 className="text-2xl font-black tracking-tighter uppercase italic">
              Arkhe OS <span className="text-cyan-400">v19-Collective</span>
            </h1>
            <p className="text-[10px] font-mono text-slate-500 tracking-[0.2em]">
              ODÔMETRO: 002186 | STATUS: ACT_IV_SCAFFOLD | TENANT: {tenantId.slice(0, 12)}...
            </p>
          </div>
        </div>

        <div className="flex gap-3">
          <button
            onClick={() => void requestPrediction()}
            className="px-6 py-2 bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 rounded-xl text-xs font-bold hover:bg-cyan-500/20 transition-all"
          >
            🔮 PREDIÇÃO FEDERADA
          </button>
          <button
            onClick={() => void handleFederatedTraining()}
            disabled={isTraining}
            className="px-6 py-2 bg-purple-500/20 border border-purple-500/40 text-purple-300 rounded-xl text-xs font-bold hover:bg-purple-500/30 transition-all disabled:opacity-50 shadow-[0_0_15px_rgba(168,85,247,0.1)]"
          >
            {isTraining ? '🤝 SINCRONIZANDO...' : '🤝 TREINO COLETIVO'}
          </button>
        </div>
      </header>

      <div className="grid grid-cols-12 gap-6">
        {/* Main Viewport */}
        <div className="col-span-12 lg:col-span-8 space-y-6">
          <div className="bg-black/40 border border-white/5 rounded-[2rem] p-8 min-h-[600px] relative overflow-hidden group">
            <div className="absolute top-8 left-8 z-20 flex gap-4">
              <button
                onClick={() => setActiveTab('3d')}
                className={`px-4 py-1.5 rounded-full text-[10px] font-bold tracking-widest transition-all ${activeTab === '3d' ? 'bg-cyan-500 text-black' : 'bg-white/5 text-slate-400'}`}
              >
                CAMPO Ω 3D
              </button>
              <button
                onClick={() => setActiveTab('scaffold')}
                className={`px-4 py-1.5 rounded-full text-[10px] font-bold tracking-widest transition-all ${activeTab === 'scaffold' ? 'bg-indigo-600 text-white shadow-[0_0_15px_rgba(79,70,229,0.5)]' : 'bg-white/5 text-slate-400'}`}
              >
                SCAFFOLD INTERNO
              </button>
              <button
                onClick={() => setActiveTab('ar')}
                className={`px-4 py-1.5 rounded-full text-[10px] font-bold tracking-widest transition-all ${activeTab === 'ar' ? 'bg-purple-500 text-white' : 'bg-white/5 text-slate-400'}`}
              >
                QUANTUM AR
              </button>
            </div>

            {activeTab === '3d' ? (
              <ArkheCore3D
                omega={metrics.omega}
                kEth={metrics.kEth}
              />
            ) : activeTab === 'scaffold' ? (
              <ArkheCore3D
                omega={metrics.omega}
                kEth={metrics.kEth}
                scaffoldMode={true}
              />
            ) : (
              <QuantumARViewer
                metrics={metrics}
                onSessionChange={() => {
                  /* noop */
                }}
              />
            )}

            {/* Bottom Metrics Overlay */}
            <div className="absolute bottom-8 left-8 right-8 grid grid-cols-4 gap-4 pointer-events-none">
              <NeuralCoherenceBar />
              <div className="bg-black/60 backdrop-blur-md p-4 rounded-2xl border border-white/5">
                <p className="text-[10px] text-slate-500 mb-1">CONSTANTE K</p>
                <p className="text-lg font-bold text-purple-400">
                  {metrics.kEth.toFixed(4)}
                </p>
              </div>
              <div className="bg-black/60 backdrop-blur-md p-4 rounded-2xl border border-white/5">
                <p className="text-[10px] text-slate-500 mb-1">FIDELIDADE Q</p>
                <p className="text-lg font-bold text-emerald-400">
                  {(metrics.quantumFidelity * 100).toFixed(1)}%
                </p>
              </div>
              <div className="bg-black/60 backdrop-blur-md p-4 rounded-2xl border border-white/5">
                <p className="text-[10px] text-slate-500 mb-1">
                  PRIVACIDADE (ε)
                </p>
                <p className="text-lg font-bold text-amber-400">
                  {federatedMetrics?.privacyBudget?.toFixed(2) || '0.00'}
                </p>
              </div>
            </div>
          </div>

          {/* Federated Summary */}
          {federatedMetrics?.roundNumber && (
            <div className="bg-gradient-to-r from-purple-900/20 to-cyan-900/20 border border-white/10 rounded-3xl p-6 flex justify-between items-center">
              <div className="flex items-center gap-6">
                <div className="flex -space-x-3">
                  {[1, 2, 3, 4].map(i => (
                    <div
                      key={i}
                      className="w-10 h-10 rounded-full bg-slate-800 border-2 border-black flex items-center justify-center text-[10px] font-bold"
                    >
                      C{i}
                    </div>
                  ))}
                  <div className="w-10 h-10 rounded-full bg-cyan-500 border-2 border-black flex items-center justify-center text-[10px] font-bold text-black">
                    +{federatedMetrics.participatingClients - 1}
                  </div>
                </div>
                <div>
                  <h4 className="text-xs font-bold text-white uppercase">
                    Rede Coletiva Ativa
                  </h4>
                  <p className="text-[10px] text-slate-400">
                    Rodada #{federatedMetrics.roundNumber} completada com
                    sucesso
                  </p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-[10px] text-slate-500">
                  PERDA MÉDIA (GLOBAL)
                </p>
                <p className="font-mono text-cyan-400">
                  {federatedMetrics.avgLoss?.toFixed(8)}
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="col-span-12 lg:col-span-4 space-y-6">
          <EthicalPredictionChart
            currentMetrics={metrics}
            prediction={predictions}
            loading={false}
          />
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-1 gap-6">
            <SafeCorePanel />
            <RetrocausalWisdomPanel />
            <QuantumMarketplacePanel />
            <SynchronicityBlockchainPanel />
            <InterCathedralPanel />
            <CoherentMeditationPanel />
            <PoCNetworkPanel networks={networks} tenantId={tenantId} />
            <CosmicMemoryViewer currentMetrics={metrics} />
            <HomomorphicTrainingPanel />
            <EthicalSimulatorPanel />
            <P2PNetworkStatus />
          </div>
          <QuantumTelepathyPanel />
          <ZKPVerificationPanel />
          <TelemetryStream metrics={metrics} />
        </div>
      </div>
    </div>
  );
}
