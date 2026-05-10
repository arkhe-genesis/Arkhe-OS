// substrates/v168_noma/mod.rs — Substrato NOMA 6G IoT integrado
use anyhow::Result;
use ndarray::{Array2, ArrayView2};
use rand::prelude::*;
use rand_distr::{Distribution, Rayleigh};

/// Configuração da simulação NOMA 6G
#[derive(Debug, Clone)]
pub struct SimulationConfig {
    pub total_iot_devices: usize,
    pub sub_channels: usize,
    pub max_power_sink: f64,
    pub min_qos_threshold: f64,
    pub circuit_power: f64,
    pub power_gap_sic: f64,
    pub noise_variance: f64,
    pub max_devices_per_sc: usize,
}

impl Default for SimulationConfig {
    fn default() -> Self {
        Self {
            total_iot_devices: 24,
            sub_channels: 12,
            max_power_sink: 20.0,
            min_qos_threshold: 1.0,
            circuit_power: 0.5,
            power_gap_sic: 0.2,
            noise_variance: 0.1,
            max_devices_per_sc: 3,
        }
    }
}

/// Manifold de alocação de potência NOMA para IoT 6G
pub struct NOMAManifold {
    pub config: SimulationConfig,
    pub channels: Array2<f64>,  // [devices, subchannels]
}

impl NOMAManifold {
    /// Criar novo manifold com canais Rayleigh gerados
    pub fn new(config: SimulationConfig) -> Self {
        let mut rng = rand::thread_rng();
        let rayleigh = Rayleigh::new(1.0).unwrap();

        let channels = Array2::from_shape_fn(
            (config.total_iot_devices, config.sub_channels),
            |_| rayleigh.sample(&mut rng),
        );

        Self { config, channels }
    }

    /// Criar com canais específicos (para testes/replay)
    pub fn with_channels(config: SimulationConfig, channels: Array2<f64>) -> Self {
        Self { config, channels }
    }

    /// Calcular SINR após SIC para dispositivo/subcanal específico
    pub fn sinr(
        &self,
        power_matrix: &Array2<f64>,
        device_idx: usize,
        subch_idx: usize,
    ) -> f64 {
        let col_powers = power_matrix.column(subch_idx);
        let col_gains = self.channels.column(subch_idx).mapv(|g| g.powi(2));

        // Ordenar por ganho decrescente para SIC
        let mut order: Vec<usize> = (0..self.config.total_iot_devices).collect();
        order.sort_by(|&a, &b| col_gains[b].partial_cmp(&col_gains[a]).unwrap());

        let pos = order.iter().position(|&i| i == device_idx).unwrap();

        // Interferência: soma das potências * ganhos dos dispositivos com ganho menor
        let interference: f64 = if pos < order.len() - 1 {
            order[pos + 1..]
                .iter()
                .map(|&i| col_powers[i] * col_gains[i])
                .sum()
        } else {
            0.0
        };

        let signal = col_powers[device_idx] * col_gains[device_idx];
        signal / (interference + self.config.noise_variance)
    }

    /// Calcular fitness: (potência total, taxa média, violações de QoS)
    pub fn fitness(&self, power_matrix: &Array2<f64>) -> (f64, f64, usize) {
        let total_power = power_matrix.sum();
        let mut rates = Vec::new();
        let mut violations = 0usize;

        for i in 0..self.config.total_iot_devices {
            for n in 0..self.config.sub_channels {
                if power_matrix[[i, n]] > 1e-9 {
                    let s = self.sinr(power_matrix, i, n);
                    let rate = (1.0 + s).log2();
                    rates.push(rate);
                    if rate < self.config.min_qos_threshold {
                        violations += 1;
                    }
                }
            }
        }

        let avg_rate = if rates.is_empty() { 0.0 } else { rates.iter().sum::<f64>() / rates.len() as f64 };
        (total_power, avg_rate, violations)
    }

    /// Projeção geométrica no núcleo do manifold: força SIC e limite de potência
    pub fn geometric_projection(&self, power_matrix: &Array2<f64>) -> Array2<f64> {
        let mut proj = power_matrix.clone();

        for n in 0..self.config.sub_channels {
            let gains = self.channels.column(n).mapv(|g| g.powi(2));
            let mut order: Vec<usize> = (0..self.config.total_iot_devices).collect();
            order.sort_by(|&a, &b| gains[b].partial_cmp(&gains[a]).unwrap());

            // Garantir ordem decrescente de potência (SIC viável)
            for idx in 1..order.len().min(self.config.max_devices_per_sc) {
                let higher = order[idx - 1];
                let lower = order[idx];
                let max_lower_power = proj[[higher, n]] - self.config.power_gap_sic / gains[higher];
                if proj[[lower, n]] > max_lower_power.max(0.0) {
                    proj[[lower, n]] = max_lower_power.max(0.0);
                }
            }

            // Zerar potência para dispositivos além do máximo por subcanal
            if order.len() > self.config.max_devices_per_sc {
                for &idx in &order[self.config.max_devices_per_sc..] {
                    proj[[idx, n]] = 0.0;
                }
            }
        }

        // Projeção no simplex de potência total
        let total: f64 = proj.sum();
        if total > self.config.max_power_sink {
            proj *= self.config.max_power_sink / total;
        }

        proj.mapv(|v| v.max(0.0))
    }
}

/// Otimizador MOGA para alocação de potência NOMA
pub struct MOGAOptimizer<'a> {
    manifold: &'a NOMAManifold,
    pop_size: usize,
    generations: usize,
    crossover_rate: f64,
    mutation_rate: f64,
}

impl<'a> MOGAOptimizer<'a> {
    pub fn new(manifold: &'a NOMAManifold) -> Self {
        Self {
            manifold,
            pop_size: 50,
            generations: 150,
            crossover_rate: 0.9,
            mutation_rate: 0.1,
        }
    }

    /// Executar otimização e retornar melhor solução
    pub fn optimize(&mut self) -> (Array2<f64>, (f64, f64, usize)) {
        let mut rng = rand::thread_rng();
        let init_power = self.manifold.config.max_power_sink /
                        (self.manifold.config.total_iot_devices * 2) as f64;

        // Inicializar população
        let mut pop: Vec<Array2<f64>> = (0..self.pop_size)
            .map(|_| {
                Array2::from_shape_fn(
                    (self.manifold.config.total_iot_devices, self.manifold.config.sub_channels),
                    |_| rng.gen_range(0.0..init_power),
                )
            })
            .collect();

        let mut best_solution = None;
        let mut best_fitness = (f64::INFINITY, 0.0, usize::MAX);

        for gen in 0..self.generations {
            // Avaliar fitness com projeção geométrica
            for individual in &mut pop {
                *individual = self.manifold.geometric_projection(individual);
            }

            let fitness_scores: Vec<_> = pop.iter()
                .map(|p| self.manifold.fitness(p))
                .collect();

            // Atualizar melhor solução (minimizar violações primeiro)
            for (i, &fs) in fitness_scores.iter().enumerate() {
                if fs.2 < best_fitness.2 || (fs.2 == best_fitness.2 && fs.0 < best_fitness.0) {
                    best_fitness = fs;
                    best_solution = Some(pop[i].clone());
                }
            }

            // Seleção por ranking não-dominado (simplificado)
            let mut new_pop = Vec::with_capacity(self.pop_size);
            let mut indices: Vec<usize> = (0..self.pop_size).collect();
            indices.sort_by(|&a, &b| {
                let (fa, fb) = (fitness_scores[a], fitness_scores[b]);
                // Dominância: menor potência, maior taxa, menos violações
                if fa.2 < fb.2 || (fa.2 == fb.2 && fa.0 < fb.0) ||
                   (fa.2 == fb.2 && fa.0 == fb.0 && fa.1 > fb.1) {
                    std::cmp::Ordering::Less
                } else {
                    std::cmp::Ordering::Greater
                }
            });

            // Preencher nova população com melhores
            for &idx in indices.iter().take(self.pop_size) {
                new_pop.push(pop[idx].clone());
            }

            // Crossover BLX-alpha
            if self.crossover_rate > 0.0 {
                for i in (0..new_pop.len() - 1).step_by(2) {
                    if rng.gen::<f64>() < self.crossover_rate {
                        let alpha = 0.5;
                        let (p1, p2) = (&new_pop[i], &new_pop[i + 1]);

                        let child1 = p1.zip(p2).mapv(|(a, b)| {
                            let low = a.min(b) - alpha * (a - b).abs();
                            let high = a.max(b) + alpha * (a - b).abs();
                            rng.gen_range(low..high)
                        });
                        let child2 = p1.zip(p2).mapv(|(a, b)| {
                            let low = a.min(b) - alpha * (a - b).abs();
                            let high = a.max(b) + alpha * (a - b).abs();
                            rng.gen_range(low..high)
                        });

                        new_pop[i] = child1;
                        new_pop[i + 1] = child2;
                    }
                }
            }

            // Mutação Gaussiana
            if self.mutation_rate > 0.0 {
                let mutation_scale = 0.1 * (1.0 - gen as f64 / self.generations as f64);
                for individual in &mut new_pop {
                    if rng.gen::<f64>() < self.mutation_rate {
                        for val in individual.iter_mut() {
                            *val += rng.gen::<f64>() * mutation_scale;
                        }
                    }
                }
            }

            pop = new_pop;
        }

        (best_solution.unwrap_or_default(), best_fitness)
    }

    /// Versão WASM-friendly da otimização
    #[cfg(target_arch = "wasm32")]
    pub fn optimize_wasm(&mut self, channels_json: &str) -> (Vec<Vec<f64>>, (f64, f64, usize)) {
        // Parse channels do JSON
        let channels: Vec<Vec<f64>> = serde_json::from_str(channels_json)
            .expect("Failed to parse channels JSON");

        // Recriar manifold com canais fornecidos
        let channels_nd = Array2::from_shape_vec(
            (self.manifold.config.total_iot_devices, self.manifold.config.sub_channels),
            channels.into_iter().flatten().collect(),
        ).expect("Invalid channels shape");

        let mut manifold = NOMAManifold::with_channels(
            self.manifold.config.clone(),
            channels_nd,
        );

        // Executar otimização
        self.manifold = &mut manifold;
        let (power_matrix, fitness) = self.optimize();

        // Converter para Vec<Vec<f64>> para retorno WASM
        let power_vec: Vec<Vec<f64>> = power_matrix
            .outer_iter()
            .map(|row| row.to_vec())
            .collect();

        (power_vec, fitness)
    }
}
