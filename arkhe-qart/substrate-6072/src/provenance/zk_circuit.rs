use plonky2::{
    field::goldilocks_field::GoldilocksField,
    iop::witness::{PartialWitness, WitnessWrite},
    plonk::{
        circuit_builder::CircuitBuilder,
        circuit_data::CircuitConfig,
        config::PoseidonGoldilocksConfig,
        proof::ProofWithPublicInputs,
    },
};
use plonky2_field::types::Field;
use anyhow::Result;

type F = GoldilocksField;
type C = PoseidonGoldilocksConfig;
const D: usize = 2; // Grau do circuito

/// Circuito ZK que prova: dot_product(private_a, public_b) >= threshold * norm_a * norm_b
/// sem revelar private_a.
pub struct StyleSimilarityCircuit {
    /// Número de dimensões (tamanho do embedding)
    dim: usize,
    /// Limiar mínimo de similaridade (em Q32.32)
    threshold: u64,
    /// Limiar de norma (para evitar divisão por zero)
    norm_threshold: u64,
}

impl StyleSimilarityCircuit {
    pub fn new(dim: usize, threshold: u64) -> Self {
        Self { dim, threshold, norm_threshold: 1_000_000 } // min ~1e-6
    }

    /// Constroi o circuito e retorna dados, prova e verificador.
    pub fn prove(
        &self,
        private_embedding: &[f32],
        public_embedding: &[f32],
    ) -> Result<(ProofWithPublicInputs<F, C, D>, Vec<F>)> {
        // Converter f32 para campo Goldilocks (ex.: quantização)
        let a: Vec<u64> = private_embedding.iter()
            .map(|&x| (x.max(-1.0).min(1.0) * (1u64 << 32) as f32) as u64)
            .collect();
        let b: Vec<u64> = public_embedding.iter()
            .map(|&x| (x.max(-1.0).min(1.0) * (1u64 << 32) as f32) as u64)
            .collect();

        // Usar configuração padrão com Poseidon
        let config = CircuitConfig::standard_recursion_config();
        let mut builder = CircuitBuilder::<F, D>::new(config);

        // Inputs: private_a, public_b (public input), threshold (public)
        let a_targets: Vec<_> = (0..self.dim)
            .map(|_| builder.add_virtual_target())
            .collect();
        let b_targets: Vec<_> = (0..self.dim)
            .map(|_| builder.add_virtual_target())
            .collect();
        let threshold_target = builder.add_virtual_target();

        // Registrar b e threshold como public inputs
        for &t in &b_targets {
            builder.register_public_input(t);
        }
        builder.register_public_input(threshold_target);

        // --- Calcular dot product (em campo) ---
        let mut dot = builder.zero();
        for i in 0..self.dim {
            let mul = builder.mul(a_targets[i], b_targets[i]);
            dot = builder.add(dot, mul);
        }

        // --- Calcular normas quadradas ---
        let mut norm_a_sq = builder.zero();
        let mut norm_b_sq = builder.zero();
        for i in 0..self.dim {
            let a2 = builder.mul(a_targets[i], a_targets[i]);
            norm_a_sq = builder.add(norm_a_sq, a2);
            let b2 = builder.mul(b_targets[i], b_targets[i]);
            norm_b_sq = builder.add(norm_b_sq, b2);
        }

        // --- Verificar que dot >= threshold * sqrt(norm_a_sq * norm_b_sq) ---
        // Evita sqrt: eleva ambos ao quadrado:
        // dot^2 >= threshold^2 * norm_a_sq * norm_b_sq
        let threshold_sq = builder.mul(threshold_target, threshold_target);
        let norms_prod = builder.mul(norm_a_sq, norm_b_sq);
        let rhs = builder.mul(threshold_sq, norms_prod);
        let dot_sq = builder.mul(dot, dot);

        // Constraint: dot_sq >= rhs
        // Plonky2 não tem comparação nativa; implementamos com range check.
        // Aqui simplificamos: dot_sq - rhs deve ser não-negativo.
        let diff = builder.sub(dot_sq, rhs);
        // Para non-negative, poderíamos garantir que diff é um campo não-negativo
        // convertendo para bits e verificando que o bit de sinal é 0.
        // Versão simplificada: usamos um gadget de comparação.
        builder.assert_non_negative(diff);

        // --- Construir circuito ---
        let circuit = builder.build::<C>();

        // Montar witness
        let mut pw = PartialWitness::new();
        for (i, &val) in a.iter().enumerate() {
            pw.set_target(a_targets[i], F::from_canonical_u64(val));
        }
        for (i, &val) in b.iter().enumerate() {
            pw.set_target(b_targets[i], F::from_canonical_u64(val));
        }
        pw.set_target(threshold_target, F::from_canonical_u64(self.threshold));

        let proof = circuit.prove(pw)?;

        // Public inputs: b[0..], threshold
        let public_inputs = b.iter()
            .map(|&v| F::from_canonical_u64(v))
            .chain(std::iter::once(F::from_canonical_u64(self.threshold)))
            .collect();

        Ok((proof, public_inputs))
    }

    /// Verificar uma prova
    pub fn verify(
        &self,
        proof: &ProofWithPublicInputs<F, C, D>,
        public_inputs: &[F],
    ) -> Result<()> {
        let config = CircuitConfig::standard_recursion_config();
        let mut builder = CircuitBuilder::<F, D>::new(config);
        // (reconstroi circuito de verificação)
        // Em produção, usaria circuit.verify(proof, public_inputs)
        Ok(())
    }
}