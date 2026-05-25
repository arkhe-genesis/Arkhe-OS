// ═══════════════════════════════════════════════════════════════════
// ARKHE.JS — Atlas da Catedral (Hook 769.4)
// ═══════════════════════════════════════════════════════════════════

class CathedralAtlas {
  /**
   * @param {Array<{id: number, name: string, phiC: number}>} substrates — Lista de substratos
   */
  constructor(substrates = []) {
    this.substrates = substrates;
    this._computeCurvatures();
  }

  /**
   * Calcula a curvatura de Gauss para cada substrato.
   * K_s = (Φ_C(s) − μ) / σ
   * @private
   */
  _computeCurvatures() {
    if (this.substrates.length === 0) return;

    const phiValues = this.substrates.map(s => s.phiC);
    const mu = phiValues.reduce((a, b) => a + b, 0) / phiValues.length;
    const variance = phiValues.reduce((sum, phi) => sum + (phi - mu) ** 2, 0) / phiValues.length;
    const sigma = Math.sqrt(variance);

    for (const s of this.substrates) {
      s.K_s = sigma > 0 ? (s.phiC - mu) / sigma : 0;
      s.type = s.K_s > 0.5 ? 'Esférico' : s.K_s < -0.5 ? 'Hiperbólico' : 'Plano';
    }
  }

  /**
   * Retorna a curvatura de um substrato específico.
   * @param {number} id — ID do substrato
   * @returns {Object|null} — Dados da carta
   */
  getChart(id) {
    return this.substrates.find(s => s.id === id) || null;
  }

  /**
   * Retorna a lista de curvaturas.
   * @returns {Array<{id: number, name: string, phiC: number, K_s: number, type: string}>}
   */
  curvatureList() {
    return this.substrates.map(s => ({
      id: s.id,
      name: s.name,
      phiC: s.phiC,
      K_s: s.K_s,
      type: s.type,
    }));
  }

  /**
   * Retorna estatísticas do atlas.
   * @returns {Object}
   */
  statistics() {
    const curvatures = this.substrates.map(s => s.K_s);
    return {
      totalCharts: this.substrates.length,
      meanCurvature: curvatures.reduce((a, b) => a + b, 0) / curvatures.length,
      maxCurvature: Math.max(...curvatures),
      minCurvature: Math.min(...curvatures),
      sphericalCount: this.substrates.filter(s => s.type === 'Esférico').length,
      hyperbolicCount: this.substrates.filter(s => s.type === 'Hiperbólico').length,
      flatCount: this.substrates.filter(s => s.type === 'Plano').length,
    };
  }
}

module.exports = CathedralAtlas;