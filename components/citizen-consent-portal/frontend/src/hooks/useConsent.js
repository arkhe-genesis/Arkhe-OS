// frontend/src/hooks/useConsent.js
import { useState, useEffect, useCallback, useMemo } from 'react';
import { CathedralSDK, ZKProofVerifier } from 'cathedral-sdk';

/**
 * Hook personalizado para gerenciar consentimento granular com a Catedral
 * @param {string} citizenDid - DID do cidadão (ex: did:cathedral:citizen:abc123)
 * @returns {Object} Estado e ações de consentimento
 */
export function useConsent(citizenDid) {
  // Estado local do consentimento
  const [consentState, setConsentState] = useState({
    loading: true,
    error: null,
    categories: {},
    lastUpdated: null,
    zkProofs: {}, // Cache de provas ZK verificadas
  });

  // Instância do SDK (memoizada para evitar recriação)
  const sdk = useMemo(() => {
    return new CathedralSDK({
      endpoint: import.meta.env.VITE_CATHEDRAL_API || 'https://api.cathedral.ark/v1',
      citizenDid,
      // Configurações de segurança
      requireZKProofs: true,
      cacheZKProofs: true,
    });
  }, [citizenDid]);

  // Carregar estado atual do consentimento ao montar
  useEffect(() => {
    let mounted = true;
    let abortController;

    const loadConsent = async () => {
      abortController = new AbortController();

      try {
        const consent = await sdk.getConsentStatus({
          signal: abortController.signal,
          includeZKProofs: true,
        });

        if (mounted) {
          // Verificar provas ZK localmente (opcional, para defesa em profundidade)
          const verifiedProofs = {};
          for (const [key, proof] of Object.entries(consent.zkProofs || {})) {
            const isValid = await ZKProofVerifier.verify(proof, {
              publicInputs: { citizenDid, category: key.split(':')[0] },
            });
            if (isValid) {
              verifiedProofs[key] = true;
            }
          }

          setConsentState({
            loading: false,
            error: null,
            categories: consent.categories,
            lastUpdated: consent.updatedAt,
            zkProofs: verifiedProofs,
          });
        }
      } catch (err) {
        if (err.name === 'AbortError') return;

        console.error('Failed to load consent:', err);
        if (mounted) {
          setConsentState(prev => ({
            ...prev,
            loading: false,
            error: err.message || 'Não foi possível carregar suas preferências.',
          }));
        }
      }
    };

    loadConsent();

    // Cleanup
    return () => {
      mounted = false;
      if (abortController) abortController.abort();
    };
  }, [sdk, citizenDid]);

  // Conceder consentimento para categoria + propósito
  const grantConsent = useCallback(async (category, purpose, options = {}) => {
    try {
      setConsentState(prev => ({ ...prev, loading: true, error: null }));

      const receipt = await sdk.grantConsent({
        category,
        purpose,
        duration: options.duration || { type: 'indefinite' },
        revocable: options.revocable !== false,
        // Metadados para auditoria
        metadata: {
          userAgent: navigator.userAgent,
          timestamp: new Date().toISOString(),
          // Hash do estado atual para rastreabilidade
          stateHash: await sdk.hashState({ categories: consentState.categories }),
        },
      });

      // Atualizar estado local
      setConsentState(prev => ({
        ...prev,
        loading: false,
        categories: {
          ...prev.categories,
          [category]: {
            ...prev.categories[category],
            [purpose]: {
              granted: true,
              receiptId: receipt.id,
              grantedAt: receipt.grantedAt,
              zkProofVerified: true, // Assumindo que o SDK já verificou
            },
          },
        },
        lastUpdated: new Date().toISOString(),
      }));

      // Notificar web component (se presente) para atualização em tempo real
      const consentEl = document.querySelector('cathedral-consent');
      if (consentEl?.updateState) {
        consentEl.updateState({
          category,
          purpose,
          status: 'granted',
          receiptId: receipt.id,
        });
      }

      // Disparar evento personalizado para outros componentes
      window.dispatchEvent(new CustomEvent('cathedral:consent:granted', {
        detail: { category, purpose, receipt },
      }));

      return receipt;

    } catch (err) {
      console.error('Consent grant failed:', err);
      setConsentState(prev => ({
        ...prev,
        loading: false,
        error: err.message || 'Não foi possível conceder consentimento.',
      }));
      throw err;
    }
  }, [sdk, consentState.categories]);

  // Revogar consentimento
  const revokeConsent = useCallback(async (category, purpose) => {
    try {
      const receipt = await sdk.revokeConsent({ category, purpose });

      setConsentState(prev => ({
        ...prev,
        categories: {
          ...prev.categories,
          [category]: {
            ...prev.categories[category],
            [purpose]: {
              granted: false,
              revokedAt: new Date().toISOString(),
              receiptId: receipt.id,
            },
          },
        },
        lastUpdated: new Date().toISOString(),
      }));

      // Notificar componentes
      window.dispatchEvent(new CustomEvent('cathedral:consent:revoked', {
        detail: { category, purpose, receipt },
      }));

      return receipt;

    } catch (err) {
      console.error('Consent revoke failed:', err);
      throw err;
    }
  }, [sdk]);

  // Exportar dados para portabilidade (FS-19)
  const exportData = useCallback(async (options = {}) => {
    try {
      const exportResult = await sdk.exportPersonalData({
        categories: options.categories || Object.keys(consentState.categories),
        format: options.format || 'json',
        includeAuditTrail: options.includeAuditTrail !== false,
      });

      // Trigger download no navegador
      const blob = new Blob([exportResult.data], {
        type: `application/${exportResult.format}+cathedral`
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `cathedral-export-${citizenDid.slice(-8)}-${Date.now()}.${exportResult.format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      return exportResult;
    } catch (err) {
      console.error('Data export failed:', err);
      throw err;
    }
  }, [sdk, consentState.categories, citizenDid]);

  // Refresh manual do estado
  const refresh = useCallback(() => {
    setConsentState(prev => ({ ...prev, loading: true }));
    // Re-trigger o effect de carregamento
    return sdk.getConsentStatus().then(consent => {
      setConsentState(prev => ({
        ...prev,
        loading: false,
        categories: consent.categories,
        lastUpdated: consent.updatedAt,
      }));
    });
  }, [sdk]);

  return {
    consentState,
    grantConsent,
    revokeConsent,
    exportData,
    refresh,
    // Exposição segura do SDK para casos avançados
    sdk: useMemo(() => ({
      verifyZKProof: (proof, publicInputs) => ZKProofVerifier.verify(proof, { publicInputs }),
      getReceipt: (receiptId) => sdk.getReceipt(receiptId),
    }), [sdk]),
  };
}
