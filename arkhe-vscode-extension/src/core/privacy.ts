// src/core/privacy.ts — Redação automática de segredos
import * as crypto from 'crypto';

/**
 * Redata padrões comuns de segredos em snippets de código
 */
export async function redactSecrets(content: string, maxLength: number = 200): Promise<string> {
  // Padrões de segredos a serem redatados
  const patterns = [
    /(?:password|passwd|pwd)\s*[=:]\s*["']?[^"'\s]+["']?/gi,
    /(?:api[_-]?key|apikey)\s*[=:]\s*["']?[^"'\s]+["']?/gi,
    /(?:token|auth[_-]?token)\s*[=:]\s*["']?[^"'\s]+["']?/gi,
    /(?:secret|client[_-]?secret)\s*[=:]\s*["']?[^"'\s]+["']?/gi,
    /(?:private[_-]?key|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)/gi,
    /(?:AWS_ACCESS_KEY_ID|AWS_SECRET_ACCESS_KEY)\s*[=:]\s*[^,\s]+/gi,
  ];

  let redacted = content;
  for (const pattern of patterns) {
    redacted = redacted.replace(pattern, (match) => {
      // Manter estrutura, redatar valor
      const parts = match.split(/([=:]\s*)/);
      if (parts.length >= 3) {
        return `${parts[0]}${parts[1]}[REDACTED]`;
      }
      return '[REDACTED_SECRET]';
    });
  }

  // Truncar para limite de snippet
  return redacted.slice(0, maxLength) + (redacted.length > maxLength ? '...' : '');
}

/**
 * Hash de path de arquivo para anonimização (SHA-256 truncado)
 */
export async function hashPath(filePath: string, salt?: string): Promise<string> {
  const input = salt ? `${filePath}:${salt}` : filePath;
  const hash = crypto.createHash('sha256').update(input).digest('hex');
  return hash.slice(0, 16); // 64 bits de entropia suficiente para referência
}

/**
 * Verifica se conteúdo contém padrões sensíveis antes de enviar
 */
export function isSensitive(content: string): boolean {
  const sensitivePatterns = [
    /-----BEGIN PRIVATE KEY-----/i,
    /(?:password|token|secret)\s*[=:]\s*["']?[A-Za-z0-9+/]{20,}["']?/i,
  ];
  return sensitivePatterns.some(pattern => pattern.test(content));
}
