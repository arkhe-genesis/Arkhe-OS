// ============================================================================
// Arkhe Plugin SDK — Ferramentas para Desenvolvimento de Plugins Éticos
// ============================================================================

import {
  EthicalRulePlugin, PluginMetadata, PluginValidationResult,
  EvaluationContext, RiskAssessment
} from './types';
import { PluginValidator } from './validator';
import { PluginBuilder } from './builder';
import { PluginPublisher } from './publisher';
import { PluginTester } from './tester';

// ============================================================================
// API PRINCIPAL DO SDK
// ============================================================================

export class ArkhePluginSDK {
  /**
   * Cria um novo plugin a partir de um template
   */
  static async createPlugin(
    name: string,
    domain: string,
    template: 'basic' | 'advanced' | 'custom' = 'basic'
  ): Promise<any> {
    return PluginBuilder.fromTemplate(name, domain, template);
  }

  /**
   * Valida um plugin antes da publicação
   */
  static async validatePlugin(
    pluginCode: string,
    metadata: PluginMetadata
  ): Promise<PluginValidationResult> {
    return PluginValidator.validate(pluginCode, metadata);
  }

  /**
   * Testa um plugin com casos de teste padrão
   */
  static async testPlugin(
    plugin: EthicalRulePlugin,
    testCases?: Array<{
      manifest: any;
      sourceFiles: Array<[string, string]>;
      expectedRisks: Record<string, number>;
    }>
  ): Promise<Array<{ passed: boolean; message: string }>> {
    return PluginTester.runTests(plugin, testCases);
  }

  /**
   * Publica um plugin no marketplace
   */
  static async publishPlugin(
    plugin: EthicalRulePlugin,
    metadata: PluginMetadata,
    authToken: string
  ): Promise<{ pluginId: string; status: string }> {
    return PluginPublisher.publish(plugin, metadata, authToken);
  }

  /**
   * Gera documentação automática para o plugin
   */
  static async generateDocumentation(
    plugin: EthicalRulePlugin,
    format: 'markdown' | 'html' | 'json' = 'markdown'
  ): Promise<string> {
    return PluginBuilder.generateDocs(plugin, format);
  }
}

// ============================================================================
// TEMPLATES DE PLUGIN
// ============================================================================

export const PluginTemplates = {
  /**
   * Template básico para plugins de verificação simples
   */
  basic: `
import { EthicalRulePlugin, EvaluationContext } from '@arkhe/plugin-sdk';

export class MyEthicalPlugin implements EthicalRulePlugin {
  pluginId = 'my-plugin-v1';
  domain = 'general';
  version = '1.0.0';
  author = 'Your Name';

  validate(): boolean {
    // Verificar configurações do plugin
    return true;
  }

  evaluate(
    manifest: any,
    sourceFiles: Array<[string, string]>,
    dependencies: any[],
    context: EvaluationContext
  ): Record<string, number> {
    const risks: Record<string, number> = {};

    // Exemplo: verificar uso de eval/exec
    for (const [filename, content] of sourceFiles) {
      if (content.includes('eval(') || content.includes('exec(')) {
        risks['security_vulnerability'] = 0.7;
      }
    }

    return risks;
  }

  getRecommendations(risks: Record<string, number>): string[] {
    const recommendations: string[] = [];

    if (risks['security_vulnerability'] > 0.5) {
      recommendations.push('Evitar uso de eval/exec; usar alternativas seguras');
    }

    return recommendations;
  }
}
  `,

  /**
   * Template avançado com configuração e estado
   */
  advanced: `
import { EthicalRulePlugin, EvaluationContext, PluginConfig } from '@arkhe/plugin-sdk';

interface MyPluginConfig extends PluginConfig {
  strictMode: boolean;
  allowedPatterns: string[];
  riskThreshold: number;
}

export class AdvancedEthicalPlugin implements EthicalRulePlugin {
  pluginId = 'advanced-plugin-v1';
  domain = 'healthcare';
  version = '1.0.0';
  author = 'Your Name';

  private config: MyPluginConfig;

  constructor(config?: Partial<MyPluginConfig>) {
    this.config = {
      strictMode: false,
      allowedPatterns: [],
      riskThreshold: 0.5,
      ...config
    };
  }

  validate(): boolean {
    // Validar configuração
    if (this.config.riskThreshold < 0 || this.config.riskThreshold > 1) {
      throw new Error('riskThreshold must be between 0 and 1');
    }
    return true;
  }

  evaluate(
    manifest: any,
    sourceFiles: Array<[string, string]>,
    dependencies: any[],
    context: EvaluationContext
  ): Record<string, number> {
    const risks: Record<string, number> = {};

    // Verificar padrões configuráveis
    for (const [filename, content] of sourceFiles) {
      for (const pattern of this.config.allowedPatterns) {
        if (new RegExp(pattern).test(content)) {
          // Padrão permitido: reduzir risco
          risks['pattern_match'] = Math.max(0, (risks['pattern_match'] || 0) - 0.2);
        }
      }
    }

    // Aplicar threshold
    return Object.fromEntries(
      Object.entries(risks).map(([key, value]) => [
        key,
        value >= this.config.riskThreshold ? value : 0
      ])
    );
  }

  getRecommendations(risks: Record<string, number>): string[] {
    // Recomendações baseadas na configuração
    if (this.config.strictMode) {
      return ['Modo estrito ativado: todas as violações são bloqueadas'];
    }
    return ['Considere ativar strictMode para maior segurança'];
  }

  // Método para atualizar configuração em tempo de execução
  updateConfig(newConfig: Partial<MyPluginConfig>): void {
    this.config = { ...this.config, ...newConfig };
    this.validate();
  }
}
  `,

  /**
   * Template customizado para domínios específicos
   */
  custom: `
// Template customizado: clone e adapte para seu domínio
// Consulte a documentação: https://docs.arkhe.io/plugins/custom
  `
};

// ============================================================================
// CLI DO SDK (para uso em terminal)
// ============================================================================

export const CLI = {
  /**
   * Comando: arkhe-plugin create <name> --domain <domain>
   */
  async create(name: string, options: { domain: string; template?: string }) {
    const builder = await ArkhePluginSDK.createPlugin(
      name,
      options.domain,
      options.template as any
    );
    await builder.writeToDisk(`./plugins/${name}`);
    console.log(`✅ Plugin \${name} criado em ./plugins/\${name}`);
  },

  /**
   * Comando: arkhe-plugin validate <path>
   */
  async validate(pluginPath: string) {
    const { code, metadata } = await PluginBuilder.loadFromPath(pluginPath);
    const result = await ArkhePluginSDK.validatePlugin(code, metadata);

    if (result.valid) {
      console.log('✅ Plugin válido');
    } else {
      console.error('❌ Erros de validação:');
      result.errors.forEach(err => console.error(`  - \${err}`));
      process.exit(1);
    }
  },

  /**
   * Comando: arkhe-plugin test <path>
   */
  async test(pluginPath: string) {
    const plugin = await PluginBuilder.loadPlugin(pluginPath);
    const results = await ArkhePluginSDK.testPlugin(plugin);

    const passed = results.filter(r => r.passed).length;
    const total = results.length;

    console.log(`📊 Testes: \${passed}/\${total} passaram`);

    if (passed < total) {
      results.filter(r => !r.passed).forEach(r =>
        console.error(`  ❌ \${r.message}`)
      );
      process.exit(1);
    }
  },

  /**
   * Comando: arkhe-plugin publish <path> --token <token>
   */
  async publish(pluginPath: string, options: { token: string }) {
    const plugin = await PluginBuilder.loadPlugin(pluginPath);
    const metadata = await PluginBuilder.loadMetadata(pluginPath);

    const result = await ArkhePluginSDK.publishPlugin(
      plugin,
      metadata,
      options.token
    );

    console.log(`🚀 Plugin publicado: \${result.pluginId}`);
    console.log(`Status: \${result.status}`);
  }
};
