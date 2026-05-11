
/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */



/**
 * @license
 * Copyright 2026 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

// License: MIT
// arkhe_sync_dashboard.tsx — Dashboard React para visualização de sincronização
import React, { useEffect, useState, useRef } from 'react';

interface SyncDashboardProps {
  aggregatorEndpoint: string;  // WebSocket endpoint do aggregator
  nodePairs: Array<[string, string]>;
  onValidationComplete?: (report: any) => void;
}

export const SyncDashboard: React.FC<SyncDashboardProps> = ({
  aggregatorEndpoint,
  nodePairs,
  onValidationComplete
}) => {
  const [jitterData, setJitterData] = useState<Record<string, any>>({});
  const [phaseCoherence, setPhaseCoherence] = useState<Record<string, any>>({});
  const [overallStatus, setOverallStatus] = useState<'IDLE' | 'RUNNING' | 'PASS' | 'FAIL'>('IDLE');
  const [starkProof, setStarkProof] = useState<any>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    // Conectar ao aggregator via WebSocket para streaming em tempo real
    wsRef.current = new WebSocket(aggregatorEndpoint);

    wsRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === 'jitter_update') {
        setJitterData(data.payload);
      } else if (data.type === 'phase_coherence_update') {
        setPhaseCoherence(data.payload);
      } else if (data.type === 'validation_complete') {
        setOverallStatus(data.payload.overall_status);
        setStarkProof(data.payload.stark_proof);
        onValidationComplete?.(data.payload);
      }
    };

    return () => {
      wsRef.current?.close();
    };
  }, [aggregatorEndpoint, onValidationComplete]);

  const startValidation = async () => {
    setOverallStatus('RUNNING');
    wsRef.current?.send(JSON.stringify({
      type: 'start_validation',
      node_pairs: nodePairs
    }));
  };

  return (
    <div className="sync-dashboard" style={{
      padding: '20px',
      background: '#0a0a1a',
      color: '#e0e0ff',
      fontFamily: 'monospace',
      borderRadius: '8px'
    }}>
      <h3 style={{ color: '#ffd700', margin: '0 0 16px 0' }}>
        🔘 ARKHE SYNC DASHBOARD v∞.293.1
      </h3>

      {/* Status geral */}
      <div style={{ marginBottom: '16px', padding: '8px', background: '#1a1a2e', borderRadius: '4px' }}>
        <strong>Status:</strong>{' '}
        <span style={{
          color: overallStatus === 'PASS' ? '#00ff88' :
                 overallStatus === 'FAIL' ? '#ff5555' : '#8888ff'
        }}>
          {overallStatus}
        </span>
      </div>

      {/* Tabela de jitter por par */}
      <div style={{ marginBottom: '16px' }}>
        <h4 style={{ margin: '0 0 8px 0', color: '#88aaff' }}>Jitter Intercontinental (ns RMS)</h4>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid #333' }}>
              <th style={{ textAlign: 'left', padding: '4px' }}>Par de Nós</th>
              <th style={{ textAlign: 'right', padding: '4px' }}>Jitter RMS</th>
              <th style={{ textAlign: 'right', padding: '4px' }}>Pico-a-Pico</th>
              <th style={{ textAlign: 'center', padding: '4px' }}>Status</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(jitterData).map(([pair, stats]: [string, any]) => (
              <tr key={pair} style={{ borderBottom: '1px solid #222' }}>
                <td style={{ padding: '4px' }}>{pair}</td>
                <td style={{ textAlign: 'right', padding: '4px' }}>
                  {stats.jitter_rms_ns?.toFixed(3) ?? 'N/A'}
                </td>
                <td style={{ textAlign: 'right', padding: '4px' }}>
                  {stats.jitter_peak_to_peak_ns?.toFixed(3) ?? 'N/A'}
                </td>
                <td style={{ textAlign: 'center', padding: '4px' }}>
                  {stats.pass ? '✅' : '❌'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Coerência de fase para fingerprint 0.58 */}
      <div style={{ marginBottom: '16px' }}>
        <h4 style={{ margin: '0 0 8px 0', color: '#88aaff' }}>Coerência de Fase (Fingerprint 0.58)</h4>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '8px' }}>
          {Object.entries(phaseCoherence).map(([pair, stats]: [string, any]) => (
            <div key={pair} style={{
              padding: '8px',
              background: stats.phase_coherent ? '#003322' : '#331111',
              borderRadius: '4px',
              border: `1px solid ${stats.phase_coherent ? '#00ff88' : '#ff5555'}`
            }}>
              <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>{pair}</div>
              <div style={{ fontSize: '11px' }}>
                Δφ: {stats.jitter_rad?.toExponential(2) ?? 'N/A'} rad<br/>
                Prob. alinhamento: {(stats.alignment_probability * 100).toFixed(1)}%<br/>
                {stats.phase_coherent ? '✅ Coerente' : '❌ Incoerente'}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Prova STARK */}
      {starkProof && (
        <div style={{ marginBottom: '16px', padding: '8px', background: '#1a1a2e', borderRadius: '4px' }}>
          <h4 style={{ margin: '0 0 8px 0', color: '#00ff88' }}>🔐 Prova STARK de Integridade Temporal</h4>
          <div style={{ fontSize: '11px', fontFamily: 'monospace' }}>
            Hash: {starkProof.data_hash?.slice(0, 16)}...<br/>
            Score de consistência: {(starkProof.consistency_score * 100).toFixed(1)}%<br/>
            Medições validadas: {starkProof.num_measurements}<br/>
            <a href={`data:application/json,${encodeURIComponent(JSON.stringify(starkProof))}`}
               download="stark_proof_temporal.json"
               style={{ color: '#88aaff', textDecoration: 'none' }}>
              ↓ Baixar prova completa
            </a>
          </div>
        </div>
      )}

      {/* Botão de ação */}
      <button
        onClick={startValidation}
        disabled={overallStatus === 'RUNNING'}
        style={{
          padding: '10px 20px',
          background: overallStatus === 'RUNNING' ? '#444' : '#ffd700',
          color: overallStatus === 'RUNNING' ? '#888' : '#000',
          border: 'none',
          borderRadius: '4px',
          cursor: overallStatus === 'RUNNING' ? 'not-allowed' : 'pointer',
          fontWeight: 'bold',
          fontSize: '14px'
        }}
      >
        {overallStatus === 'RUNNING' ? 'Validando...' : 'Iniciar Validação Global'}
      </button>
    </div>
  );
};
