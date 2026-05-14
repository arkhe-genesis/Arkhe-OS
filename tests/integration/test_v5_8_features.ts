// ============================================================================
// Teste de Integração — Features v5.8.0
// ============================================================================

import { ArkhePluginSDK, PluginTemplates } from '../../arkp-plugin-sdk/src';
import { ORCIDIntegration } from '../../arkp-orcid/src/ORCIDIntegration';
import { OfflineSyncEngine } from '../../arkp-mobile/src/services/OfflineSyncEngine';
import { initI18n, supportedLocales } from '../../arkp-i18n/src/ArkheI18n';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { AcademicProfile } from '../../arkp-orcid/src/types';

// Mock AsyncStorage
jest.mock('@react-native-async-storage/async-storage', () => ({
  getItem: jest.fn(),
  setItem: jest.fn(),
}));

describe('ARKHE v5.8.0 Integration Tests', () => {

  describe('Mobile App — OfflineSyncEngine', () => {
    it('should queue votes when offline and sync when online', async () => {
      // Simular ambiente offline
      jest.spyOn(global, 'fetch').mockImplementation(() =>
        Promise.reject(new Error('Network error'))
      );

      // Submeter voto offline
      await OfflineSyncEngine.queueVote(
        'task-123',
        'approve',
        'Test rationale',
        0.9
      );

      // Verificar que voto foi armazenado localmente
      const pendingVotes = await AsyncStorage.getItem(
        (OfflineSyncEngine as any)['STORAGE_KEYS'].SUBMITTED_VOTES
      );
      expect(pendingVotes).toContain('task-123');

      // Simular volta da conectividade
      jest.spyOn(global, 'fetch').mockImplementation(() =>
        Promise.resolve({ ok: true, json: () => Promise.resolve({}) }) as any
      );

      // Sincronizar
      await OfflineSyncEngine.syncAll('reviewer-001', 'token-abc', false);

      // Verificar que voto foi removido da fila pendente
      const remainingVotes = await AsyncStorage.getItem(
        (OfflineSyncEngine as any)['STORAGE_KEYS'].SUBMITTED_VOTES
      );
      expect(remainingVotes).not.toContain('task-123');
    });

    it('should adapt sync strategy based on network quality', async () => {
      const strategies = [
        { quality: 'none' as const, expected: { votes: true, tasks: true, plugins: false, metrics: false } },
        { quality: 'poor' as const, expected: { votes: true, tasks: true, plugins: false, metrics: false } },
        { quality: 'good' as const, expected: { votes: true, tasks: true, plugins: true, metrics: true } },
        { quality: 'excellent' as const, expected: { votes: true, tasks: true, plugins: true, metrics: true } },
      ];

      for (const { quality, expected } of strategies) {
        const strategy = (OfflineSyncEngine as any).determineSyncStrategy(quality, false);
        expect(strategy).toEqual(expected);
      }
    });
  });

  describe('Multi-idioma — ArkheI18n', () => {
    beforeEach(async () => {
      await initI18n('en');
    });

    it('should support all declared locales', () => {
      expect(supportedLocales.length).toBeGreaterThanOrEqual(50);
      expect(supportedLocales).toContain('pt');
      expect(supportedLocales).toContain('ar'); // RTL support
      expect(supportedLocales).toContain('zh');
    });

    it('should translate domain-specific terms', async () => {
      const terms = ['security_vulnerability', 'privacy_violation', 'algorithmic_bias'];

      const translations = await import('../../arkp-i18n/src/ArkheI18n')
        .then(m => m.translateDomainTerms(terms, 'en', 'pt', 'ethics'));

      expect(translations['security_vulnerability']).toBeDefined();
      expect(translations['privacy_violation']).toBeDefined();
      expect(translations['algorithmic_bias']).toBeDefined();
    });

  });

  describe('Plugin SDK — ArkhePluginSDK', () => {
    it('should create plugin from template', async () => {
      const builder = await ArkhePluginSDK.createPlugin(
        'test-security-plugin',
        'general',
        'basic'
      );

      const pluginCode = await (builder as any).getCode();
      expect(pluginCode).toContain('implements EthicalRulePlugin');
      expect(pluginCode).toContain('evaluate(');
      expect(pluginCode).toContain('getRecommendations(');
    });

    it('should validate plugin code', async () => {
      const validCode = PluginTemplates.basic
        .replace('MyEthicalPlugin', 'ValidPlugin')
        .replace('general', 'healthcare');

      const metadata = {
        pluginId: 'valid-plugin-v1',
        domain: 'healthcare',
        version: '1.0.0',
        author: 'Test Author',
        description: 'Test plugin',
        checksum: 'abc123',
        compatibleVersions: ['5.8.0'],
        requiredPermissions: [],
      };

      const result = await ArkhePluginSDK.validatePlugin(validCode, metadata as any);
      expect(result.valid).toBe(true);
    });

    it('should detect invalid plugin code', async () => {
      const invalidCode = 'export class InvalidPlugin { /* missing interface */ }';

      const metadata = {
        pluginId: 'invalid-plugin-v1',
        domain: 'general',
        version: '1.0.0',
        author: 'Test',
        description: 'Invalid',
        checksum: 'xyz789',
        compatibleVersions: ['5.8.0'],
        requiredPermissions: [],
      };

      const result = await ArkhePluginSDK.validatePlugin(invalidCode, metadata as any);
      expect(result.valid).toBe(false);
      expect(result.errors.length).toBeGreaterThan(0);
    });

    it('should run plugin tests', async () => {
      // Criar plugin de teste
      const builder = await ArkhePluginSDK.createPlugin('test-plugin', 'general', 'basic');
      const plugin = await (builder as any).build();

      // Definir casos de teste
      const testCases = [
        {
          manifest: { package: { name: 'safe-pkg' } },
          sourceFiles: [['main.py', 'def safe(): return 42']] as [string, string][],
          expectedRisks: {} as Record<string, number>,
        },
        {
          manifest: { package: { name: 'risky-pkg' } },
          sourceFiles: [['main.py', "eval('dangerous')"]] as [string, string][],
          expectedRisks: { security_vulnerability: 0.7 },
        },
      ];

      const results = await ArkhePluginSDK.testPlugin(plugin, testCases);
      expect(results.every(r => r.passed)).toBe(true);
    });
  });

  describe('ORCID Integration — ORCIDIntegration', () => {
    let orcid: ORCIDIntegration;

    beforeEach(() => {
      orcid = new ORCIDIntegration('test-client', 'test-secret', 'https://test/callback');
    });

    it('should generate correct authorization URL', () => {
      const url = orcid.getAuthorizationUrl('state-123');
      expect(url).toContain('https://pub.orcid.org/v3.0/oauth/authorize');
      expect(url).toContain('client_id=test-client');
      expect(url).toContain('state=state-123');
    });

    it('should calculate academic reputation', async () => {
      const profile: AcademicProfile = {
        orcid: '0000-0001-2345-6789',
        name: 'Test Researcher',
        emails: ['test@example.com'],
        keywords: ['ai ethics', 'formal methods'],
        publications: Array(15).fill(null).map((_, i) => ({
          title: `Paper ${i + 1}`,
          authors: [{ name: 'Test Researcher' }],
          publicationDate: `202${i % 4}-01-01`,
          citationCount: 50 + i * 10,
        })),
        affiliations: [
          { organization: 'University of Test', type: 'employment', country: 'BR' },
          { organization: 'ARKHE Institute', type: 'employment', country: 'US' },
        ],
        citations: { total: 750, byYear: {}, byPublication: {} },
        hIndex: 12,
        primaryCountry: 'BR',
        lastUpdated: new Date().toISOString(),
      };

      const reputation = await orcid.calculateAcademicReputation(profile);
      expect(reputation).toBeGreaterThan(0.5);
      expect(reputation).toBeLessThanOrEqual(1.0);
    });

    it('should calculate QIP bonus for academic profile', () => {
      const profile: AcademicProfile = {
        orcid: '0000-0001-2345-6789',
        name: 'Test',
        emails: [],
        keywords: ['ai ethics'],
        publications: [
          {
            title: 'High Impact Paper',
            authors: [],
            publicationDate: '2024-01-01',
            journal: { name: 'Nature', impactFactor: 49.96 },
            citationCount: 200,
          },
          {
            title: 'ARKHE Collaboration',
            authors: [{ name: 'Test', orcid: 'ARKHE-001' }],
            publicationDate: '2024-01-01',
          }
        ],
        affiliations: [
          { organization: 'Harvard University', type: 'employment', country: 'US' },
        ],
        lastUpdated: new Date().toISOString(),
      };

      const academicRep = 0.7;
      const bonus = (orcid as any).calculateQIPBonus(profile, academicRep);

      // Deve incluir bônus por: high-impact pub + elite institution + arkhe collab + keyword
      expect(bonus).toBeGreaterThan(0.05);
      expect(bonus).toBeLessThanOrEqual(0.30); // Limite máximo
    });
  });

  describe('Full Integration — Mobile + I18n + SDK + ORCID', () => {
    it('should support complete reviewer workflow', async () => {
      // 1. Inicializar i18n
      await initI18n('pt');

      // 2. Criar plugin de teste via SDK
      const builder = await ArkhePluginSDK.createPlugin('test-review-plugin', 'general');
      const plugin = await (builder as any).build();

      // 3. Simular perfil ORCID
      const orcid = new ORCIDIntegration('test', 'test', 'test');
      const profile: AcademicProfile = {
        orcid: '0000-0001-2345-6789',
        name: 'Dr. Test',
        emails: ['test@arkhe.io'],
        keywords: [],
        publications: [],
        affiliations: [],
        lastUpdated: new Date().toISOString(),
      };

      // 4. Calcular reputação acadêmica
      const academicRep = await orcid.calculateAcademicReputation(profile);
      expect(academicRep).toBeDefined();

      // 5. Simular uso no mobile app
      await OfflineSyncEngine.queueVote(
        'task-456',
        'approve',
        'Aprovado com base na análise ética',
        0.85
      );

      // 6. Verificar que voto foi armazenado
      const pending = await AsyncStorage.getItem(
        (OfflineSyncEngine as any)['STORAGE_KEYS'].SUBMITTED_VOTES
      );
      expect(pending).toContain('task-456');

      console.log('✅ Full integration test passed');
    });
  });
});
