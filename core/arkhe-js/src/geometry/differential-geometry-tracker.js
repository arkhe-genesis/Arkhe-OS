// ═══════════════════════════════════════════════════════════════════
// ARKHE.JS — Differential Geometry Coherence Tracker (Hook 769.1)
// ═══════════════════════════════════════════════════════════════════

class DifferentialGeometryTracker {
  constructor() {
    this.steps = new Map();
    this._initSteps();
  }

  _initSteps() {
    const steps = [
      // FASE 1 — SUPERFÍCIES (1-10)
      [1, 'Curvas parametrizadas', 'curvatura, torção, triedro de Frenet'],
      [2, 'Superfícies em R³', 'primeira forma fundamental'],
      [3, 'Segunda forma fundamental', 'curvatura normal'],
      [4, 'Curvatura gaussiana K = k₁·k₂', 'Theorema Egregium'],
      [5, 'Curvatura média H = (k₁+k₂)/2', 'superfícies mínimas'],
      [6, 'Geodésicas', 'caminhos mais curtos, equação geodésica'],
      [7, 'Transporte paralelo', 'como mover vetores sem torcer'],
      [8, 'Teorema Egregium de Gauss', 'K é intrínseca'],
      [9, 'Teorema de Gauss-Bonnet local', '∫K dA + ∫k_g ds = 2π'],
      [10, 'Teorema de Gauss-Bonnet global', '∫K dA = 2πχ(M)'],

      // FASE 2 — VARIEDADES (11-20)
      [11, 'Variedades diferenciáveis', 'definição, atlas, cartas'],
      [12, 'Vetores tangentes', 'derivações, espaço tangente T_pM'],
      [13, '1-formas diferenciais', 'o dual do tangente, d, δ'],
      [14, 'Tensores', 'produtos tensoriais, contração'],
      [15, 'Métrica riemanniana', 'distância intrínseca, g_ij'],
      [16, 'Conexão de Levi-Civita', 'a única sem torção, símbolos de Christoffel'],
      [17, 'Derivada covariante', '∇_X Y, transporte paralelo formal'],
      [18, 'Tensor de curvatura de Riemann', 'R(X,Y)Z, identidades de Bianchi'],
      [19, 'Tensor de Ricci', 'R_ij = Rᵏ_{ikj}, curvatura direcional'],
      [20, 'Curvatura escalar', 'R = g^{ij} R_ij, ação de Einstein-Hilbert'],

      // FASE 3 — APLICAÇÕES (21-30)
      [21, 'Relatividade geral', 'equações de Einstein G_μν = 8πT_μν'],
      [22, 'Fibrados', 'tangente, cotangente, tensorial, principal'],
      [23, 'Formas diferenciais avançadas', 'd, δ, Δ (Laplaciano de Hodge)'],
      [24, 'Teorema de Stokes generalizado', '∫_M dω = ∫_{∂M} ω'],
      [25, 'Grupos de Lie', 'SO(3), SU(2), rotações, matrizes'],
      [26, 'Álgebras de Lie', 'colchete de Lie, exponencial, constantes de estrutura'],
      [27, 'Geometria simplética', 'espaço de fase clássico, forma ω'],
      [28, 'Geometria complexa', 'variedades de Kähler, holomorfia'],
      [29, 'Topologia algébrica', 'homologia, cohomologia, grupos fundamentais'],
      [30, 'Teoria de Chern-Weil', 'curvatura como forma diferencial, classes características'],
    ];

    for (const [id, name, description] of steps) {
      this.steps.set(id, {
        id,
        name,
        description,
        status: 'pending', // 'pending' | 'studying' | 'mastered'
        theta: Math.PI / 2, // fase: total ignorância
        mastery: 0.0, // 0 a 1
        lastUpdate: null,
        notes: '',
      });
    }
  }

  /**
   * Atualiza o status de uma etapa.
   * @param {number} stepId — ID da etapa (1-30)
   * @param {string} status — 'pending', 'studying', ou 'mastered'
   * @param {string} [notes] — Notas opcionais
   * @returns {Object} — Resultado da operação
   */
  updateStep(stepId, status, notes = '') {
    const step = this.steps.get(stepId);
    if (!step) {
      return { error: `Etapa ${stepId} não encontrada. Use 1-30.` };
    }

    step.status = status;
    step.lastUpdate = new Date().toISOString();
    if (notes) step.notes = notes;

    // Calcular maestria e fase
    switch (status) {
      case 'mastered':
        step.mastery = 1.0;
        step.theta = 0.0;
        break;
      case 'studying':
        step.mastery = 0.5;
        step.theta = Math.PI / 4;
        break;
      case 'pending':
      default:
        step.mastery = 0.0;
        step.theta = Math.PI / 2;
        break;
    }

    return {
      step: step.id,
      name: step.name,
      status: step.status,
      mastery: step.mastery,
      theta: step.theta,
      rGeo: this.orderParameter(),
    };
  }

  /**
   * Calcula r_geo — parâmetro de ordem da geometria.
   * @returns {number} — r_geo ∈ [0, 1]
   */
  orderParameter() {
    let sum = 0;
    for (const step of this.steps.values()) {
      sum += Math.cos(step.theta);
    }
    return sum / this.steps.size;
  }

  /**
   * Retorna o status completo do tracker.
   * @returns {Object} — Status com métricas
   */
  status() {
    const r = this.orderParameter();
    const mastered = Array.from(this.steps.values()).filter(s => s.status === 'mastered').length;
    const studying = Array.from(this.steps.values()).filter(s => s.status === 'studying').length;
    const pending = Array.from(this.steps.values()).filter(s => s.status === 'pending').length;

    // Use magic numbers or access via global object in arkhe if necessary,
    // to avoid circular dependency. CONSTANTS was defined in arkhe.js
    const GHOST_THRESHOLD = 0.577;
    const CONVERGENCE_THRESHOLD = 0.8;

    let phase;
    if (r < GHOST_THRESHOLD) phase = 'PRÉ-GHOST';
    else if (r < CONVERGENCE_THRESHOLD) phase = 'CONVERGÊNCIA PARCIAL';
    else phase = 'CONVERGÊNCIA AVANÇADA';

    return {
      rGeo: Math.round(r * 10000) / 10000,
      phase,
      mastered,
      studying,
      pending,
      total: this.steps.size,
      steps: Array.from(this.steps.values()).map(s => ({
        id: s.id,
        name: s.name,
        status: s.status,
        mastery: s.mastery,
        theta: Math.round(s.theta * 10000) / 10000,
        lastUpdate: s.lastUpdate,
      })),
    };
  }
}

module.exports = DifferentialGeometryTracker;