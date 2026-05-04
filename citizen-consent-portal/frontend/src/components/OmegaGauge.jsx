// frontend/src/components/OmegaGauge.jsx
import { memo } from 'react';

export const OmegaGauge = memo(({ value, status, onRefresh }) => {
  const displayValue = value !== null ? value.toFixed(3) : '---';

  return (
    <section className="omega-gauge" aria-labelledby="omega-heading">
      <h2 id="omega-heading" className="sr-only">Status de Saúde do Organismo</h2>
      <div className="omega-value" aria-label={`Ω-score atual: ${displayValue}`}>
        {displayValue}
      </div>
      <div className="omega-label">Ω_score Global</div>

      {status !== 'unknown' && (
        <div className={`omega-status ${status}`} role="status">
          <span className="status-dot"></span>
          {status === 'healthy' ? 'Sistema Estável' :
           status === 'warning' ? 'Degradação Leve' : 'Estado Crítico'}
        </div>
      )}

      <button
        onClick={onRefresh}
        className="refresh-button"
        aria-label="Atualizar status de saúde"
        title="Atualizar"
      >
        🔄
      </button>
    </section>
  );
});

OmegaGauge.displayName = 'OmegaGauge';
