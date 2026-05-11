
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { Shield, Zap,  Clock } from 'lucide-react';
import React, { useState, useEffect } from 'react';

import type { RamseyPendingAction } from '../../server/types';

interface RamseyConfirmationModalProps {
  pendingAction: RamseyPendingAction;
  onClose: () => void;
}

export default function RamseyConfirmationModal({ pendingAction, onClose }: RamseyConfirmationModalProps) {
  const [timeLeft, setTimeLeft] = useState(30);

  useEffect(() => {
    const expiresAt = new Date(pendingAction.expiresAt).getTime();
    const interval = setInterval(() => {
      const now = Date.now();
      const diff = Math.max(0, Math.floor((expiresAt - now) / 1000));
      setTimeLeft(diff);
      if (diff === 0) {
        clearInterval(interval);
        onClose();
      }
    }, 1000);
    return () => clearInterval(interval);
  }, [pendingAction.expiresAt, onClose]);

  const [justification, setJustification] = useState('');
  const [showDetails, setShowDetails] = useState(false);

  const handleConfirm = async (status: 'approved' | 'rejected' | 'postponed') => {
    try {
      await fetch('/api/ramsey/confirm', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          actionId: pendingAction.id,
          status: status,
          justification: justification,
          signature: status === 'approved' ? "0x" + Math.random().toString(16).slice(2, 130) : undefined // Simulated ECDSA signature
        })
      });
      onClose();
    } catch (e) {
      console.error("Failed to confirm Ramsey action:", e);
    }
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/90 backdrop-blur-md p-4 font-mono">
      <div className="bg-arkhe-bg border border-arkhe-cyan/50 rounded-xl overflow-hidden shadow-[0_0_50px_rgba(0,255,170,0.2)] max-w-lg w-full flex flex-col">
        {/* Header */}
        <div className="bg-arkhe-cyan/10 border-b border-arkhe-cyan/30 p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Zap className="w-5 h-5 text-arkhe-cyan animate-pulse" />
            <h2 className="text-arkhe-cyan font-bold tracking-[0.2em] uppercase text-sm">Protocolo Archimedes-Ω</h2>
          </div>
          <div className="flex items-center gap-2 text-arkhe-muted">
            <Clock className="w-4 h-4" />
            <span className={`text-xs font-bold ${timeLeft < 10 ? 'text-arkhe-red' : 'text-arkhe-text'}`}>
              {timeLeft}s
            </span>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4 overflow-y-auto max-h-[70vh]">
          <div className="flex items-start gap-4">
            <div className="p-3 bg-arkhe-cyan/20 rounded-lg shrink-0">
              <Shield className="w-8 h-8 text-arkhe-cyan" />
            </div>
            <div>
              <h3 className="text-arkhe-text font-bold uppercase tracking-widest mb-1">Confirmação de Injeção Global</h3>
              <p className="text-[10px] text-arkhe-muted leading-relaxed uppercase">
                O SISTEMA DETECTOU UM PICO DE COERÊNCIA EM UM ÂNGULO CRÍTICO DE VARREDURA RAMSEY. AÇÃO GLOBAL REQUERIDA.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="bg-black/40 border border-arkhe-border p-3 rounded-lg">
              <div className="text-[10px] text-arkhe-muted uppercase mb-1 tracking-tighter">Ângulo θ</div>
              <div className="text-sm font-bold text-arkhe-cyan">{pendingAction.angle.toFixed(4)} rad</div>
            </div>
            <div className="bg-black/40 border border-arkhe-border p-3 rounded-lg">
              <div className="text-[10px] text-arkhe-muted uppercase mb-1 tracking-tighter">Coerência R(θ)</div>
              <div className="text-sm font-bold text-arkhe-green">{pendingAction.coherence.toFixed(4)}</div>
            </div>
          </div>

          <div className="bg-black/60 border border-arkhe-border p-4 rounded-lg">
            <div className="text-[10px] text-arkhe-muted uppercase mb-2">Ação Sugerida</div>
            <div className="text-xs font-bold text-arkhe-text mb-2 tracking-widest">{pendingAction.type}</div>
            <div className="text-[10px] text-arkhe-muted leading-relaxed mb-3">
              APLICAÇÃO DE SEQUÊNCIA DE PULSOS PARA SINCRONIZAÇÃO DISCRETA SL(3,ℤ).
            </div>

            {Math.abs(pendingAction.angle - 0.6283) < 0.01 && (
              <div className="border-t border-arkhe-border/30 pt-3 space-y-2">
                <div className="text-[9px] text-arkhe-cyan font-bold uppercase tracking-widest">Injeção Fibonacci (π/5)</div>
                <div className="flex flex-wrap gap-2">
                  {["S", "T", "S⁻¹", "T", "S"].map((gen, i) => (
                    <div key={i} className="px-2 py-1 bg-arkhe-cyan/10 border border-arkhe-cyan/30 rounded text-[9px] text-arkhe-cyan font-bold">
                      {gen}
                    </div>
                  ))}
                </div>
                <div className="grid grid-cols-2 gap-2 text-[8px] text-arkhe-muted uppercase">
                  <div>Duração: 157.1 fs/pulso</div>
                  <div>Pico: 1.2e13 W/cm²</div>
                </div>
              </div>
            )}
          </div>

          <div className="space-y-2">
            <div className="text-[10px] text-arkhe-muted uppercase tracking-tighter">Justificativa (Opcional)</div>
            <textarea
              value={justification}
              onChange={(e) => setJustification(e.target.value)}
              className="w-full bg-black/40 border border-arkhe-border rounded p-2 text-[10px] text-arkhe-text outline-none focus:border-arkhe-cyan/50 h-16 resize-none"
              placeholder="Descreva o motivo da decisão..."
            />
          </div>

          {showDetails && (
            <div className="p-3 bg-arkhe-cyan/5 border border-arkhe-cyan/20 rounded-lg animate-in fade-in slide-in-from-top-2">
              <div className="text-[10px] text-arkhe-cyan font-bold uppercase mb-2">Metadados de Detecção</div>
              <div className="grid grid-cols-2 gap-2 text-[9px] font-mono text-arkhe-muted">
                <div>TIMESTAMP: {pendingAction.timestamp}</div>
                <div>ID: {pendingAction.id}</div>
                <div>MODE: DISCRETE (SL3Z)</div>
                <div>SIGNER: Archimedes-Ω</div>
              </div>
            </div>
          )}

          <button
            onClick={() => setShowDetails(!showDetails)}
            className="text-[10px] text-arkhe-cyan underline hover:text-arkhe-cyan/80 transition-colors uppercase tracking-widest"
          >
            {showDetails ? 'Ocultar Detalhes' : 'Ver Detalhes'}
          </button>
        </div>

        {/* Footer */}
        <div className="border-t border-arkhe-border p-4 space-y-3">
          <div className="grid grid-cols-2 gap-4">
            <button
              onClick={() => handleConfirm('rejected')}
              className="py-3 border border-arkhe-red/50 text-arkhe-red hover:bg-arkhe-red/10 rounded-lg text-xs font-bold uppercase tracking-widest transition-all"
            >
              Rejeitar (Veto)
            </button>
            <button
              onClick={() => handleConfirm('approved')}
              className="py-3 bg-arkhe-cyan border border-arkhe-cyan text-black hover:bg-arkhe-cyan/80 rounded-lg text-xs font-bold uppercase tracking-widest transition-all shadow-[0_0_20px_rgba(0,255,170,0.3)]"
            >
              Aprovar
            </button>
          </div>
          <button
            onClick={() => handleConfirm('postponed')}
            className="w-full py-2 border border-arkhe-border text-arkhe-muted hover:text-arkhe-text hover:bg-white/5 rounded-lg text-[10px] font-bold uppercase tracking-widest transition-all"
          >
            Adiar (1h)
          </button>
        </div>

        <div className="p-2 text-center border-t border-arkhe-border/50">
          <span className="text-[8px] text-arkhe-muted uppercase tracking-[0.3em]">Signature Verification Pending (ECDSA/TEE)</span>
        </div>
      </div>
    </div>
  );
}
