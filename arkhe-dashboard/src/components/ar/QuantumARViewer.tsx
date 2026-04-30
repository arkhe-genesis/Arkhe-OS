
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

// arkhe-dashboard/src/components/ar/QuantumARViewer.tsx
'use client';

import {useEffect, useRef, useState} from 'react';

import {QuantumAROverlay} from '@/lib/ar/quantumAROverlay';
import type {EthicalMetrics} from '@/types/ethics';

interface QuantumARViewerProps {
  metrics: EthicalMetrics;
  onSessionChange?: (active: boolean) => void;
}

export default function QuantumARViewer({
  metrics,
  onSessionChange,
}: QuantumARViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const arOverlayRef = useRef<QuantumAROverlay | null>(null);
  const [arSupported, setArSupported] = useState(false);
  const [sessionActive, setSessionActive] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const checkARSupport = async () => {
      if (typeof window !== 'undefined' && 'xr' in navigator) {
        try {

          const supported = await (
            navigator as unknown as {
              xr: {isSessionSupported: (mode: string) => Promise<boolean>};
            }
          ).xr.isSessionSupported('immersive-ar');
          setArSupported(supported);
        } catch (_err) {
          setArSupported(false);
        }
      }
    };
    checkARSupport().catch(() => {
      /* ignore */
    });
  }, []);

  useEffect(() => {
    if (arOverlayRef.current && sessionActive) {
      arOverlayRef.current.updateOverlayMetrics(metrics);
    }
  }, [metrics, sessionActive]);

  const startARSession = async () => {
    if (!containerRef.current) {return;}

    try {

      const arOverlay = new QuantumAROverlay({
        enableWorldTracking: true,
        enableHandTracking: true,
        enableQpuSimulation: true,
        overlayOpacity: 0.7,
        coherenceVisualizationMode: 'field',
      });

      const success = await arOverlay.initialize(containerRef.current);

      if (success) {
        arOverlayRef.current = arOverlay;
        setSessionActive(true);
        onSessionChange?.(true);
      } else {
        setError(
          'Failed to start AR session. Make sure you are on a compatible device.',
        );
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'AR initialization failed');
    }
  };

  const stopARSession = async () => {
    if (arOverlayRef.current) {
      await arOverlayRef.current.dispose();
      arOverlayRef.current = null;
      setSessionActive(false);
      onSessionChange?.(false);
    }
  };

  return (
    <div className="relative w-full h-full">
      <div
        ref={containerRef}
        className="w-full h-full min-h-[400px] bg-black/20 rounded-xl overflow-hidden flex items-center justify-center border border-white/5"
      >
        {!sessionActive && (
          <div className="text-center p-6 bg-black/40 backdrop-blur-md rounded-2xl max-w-sm border border-white/10">
            <div className="text-4xl mb-4">🔮</div>
            <h4 className="text-lg font-bold text-white mb-2">
              Realidade Aumentada Quântica
            </h4>
            <p className="text-sm text-slate-400 mb-6">
              Sobreponha o campo de coerência Ω ao seu ambiente físico via
              WebXR.
            </p>
            <button
              onClick={startARSession}
              disabled={!arSupported}
              className={`w-full py-3 rounded-xl font-bold transition-all shadow-lg ${
                arSupported
                  ? 'bg-cyan-500 hover:bg-cyan-400 text-black shadow-cyan-500/20'
                  : 'bg-slate-800 text-slate-500 cursor-not-allowed'
              }`}
            >
              {arSupported
                ? 'Iniciar Experiência AR'
                : 'AR Não Suportado neste Browser'}
            </button>
          </div>
        )}
      </div>

      {sessionActive && (
        <div className="absolute top-4 left-4 right-4 flex justify-between items-start pointer-events-none">
          <div className="bg-black/60 backdrop-blur-md rounded-lg p-3 text-[10px] font-mono border border-white/10">
            <div className="text-cyan-400">Ω: {metrics.omega.toFixed(6)}</div>
            <div className="text-purple-400">
              K_ETH: {metrics.kEth.toFixed(6)}
            </div>
            <div className="text-emerald-400">
              Q_FID: {(metrics.quantumFidelity || 0.99).toFixed(4)}
            </div>
          </div>
          <button
            onClick={stopARSession}
            className="pointer-events-auto px-4 py-2 bg-red-500/80 hover:bg-red-500 text-white rounded-lg text-xs font-bold transition-all shadow-lg"
          >
            Sair AR
          </button>
        </div>
      )}

      {error && (
        <div className="absolute top-4 right-4 bg-red-900/80 text-white px-4 py-2 rounded-lg text-xs border border-red-500/50">
          {error}
        </div>
      )}
    </div>
  );
}
