#[cfg(feature = "plonky2")]
use plonky2::field::extension::Extendable;
#[cfg(feature = "plonky2")]
use plonky2::hash::hash_types::RichField;
#[cfg(feature = "plonky2")]
use plonky2::iop::target::Target;
#[cfg(feature = "plonky2")]
use plonky2::plonk::circuit_builder::CircuitBuilder;

#[cfg(feature = "plonky2")]
pub fn build_wassenaar_circuit<F: RichField + Extendable<D>, const D: usize>(
    builder: &mut CircuitBuilder<F, D>,
    qubit_count_target: Target,
    qubit_threshold: Target,
) {
    let below_threshold = builder.sub(qubit_threshold, qubit_count_target);
    // In a real implementation we would assert `below_threshold > 0` or use `is_less_than`.
    // But for this stub we just assume it exists.
    let _ = below_threshold;
}
