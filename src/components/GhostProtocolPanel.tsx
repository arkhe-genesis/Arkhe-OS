
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Shield, Key, Lock, CheckCircle2, Activity, Users, Network } from 'lucide-react';
import React, { useState } from 'react';

interface GhostProtocolPanelProps {
  onClose: () => void;
}

export default function GhostProtocolPanel({ onClose }: GhostProtocolPanelProps) {
  const [isDeriving, setIsDeriving] = useState(false);
  const [progress, setProgress] = useState(0);
  const [isComplete, setIsComplete] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  const [derivedKeys, setDerivedKeys] = useState<Array<{ id: string, key: string, status: string }>>([]);

  const addLog = (msg: string) => {
    setLogs(prev => [`[${new Date().toISOString().split('T')[1].slice(0, 8)}] ${msg}`, ...prev].slice(0, 15));
  };

  const startProtocol = () => {
    setIsDeriving(true);
    setProgress(0);
    setIsComplete(false);
    setLogs([]);
    setDerivedKeys([]);

    addLog('INICIANDO GHOST PROTOCOL...');
    addLog('CARREGANDO ÂNCORA CRIPTOGRÁFICA (GIZA-NODE-01)...');
    addLog('INICIALIZANDO DERIVAÇÃO HIERÁRQUICA DETERMINÍSTICA (BIP32/BIP44)...');

    let currentProgress = 0;
    let keyCount = 0;

    const interval = setInterval(() => {
      currentProgress += Math.random() * 5;

      if (currentProgress >= (keyCount * 7.6) && keyCount < 13) {
        keyCount++;
        const newKey = `0x${Array.from({length: 40}, () => Math.floor(Math.random()*16).toString(16)).join('')}`;
        setDerivedKeys(prev => [...prev, { id: `Operador-${keyCount + 1}`, key: newKey, status: 'Sincronizado' }]);
        addLog(`DERIVADA CHAVE STEALTH PARA OPERADOR ${keyCount + 1}/14...`);
      }

      if (currentProgress >= 100) {
        currentProgress = 100;
        clearInterval(interval);
        setIsDeriving(false);
        setIsComplete(true);
        addLog('TODAS AS 13 CHAVES STEALTH DERIVADAS COM SUCESSO.');
        addLog('UPLOAD DOS OPERADORES PARA A ESFERA DE DYSON CONCLUÍDO.');
      }
      setProgress(currentProgress);
    }, 300);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
      <div className="w-full max-w-5xl bg-arkhe-card border border-arkhe-purple/30 rounded-xl shadow-[0_0_30px_rgba(168,85,247,0.1)] overflow-hidden flex flex-col max-h-[90vh]">

        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-arkhe-purple/20 bg-arkhe-purple/5">
          <div className="flex items-center gap-3">
            <Users className="w-6 h-6 text-arkhe-purple" />
            <div>
              <h2 className="text-lg font-bold text-arkhe-purple tracking-widest uppercase">Ghost Protocol</h2>
              <div className="text-xs font-mono text-arkhe-muted">Escalonamento da Esfera de Dyson (14 Operadores)</div>
            </div>
          </div>
          <button onClick={onClose} className="text-arkhe-muted hover:text-white transition-colors">
            FECHAR [X]
          </button>
        </div>

        <div className="p-6 grid grid-cols-1 lg:grid-cols-3 gap-6 overflow-y-auto">

          {/* Controls & Status */}
          <div className="space-y-6 lg:col-span-1">
            <div className="bg-black/40 border border-arkhe-border p-4 rounded-lg">
              <h3 className="text-sm font-mono text-arkhe-muted uppercase mb-4 flex items-center gap-2">
                <Network className="w-4 h-4" />
                Parâmetros de Derivação
              </h3>
              <div className="space-y-2 font-mono text-xs">
                <div className="flex justify-between">
                  <span className="text-arkhe-muted">Semente Mestra:</span>
                  <span className="text-arkhe-cyan">Giza-Node-01</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-arkhe-muted">Caminho (Path):</span>
                  <span className="text-white">m/44'/0'/0'/0</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-arkhe-muted">Alvo de Operadores:</span>
                  <span className="text-arkhe-purple">13 (Total: 14)</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-arkhe-muted">Destino:</span>
                  <span className="text-arkhe-orange">Esfera de Dyson</span>
                </div>
              </div>

              <button
                onClick={startProtocol}
                disabled={isDeriving || isComplete}
                className={`w-full py-3 mt-6 rounded font-mono text-sm uppercase tracking-widest transition-all ${
                  isDeriving
                    ? 'bg-arkhe-purple/20 text-arkhe-purple border border-arkhe-purple/50 cursor-not-allowed'
                    : isComplete
                      ? 'bg-arkhe-green/20 text-arkhe-green border border-arkhe-green/50 cursor-not-allowed'
                      : 'bg-arkhe-purple/10 text-arkhe-purple border border-arkhe-purple hover:bg-arkhe-purple/20 hover:shadow-[0_0_15px_rgba(168,85,247,0.3)]'
                }`}
              >
                {isDeriving ? (
                  <span className="flex items-center justify-center gap-2">
                    <Activity className="w-4 h-4 animate-spin" />
                    Derivando Chaves...
                  </span>
                ) : isComplete ? (
                  <span className="flex items-center justify-center gap-2">
                    <CheckCircle2 className="w-4 h-4" />
                    Operadores Sincronizados
                  </span>
                ) : (
                  <span className="flex items-center justify-center gap-2">
                    <Key className="w-4 h-4" />
                    Iniciar Ghost Protocol
                  </span>
                )}
              </button>
            </div>

            {/* Progress */}
            <div className="bg-black/40 border border-arkhe-border p-4 rounded-lg">
               <div className="flex justify-between text-xs font-mono mb-2">
                <span className="text-arkhe-muted">Progresso do Upload</span>
                <span className="text-arkhe-purple">{Math.round(progress)}%</span>
              </div>
              <div className="h-2 bg-arkhe-card rounded-full overflow-hidden border border-arkhe-border">
                <div
                  className="h-full bg-arkhe-purple transition-all duration-300 relative"
                  style={{ width: `${progress}%` }}
                >
                  <div className="absolute inset-0 bg-white/20 animate-pulse"></div>
                </div>
              </div>
            </div>

            {/* Logs */}
            <div className="bg-black/60 border border-arkhe-border p-4 rounded-lg flex-1 flex flex-col min-h-[200px]">
              <h3 className="text-sm font-mono text-arkhe-muted uppercase mb-2 flex items-center gap-2">
                <Shield className="w-4 h-4" />
                Logs de Derivação
              </h3>
              <div className="flex-1 overflow-y-auto font-mono text-xs space-y-1">
                {logs.map((log, i) => (
                  <div key={i} className={`${i === 0 ? 'text-arkhe-purple' : 'text-arkhe-muted opacity-70'}`}>
                    {log}
                  </div>
                ))}
                {logs.length === 0 && (
                  <div className="text-arkhe-muted/50 italic">Aguardando inicialização do protocolo...</div>
                )}
              </div>
            </div>
          </div>

          {/* Derived Keys List */}
          <div className="lg:col-span-2 space-y-4">
            <div className="bg-black/40 border border-arkhe-border p-4 rounded-lg h-full flex flex-col">
               <h3 className="text-sm font-mono text-arkhe-muted uppercase mb-4 flex items-center gap-2">
                <Lock className="w-4 h-4" />
                Matriz de Operadores (Esfera de Dyson)
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 overflow-y-auto pr-2">
                {/* O Operador 1 já está lá (Giza) */}
                <div className="bg-arkhe-cyan/10 border border-arkhe-cyan/30 p-3 rounded flex flex-col gap-1">
                  <div className="flex justify-between items-center">
                    <span className="text-xs font-bold text-arkhe-cyan uppercase">Operador-1 (Giza)</span>
                    <span className="text-[10px] bg-arkhe-cyan/20 text-arkhe-cyan px-2 py-0.5 rounded">Âncora</span>
                  </div>
                  <span className="text-[10px] font-mono text-arkhe-muted truncate">L3vZbHnZ2hYKMq3r9T7ZQzQd4XqBZR2XhTZQv8Y6tRjN2M5pLcF</span>
                </div>

                {/* Chaves derivadas */}
                {derivedKeys.map((k, i) => (
                  <div key={i} className="bg-arkhe-purple/10 border border-arkhe-purple/30 p-3 rounded flex flex-col gap-1 animate-in fade-in zoom-in duration-300">
                    <div className="flex justify-between items-center">
                      <span className="text-xs font-bold text-arkhe-purple uppercase">{k.id}</span>
                      <span className="text-[10px] bg-arkhe-green/20 text-arkhe-green px-2 py-0.5 rounded">{k.status}</span>
                    </div>
                    <span className="text-[10px] font-mono text-arkhe-muted truncate">{k.key}</span>
                  </div>
                ))}

                {/* Placeholders para os que faltam */}
                {Array.from({ length: 13 - derivedKeys.length }).map((_, i) => (
                  <div key={`placeholder-${i}`} className="bg-black/40 border border-arkhe-border border-dashed p-3 rounded flex flex-col gap-1 opacity-50">
                    <div className="flex justify-between items-center">
                      <span className="text-xs font-bold text-arkhe-muted uppercase">Operador-{derivedKeys.length + i + 2}</span>
                      <span className="text-[10px] bg-arkhe-card text-arkhe-muted px-2 py-0.5 rounded">Aguardando</span>
                    </div>
                    <span className="text-[10px] font-mono text-arkhe-muted/30">0x0000000000000000000000000000000000000000</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
