// frontend/src/main.jsx - Conexão com o DOM e registro de componentes
import { createRoot } from 'react-dom/client';
import { App } from './App.jsx';
import { registerCathedralComponents } from 'cathedral-sdk/dom';

// Registrar web components do SDK Cathedral (se não carregados via CDN)
// Isso permite uso de <cathedral-consent>, <cathedral-audit>, etc.
registerCathedralComponents({
  // Configurações globais para componentes
  theme: 'crystal',
  apiEndpoint: import.meta.env.VITE_CATHEDRAL_API,
  // Callbacks para eventos de soberania
  onConsentChange: (event) => {
    console.log('🔐 Consentimento alterado:', event.detail);
    // Disparar analytics anonimizado (se habilitado)
    if (import.meta.env.VITE_ENABLE_ANALYTICS === 'true') {
      // Apenas metadados, nunca dados pessoais
      fetch('/api/anonymized-event', {
        method: 'POST',
        body: JSON.stringify({
          type: 'consent_change',
          category: event.detail.category,
          action: event.detail.status,
          timestamp: event.timeStamp,
        }),
        headers: { 'Content-Type': 'application/json' },
      }).catch(() => {}); // Fail silently para não bloquear UX
    }
  },
});

// Renderizar aplicação React
const rootElement = document.getElementById('root');
if (!rootElement) {
  throw new Error('Elemento #root não encontrado. Verifique seu HTML.');
}

const root = createRoot(rootElement);
root.render(<App />);

// ===== FUNÇÕES DE UTILIDADE PARA MANIPULAÇÃO DO DOM =====

/**
 * Atualiza a timeline de auditoria com novas entradas
 * @param {Array} entries - Lista de entradas de auditoria
 */
export function updateAuditTimeline(entries) {
  const container = document.getElementById('audit-timeline');
  if (!container) return;

  // Indicador de carregamento
  container.setAttribute('aria-busy', 'true');

  if (!entries || entries.length === 0) {
    container.innerHTML = '<p class="empty-state">Nenhuma decisão registrada ainda.</p>';
    container.setAttribute('aria-busy', 'false');
    return;
  }

  // Renderizar entradas (ordenadas por timestamp descendente)
  const sorted = [...entries].sort((a, b) =>
    new Date(b.timestamp) - new Date(a.timestamp)
  );

  container.innerHTML = sorted.map(entry => `
    <article
      class="audit-entry"
      data-receipt-id="${entry.receiptId}"
      data-category="${entry.category}"
      data-purpose="${entry.purpose}"
      tabindex="0"
      role="listitem"
    >
      <time datetime="${entry.timestamp}" title="${new Date(entry.timestamp).toLocaleString()}">
        ${new Date(entry.timestamp).toLocaleDateString('pt-BR')} ${new Date(entry.timestamp).toLocaleTimeString('pt-BR', {hour: '2-digit', minute:'2-digit'})}
      </time>
      <p>
        <strong>${entry.action === 'grant' ? '✅ Consentido' : '❌ Revogado'}</strong>:
        <code>${entry.category}</code> → <code>${entry.purpose}</code>
      </p>
      <small>
        Receipt:
        <a
          href="https://codex.cathedral.ark/receipt/${entry.receiptId}"
          target="_blank"
          rel="noopener noreferrer"
          title="Verificar no Códice Cristalino"
        >
          ${entry.receiptId.slice(0, 8)}...
        </a>
      </small>
    </article>
  `).join('');

  // Anunciar atualização para leitores de tela
  container.setAttribute('aria-busy', 'false');

  // Adicionar listeners para navegação por teclado
  container.querySelectorAll('.audit-entry').forEach(entry => {
    entry.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        // Abrir modal com detalhes do receipt (implementação opcional)
        console.log('Receipt selecionado:', entry.dataset.receiptId);
      }
    });
  });
}

/**
 * Exibe notificação toast para feedback do usuário
 * @param {string} message - Mensagem a exibir
 * @param {'success'|'error'|'info'} type - Tipo da notificação
 */
export function showToast(message, type = 'info') {
  // Remover toasts existentes
  document.querySelectorAll('.cathedral-toast').forEach(el => el.remove());

  const toast = document.createElement('div');
  toast.className = `cathedral-toast toast-${type}`;
  toast.setAttribute('role', 'alert');
  toast.setAttribute('aria-live', 'assertive');
  toast.innerHTML = `
    <span class="toast-icon">${type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️'}</span>
    <span class="toast-message">${message}</span>
    <button class="toast-close" aria-label="Fechar notificação">&times;</button>
  `;

  // Estilos inline para o toast (em produção, usar CSS classes)
  Object.assign(toast.style, {
    position: 'fixed',
    bottom: '2rem',
    right: '2rem',
    padding: '1rem',
    background: type === 'success' ? 'var(--cathedral-success)' :
                type === 'error' ? 'var(--cathedral-error)' :
                'var(--cathedral-blue-500)',
    color: 'white',
    borderRadius: 'var(--border-radius)',
    boxShadow: 'var(--shadow-lg)',
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    zIndex: '1000',
    animation: 'fadeIn 200ms ease',
    maxWidth: '300px',
  });

  // Botão de fechar
  toast.querySelector('.toast-close').onclick = () => {
    toast.style.animation = 'fadeIn 200ms ease reverse';
    setTimeout(() => toast.remove(), 200);
  };

  // Auto-remove após 5 segundos
  setTimeout(() => {
    if (toast.parentNode) {
      toast.style.animation = 'fadeIn 200ms ease reverse';
      setTimeout(() => toast.remove(), 200);
    }
  }, 5000);

  document.body.appendChild(toast);
}
