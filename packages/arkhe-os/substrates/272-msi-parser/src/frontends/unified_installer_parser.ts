// Parser unificado que delega para o parser específico do formato
import * as fs from 'fs/promises';
import { InstallerFormatDetector, InstallerFormat } from './installer_format_detector.js';

export interface ParseOptions {
  [key: string]: any;
}

export interface LFIRGraph {
  nodes: any[];
  edges: any[];
}

export interface AuditFinding {
  ruleId: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  component: string;
  message: string;
  recommendation: string;
}

export interface ParsedInstaller {
  format: string;
  platform: string;
  metadata: {
    name: string;
    version: string;
    publisher: string;
    architecture?: string;
    minOS?: string;
    dependencies?: string[];
  };
  components: InstallerComponent[];
  signatures: DigitalSignature[];
  coherence: {
    score: number;
    findings: AuditFinding[];
    orphanRisk?: Map<string, number>;
  };
  lfirGraph: LFIRGraph;
}

export interface InstallerComponent {
  id: string;
  type: 'file' | 'registry' | 'service' | 'shortcut' | 'environment';
  path: string;
  condition?: string;
  keyPath?: boolean;
  version?: string;
}

export interface DigitalSignature {
  algorithm: string;
  certificate: {
    subject: string;
    issuer: string;
    validFrom: Date;
    validTo: Date;
    serialNumber: string;
  };
  timestamp?: Date;
  valid: boolean;
  chainValid: boolean;
}

import { ExtendedMSIFrontend as MsiExtendedFrontend } from '../../../../parser/frontends/msi_extended_frontend.js';
import { PageRankOrphanMapper } from '../../../../integration/pagerank_orphan_mapper.js';

// Dummy classes for parsers that are missing
class ExeWrapperParser { async parse(buffer: any, filePath: string, options: any): Promise<any> { return { metadata: {}, components: [], signatures: [], lfirGraph: { nodes: [], edges: [] } }; } }
class AppxManifestParser { async parse(buffer: any, filePath: string, options: any): Promise<any> { return { metadata: {}, components: [], signatures: [], lfirGraph: { nodes: [], edges: [] } }; } }
class DebControlParser { async parse(buffer: any, filePath: string, options: any): Promise<any> { return { metadata: {}, components: [], signatures: [], lfirGraph: { nodes: [], edges: [] } }; } }
class RpmSpecParser { async parse(buffer: any, filePath: string, options: any): Promise<any> { return { metadata: {}, components: [], signatures: [], lfirGraph: { nodes: [], edges: [] } }; } }
class ApkManifestParser { async parse(buffer: any, filePath: string, options: any): Promise<any> { return { metadata: {}, components: [], signatures: [], lfirGraph: { nodes: [], edges: [] } }; } }
class AabBundleParser { async parse(buffer: any, filePath: string, options: any): Promise<any> { return { metadata: {}, components: [], signatures: [], lfirGraph: { nodes: [], edges: [] } }; } }
class IpaInfoPlistParser { async parse(buffer: any, filePath: string, options: any): Promise<any> { return { metadata: {}, components: [], signatures: [], lfirGraph: { nodes: [], edges: [] } }; } }
class PkgDistributionParser { async parse(buffer: any, filePath: string, options: any): Promise<any> { return { metadata: {}, components: [], signatures: [], lfirGraph: { nodes: [], edges: [] } }; } }
class DmgVolumeParser { async parse(buffer: any, filePath: string, options: any): Promise<any> { return { metadata: {}, components: [], signatures: [], lfirGraph: { nodes: [], edges: [] } }; } }

export class UnifiedInstallerParser {
  private parsers: Map<string, any>;

  constructor() {
    this.parsers = new Map();
    this._registerParsers();
  }

  private _registerParsers(): void {
    // Windows
    this.parsers.set('MsiExtendedFrontend', new MsiExtendedFrontend());
    this.parsers.set('ExeWrapperParser', new ExeWrapperParser());
    this.parsers.set('AppxManifestParser', new AppxManifestParser());

    // Linux
    this.parsers.set('DebControlParser', new DebControlParser());
    this.parsers.set('RpmSpecParser', new RpmSpecParser());

    // Android
    this.parsers.set('ApkManifestParser', new ApkManifestParser());
    this.parsers.set('AabBundleParser', new AabBundleParser());

    // iOS/macOS
    this.parsers.set('IpaInfoPlistParser', new IpaInfoPlistParser());
    this.parsers.set('PkgDistributionParser', new PkgDistributionParser());
    this.parsers.set('DmgVolumeParser', new DmgVolumeParser());
  }

  async parse(filePath: string, options: ParseOptions = {}): Promise<ParsedInstaller> {
    const buffer = await fs.readFile(filePath);
    const format = await InstallerFormatDetector.detectFormat(filePath, buffer);

    if (!format) {
      throw new Error(`Unknown installer format: ${filePath}`);
    }

    const parser = this.parsers.get(format.parser);
    if (!parser) {
      throw new Error(`Parser not registered for format: ${format.parser}`);
    }

    // Delegar parsing para o parser específico
    const result = await parser.parse(buffer, filePath, options);

    // Calcular coerência específica do instalador
    const coherence = await this._computeInstallerCoherence(result, format);

    return {
      format: format.extension,
      platform: format.platform,
      metadata: result.metadata,
      components: result.components,
      signatures: result.signatures || [],
      coherence,
      lfirGraph: result.lfirGraph
    };
  }

  private async _computeInstallerCoherence(
    parsed: any,
    format: InstallerFormat
  ): Promise<ParsedInstaller['coherence']> {
    const findings: AuditFinding[] = [];

    // Verificação comum: assinatura digital
    if (format.metadata.signaturePath && (!parsed.signatures || parsed.signatures.length === 0)) {
      findings.push({
        ruleId: 'INST-001',
        severity: 'high',
        component: 'signature',
        message: 'Installer lacks digital signature',
        recommendation: 'Sign installer with trusted certificate for integrity verification'
      });
    }

    // Verificação: componentes sem KeyPath (Windows)
    if (format.platform === 'windows' && parsed.components) {
      const orphanComponents = parsed.components.filter((c: any) => !c.keyPath && c.type === 'file');
      if (orphanComponents.length > 0) {
        findings.push({
          ruleId: 'INST-002',
          severity: 'medium',
          component: 'components',
          message: `${orphanComponents.length} file components lack KeyPath`,
          recommendation: 'Define KeyPath for repair/reinstall reliability'
        });
      }
    }

    // Verificação: dependências não declaradas
    if (parsed.metadata?.dependencies?.length === 0 && parsed.components?.some((c: any) => c.type === 'service')) {
      findings.push({
        ruleId: 'INST-003',
        severity: 'low',
        component: 'dependencies',
        message: 'Services installed without declared dependencies',
        recommendation: 'Declare service dependencies for reliable startup order'
      });
    }

    // Calcular score base
    let score = 1.0;
    for (const finding of findings) {
      const penalty = { 'critical': 0.3, 'high': 0.15, 'medium': 0.05, 'low': 0.02 }[finding.severity];
      score -= penalty;
    }
    score = Math.max(0, Math.min(1, score));

    // Calcular orphanRisk via PageRank adaptado (se aplicável)
    let orphanRisk: Map<string, number> | undefined;
    if (parsed.lfirGraph && format.platform === 'windows' && parsed.components) {
      const pagerank = new PageRankOrphanMapper();
      const componentIds = parsed.components.map((c: any) => c.id);
      orphanRisk = pagerank.computeOrphanRisk(parsed.lfirGraph, componentIds);
    }

    return {
      score: Math.round(score * 100) / 100,
      findings,
      orphanRisk
    };
  }
}
