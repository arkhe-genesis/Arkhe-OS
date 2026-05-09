// frontend/src/components/ConsentPanel.jsx
import { useState, useCallback } from 'react';

export function ConsentPanel({
  categories,
  onGrant,
  onRevoke,
  lastUpdated,
  loading
}) {
  // Estado para controlar qual categoria está expandida
  const [expanded, setExpanded] = useState(null);

  // Toggle de expansão com acessibilidade
  const toggleCategory = useCallback((category) => {
    setExpanded(prev => prev === category ? null : category);
  }, []);

  // Handler para mudança de checkbox com confirmação
  const handleConsentChange = useCallback(async (category, purpose, checked) => {
    try {
      if (checked) {
        // Confirmação para conceder (boas práticas de UX para consentimento)
        const confirmed = window.confirm(
          `Conceder consentimento para:\n\nCategoria: ${category}\nPropósito: ${purpose}\n\nIsso permitirá o processamento de seus dados para este fim específico. Você pode revogar a qualquer momento.`
        );
        if (!confirmed) return;

        await onGrant(category, purpose);
      } else {
        // Confirmação para revogar
        const confirmed = window.confirm(
          `Revogar consentimento para:\n\nCategoria: ${category}\nPropósito: ${purpose}\n\nIsso interromperá o processamento de seus dados para este fim.`
        );
        if (!confirmed) return;

        await onRevoke(category, purpose);
      }
    } catch (err) {
      // Erro já tratado no hook, mas podemos dar feedback adicional
      console.error('Consent change failed:', err);
    }
  }, [onGrant, onRevoke]);

  return (
    <section
      className="consent-card"
      aria-labelledby="consent-heading"
      aria-busy={loading}
    >
      <h2 id="consent-heading">⚙️ Preferências de Consentimento</h2>

      {lastUpdated && (
        <p className="last-updated" aria-label={`Última atualização em ${new Date(lastUpdated).toLocaleString()}`}>
          Última atualização: {new Date(lastUpdated).toLocaleString('pt-BR')}
        </p>
      )}

      {loading && (
        <p className="loading-text" role="status">
          <span className="spinner-small" aria-hidden="true"></span>
          Atualizando preferências...
        </p>
      )}

      <div className="categories-list" role="list">
        {Object.entries(categories || {}).map(([category, purposes]) => (
          <div key={category} className="category-group" role="listitem">
            <button
              className="category-header"
              onClick={() => toggleCategory(category)}
              aria-expanded={expanded === category}
              aria-controls={`purposes-${category}`}
              type="button"
            >
              <span className="category-name">{category}</span>
              <span className="toggle-icon" aria-hidden="true">
                {expanded === category ? '−' : '+'}
              </span>
            </button>

            {expanded === category && (
              <div
                id={`purposes-${category}`}
                className="purposes-list"
                role="group"
                aria-label={`Propósitos para ${category}`}
              >
                {Object.entries(purposes || {}).map(([purpose, state]) => (
                  <label key={purpose} className="purpose-item">
                    <input
                      type="checkbox"
                      id={`${category}-${purpose}`}
                      checked={!!state.granted}
                      onChange={(e) => handleConsentChange(category, purpose, e.target.checked)}
                      disabled={loading || state.loading}
                      aria-describedby={`${category}-${purpose}-desc`}
                    />
                    <span className="purpose-label" id={`${category}-${purpose}-desc`}>
                      {purpose}
                    </span>
                    {state.revokedAt && (
                      <small className="revoked-badge" aria-label="Revogado">
                        Revogado
                      </small>
                    )}
                    {state.zkProofVerified && (
                      <span className="zk-badge" title="Prova ZK verificada" aria-label="Verificado criptograficamente">
                        🔐
                      </span>
                    )}
                  </label>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Help text para acessibilidade */}
      <p className="help-text">
        <small>
          ℹ️ Cada consentimento é registrado com prova criptográfica no Códice Cristalino.
          Você pode auditar todas as decisões a qualquer momento.
        </small>
      </p>
    </section>
  );
}
