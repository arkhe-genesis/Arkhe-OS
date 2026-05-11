// frontend/src/components/AuditTimeline.jsx
import { useState, useEffect, memo } from 'react';

export const AuditTimeline = memo(({ citizenId, onExport }) => {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Simulação de busca de logs de auditoria
    const fetchAuditLogs = async () => {
      try {
        setLoading(true);
        // Em produção: fetch(`${import.meta.env.VITE_CATHEDRAL_API}/audit/logs/${citizenId}`)
        await new Promise(resolve => setTimeout(resolve, 800));

        setEntries([
          {
            receiptId: 'receipt_1703456789_abc1',
            timestamp: new Date(Date.now() - 3600000).toISOString(),
            action: 'grant',
            category: 'health',
            purpose: 'research'
          },
          {
            receiptId: 'receipt_1703451234_xyz2',
            timestamp: new Date(Date.now() - 86400000).toISOString(),
            action: 'grant',
            category: 'location',
            purpose: 'service'
          }
        ]);
      } catch (err) {
        console.error('Failed to fetch audit logs:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchAuditLogs();
  }, [citizenId]);

  return (
    <section className="audit-section" aria-labelledby="audit-heading">
      <div className="section-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h2 id="audit-heading">🔍 Auditoria de Decisões</h2>
        <button onClick={onExport} className="btn-secondary" style={{ fontSize: '0.75rem' }}>
          Exportar Logs
        </button>
      </div>

      <details open>
        <summary>
          <span className="toggle-icon">▶</span>
          Histórico de consentimentos
        </summary>

        <div id="audit-timeline" aria-live="polite" aria-busy={loading}>
          {loading ? (
            <p className="loading-state">Carregando histórico...</p>
          ) : entries.length === 0 ? (
            <p className="empty-state">Nenhuma decisão registrada ainda.</p>
          ) : (
            entries.map(entry => (
              <article key={entry.receiptId} className="audit-entry">
                <time datetime={entry.timestamp}>
                  {new Date(entry.timestamp).toLocaleString('pt-BR')}
                </time>
                <p>
                  <strong>{entry.action === 'grant' ? '✅ Consentido' : '❌ Revogado'}</strong>:
                  <code>{entry.category}</code> → <code>{entry.purpose}</code>
                </p>
                <small>
                  Receipt: <code>{entry.receiptId.slice(0, 8)}...</code>
                </small>
              </article>
            ))
          )}
        </div>
      </details>
    </section>
  );
});

AuditTimeline.displayName = 'AuditTimeline';
