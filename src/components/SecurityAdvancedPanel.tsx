
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Shield, Lock, Zap, Eye, Database, RefreshCw, AlertTriangle, CheckCircle2, Flame } from 'lucide-react';
import React, { useState } from 'react';

import type { SimulationState } from '../../server/types';
import { useArkheSimulation } from '../hooks/useArkheSimulation';

interface SecurityAdvancedPanelProps {
  onClose: () => void;
}

export default function SecurityAdvancedPanel({ onClose }: SecurityAdvancedPanelProps) {
  const state: any = useArkheSimulation();
  const [activeTab, setActiveTab] = useState<'l1' | 'l2' | 'l3' | 'l4' | 'l5' | 'qhttp'>('l1');
  const [attesting, setAttesting] = useState(false);
  const [syncing, setSyncing] = useState(false);

  const security = state.securityAdvanced;

  const triggerAttestation = async () => {
    setAttesting(true);
    await fetch('/api/security/remote-attestation', { method: 'POST' });
    setAttesting(false);
  };

  const triggerHsmSync = async () => {
    setSyncing(true);
    await fetch('/api/security/hsm-sync', { method: 'POST' });
    setSyncing(false);
  };

  const toggleThermal = async () => {
    await fetch('/api/security/thermal-destruction', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ arm: !security.l1.thermalDestructionArmed })
    });
  };

  const signOntology = async () => {
    await fetch('/api/security/ontology-sign', { method: 'POST' });
  };

  const LayerStatus = ({ status, label }: { status: boolean | string, label: string }) => {
    const isValid = typeof status === 'string' ? (status === 'secure' || status === 'active' || status === 'verified' || status === 'enforced') : status;
    return (
      <div className="flex items-center justify-between p-2 border-b border-arkhe-border/30">
        <span className="text-arkhe-muted uppercase tracking-tighter">{label}</span>
        <div className="flex items-center gap-2">
          <span className={`text-[10px] font-bold uppercase ${isValid ? 'text-arkhe-green' : 'text-arkhe-red'}`}>
            {typeof status === 'string' ? status : (status ? 'VERIFIED' : 'FAILED')}
          </span>
          {isValid ? <CheckCircle2 className="w-3 h-3 text-arkhe-green" /> : <AlertTriangle className="w-3 h-3 text-arkhe-red" />}
        </div>
      </div>
    );
  };

  return (
    <div className="bg-arkhe-bg border border-arkhe-cyan/50 rounded-xl overflow-hidden shadow-[0_0_30px_rgba(0,255,170,0.15)] flex flex-col h-[600px] w-full max-w-4xl font-mono">
      {/* Header */}
      <div className="bg-arkhe-cyan/10 border-b border-arkhe-cyan/30 p-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Shield className="w-6 h-6 text-arkhe-cyan animate-pulse" />
          <div>
            <h2 className="text-arkhe-cyan font-bold tracking-[0.2em] uppercase text-sm">Arquiteto da República HYDRO-Ω</h2>
            <p className="text-[10px] text-arkhe-muted">SISTEMA DE SEGURANÇA AVANÇADA // CAMADAS L1-L5</p>
          </div>
        </div>
        <button onClick={onClose} className="text-arkhe-muted hover:text-arkhe-cyan transition-colors text-xs">[ FECHAR ]</button>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Navigation */}
        <div className="w-48 bg-black/40 border-r border-arkhe-border flex flex-col p-2 gap-1">
          {(['l1', 'l2', 'l3', 'l4', 'l5', 'qhttp'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`p-3 text-left rounded-lg transition-all border ${activeTab === tab ? 'bg-arkhe-cyan/20 border-arkhe-cyan/50 text-arkhe-cyan shadow-[0_0_10px_rgba(0,255,170,0.2)]' : 'border-transparent text-arkhe-muted hover:bg-white/5'}`}
            >
              <div className="text-[10px] opacity-60">CAMADA</div>
              <div className="text-xs font-bold uppercase tracking-widest">{tab === 'qhttp' ? 'qhttp-Ω' : tab.toUpperCase()}</div>
            </button>
          ))}
          <div className="mt-auto p-2 border-t border-arkhe-border/30">
            <div className="text-[10px] text-arkhe-muted mb-1 uppercase">Coerência Kuramoto</div>
            <div className="h-1 bg-arkhe-border rounded-full overflow-hidden">
              <div className="h-full bg-arkhe-cyan transition-all duration-1000" style={{ width: `${state.currentLambda * 100}%` }}></div>
            </div>
            <div className="text-right text-[10px] text-arkhe-cyan mt-1">R(t): {state.currentLambda.toFixed(4)}</div>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 p-6 bg-arkhe-card/50 overflow-y-auto">
          {activeTab === 'l1' && (
            <div className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-black/60 border border-arkhe-border p-4 rounded-lg">
                  <h4 className="text-arkhe-cyan text-xs font-bold mb-3 uppercase tracking-widest flex items-center gap-2">
                    <Database className="w-4 h-4" /> Hardware / QD-L1
                  </h4>
                  <div className="space-y-2">
                    <LayerStatus label="Status TEE (SGX)" status={security.l1.teeStatus} />
                    <LayerStatus label="Sensor de Intrusão" status={security.l1.intrusionSensor} />
                    <LayerStatus label="HSM Cloud Sync" status={security.l1.hsmBackupSynced} />
                  </div>
                </div>
                <div className="bg-black/60 border border-arkhe-border p-4 rounded-lg flex flex-col justify-between">
                  <div>
                    <h4 className="text-arkhe-red text-xs font-bold mb-3 uppercase tracking-widest flex items-center gap-2">
                      <Flame className="w-4 h-4" /> Protocolo de Extermínio
                    </h4>
                    <p className="text-[10px] text-arkhe-muted mb-4 leading-relaxed">
                      ATIVAÇÃO TÉRMICA DOS CENTROS NV (+600°C) EM CASO DE VIOLAÇÃO FÍSICA DETECTADA PELO ENCLAVE.
                    </p>
                  </div>
                  <button
                    onClick={toggleThermal}
                    className={`w-full py-2 rounded border font-bold text-[10px] transition-all ${security.l1.thermalDestructionArmed ? 'bg-arkhe-red border-arkhe-red text-white shadow-[0_0_15px_rgba(255,51,51,0.4)]' : 'border-arkhe-red/50 text-arkhe-red hover:bg-arkhe-red/10'}`}
                  >
                    {security.l1.thermalDestructionArmed ? 'SISTEMA ARMADO' : 'ARMAR DESTRUIÇÃO TÉRMICA'}
                  </button>
                </div>
              </div>

              <div className="bg-black/40 border border-arkhe-border p-4 rounded-lg">
                <h4 className="text-arkhe-cyan text-xs font-bold mb-4 uppercase tracking-widest">Atestação Remota Periódica</h4>
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <div className="text-[10px] text-arkhe-muted mb-1">ÚLTIMO QUOTE VALIDADO</div>
                    <div className="text-xs font-mono text-arkhe-text">{security.l1.lastRemoteAttestation}</div>
                  </div>
                  <button
                    onClick={triggerAttestation}
                    disabled={attesting}
                    className="px-4 py-2 bg-arkhe-cyan/10 border border-arkhe-cyan/50 text-arkhe-cyan rounded text-[10px] hover:bg-arkhe-cyan/20 transition-all flex items-center gap-2 disabled:opacity-50"
                  >
                    <RefreshCw className={`w-3 h-3 ${attesting ? 'animate-spin' : ''}`} />
                    SOLICITAR ATTESTATION
                  </button>
                </div>
                <button
                  onClick={triggerHsmSync}
                  disabled={syncing}
                  className="w-full py-2 bg-white/5 border border-white/10 text-arkhe-text rounded text-[10px] hover:bg-white/10 transition-all"
                >
                  FORÇAR SINCRONIZAÇÃO HSM DISTRIBUÍDO
                </button>
              </div>
            </div>
          )}

          {activeTab === 'l2' && (
            <div className="space-y-4">
              <div className="bg-black/60 border border-arkhe-border p-4 rounded-lg">
                <h4 className="text-arkhe-cyan text-xs font-bold mb-4 uppercase tracking-widest flex items-center gap-2">
                  <Zap className="w-4 h-4" /> Coerência Kuramoto (Sincronia)
                </h4>
                <div className="space-y-1">
                  <LayerStatus label="Handshake EPR (Viol. Bell)" status={security.l2.eprHandshake} />
                  <LayerStatus label="MuSig2 Heartbeat Sign" status={security.l2.muSig2Heartbeat} />
                  <LayerStatus label="Pneuma Phase Outlier" status={!security.l2.pneumaOutlierDetected} />
                </div>
                <div className="mt-4 pt-4 border-t border-arkhe-border/30 grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-[10px] text-arkhe-muted mb-1">QRNG JITTER</div>
                    <div className="text-sm font-bold text-arkhe-text">{security.l2.qrngJitterMs.toFixed(2)} ms</div>
                  </div>
                  <div>
                    <div className="text-[10px] text-arkhe-muted mb-1">ISO-PHASE LOCK</div>
                    <div className="text-sm font-bold text-arkhe-green">LOCKED</div>
                  </div>
                </div>
              </div>
              <div className="p-4 bg-arkhe-cyan/5 border border-arkhe-cyan/20 rounded-lg">
                <p className="text-[10px] text-arkhe-cyan/80 leading-relaxed italic">
                  {"O subagente Pneuma monitora o desvio de fase de cada nó. Se a fase de um nó divergir da média por > π/2, o isolamento é automático para proteger R(t)."}
                </p>
              </div>
            </div>
          )}

          {activeTab === 'l3' && (
            <div className="space-y-4">
              <div className="bg-black/60 border border-arkhe-border p-4 rounded-lg">
                <h4 className="text-arkhe-cyan text-xs font-bold mb-4 uppercase tracking-widest flex items-center gap-2">
                  <Lock className="w-4 h-4" /> Zero-Knowledge Proofs
                </h4>
                <div className="space-y-1">
                  <LayerStatus label="Nullifier Unique Status" status={security.l3.nullifierVerified} />
                  <LayerStatus label="TTL Window (5m)" status={security.l3.ttlValid} />
                  <LayerStatus label="Quantum Witness (T2*)" status={security.l3.t2StarMicroseconds > 50} />
                </div>
                <div className="mt-4 pt-4 border-t border-arkhe-border/30">
                  <div className="text-[10px] text-arkhe-muted mb-2 uppercase">Integridade QRNG Timestamp</div>
                  <div className="bg-black/40 p-2 rounded text-[10px] font-mono break-all text-arkhe-cyan/70">
                    {security.l3.timestampQRNG}
                  </div>
                </div>
                <div className="mt-4 flex justify-between items-center">
                  <span className="text-[10px] text-arkhe-muted">T2* COHERENCE</span>
                  <span className="text-xs font-bold text-arkhe-green">{security.l3.t2StarMicroseconds.toFixed(2)} μs</span>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'l4' && (
            <div className="space-y-4">
              <div className="bg-black/60 border border-arkhe-border p-4 rounded-lg">
                <h4 className="text-arkhe-cyan text-xs font-bold mb-4 uppercase tracking-widest flex items-center gap-2">
                  <Database className="w-4 h-4" /> Ontologia Arkhe-Ω
                </h4>
                <div className="space-y-1">
                  <LayerStatus label="Assinatura OWL (MuSig2)" status={security.l4.owlSignatureValid} />
                  <LayerStatus label="Conformidade ZK-Ontology" status={security.l4.zkOntologicalProof} />
                </div>
                <div className="mt-4 space-y-2">
                  <div className="flex justify-between text-[10px] mb-1">
                    <span className="text-arkhe-muted uppercase">Consistência LOGOS</span>
                    <span className="text-arkhe-cyan">{(security.l4.logosConsistency * 100).toFixed(1)}%</span>
                  </div>
                  <div className="h-1 bg-arkhe-border rounded-full overflow-hidden">
                    <div className="h-full bg-arkhe-cyan" style={{ width: `${security.l4.logosConsistency * 100}%` }}></div>
                  </div>
                </div>
              </div>
              <div className="bg-black/60 border border-arkhe-border p-4 rounded-lg">
                <h4 className="text-arkhe-muted text-[10px] font-bold mb-3 uppercase">Merkle-DAG Root Hash (Semanal)</h4>
                <div className="bg-black/40 p-2 rounded text-[10px] font-mono break-all text-arkhe-purple/70 mb-4">
                  {security.l4.merkleDagRoot}
                </div>
                <button
                  onClick={signOntology}
                  className="w-full py-2 border border-arkhe-purple/50 text-arkhe-purple hover:bg-arkhe-purple/10 rounded text-[10px] uppercase font-bold"
                >
                  RE-ASSINAR ESQUEMAS OWL
                </button>
              </div>
            </div>
          )}

          {activeTab === 'l5' && (
            <div className="space-y-4">
              <div className="bg-black/60 border border-arkhe-border p-4 rounded-lg">
                <h4 className="text-arkhe-cyan text-xs font-bold mb-4 uppercase tracking-widest flex items-center gap-2">
                  <Eye className="w-4 h-4" /> Interface Svelte (Aegis)
                </h4>
                <div className="space-y-1">
                  <LayerStatus label="CSP Enforcement" status={security.l5.cspStatus} />
                  <LayerStatus label="Asset Integrity (SRI)" status={security.l5.sriVerified} />
                  <LayerStatus label="Anti-CSRF Session Token" status={true} />
                  <LayerStatus label="ZK-Proof UI Verify" status={security.l5.zkUiVerified} />
                  <LayerStatus label="Cache PWA Assinado" status={security.l5.pwaCacheSigned} />
                </div>
              </div>
            </div>
          )}

          {activeTab === 'qhttp' && (
            <div className="space-y-4">
              <div className="bg-black/60 border border-arkhe-border p-4 rounded-lg">
                <h4 className="text-arkhe-cyan text-xs font-bold mb-4 uppercase tracking-widest flex items-center gap-2">
                  <RefreshCw className="w-4 h-4" /> Protocolo qhttp-H
                </h4>
                <div className="space-y-2">
                  <div className="flex justify-between items-center p-2 bg-black/40 rounded">
                    <span className="text-[10px] text-arkhe-muted uppercase">PQ-TLS Strategy</span>
                    <span className="text-[10px] font-bold text-arkhe-cyan">{security.qhttp.pqTlsStatus}</span>
                  </div>
                  <div className="flex justify-between items-center p-2 bg-black/40 rounded">
                    <span className="text-[10px] text-arkhe-muted uppercase">X-Kuramoto-Header</span>
                    <span className="text-[10px] font-mono text-arkhe-muted">{security.qhttp.xKuramotoHeader}</span>
                  </div>
                </div>
                <div className="mt-4 pt-4 border-t border-arkhe-border/30">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-[10px] text-arkhe-muted uppercase">Medição Viol. Bell (|S|)</span>
                    <span className={`text-xs font-bold ${security.qhttp.bellViolationS > 2 ? 'text-arkhe-green' : 'text-arkhe-red'}`}>
                      {security.qhttp.bellViolationS.toFixed(4)}
                    </span>
                  </div>
                  <div className="h-1 bg-arkhe-border rounded-full overflow-hidden">
                    <div className={`h-full transition-all duration-500 ${security.qhttp.bellViolationS > 2 ? 'bg-arkhe-green' : 'bg-arkhe-red'}`}
                      style={{ width: `${(security.qhttp.bellViolationS / 2.82) * 100}%` }}></div>
                  </div>
                  <div className="flex justify-between text-[8px] text-arkhe-muted mt-1">
                    <span>CLASSICAL (S=2.0)</span>
                    <span>QUANTUM (S=2.82)</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
