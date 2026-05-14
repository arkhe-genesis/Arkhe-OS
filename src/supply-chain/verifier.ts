// src/supply-chain/verifier.ts
/**
 * Substrato 6131: NPM Supply Chain Hardening
 *
 * Princípio: Cada dependência é um nó na cadeia de confiança.
 * Cada pacote é verificado por assinatura, hash e comportamento.
 * Cada vulnerabilidade é um paradoxo a ser resolvido.
 */

import * as crypto from 'crypto';

export interface SupplyChainConfig {
    trustedMaintainers: string[];
    blockedPackages: string[];
    vulnFeed: string;
}

export interface PackageVerification {
  name: string;
  version: string;
  integrity: {
    sha512: string;           // Hash do tarball
    provenance?: Provenance;  // SLSA provenance
    signature?: Signature;    // Assinatura do maintainer
  };
  dependencies: DependencyGraph;
  vulnerabilities: VulnerabilityReport;
  behavior_analysis: BehaviorReport;
  trust_score: number;        // 0.0 - 1.0
}

export interface Provenance {
  builder_id: string;
  build_type: string;
  parameters: Record<string, any>;
  materials: Material[];
  statement: string;          // in-toto statement
  signature: string;
}

export interface Material {
    uri: string;
    digest: Record<string, string>;
}

export interface Signature {
  key_id: string;
  sig: string;
  method: 'pgp' | 'sigstore' | 'arkhe-signature';
}

export interface PackageRef {
    name: string;
    version: string;
}

export interface DependencyGraph {
  direct: PackageRef[];
  transitive: PackageRef[];
  cycles: string[][];         // Ciclos detectados
  depth: number;
}

export interface Vulnerability {
    id: string;
    severity: 'critical' | 'high' | 'medium' | 'low';
}

export interface VulnerabilityReport {
  critical: number;
  high: number;
  medium: number;
  low: number;
  details: Vulnerability[];
  fix_available: boolean;
}

export interface BehaviorReport {
  // Análise estática do comportamento do pacote
  filesystem_access: string[];     // Paths acessados
  network_calls: string[];         // Domínios contatados
  env_vars_read: string[];         // Variáveis de ambiente lidas
  child_processes: string[];       // Comandos executados
  eval_usage: 'none' | 'safe' | 'dangerous';
  obfuscation_detected: boolean;
  suspicious_patterns: string[];
}

export interface DependencyRiskAssessment {
    highRiskTransitive: number;
}

export class SecurityError extends Error {}
export class IntegrityError extends Error {}

export class VulnerabilityDatabase {
    constructor(private feedUrl: string) {}
    async query(name: string, version: string): Promise<VulnerabilityReport> {
        // Stub implementation
        return {
            critical: 0,
            high: 0,
            medium: 0,
            low: 0,
            details: [],
            fix_available: false
        };
    }
}

async function computeSRI(buffer: ArrayBuffer): Promise<string> {
    const hash = crypto.createHash('sha512').update(Buffer.from(buffer)).digest('base64');
    return `sha512-${hash}`;
}

export class SupplyChainVerifier {
  private trustedMaintainers: Set<string>;
  private blockedPackages: Set<string>;
  private vulnerabilityDb: VulnerabilityDatabase;

  constructor(config: SupplyChainConfig) {
    this.trustedMaintainers = new Set(config.trustedMaintainers);
    this.blockedPackages = new Set(config.blockedPackages);
    this.vulnerabilityDb = new VulnerabilityDatabase(config.vulnFeed);
  }

  async verifyPackage(name: string, version: string): Promise<PackageVerification> {
    // 1. Verificar se pacote está bloqueado
    if (this.blockedPackages.has(`${name}@${version}`)) {
      throw new SecurityError(`Package blocked: ${name}@${version}`);
    }

    // 2. Baixar metadados do registry com verificação de integridade
    const metadata = await this.fetchWithIntegrity(name, version);

    // 3. Verificar assinatura do maintainer
    const signatureValid = await this.verifySignature(metadata);

    // 4. Verificar provenance SLSA (se disponível)
    const provenanceValid = metadata.integrity?.provenance
      ? await this.verifyProvenance(metadata.integrity.provenance)
      : true;

    // 5. Analisar dependências transitivas
    const depGraph = await this.buildDependencyGraph(metadata);
    const depRisks = await this.assessDependencyRisks(depGraph);

    // 6. Verificar vulnerabilidades conhecidas
    const vulns = await this.vulnerabilityDb.query(name, version);

    // 7. Analisar comportamento estático (sandboxed)
    const behavior = await this.analyzeBehavior(metadata.tarball);

    // 8. Calcular trust score
    const trustScore = this.calculateTrustScore({
      signatureValid,
      provenanceValid,
      depRisks,
      vulns,
      behavior,
      maintainerTrusted: this.trustedMaintainers.has(metadata.maintainer)
    });

    return {
      name,
      version,
      integrity: metadata.integrity || { sha512: '' },
      dependencies: depGraph,
      vulnerabilities: vulns,
      behavior_analysis: behavior,
      trust_score: trustScore
    };
  }

  private async verifySignature(metadata: any): Promise<boolean> {
      return true; // stub
  }

  private async verifyProvenance(provenance: Provenance): Promise<boolean> {
      return true; // stub
  }

  private async buildDependencyGraph(metadata: any): Promise<DependencyGraph> {
      return { direct: [], transitive: [], cycles: [], depth: 0 }; // stub
  }

  private async assessDependencyRisks(graph: DependencyGraph): Promise<DependencyRiskAssessment> {
      return { highRiskTransitive: 0 }; // stub
  }

  private async analyzeBehavior(tarball: ArrayBuffer): Promise<BehaviorReport> {
      return {
          filesystem_access: [],
          network_calls: [],
          env_vars_read: [],
          child_processes: [],
          eval_usage: 'none',
          obfuscation_detected: false,
          suspicious_patterns: []
      }; // stub
  }

  private async fetchWithIntegrity(name: string, version: string): Promise<any> {
    // Fetch do registry com verificação de SRI
    const response = await fetch(`https://registry.npmjs.org/${name}/${version}`);
    const metadata = await response.json();

    // Verificar integrity field (SRI)
    if (metadata.dist?.integrity) {
      const expected = metadata.dist.integrity;
      const tarballResp = await fetch(metadata.dist.tarball);
      const tarball = await tarballResp.arrayBuffer();
      const actual = await computeSRI(tarball);

      if (expected !== actual) {
        throw new IntegrityError(`SRI mismatch for ${name}@${version}`);
      }

      metadata.tarball = tarball;
    }

    return metadata;
  }

  private calculateTrustScore(factors: {
    signatureValid: boolean;
    provenanceValid: boolean;
    depRisks: DependencyRiskAssessment;
    vulns: VulnerabilityReport;
    behavior: BehaviorReport;
    maintainerTrusted: boolean;
  }): number {
    let score = 1.0;

    // Penalidades
    if (!factors.signatureValid) score -= 0.3;
    if (!factors.provenanceValid) score -= 0.1;
    if (factors.vulns.critical > 0) score -= 0.4;
    if (factors.vulns.high > 0) score -= 0.2;
    if (factors.behavior.eval_usage === 'dangerous') score -= 0.3;
    if (factors.behavior.obfuscation_detected) score -= 0.2;
    if (factors.depRisks.highRiskTransitive > 0) score -= 0.1 * factors.depRisks.highRiskTransitive;

    // Bônus
    if (factors.maintainerTrusted) score += 0.1;
    if (factors.provenanceValid && factors.signatureValid) score += 0.05;

    return Math.max(0, Math.min(1, score));
  }
}