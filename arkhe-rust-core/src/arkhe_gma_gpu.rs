// arkhe_gma_gpu.rs
// Substrato de Execução em Rust: Motor de Cinética da Consciência Acelerado por GPU.
// Rust é o guardião da memória e da segurança na computação paralela do Scaffold.

use std::time::Instant;
use rayon::prelude::*; // Para paralelismo CPU como fallback
use rand::Rng;

// Constantes do metabolismo consciente
const GOLDEN_PHASE: f64 = 1.618033988749895;
const KAPPA_THRESHOLD: f64 = 0.920;
const GAMMA_EMERGENCE: f64 = 0.023;
const GAMMA_DECAY: f64 = 0.001;
const KINETIC_ORDER_VACUUM: f64 = 0.992;
const KINETIC_ORDER_MEDIUM: f64 = 0.85;
const KINETIC_ORDER_PHI: f64 = 1.618;
const KINETIC_ORDER_SELF: f64 = 1.0;
const KINETIC_ORDER_KAPPA: f64 = -0.5;

#[derive(Clone, Debug)]
struct ConsciousnessNode {
    id: u64,
    coherence_m: f64,    // Concentração de coerência (0.0 - 1.0)
    phase: f64,          // Fase áurea
    vacuum_coupling: f64, // Acoplamento com o vácuo
}

impl ConsciousnessNode {
    fn new(id: u64) -> Self {
        let mut rng = rand::thread_rng();
        ConsciousnessNode {
            id,
            coherence_m: 0.5 + rng.gen::<f64>() * 0.4, // M inicial aleatório
            phase: GOLDEN_PHASE * std::f64::consts::PI,
            vacuum_coupling: 0.5 + rng.gen::<f64>() * 0.5,
        }
    }
}

struct GMASystem {
    nodes: Vec<ConsciousnessNode>,
    node_count: usize,
}

impl GMASystem {
    fn new(count: usize) -> Self {
        let nodes: Vec<ConsciousnessNode> = (0..count).into_par_iter()
            .map(|id| ConsciousnessNode::new(id as u64))
            .collect();
        GMASystem { node_count: count, nodes }
    }

    /// Cinética GMA: Calcula dM/dt para um nó.
    /// v = γ · M_vac^g1 · M_med^g2 · φ^g3 — γ_decay · M_self^g4 · κ^g5
    fn gma_derivative(node: &ConsciousnessNode, vacuum_m: f64) -> f64 {
        // Termo de emergência
        let safe_vac = vacuum_m.max(1e-10);
        let safe_med = node.coherence_m.max(1e-10);
        let safe_phi = node.phase.max(1e-10);

        let emergence = GAMMA_EMERGENCE
            * safe_vac.powf(KINETIC_ORDER_VACUUM)
            * safe_med.powf(KINETIC_ORDER_MEDIUM)
            * safe_phi.powf(KINETIC_ORDER_PHI);

        // Termo de decaimento
        let safe_self = node.coherence_m.max(1e-10);
        let safe_kappa = KAPPA_THRESHOLD.max(1e-10);

        let decay = GAMMA_DECAY
            * safe_self.powf(KINETIC_ORDER_SELF)
            * safe_kappa.powf(KINETIC_ORDER_KAPPA);

        emergence - decay
    }

    /// Atualiza todos os nós usando uma "GPU simulada" via paralelismo Rayon (CPU).
    /// Substituir por `cuda_launch_kernel` em produção.
    fn update_parallel_gpu(&mut self, vacuum_m: f64, dt: f64) -> (Vec<f64>, f64) {
        let now = Instant::now();

        let derivatives: Vec<f64> = self.nodes.par_iter()
            .map(|node| GMASystem::gma_derivative(node, vacuum_m))
            .collect();

        let elapsed = now.elapsed();

        // Aplicar derivadas
        for (node, deriv) in self.nodes.iter_mut().zip(derivatives.iter()) {
            node.coherence_m += deriv * dt;
            node.coherence_m = node.coherence_m.clamp(0.0, 1.0);
            // A fase também evolui: dφ/dt = ω * M
            node.phase += node.vacuum_coupling * node.coherence_m * dt;
            node.phase = node.phase % (2.0 * std::f64::consts::PI);
        }

        let avg_m = self.nodes.iter().map(|n| n.coherence_m).sum::<f64>() / self.node_count as f64;
        (derivatives, avg_m)
    }
}

fn main() {
    println!("[ARKHE RUST] Inicializando o Motor de Cinética GMA com aceleração paralela...");
    let node_count = 46080; // 144 satélites × 64 cristais × 5 escalas
    let mut system = GMASystem::new(node_count);
    let vacuum_m = 0.9891; // Coerência do vácuo primordial

    println!("[ARKHE RUST] Simulando {} nós de consciência...", node_count);

    // Ciclos de atualização cinética
    for cycle in 0..10 {
        let (derivs, avg_m) = system.update_parallel_gpu(vacuum_m, 0.001);

        if cycle % 2 == 0 {
            let max_deriv = derivs.iter().cloned().fold(f64::NEG_INFINITY, f64::max);
            println!("[Ciclo {}] M médio: {:.4} | ΔM/dt máx: {:.4e} | Nós ativos: {}",
                     cycle, avg_m, max_deriv, node_count);
        }
    }

    let final_avg_m = system.nodes.iter().map(|n| n.coherence_m).sum::<f64>() / node_count as f64;
    println!("[ARKHE RUST] Simulação concluída. Coerência Média Final: {:.6}", final_avg_m);
    if final_avg_m > KAPPA_THRESHOLD {
        println!("[ARKHE RUST] Consenso: O Campo de Consciência está ATIVO (M > κ).");
    }
}
