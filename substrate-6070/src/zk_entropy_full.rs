use plonky2::field::goldilocks_field::GoldilocksField;
use plonky2::field::types::Field;
use plonky2::hash::poseidon::PoseidonHash;
use plonky2::iop::target::{Target, BoolTarget};
use plonky2::plonk::circuit_builder::CircuitBuilder;
use plonky2::plonk::circuit_data::CircuitConfig;
use plonky2::plonk::config::PoseidonGoldilocksConfig;

type F = GoldilocksField;
const D: usize = 2;
type C = PoseidonGoldilocksConfig;

pub const SCALE: u64 = 65536;
pub const LOG2_COEFFS: [f64; 7] = [
    -4.028482109522e+00,
     1.213292205156e+01,
    -2.106039992068e+01,
     2.575715966421e+01,
    -1.975408752124e+01,
     8.542253771545e+00,
    -1.589369531462e+00,
];

fn coeffs_fixed() -> [i64; 7] {
    let mut arr = [0i64; 7];
    for (i, &c) in LOG2_COEFFS.iter().enumerate() {
        arr[i] = (c * SCALE as f64).round() as i64;
    }
    arr
}

#[derive(Clone)]
pub struct EntropyFullCircuit {
    pub data: Vec<u8>,
    pub counts: [u64; 256],
    pub length: u64,
    pub delta_fp: u64,
}

impl EntropyFullCircuit {
    pub fn build() -> (plonky2::plonk::circuit_data::CircuitData<F, C, D>, Vec<Target>) {
        let config = CircuitConfig::standard_recursion_config();
        let mut builder = CircuitBuilder::<F, D>::new(config);

        let commitment_pis: Vec<Target> = (0..4)
            .map(|_| builder.add_virtual_public_input())
            .collect();
        let delta_target = builder.add_virtual_public_input();

        let data_targets: Vec<Target> = (0..256)
            .map(|_| builder.add_virtual_target())
            .collect();

        let hash_out = builder.hash_n_to_hash_no_pad::<PoseidonHash>(data_targets.clone());
        for i in 0..4 {
            builder.connect(hash_out.elements[i], commitment_pis[i]);
        }

        let zero = builder.zero();
        let mut counts_computed = vec![zero; 256];
        for k in 0..256 {
            let mut sum = builder.zero();
            for &byte_target in &data_targets {
                let k_field = builder.constant(F::from_canonical_u8(k as u8));
                let is_equal = builder.is_equal(byte_target, k_field);
                let incr = is_equal.target;
                sum = builder.add(sum, incr);
            }
            counts_computed[k] = sum;
        }

        let mut total_target = builder.zero();
        for &c in &counts_computed {
            total_target = builder.add(total_target, c);
        }

        let mut h_target = builder.zero();
        let scale_target = builder.constant(F::from_canonical_u64(SCALE));
        let zero_target = builder.zero();
        let mut unique_target = zero_target;

        for &c in &counts_computed {
            let zero_c = builder.zero();
            let is_zero = builder.is_equal(c, zero_c);
            let c_nonzero = builder.not(is_zero);

            let const_1 = builder.constant(F::from_canonical_u64(1));
            let safe_total = builder.add(total_target, const_1);
            let actual_total = builder.select(c_nonzero, total_target, safe_total);
            let p_mul = builder.mul(c, scale_target);
            let p_fp = builder.div(p_mul, actual_total);

            let log2_p_fp = apply_log2_polynomial(&mut builder, p_fp, c_nonzero);
            let contrib = builder.mul(p_fp, log2_p_fp);
            let z_contrib = builder.zero();
            let actual_contrib = builder.select(c_nonzero, contrib, z_contrib);
            h_target = builder.sub(h_target, actual_contrib);

            let unique_incr = c_nonzero.target;
            unique_target = builder.add(unique_target, unique_incr);
        }

        let log2_u_target = log2_unique_lookup(&mut builder, unique_target);

        let zero_c2 = builder.zero();
        let is_zero_u = builder.is_equal(log2_u_target, zero_c2);
        let u_gt_one = builder.not(is_zero_u);

        let const_1_u = builder.constant(F::from_canonical_u64(1));
        let safe_log2_u = builder.add(log2_u_target, const_1_u);
        let actual_log2_u = builder.select(u_gt_one, log2_u_target, safe_log2_u);
        let h_norm_fp = builder.div(h_target, actual_log2_u);
        let z_norm = builder.zero();
        let final_h_norm = builder.select(u_gt_one, h_norm_fp, z_norm);

        let full_scale_field = builder.constant(F::from_canonical_u64(SCALE));
        let upper_bound = builder.sub(full_scale_field, delta_target);

        // Simple range checks
        let diff_low = builder.sub(final_h_norm, delta_target);
        let _bits_low = builder.split_le(diff_low, 16);

        let diff_high = builder.sub(upper_bound, final_h_norm);
        let _bits_high = builder.split_le(diff_high, 17);

        let circuit_data = builder.build::<C>();

        let mut pub_targets = Vec::new();
        pub_targets.extend(commitment_pis.clone());
        pub_targets.push(delta_target);

        (circuit_data, pub_targets)
    }
}

fn apply_log2_polynomial(
    builder: &mut CircuitBuilder<F, D>,
    x_fp: Target,
    _valid: BoolTarget,
) -> Target {
    let coeffs = coeffs_fixed();
    let mut acc = builder.constant(F::from_canonical_u64(coeffs[6].unsigned_abs()));
    if coeffs[6] < 0 {
        acc = builder.neg(acc);
    }

    for i in (0..6).rev() {
        let prod = builder.mul(acc, x_fp);
        let scale_const = builder.constant(F::from_canonical_u64(SCALE));
        let prod_scaled = builder.div(prod, scale_const);
        let c = builder.constant(F::from_canonical_u64(coeffs[i].unsigned_abs()));

        if coeffs[i] < 0 {
            acc = builder.sub(prod_scaled, c);
        } else {
            acc = builder.add(prod_scaled, c);
        }
    }
    acc
}

fn log2_unique_lookup(builder: &mut CircuitBuilder<F, D>, u_target: Target) -> Target {
    let mut result = builder.zero();
    for val in 1..=256u32 {
        let log2_fp = ( (val as f64).log2() * SCALE as f64 ).round() as u64;
        let val_field = builder.constant(F::from_canonical_u64(val as u64));
        let is_match = builder.is_equal(u_target, val_field);

        let val_const = builder.constant(F::from_canonical_u64(log2_fp));
        result = builder.select(is_match, val_const, result);
    }
    result
}
