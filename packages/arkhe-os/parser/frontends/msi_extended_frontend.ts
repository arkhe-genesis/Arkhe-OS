// @ts-ignore
import { MsiDatabase, getTable, openDatabase } from 'msi-reader';
import { LFIRGraph, LFIRNode, LFIRNodeType } from '../lfir';

export interface MergeModuleInfo {
  ModuleId: string;
  ModuleName: string;
  Language: number;
  Version: string;
  Manufacturer: string;
}

export interface PatchInfo {
  PatchCode: string;
  TargetProductCode: string;
  UpgradeCode: string;
  Sequence: number;
  Attributes: number;
}

export interface TransformInfo {
  TransformCode: string;
  ValidationFlags: number;
  ErrorCondition: number;
  TransformType: 'upgrade' | 'customization' | 'localization';
}

export class ExtendedMSIFrontend {
  async parseMergeModule(source: Buffer, filename: string): Promise<LFIRGraph> {
    const graph = new LFIRGraph();
    const db = await openDatabase(source);

    // Extrair metadados do Merge Module
    const modules = await getTable<MergeModuleInfo>(db, 'ModuleSignature');
    const module = modules[0];

    const rootNode = new LFIRNode(`msm/${module.ModuleName}`, LFIRNodeType.Module, 'msm');
    rootNode.attributes = {
      module_id: module.ModuleId,
      version: module.Version,
      manufacturer: module.Manufacturer,
      language: module.Language,
      package_type: 'merge_module'
    };
    graph.addNode(rootNode);

    // Extrair componentes do MSM (mesma estrutura que MSI)
    await this._extractComponentGraph(db, graph, rootNode.id, 'msm');

    // Validar consistência: componentes do MSM devem ter prefixo único
    await this._validateMergeModuleConsistency(graph, module.ModuleId);

    return graph;
  }

  async parsePatch(source: Buffer, filename: string): Promise<LFIRGraph> {
    const graph = new LFIRGraph();
    const db = await openDatabase(source);

    const patches = await getTable<PatchInfo>(db, 'Patch');
    const patch = patches[0];

    const rootNode = new LFIRNode(`msp/${patch.PatchCode}`, LFIRNodeType.Module, 'msp');
    rootNode.attributes = {
      patch_code: patch.PatchCode,
      target_product: patch.TargetProductCode,
      upgrade_code: patch.UpgradeCode,
      sequence: patch.Sequence,
      package_type: 'patch'
    };
    graph.addNode(rootNode);

    // Extrair tabelas modificadas pelo patch (MsiPatchMetadata)
    const modifiedTables = await getTable<any>(db, 'MsiPatchMetadata');
    for (const table of modifiedTables) {
      const tableNode = new LFIRNode(`patch_table/${table.Table}`, LFIRNodeType.Module, 'msp');
      tableNode.attributes = {
        operation: table.Operation, // 'add', 'modify', 'remove'
        rows_affected: table.RowCount
      };
      graph.addNode(tableNode);
      graph.link(rootNode.id, tableNode.id);
    }

    return graph;
  }

  async parseTransform(source: Buffer, filename: string, baseMsi: string): Promise<LFIRGraph> {
    const graph = new LFIRGraph();
    const db = await openDatabase(source);

    const transforms = await getTable<TransformInfo>(db, 'Transform');
    const transform = transforms[0];

    const rootNode = new LFIRNode(`mst/${transform.TransformCode}`, LFIRNodeType.Module, 'mst');
    rootNode.attributes = {
      transform_code: transform.TransformCode,
      base_package: baseMsi,
      transform_type: transform.TransformType,
      validation_flags: transform.ValidationFlags,
      package_type: 'transform'
    };
    graph.addNode(rootNode);

    // Extrair diferenças entre base e transform (via MsiViewGenerateTransform)
    const differences = await this._computeTransformDifferences(db, baseMsi);
    for (const diff of differences) {
      const diffNode = new LFIRNode(`diff/${diff.table}_${diff.row}`, LFIRNodeType.Operation, 'mst');
      diffNode.attributes = {
        table: diff.table,
        operation: diff.operation, // 'insert', 'update', 'delete'
        old_value: diff.oldValue,
        new_value: diff.newValue
      };
      graph.addNode(diffNode);
      graph.link(rootNode.id, diffNode.id);
    }

    return graph;
  }

  private async _extractComponentGraph(db: any, graph: LFIRGraph, rootId: string, lang: string): Promise<void> {
    // Mock implementation for extracting components
  }

  private async _validateMergeModuleConsistency(graph: LFIRGraph, moduleId: string): Promise<void> {
    // Garantir que todos os componentes do MSM tenham prefixo único
    const components = graph.nodes.filter(n => n.type === LFIRNodeType.Module && n.sourceLang === 'msm');
    for (const comp of components) {
      if (!comp.id.startsWith(`${moduleId}/`)) {
        throw new Error(`Component ${comp.id} violates MSM namespace isolation`);
      }
    }
  }

  private async _computeTransformDifferences(transformDb: any, baseMsiPath: string): Promise<Array<any>> {
    return [];
  }
}
