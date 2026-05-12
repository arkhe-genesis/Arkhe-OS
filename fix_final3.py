with open('substrate-6070/src/lib.rs') as f:
    lines = f.readlines()

new_lines = []
skip = False
for i, line in enumerate(lines):
    if line.startswith('use plonky2::field::types::Field;') and i > 100:
        continue
    if line.startswith('use plonky2::field::goldilocks_field::GoldilocksField;') and i > 100:
        continue
    if line.startswith('use plonky2::plonk::circuit_builder::CircuitBuilder;') and i > 100:
        continue
    if line.startswith('use plonky2::plonk::config::{GenericConfig, PoseidonGoldilocksConfig};') and i > 100:
        continue
    if line.startswith('use plonky2::plonk::circuit_data::CircuitConfig;') and i > 100:
        continue
    if line.startswith('const D: usize = 2;') and i > 100:
        continue
    if line.startswith('type C = PoseidonGoldilocksConfig;') and i > 100:
        continue
    if line.startswith('type F = <C as GenericConfig<D>>::F;') and i > 100:
        continue
    if line.startswith('pub fn shannon_entropy(data: &[u8]) -> f64 {') and i > 100:
        skip = True

    if not skip:
        new_lines.append(line)

    if skip and line == '}\n':
        skip = False


with open('substrate-6070/src/lib.rs', 'w') as f:
    f.writelines(new_lines)
