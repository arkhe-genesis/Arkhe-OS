import { redactSecrets, hashPath } from '../../src/core/privacy';
import { MinimalIDEParser } from '../../src/core/parser';

describe('MinimalIDEParser', () => {
  it('should redact secrets correctly', async () => {
    const content = "password = 'super_secret_password'";
    const redacted = await redactSecrets(content);
    expect(redacted).not.toContain('super_secret_password');
    expect(redacted).toContain('[REDACTED]');
  });

  it('should calculate local coherence', () => {
    const parser = new MinimalIDEParser();
    const testCases = [
      { event: 'save', expected: 0.8 },
      { event: 'edit', expected: 0.3 },
      { event: 'completion_accept', expected: 0.7 },
      { event: 'diagnostic_fix', expected: 0.9 },
    ];
    for (const { event, expected } of testCases) {
      const coherence = (parser as any).computeLocalCoherence({ event_type: event });
      expect(Math.abs(coherence - expected)).toBeLessThan(0.01);
    }
  });
});
