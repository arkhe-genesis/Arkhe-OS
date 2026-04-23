
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Activity, AlertTriangle, Brain, MessageSquare, Zap, X } from 'lucide-react';
import React, { useState, useEffect } from 'react';

interface Alert {
  id: string;
  timestamp: string;
  level: 'INFO' | 'WARNING' | 'CRITICAL' | 'INSIGHT';
  title: string;
  message: string;
}

interface IntelligencePanelProps {
  onClose: () => void;
}

export default function IntelligencePanel({ onClose }: IntelligencePanelProps) {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const isLive = true;

  // Simulação de um feed de inteligência ao vivo, inspirado no Crucix
  useEffect(() => {
    if (!isLive) {return;}

    const mockAlerts: Alert[] = [
      {
        id: '1',
        timestamp: new Date().toISOString(),
        level: 'INSIGHT',
        title: 'Análise Autônoma LLM',
        message: 'A rede está operando com alta coerência (0.98). O tempo de geração de provas ZK caiu 12% na última hora, indicando otimização no prover Plonky3. Nenhuma anomalia de consenso detectada.',
      },
      {
        id: '2',
        timestamp: new Date(Date.now() - 50000).toISOString(),
        level: 'INFO',
        title: 'Transição de Fase',
        message: 'A rede entrou na Fase Solar. O multiplicador de recompensa base foi ajustado.',
      },
      {
        id: '3',
        timestamp: new Date(Date.now() - 120000).toISOString(),
        level: 'WARNING',
        title: 'Pico de Transações zkERC',
        message: 'Aumento de 300% no volume de transações zkERC detectado no último bloco.',
      }
    ];

    setAlerts(mockAlerts);

    // Simula a chegada de novos alertas via WebSocket
    const interval = setInterval(() => {
      const newAlert: Alert = {
        id: Math.random().toString(36).substring(7),
        timestamp: new Date().toISOString(),
        level: Math.random() > 0.8 ? 'WARNING' : 'INFO',
        title: 'Sinal do Oráculo Sentinela',
        message: 'Verificação de integridade do bloco concluída. Prova STARK validada em 45ms.',
      };
      setAlerts(prev => [newAlert, ...prev].slice(0, 10)); // Mantém os 10 mais recentes
    }, 15000);

    return () => clearInterval(interval);
  }, [isLive]);

  const getLevelIcon = (level: string) => {
    switch (level) {
      case 'CRITICAL': return <AlertTriangle className="w-5 h-5 text-red-500" />;
      case 'WARNING': return <Zap className="w-5 h-5 text-yellow-500" />;
      case 'INSIGHT': return <Brain className="w-5 h-5 text-purple-500" />;
      default: return <Activity className="w-5 h-5 text-blue-500" />;
    }
  };

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'CRITICAL': return 'border-red-500/50 bg-red-500/10 text-red-400';
      case 'WARNING': return 'border-yellow-500/50 bg-yellow-500/10 text-yellow-400';
      case 'INSIGHT': return 'border-purple-500/50 bg-purple-500/10 text-purple-400';
      default: return 'border-blue-500/50 bg-blue-500/10 text-blue-400';
    }
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4 md:p-8">
      <div className="bg-[#111214] border border-[#1f2024] rounded-xl w-full max-w-4xl h-[80vh] flex flex-col shadow-2xl overflow-hidden relative">
        <button 
          onClick={onClose}
          className="absolute top-4 right-4 text-arkhe-muted hover:text-white transition-colors z-10"
        >
          <X className="w-6 h-6" />
        </button>
        
        <div className="p-6 border-b border-[#1f2024] flex items-center justify-between bg-black/40">
          <div className="flex items-center space-x-3">
            <Brain className="w-6 h-6 text-purple-400" />
            <h2 className="text-xl font-bold text-white tracking-widest uppercase">Inteligência Sentinela</h2>
          </div>
          <div className="flex items-center space-x-2 mr-8">
            <span className="text-xs text-white/50 uppercase tracking-wider">Status:</span>
            <div className={`flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-medium border ${isLive ? 'bg-green-500/10 text-green-400 border-green-500/30' : 'bg-red-500/10 text-red-400 border-red-500/30'}`}>
              <div className={`w-2 h-2 rounded-full ${isLive ? 'bg-green-400 animate-pulse' : 'bg-red-400'}`} />
              <span>{isLive ? 'VIGÍLIA ATIVA' : 'OFFLINE'}</span>
            </div>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-4 custom-scrollbar bg-black/20">
          {alerts.map((alert) => (
            <div key={alert.id} className={`p-4 rounded-lg border ${getLevelColor(alert.level)} transition-all hover:bg-opacity-20`}>
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center space-x-2">
                  {getLevelIcon(alert.level)}
                  <h3 className="font-semibold text-sm tracking-wide">{alert.title}</h3>
                </div>
                <span className="text-xs opacity-60 font-mono">
                  {new Date(alert.timestamp).toLocaleTimeString()}
                </span>
              </div>
              <p className="text-sm opacity-80 leading-relaxed">
                {alert.message}
              </p>
            </div>
          ))}
        </div>

        <div className="p-4 border-t border-[#1f2024] flex justify-between items-center text-xs text-white/40 bg-black/40">
          <div className="flex items-center space-x-2">
            <MessageSquare className="w-4 h-4" />
            <span>Telegram / Discord Bots Conectados</span>
          </div>
          <span>LLM: Gemini 3.1 Pro</span>
        </div>
      </div>
    </div>
  );
}
