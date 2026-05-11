// arkhe-os/parser/frontends/ontology_diff_tool.ts
import { LFIRGraph, LFIRNode } from '../lfir';

export interface EmbeddingModel {
  encode(input: { text: string; structure: any }): Promise<number[]>;
}

function getStructuralContext(node: LFIRNode, graph: LFIRGraph): any {
  // Retornar nós relacionados e contexto estrutural (mocked)
  return { id: node.id, type: node.type };
}

function computeCosineSimilarityMatrix(embeddings1: number[][], embeddings2: number[][]): number[][] {
  const matrix: number[][] = [];
  for (let i = 0; i < embeddings1.length; i++) {
    matrix[i] = [];
    for (let j = 0; j < embeddings2.length; j++) {
      let dotProduct = 0;
      let normA = 0;
      let normB = 0;
      for (let k = 0; k < embeddings1[i].length; k++) {
        dotProduct += embeddings1[i][k] * embeddings2[j][k];
        normA += embeddings1[i][k] * embeddings1[i][k];
        normB += embeddings2[j][k] * embeddings2[j][k];
      }
      matrix[i][j] = normA === 0 || normB === 0 ? 0 : dotProduct / (Math.sqrt(normA) * Math.sqrt(normB));
    }
  }
  return matrix;
}

function hungarianAlgorithm(matrix: number[][]): [number, number][] {
  // Implementação simplificada greedy do Hungarian Algorithm para matching
  const matching: [number, number][] = [];
  const usedCols = new Set<number>();

  for (let i = 0; i < matrix.length; i++) {
    let maxVal = -1;
    let maxJ = -1;
    for (let j = 0; j < matrix[i].length; j++) {
      if (!usedCols.has(j) && matrix[i][j] > maxVal) {
        maxVal = matrix[i][j];
        maxJ = j;
      }
    }
    if (maxJ !== -1) {
      matching.push([i, maxJ]);
      usedCols.add(maxJ);
    }
  }

  return matching;
}

export async function ontologySemanticDistance(
  ontology1: LFIRGraph,
  ontology2: LFIRGraph,
  embeddingModel: EmbeddingModel
): Promise<number> {
  // Extrair classes de ambas as ontologias
  // Nós com typo 'Class' mockado para o exemplo (ou baseando no tipo se disponível)
  const classes1 = ontology1.nodes.filter(n => n.type === 'Class' as any || n.id.includes('class'));
  const classes2 = ontology2.nodes.filter(n => n.type === 'Class' as any || n.id.includes('class'));

  if (classes1.length === 0 || classes2.length === 0) return 1.0;

  // Gerar embeddings para cada classe (label + comment + contexto estrutural)
  const embeddings1 = await Promise.all(
    classes1.map(c => embeddingModel.encode({
      text: `${c.attributes['label'] || ''} ${c.attributes['comment'] || ''}`,
      structure: getStructuralContext(c, ontology1)
    }))
  );

  const embeddings2 = await Promise.all(
    classes2.map(c => embeddingModel.encode({
      text: `${c.attributes['label'] || ''} ${c.attributes['comment'] || ''}`,
      structure: getStructuralContext(c, ontology2)
    }))
  );

  // Calcular similaridade máxima por classe (Hungarian algorithm para matching ótimo)
  const similarityMatrix = computeCosineSimilarityMatrix(embeddings1, embeddings2);
  const optimalMatching = hungarianAlgorithm(similarityMatrix);

  const totalSimilarity = optimalMatching.reduce((sum, [i, j]) =>
    sum + similarityMatrix[i][j], 0
  );

  return 1 - (totalSimilarity / Math.max(classes1.length, classes2.length));
}
