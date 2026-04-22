
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Activity, Radio, BrainCircuit, Mic, Globe, Zap } from 'lucide-react';
import React, { useState } from 'react';

import { logger } from '../../server/logger';

import { Card } from './ui/Card';

export function DysonSphereTelemetry() {
  const [operatorId, setOperatorId] = useState('BEXORG-OP-001');
  const [brainwaveFreq, setBrainwaveFreq] = useState(40.0);
  const [mappingResult, setMappingResult] = useState<unknown>(null);
  
  const [voiceResult, setVoiceResult] = useState<unknown>(null);
  const [isFiltering, setIsFiltering] = useState(false);

  const [genesisResult, setGenesisResult] = useState<unknown>(null);
  const [isGenesisLoading, setIsGenesisLoading] = useState(false);

  const [massSyncResult, setMassSyncResult] = useState<unknown>(null);
  const [isMassSyncLoading, setIsMassSyncLoading] = useState(false);

  const handleGenesisDIP = async () => {
    setIsGenesisLoading(true);
    try {
      const res = await fetch('/api/arkhe-chain/genesis-dip', { method: 'POST' });
      const data = await res.json();
      if (data.success) {
        setGenesisResult(data);
      }
    } catch (err) {
      logger.error("Erro no Genesis DIP: " + err);
    } finally {
      setIsGenesisLoading(false);
    }
  };

  const handleMassSync = async () => {
    setIsMassSyncLoading(true);
    try {
      const res = await fetch('/api/arkhe-chain/mass-sync', { method: 'POST' });
      const data = await res.json();
      if (data.success) {
        setMassSyncResult(data);
      }
    } catch (err) {
      logger.error("Erro na Sincronização em Massa: " + err);
    } finally {
      setIsMassSyncLoading(false);
    }
  };

  const handleDIPMapping = async () => {
    try {
      const res = await fetch('/api/telemetry/dip-mapping', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ operatorId, brainwaveFreq: Number(brainwaveFreq) })
      });
      const data = await res.json();
      if (data.success) {
        setMappingResult(data.mapping);
      }
    } catch (err) {
      logger.error("Erro no mapeamento DIP: " + err);
    }
  };

  const handleIsolateVoice = async () => {
    setIsFiltering(true);
    try {
      // Gerar um stream de plasma simulado com anomalia Phi (1.618) injetada aleatoriamente
      const stream = Array.from({ length: 2048 }, () => {
        const noise = (Math.random() * 2 - 1) * 2.0;
        // 10% de chance de injetar um sinal ressonante
        if (Math.random() > 0.9) {
           return noise + (1.6180339887 * (Math.random() > 0.5 ? 1 : -1));
        }
        return noise;
      });

      const res = await fetch('/api/telemetry/isolate-voice', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ plasmaStreamData: stream })
      });
      const data = await res.json();
      if (data.success) {
        setVoiceResult(data.result);
      }
    } catch (err) {
      logger.error("Erro ao isolar voz: " + err);
    } finally {
      setIsFiltering(false);
    }
  };

  return (
    <div className="space-y-6">
      <Card 
        title="Mapeamento Neural (DIP) - Esfera de Dyson" 
        icon={<BrainCircuit className="w-5 h-5 text-purple-500" />}
        className="bg-black border-zinc-800"
      >
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-xs text-zinc-400 uppercase">ID do Operador</label>
              <input 
                value={operatorId} 
                onChange={(e) => setOperatorId(e.target.value)}
                className="w-full bg-zinc-900 border border-zinc-800 text-zinc-100 px-3 py-2 rounded focus:outline-none focus:border-purple-500"
              />
            </div>
            <div className="space-y-2">
              <label className="text-xs text-zinc-400 uppercase">Frequência Cerebral (Hz)</label>
              <input 
                type="number"
                step="0.1"
                value={brainwaveFreq} 
                onChange={(e) => setBrainwaveFreq(Number(e.target.value))}
                className="w-full bg-zinc-900 border border-zinc-800 text-zinc-100 px-3 py-2 rounded focus:outline-none focus:border-purple-500"
              />
            </div>
          </div>
          <button 
            onClick={handleDIPMapping}
            className="w-full bg-purple-600 hover:bg-purple-700 text-white py-2 rounded transition-colors font-mono uppercase tracking-widest text-sm"
          >
            Iniciar Mapeamento DIP
          </button>

          {mappingResult && (
            <div className="mt-4 p-4 bg-zinc-900 border border-zinc-800 rounded-md font-mono text-sm space-y-2">
              <div className="flex justify-between">
                <span className="text-zinc-500">Setor Dyson:</span>
                <span className="text-purple-400">{mappingResult.dysonSector}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-500">Sincronização de Coerência:</span>
                <span className="text-zinc-300">{(mappingResult.coherenceSync * 100).toFixed(2)}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-500">Status Quântico:</span>
                <span className={mappingResult.quantumEntanglementStatus === 'LOCKED_TO_DYSON_SPHERE' ? 'text-green-400' : 'text-yellow-400'}>
                  {mappingResult.quantumEntanglementStatus}
                </span>
              </div>
            </div>
          )}
        </div>
      </Card>

      <Card 
        title="Operações Globais da Esfera de Dyson" 
        icon={<Globe className="w-5 h-5 text-emerald-500" />}
        className="bg-black border-zinc-800"
      >
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <button 
              onClick={handleGenesisDIP}
              disabled={isGenesisLoading}
              className="w-full bg-emerald-600 hover:bg-emerald-700 text-white py-2 rounded transition-colors font-mono uppercase tracking-widest text-xs flex items-center justify-center gap-2 disabled:opacity-50"
            >
              <Zap className="w-4 h-4" />
              {isGenesisLoading ? "Forjando Genesis..." : "Genesis DIP (Kaelen)"}
            </button>
            <button 
              onClick={handleMassSync}
              disabled={isMassSyncLoading}
              className="w-full bg-teal-600 hover:bg-teal-700 text-white py-2 rounded transition-colors font-mono uppercase tracking-widest text-xs flex items-center justify-center gap-2 disabled:opacity-50"
            >
              <Activity className="w-4 h-4" />
              {isMassSyncLoading ? "Sincronizando..." : "Sincronização em Massa (14 OP)"}
            </button>
          </div>

          {genesisResult && (
            <div className="mt-4 p-4 bg-zinc-900 border border-emerald-800/50 rounded-md font-mono text-sm space-y-2">
              <div className="text-emerald-400 font-bold mb-2">Genesis Block Forjado</div>
              <div className="text-zinc-400 text-xs break-all">Hash: {genesisResult.block.hash}</div>
              <div className="text-zinc-400 text-xs mt-1">Transação: {genesisResult.block.transactions[0].memoryFragment}</div>
              <div className="text-zinc-500 text-xs mt-2 italic">Evento publicado na rede Nostr.</div>
            </div>
          )}

          {massSyncResult && (
            <div className="mt-4 p-4 bg-zinc-900 border border-teal-800/50 rounded-md font-mono text-sm space-y-2">
              <div className="flex justify-between items-center mb-2">
                <span className="text-teal-400 font-bold">Status TZINOR Planetário:</span>
                <span className={massSyncResult.planetaryTzinorStabilized ? "text-green-400" : "text-yellow-400"}>
                  {massSyncResult.planetaryTzinorStabilized ? "ESTÁVEL" : "INSTÁVEL"}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-500">Coerência Média:</span>
                <span className="text-zinc-300">{(massSyncResult.averageCoherence * 100).toFixed(2)}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-500">Operadores Sincronizados:</span>
                <span className="text-zinc-300">{massSyncResult.syncResults.length}</span>
              </div>
              <div className="text-zinc-500 text-xs mt-2 italic">Evento publicado na rede Nostr.</div>
            </div>
          )}
        </div>
      </Card>

      <Card 
        title="Filtro de Áudio do Plasma (Isolamento de Satoshi)" 
        icon={<Radio className="w-5 h-5 text-blue-500" />}
        className="bg-black border-zinc-800"
      >
        <div className="space-y-4">
          <button 
            onClick={handleIsolateVoice}
            disabled={isFiltering}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 rounded transition-colors font-mono uppercase tracking-widest text-sm flex items-center justify-center gap-2 disabled:opacity-50"
          >
            <Mic className="w-4 h-4" />
            {isFiltering ? "Processando Stream do W7-X..." : "Filtrar Stream do Plasma"}
          </button>

          {voiceResult && (
            <div className="mt-4 p-4 bg-zinc-900 border border-zinc-800 rounded-md font-mono text-sm space-y-3">
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="bg-black p-2 rounded border border-zinc-800">
                  <span className="text-zinc-500 block mb-1">Ruído de Fundo (NF)</span>
                  <span className="text-zinc-300">{voiceResult.noiseFloor.toFixed(2)} dB</span>
                </div>
                <div className="bg-black p-2 rounded border border-zinc-800">
                  <span className="text-zinc-500 block mb-1">Relação Sinal-Ruído (SNR)</span>
                  <span className="text-zinc-300">{voiceResult.signalToNoiseRatio.toFixed(4)}</span>
                </div>
                <div className="bg-black p-2 rounded border border-zinc-800">
                  <span className="text-zinc-500 block mb-1">Ressonância Espectral (Φ)</span>
                  <span className="text-blue-400">{voiceResult.spectralResonance.toFixed(4)}</span>
                </div>
                <div className="bg-black p-2 rounded border border-zinc-800">
                  <span className="text-zinc-500 block mb-1">Detecção de Voz</span>
                  <span className={voiceResult.satoshiVoiceDetected ? 'text-green-400' : 'text-red-400'}>
                    {voiceResult.satoshiVoiceDetected ? 'POSITIVO' : 'NEGATIVO'}
                  </span>
                </div>
              </div>

              {voiceResult.satoshiVoiceDetected && voiceResult.extractedMessage && (
                <div className="mt-4 p-3 bg-blue-900/20 border border-blue-500/30 rounded text-blue-300 italic">
                  "{voiceResult.extractedMessage}"
                </div>
              )}
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}
