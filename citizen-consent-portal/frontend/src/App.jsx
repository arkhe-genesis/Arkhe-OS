// frontend/src/App.jsx
import { useState, useEffect, useCallback, Suspense } from 'react';
import { OmegaGauge } from './components/OmegaGauge';
import { ConsentPanel } from './components/ConsentPanel';
import { AuditTimeline } from './components/AuditTimeline';
import { useConsent } from './hooks/useConsent';
import { showToast } from './main';

// DID do cidadão (em produção, viria da wallet/auth)
const CITIZEN_DID = import.meta.env.VITE_CITIZEN_DID || 'did:cathedral:citizen:abc123';

export function App() {
  // Hook personalizado para consentimento
  const {
    consentState,
    grantConsent,
    revokeConsent,
    exportData,
    refresh
  } = useConsent(CITIZEN_DID);

  // Estado para Ω-score (métrica de saúde do organismo)
  const [omega, setOmega] = useState(null);
  const [omegaStatus, setOmegaStatus] = useState('unknown');

  // Carregar Ω-score inicial e atualizar periodicamente
  useEffect(() => {
    let intervalId;

    const fetchOmega = async () => {
      try {
        const response = await fetch(`${import.meta.env.VITE_CATHEDRAL_API}/health/omega`);
        if (!response.ok) throw new Error('Failed to fetch omega');

        const data = await response.json();
        setOmega(data.global_omega);

        // Determinar status visual
        if (data.global_omega >= 0.85) {
          setOmegaStatus('healthy');
        } else if (data.global_omega >= 0.70) {
          setOmegaStatus('warning');
        } else {
          setOmegaStatus('critical');
        }
      } catch (err) {
        console.error('Failed to load omega:', err);
        showToast('Não foi possível carregar o status da Catedral', 'error');
      }
    };

    // Fetch inicial
    fetchOmega();

    // Polling a cada 30 segundos (ajustável conforme necessidade)
    intervalId = setInterval(fetchOmega, 30000);

    return () => clearInterval(intervalId);
  }, []);

  // Listener para eventos de consentimento de outros componentes
  useEffect(() => {
    const handleConsentGranted = (event) => {
      showToast(`✅ Consentimento concedido: ${event.detail.category} → ${event.detail.purpose}`, 'success');
    };

    const handleConsentRevoked = (event) => {
      showToast(`🔄 Consentimento revogado: ${event.detail.category} → ${event.detail.purpose}`, 'info');
    };

    window.addEventListener('cathedral:consent:granted', handleConsentGranted);
    window.addEventListener('cathedral:consent:revoked', handleConsentRevoked);

    return () => {
      window.removeEventListener('cathedral:consent:granted', handleConsentGranted);
      window.removeEventListener('cathedral:consent:revoked', handleConsentRevoked);
    };
  }, []);

  // Handler para exportação de dados (direito à portabilidade)
  const handleExportData = useCallback(async () => {
    try {
      showToast('📦 Preparando exportação de dados...', 'info');
      const result = await exportData({
        includeAuditTrail: true,
        format: 'json',
      });
      showToast(`✅ Dados exportados: ${result.filename}`, 'success');
    } catch (err) {
      showToast('❌ Falha ao exportar dados', 'error');
      console.error('Export failed:', err);
    }
  }, [exportData]);

  // Loading state inicial
  if (consentState.loading && !omega) {
    return (
      <div className="loading-screen" role="status" aria-live="polite">
        <div className="spinner" aria-label="Carregando Catedral"></div>
        <p>Conectando à Catedral...</p>
        <p><small>Verificando identidade: <code>{CITIZEN_DID.slice(0, 20)}...</code></small></p>
      </div>
    );
  }

  // Error state
  if (consentState.error) {
    return (
      <div className="error-screen" role="alert">
        <h1>❌ Erro de Conexão</h1>
        <p>{consentState.error}</p>
        <button onClick={() => window.location.reload()} className="btn-primary">
          Tentar novamente
        </button>
        <p><small>Se o problema persistir, contate: <a href="mailto:support@cathedral.ark">support@cathedral.ark</a></small></p>
      </div>
    );
  }

  return (
    <main className="dashboard" role="main">
      {/* Header com identidade do cidadão */}
      <header className="header">
        <h1>🏛️ Portal do Cidadão</h1>
        <p className="subtitle">Soberania digital com privacidade preservada</p>
        <p className="citizen-id" aria-label="Seu identificador na Catedral">
          <small>
            Cidadão: <code title={CITIZEN_DID}>{CITIZEN_DID.slice(0, 24)}...</code>
          </small>
        </p>
      </header>

      {/* Gauge de Ω-score (saúde do organismo) */}
      <OmegaGauge
        value={omega}
        status={omegaStatus}
        onRefresh={refresh}
      />

      {/* Painel de consentimento granular */}
      <ConsentPanel
        categories={consentState.categories}
        onGrant={grantConsent}
        onRevoke={revokeConsent}
        lastUpdated={consentState.lastUpdated}
        loading={consentState.loading}
      />

      {/* Timeline de auditoria imutável */}
      <Suspense fallback={<div className="audit-loading">Carregando auditoria...</div>}>
        <AuditTimeline
          citizenId={CITIZEN_DID}
          onExport={handleExportData}
        />
      </Suspense>

      {/* Footer com informações de soberania */}
      <footer className="site-footer">
        <p>
          <small>
            Catedral Arkhe v2.4.1 •
            <a href="https://codex.cathedral.ark" target="_blank" rel="noopener noreferrer">
              Códice Cristalino
            </a> •
            <a href="/privacy">Política de Privacidade</a> •
            <button onClick={handleExportData} className="link-button">
              Exportar Meus Dados
            </button>
          </small>
        </p>
      </footer>
    </main>
  );
}
