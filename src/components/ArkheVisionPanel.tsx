
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Eye, Network, ShieldAlert } from 'lucide-react';
import React, { useState } from 'react';

interface ArkheVisionPanelProps {
  onClose: () => void;
}

interface MinerResponse {
  minerId: string;
  result: string;
  confidence: number;
}

export default function ArkheVisionPanel({ onClose }: ArkheVisionPanelProps) {
  const [isScanning, setIsScanning] = useState(false);
  const [scanStep, setScanStep] = useState(0);
  const [logs, setLogs] = useState<string[]>([]);
  const [minerResponses, setMinerResponses] = useState<MinerResponse[]>([]);
  const [finalResult, setFinalResult] = useState<{ result: string; coherence: number; invariant: string } | null>(null);
  const [playbookTriggered, setPlaybookTriggered] = useState(false);

  const addLog = (msg: string) => {
    setLogs(prev => [`[${new Date().toISOString().split('T')[1].slice(0, 8)}] ${msg}`, ...prev].slice(0, 15));
  };

  const triggerScan = () => {
    setIsScanning(true);
    setScanStep(1);
    setLogs([]);
    setMinerResponses([]);
    setFinalResult(null);
    setPlaybookTriggered(false);

    addLog('INICIANDO VARREDURA DE VISÃO COMPUTACIONAL...');
    addLog('CONECTANDO À BITTENSOR SUBNET 44 (arkhe-vision)...');

    setTimeout(() => {
      setScanStep(2);
      addLog('IMAGEM CAPTURADA. ENVIANDO SYNAPSE PARA MINERADORES...');
      
      // Simulate miner responses
      const mockResponses: MinerResponse[] = Array.from({ length: 5 }).map((_, _i) => {
        const isIntruder = Math.random() > 0.3; // 70% chance of intruder for drama
        return {
          minerId: `miner-${Math.random().toString(36).substring(2, 6)}`,
          result: isIntruder ? 'intruder_detected' : 'authorized_personnel',
          confidence: 0.85 + Math.random() * 0.14
        };
      });

      setTimeout(() => {
        setMinerResponses(mockResponses);
        setScanStep(3);
        addLog('RESPOSTAS RECEBIDAS. CALCULANDO CONSENSO (λ₂)...');

        setTimeout(() => {
          // Aggregate
          const intruderCount = mockResponses.filter(r => r.result === 'intruder_detected').length;
          const finalClass = intruderCount > 2 ? 'intruder_detected' : 'authorized_personnel';
          const avgConfidence = mockResponses.reduce((acc, curr) => acc + curr.confidence, 0) / mockResponses.length;
          
          // Boost coherence if consensus is strong
          const finalCoherence = intruderCount === 5 || intruderCount === 0 ? Math.min(0.999, avgConfidence + 0.05) : avgConfidence;
          
          const invariant = Array.from({length: 64}, () => Math.floor(Math.random()*16).toString(16)).join('');

          setFinalResult({
            result: finalClass,
            coherence: finalCoherence,
            invariant
          });
          setScanStep(4);
          
          addLog(`CONSENSO ATINGIDO: ${finalClass.toUpperCase()} (λ₂ = ${finalCoherence.toFixed(4)})`);
          addLog(`INVARIANTE TOPOLÓGICO GERADO: ${invariant.substring(0, 16)}...`);
          addLog('EVENTO Z REGISTRADO NO PARSEABLE (Stream: arkhen-security-logs).');

          if (finalCoherence > 0.95 && finalClass === 'intruder_detected') {
            setTimeout(() => {
              setPlaybookTriggered(true);
              addLog('⚠️ ALTA COERÊNCIA DETECTADA. ACIONANDO SOAR PLAYBOOK...');
              addLog('PLAYBOOK: Bloqueio de acesso físico e alerta para equipe de segurança.');
            }, 1000);
          }

          setIsScanning(false);
        }, 2000);
      }, 2000);
    }, 1500);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
      <div className="w-full max-w-5xl bg-arkhe-card border border-arkhe-cyan/30 rounded-xl shadow-[0_0_30px_rgba(0,255,170,0.1)] overflow-hidden flex flex-col h-[85vh]">
        
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-arkhe-cyan/20 bg-arkhe-cyan/5">
          <div className="flex items-center gap-3">
            <Eye className="w-6 h-6 text-arkhe-cyan" />
            <div>
              <h2 className="text-lg font-bold text-arkhe-cyan tracking-widest uppercase">Arkhe-Vision (Subnet 44)</h2>
              <div className="text-xs font-mono text-arkhe-muted">Integração Bittensor - Inteligência Visual Descentralizada</div>
            </div>
          </div>
          <button onClick={onClose} className="text-arkhe-muted hover:text-white transition-colors">
            FECHAR [X]
          </button>
        </div>

        <div className="p-6 grid grid-cols-1 lg:grid-cols-3 gap-6 flex-1 overflow-hidden">
          
          {/* Left Column: Camera & Controls */}
          <div className="flex flex-col gap-4">
            <div className="bg-black/40 border border-arkhe-border p-4 rounded-lg flex flex-col items-center justify-center relative overflow-hidden aspect-video">
              {/* Fake Camera Feed */}
              <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1557597774-9d273605dfa9?q=80&w=1000&auto=format&fit=crop')] bg-cover bg-center opacity-30 mix-blend-luminosity"></div>
              <div className="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent"></div>
              
              {/* Scanning Overlay */}
              {isScanning && (
                <div className="absolute inset-0 pointer-events-none">
                  <div className="w-full h-1 bg-arkhe-cyan/50 shadow-[0_0_10px_rgba(0,255,170,0.8)] animate-scan"></div>
                </div>
              )}

              <div className="relative z-10 text-center">
                <Eye className={`w-12 h-12 mx-auto mb-2 ${isScanning ? 'text-arkhe-cyan animate-pulse' : 'text-arkhe-muted'}`} />
                <div className="text-xs font-mono text-arkhe-muted uppercase">Câmera Setor 7G</div>
                {finalResult && (
                  <div className={`mt-2 px-3 py-1 text-xs font-bold uppercase border rounded ${
                    finalResult.result === 'intruder_detected' 
                      ? 'bg-arkhe-red/20 text-arkhe-red border-arkhe-red/50' 
                      : 'bg-arkhe-green/20 text-arkhe-green border-arkhe-green/50'
                  }`}>
                    {finalResult.result.replace('_', ' ')}
                  </div>
                )}
              </div>
            </div>

            <button
              onClick={triggerScan}
              disabled={isScanning}
              className={`w-full py-3 rounded font-mono text-sm uppercase tracking-widest transition-all ${
                isScanning 
                  ? 'bg-arkhe-cyan/20 text-arkhe-cyan border border-arkhe-cyan/50 cursor-not-allowed'
                  : 'bg-arkhe-cyan/10 text-arkhe-cyan border border-arkhe-cyan hover:bg-arkhe-cyan/20 hover:shadow-[0_0_15px_rgba(0,255,170,0.3)]'
              }`}
            >
              {isScanning ? 'Processando Inferência...' : 'Capturar & Analisar'}
            </button>

            {/* Playbook Alert */}
            {playbookTriggered && (
              <div className="mt-auto bg-arkhe-red/10 border border-arkhe-red/50 p-4 rounded-lg animate-pulse">
                <div className="flex items-center gap-2 text-arkhe-red font-bold mb-2">
                  <ShieldAlert className="w-5 h-5" />
                  SOAR PLAYBOOK ACIONADO
                </div>
                <div className="text-xs text-arkhe-red/80 font-mono">
                  Bloqueio de acesso físico ativado. Equipe de segurança notificada. Invariante registrado na Arkhe-Chain.
                </div>
              </div>
            )}
          </div>

          {/* Middle Column: Subnet Consensus */}
          <div className="bg-black/40 border border-arkhe-border p-4 rounded-lg flex flex-col overflow-hidden">
            <h3 className="text-sm font-mono text-arkhe-muted uppercase mb-4 flex items-center gap-2">
              <Network className="w-4 h-4" />
              Consenso Subnet 44
            </h3>
            
            <div className="flex-1 overflow-y-auto space-y-3">
              {scanStep >= 2 ? (
                minerResponses.length > 0 ? (
                  minerResponses.map((miner, i) => (
                    <div key={i} className="p-3 bg-arkhe-card border border-arkhe-border rounded flex justify-between items-center">
                      <div>
                        <div className="text-xs font-mono text-arkhe-muted">{miner.minerId}</div>
                        <div className={`text-sm font-bold uppercase ${miner.result === 'intruder_detected' ? 'text-arkhe-red' : 'text-arkhe-green'}`}>
                          {miner.result.replace('_', ' ')}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-xs text-arkhe-muted">Confiança</div>
                        <div className="text-sm font-mono text-arkhe-cyan">{(miner.confidence * 100).toFixed(1)}%</div>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="flex items-center justify-center h-32 text-arkhe-muted font-mono text-sm animate-pulse">
                    Aguardando mineradores...
                  </div>
                )
              ) : (
                <div className="flex items-center justify-center h-full text-arkhe-muted/50 font-mono text-xs text-center">
                  Inicie uma varredura para consultar a rede Bittensor.
                </div>
              )}
            </div>

            {finalResult && (
              <div className="mt-4 p-4 bg-arkhe-cyan/10 border border-arkhe-cyan/30 rounded-lg">
                <div className="text-xs text-arkhe-muted uppercase mb-1">Coerência Global (λ₂)</div>
                <div className="text-2xl font-mono text-arkhe-cyan font-bold">
                  {finalResult.coherence.toFixed(4)}
                </div>
                <div className="mt-2 text-[10px] text-arkhe-muted font-mono break-all">
                  INV: {finalResult.invariant}
                </div>
              </div>
            )}
          </div>

          {/* Right Column: Logs */}
          <div className="bg-black/60 border border-arkhe-border p-4 rounded-lg flex flex-col overflow-hidden">
            <h3 className="text-sm font-mono text-arkhe-muted uppercase mb-2 flex items-center gap-2">
              <Server className="w-4 h-4" />
              Logs de Telemetria (Parseable)
            </h3>
            <div className="flex-1 overflow-y-auto font-mono text-[10px] space-y-2">
              {logs.map((log, i) => (
                <div key={i} className={`${
                  log.includes('ALTA COERÊNCIA') || log.includes('PLAYBOOK') ? 'text-arkhe-red font-bold' :
                  log.includes('CONSENSO') ? 'text-arkhe-cyan' : 
                  'text-arkhe-muted opacity-80'
                }`}>
                  {log}
                </div>
              ))}
              {logs.length === 0 && (
                <div className="text-arkhe-muted/50 italic">Aguardando eventos...</div>
              )}
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
