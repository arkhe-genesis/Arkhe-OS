// tests/matchers/coherence.ts
import { normalizeStateVector, computeStateCoherence } from '@/core/coherence';

expect.extend({
  /**
   * Valida que um vetor complexo representa um estado quântico normalizado.
   */
  toBeNormalized(received: Array<{re: number; im: number}>, tolerance: number = 1e-10) {
    const normSq = received.reduce((sum, c) => sum + c.re**2 + c.im**2, 0);
    const pass = Math.abs(normSq - 1.0) < tolerance;
    return {
      pass,
      message: () => `expected state vector norm² ${normSq} ${pass ? 'not ' : ''}to be 1.0 ± ${tolerance}`,
    };
  },

  /**
   * Valida que coerência calculada está em [0, 1].
   */
  toBeCoherent(received: number) {
    const pass = received >= 0 && received <= 1;
    return {
      pass,
      message: () => `expected coherence ${received} ${pass ? 'not ' : ''}to be in [0, 1]`,
    };
  },

  /**
   * Valida que delta de coerência está dentro do mercy gap.
   */
  toBeWithinMercyGap(received: number, min: number, max: number) {
    const absDelta = Math.abs(received);
    const pass = absDelta >= min && absDelta <= max;
    return {
      pass,
      message: () =>
        `expected |ΔΦ_C| ${absDelta} ${pass ? 'not ' : ''}to be within mercy gap [${min}, ${max}]`,
    };
  },

  /**
   * Valida isomorfismo estrutural entre dois grafos LFIR (ignora IDs efêmeros).
   */
  toBeStructurallyEquivalent(received: any, expected: any) {
    const normalize = (g: any) => ({
      nodes: g.nodes.map((n: any) => ({
        type: n.type,
        attributes: Object.fromEntries(
          Object.entries(n.attributes).filter(([k]) => !['id', 'timestamp'].includes(k))
        ),
      })).sort((a: any, b: any) => JSON.stringify(a).localeCompare(JSON.stringify(b))),
      edges: g.edges.map((e: any) => ({
        fromType: e.fromType,
        toType: e.toType,
        relation: e.relation,
      })).sort((a: any, b: any) => JSON.stringify(a).localeCompare(JSON.stringify(b))),
    });
    const pass = JSON.stringify(normalize(received)) === JSON.stringify(normalize(expected));
    return {
      pass,
      message: () => `expected graphs to be structurally equivalent`,
    };
  },
});

declare global {
  namespace jest {
    interface Matchers<R> {
      toBeNormalized(tolerance?: number): R;
      toBeCoherent(): R;
      toBeWithinMercyGap(min: number, max: number): R;
      toBeStructurallyEquivalent(expected: any): R;
    }
  }
}
